<template>
  <div class="account-management">
    <div class="page-header">
      <div class="header-info">
        <h1>Quản lý tài khoản</h1>
        <p class="subtitle">Quản lý các tài khoản mạng xã hội & trạng thái Cookie đăng nhập</p>
      </div>
      <div class="header-actions">
        <el-button type="primary" size="large" icon="Plus" @click="handleAddAccount">
          + Thêm tài khoản
        </el-button>
        <el-button type="default" size="large" @click="fetchAccounts" :loading="appStore.isAccountRefreshing">
          <el-icon :class="{ 'is-loading': appStore.isAccountRefreshing }"><Refresh /></el-icon>
          <span>Làm mới</span>
        </el-button>
      </div>
    </div>
    
    <div class="account-container">
      <div class="toolbar-wrapper">
        <el-tabs v-model="activeTab" class="account-tabs-nav">
          <el-tab-pane label="Tất cả" name="all" />
          <el-tab-pane label="Facebook" name="facebook" />
          <el-tab-pane label="Instagram" name="instagram" />
          <el-tab-pane label="TikTok" name="tiktok" />
          <el-tab-pane label="YouTube" name="youtube" />
          <el-tab-pane label="Threads" name="threads" />
          <el-tab-pane label="Twitter / X" name="twitter" />
          <el-tab-pane label="Pinterest" name="pinterest" />
          <el-tab-pane label="Zalo" name="zalo" />
        </el-tabs>

        <div class="search-wrap">
          <el-input
            v-model="searchKeyword"
            placeholder="Tìm theo tên hoặc nền tảng..."
            prefix-icon="Search"
            clearable
            @clear="handleSearch"
            @input="handleSearch"
          />
        </div>
      </div>

      <div class="table-card">
        <el-table :data="displayedAccounts" style="width: 100%" v-loading="appStore.isAccountRefreshing">
          <el-table-column label="Avatar" width="80" align="center">
            <template #default="scope">
              <el-avatar :src="getDefaultAvatar(scope.row.name)" :size="40" />
            </template>
          </el-table-column>
          <el-table-column prop="name" label="Tên tài khoản" width="220" />
          <el-table-column prop="platform" label="Nền tảng" width="180">
            <template #default="scope">
              <el-tag :type="getPlatformTagType(scope.row.platform)" effect="plain">
                {{ getPlatformDisplayName(scope.row.platform) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="status" label="Trạng thái" width="180">
            <template #default="scope">
              <el-tag
                :type="getStatusTagType(scope.row.status)"
                effect="plain"
                :class="{'clickable-status': isStatusClickable(scope.row.status)}"
                @click="handleStatusClick(scope.row)"
              >
                <el-icon class="is-loading" v-if="scope.row.status === '验证中' || scope.row.status === 'Đang xác thực'">
                  <Loading />
                </el-icon>
                {{ getStatusDisplayName(scope.row.status) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="Thao tác" min-width="260">
            <template #default="scope">
              <el-button size="small" @click="handleEdit(scope.row)">Sửa</el-button>
              <el-button size="small" type="primary" :icon="Download" @click="handleDownloadCookie(scope.row)">Tải Cookie</el-button>
              <el-button size="small" type="info" :icon="Upload" @click="handleUploadCookie(scope.row)">Nhập Cookie</el-button>
              <el-button size="small" type="danger" @click="handleDelete(scope.row)">Xóa</el-button>
            </template>
          </el-table-column>
        </el-table>

        <div v-if="displayedAccounts.length === 0 && !appStore.isAccountRefreshing" class="empty-data">
          <el-empty description="Chưa có tài khoản nào">
            <el-button type="primary" size="large" @click="handleAddAccount">+ Thêm tài khoản ngay</el-button>
          </el-empty>
        </div>
      </div>
    </div>
    
    <!-- Hộp thoại Thêm/Sửa tài khoản -->
    <el-dialog
      v-model="dialogVisible"
      :title="dialogType === 'add' ? 'Thêm tài khoản mới' : 'Chỉnh sửa tài khoản'"
      width="520px"
      :close-on-click-modal="false"
      :close-on-press-escape="!sseConnecting"
      :show-close="!sseConnecting"
    >
      <el-form :model="accountForm" label-width="120px" :rules="rules" ref="accountFormRef">
        <el-form-item label="Nền tảng" prop="platform">
          <el-select 
            v-model="accountForm.platform" 
            placeholder="Chọn nền tảng" 
            style="width: 100%"
            :disabled="dialogType === 'edit' || sseConnecting"
          >
            <el-option label="Facebook (Reels & Fanpage)" value="Facebook" />
            <el-option label="Instagram (Reels & Post)" value="Instagram" />
            <el-option label="TikTok Quốc tế" value="TikTok" />
            <el-option label="YouTube Studio" value="YouTube" />
            <el-option label="Threads (Meta)" value="Threads" />
            <el-option label="Twitter / X" value="Twitter" />
            <el-option label="Pinterest" value="Pinterest" />
            <el-option label="Zalo Video / OA" value="Zalo" />
          </el-select>
        </el-form-item>
        <el-form-item label="Tên tài khoản" prop="name">
          <el-input 
            v-model="accountForm.name" 
            placeholder="Nhập tên định danh tài khoản" 
            :disabled="sseConnecting"
          />
        </el-form-item>
        
        <el-form-item label="Phương thức" prop="loginMethod" v-if="dialogType === 'add'">
          <el-radio-group v-model="accountForm.loginMethod" :disabled="sseConnecting">
            <el-radio label="browser">Mở trình duyệt đăng nhập</el-radio>
            <el-radio label="manual">Tạo nhanh hồ sơ</el-radio>
          </el-radio-group>
        </el-form-item>

        <!-- Vùng hiển thị mã QR / thông báo đăng nhập -->
        <div v-if="sseConnecting" class="qrcode-container">
          <div v-if="qrCodeData && !loginStatus" class="qrcode-wrapper">
            <p class="qrcode-tip">Dùng App trên điện thoại quét mã QR để đăng nhập</p>
            <img :src="qrCodeData" alt="Mã QR đăng nhập" class="qrcode-image" />
          </div>
          <div v-else-if="!qrCodeData && !loginStatus" class="loading-wrapper">
            <el-icon class="is-loading"><Refresh /></el-icon>
            <span>Đang mở trình duyệt kết nối...</span>
          </div>
          <div v-else-if="loginStatus === '200'" class="success-wrapper">
            <el-icon><CircleCheckFilled /></el-icon>
            <span>Thêm tài khoản thành công!</span>
          </div>
          <div v-else-if="loginStatus === '500'" class="error-wrapper">
            <el-icon><CircleCloseFilled /></el-icon>
            <span>Thêm thất bại, vui lòng thử lại</span>
          </div>
        </div>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="dialogVisible = false">Hủy</el-button>
          <el-button 
            type="primary" 
            @click="submitAccountForm" 
            :loading="sseConnecting" 
            :disabled="sseConnecting"
          >
            {{ sseConnecting ? 'Đang xử lý...' : 'Xác nhận' }}
          </el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, onBeforeUnmount } from 'vue'
import { Refresh, CircleCheckFilled, CircleCloseFilled, Download, Upload, Loading } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { accountApi } from '@/api/account'
import { useAccountStore } from '@/stores/account'
import { useAppStore } from '@/stores/app'
import { http } from '@/utils/request'

// 获取账号状态管理
const accountStore = useAccountStore()
// 获取应用状态管理
const appStore = useAppStore()

// 当前激活的标签页
const activeTab = ref('all')

// 搜索关键词
const searchKeyword = ref('')

// 获取账号数据（快速，不验证）
const fetchAccountsQuick = async () => {
  try {
    const res = await accountApi.getAccounts()
    if (res.code === 200 && res.data) {
      // 将所有账号的状态暂时设为"验证中"
      const accountsWithPendingStatus = res.data.map(account => {
        const updatedAccount = [...account];
        updatedAccount[4] = -1; // -1 表示验证中的临时状态
        return updatedAccount;
      });
      accountStore.setAccounts(accountsWithPendingStatus);
    }
  } catch (error) {
    console.error('快速获取账号数据失败:', error)
  }
}

// 获取账号数据（带验证）
const fetchAccounts = async () => {
  if (appStore.isAccountRefreshing) return

  appStore.setAccountRefreshing(true)

  try {
    const res = await accountApi.getValidAccounts()
    if (res.code === 200 && res.data) {
      accountStore.setAccounts(res.data)
      ElMessage.success('Lấy dữ liệu tài khoản thành công')
      // 标记为已访问
      if (appStore.isFirstTimeAccountManagement) {
        appStore.setAccountManagementVisited()
      }
    } else {
      ElMessage.error('Lấy dữ liệu tài khoản thất bại')
    }
  } catch (error) {
    console.error('Lấy dữ liệu tài khoản thất bại:', error)
    ElMessage.error('Lấy dữ liệu tài khoản thất bại')
  } finally {
    appStore.setAccountRefreshing(false)
  }
}

// 后台验证所有账号（优化版本，使用setTimeout避免阻塞UI）
const validateAllAccountsInBackground = async () => {
  // 使用setTimeout将验证过程放在下一个事件循环，避免阻塞UI
  setTimeout(async () => {
    try {
      const res = await accountApi.getValidAccounts()
      if (res.code === 200 && res.data) {
        accountStore.setAccounts(res.data)
      }
    } catch (error) {
      console.error('后台验证账号失败:', error)
    }
  }, 0)
}

// 页面加载时获取账号数据
onMounted(() => {
  // 快速获取账号列表（不验证），立即显示
  fetchAccountsQuick()

  // 在后台验证所有账号
  setTimeout(() => {
    validateAllAccountsInBackground()
  }, 100) // 稍微延迟一下，让用户看到快速加载的效果
})

// 获取平台显示名称
const getPlatformDisplayName = (platform) => {
  const map = {
    'Facebook': 'Facebook (Meta)',
    'Instagram': 'Instagram (Reels)',
    'Twitter': 'Twitter / X',
    'Threads': 'Threads (Meta)',
    'Pinterest': 'Pinterest',
    'Zalo': 'Zalo Video / OA',
    'YouTube': 'YouTube Studio',
    'TikTok': 'TikTok Quốc tế'
  }
  return map[platform] || platform
}

// 获取状态显示名称
const getStatusDisplayName = (status) => {
  const map = {
    '正常': 'Hoạt động',
    'Hoạt động': 'Hoạt động',
    '异常': 'Chưa có Cookie',
    'Chưa có Cookie': 'Chưa có Cookie',
    '验证中': 'Đang xác thực',
    'Đang xác thực': 'Đang xác thực'
  }
  return map[status] || status
}

// 获取平台标签类型
const getPlatformTagType = (platform) => {
  const typeMap = {
    'Facebook': 'primary',
    'Instagram': 'danger',
    'Twitter': 'info',
    'Threads': 'success',
    'Pinterest': 'danger',
    'Zalo': 'primary',
    'YouTube': 'danger',
    'TikTok': 'success'
  }
  return typeMap[platform] || 'primary'
}

// 判断状态是否可点击
const isStatusClickable = (status) => {
  return status === 'Chưa có Cookie' || status === '异常' || status === 'Lỗi / Cần đăng nhập lại';
}

// 获取状态标签类型
const getStatusTagType = (status) => {
  if (status === '验证中' || status === 'Đang xác thực') {
    return 'info';
  } else if (status === '正常' || status === 'Hoạt động') {
    return 'success';
  } else {
    return 'warning';
  }
}

// 处理状态点击事件
const handleStatusClick = (row) => {
  if (isStatusClickable(row.status)) {
    handleEdit(row)
  }
}

// 过滤后的账号列表 (Theo tab và từ khóa tìm kiếm)
const displayedAccounts = computed(() => {
  let list = accountStore.accounts || []
  if (activeTab.value && activeTab.value !== 'all') {
    list = list.filter(account => account.platform?.toLowerCase().includes(activeTab.value.toLowerCase()))
  }
  if (searchKeyword.value && searchKeyword.value.trim()) {
    const kw = searchKeyword.value.trim().toLowerCase()
    list = list.filter(account =>
      (account.name && account.name.toLowerCase().includes(kw)) ||
      (account.platform && account.platform.toLowerCase().includes(kw))
    )
  }
  return list
})

// 搜索处理
const handleSearch = () => {
  // 搜索逻辑已通过计算属性实现
}

// 对话框相关
const dialogVisible = ref(false)
const dialogType = ref('add') // 'add' 或 'edit'
const accountFormRef = ref(null)

// 账号表单
const accountForm = reactive({
  id: null,
  name: '',
  platform: '',
  loginMethod: 'browser',
  status: '正常'
})

// 表单验证规则
const rules = {
  platform: [{ required: true, message: 'Vui lòng chọn nền tảng', trigger: 'change' }],
  name: [{ required: true, message: 'Vui lòng nhập tên tài khoản', trigger: 'blur' }]
}

// SSE连接状态
const sseConnecting = ref(false)
const qrCodeData = ref('')
const loginStatus = ref('')

// 添加账号
const handleAddAccount = () => {
  dialogType.value = 'add'
  Object.assign(accountForm, {
    id: null,
    name: '',
    platform: '',
    status: '正常'
  })
  // 重置SSE状态
  sseConnecting.value = false
  qrCodeData.value = ''
  loginStatus.value = ''
  dialogVisible.value = true
}

// 编辑账号
const handleEdit = (row) => {
  dialogType.value = 'edit'
  Object.assign(accountForm, {
    id: row.id,
    name: row.name,
    platform: row.platform,
    status: row.status
  })
  dialogVisible.value = true
}

// 删除账号
const handleDelete = (row) => {
  ElMessageBox.confirm(
    `Bạn có chắc chắn muốn xóa tài khoản "${row.name}" không?`,
    'Cảnh báo',
    {
      confirmButtonText: 'Xác nhận xóa',
      cancelButtonText: 'Hủy',
      type: 'warning',
    }
  )
    .then(async () => {
      try {
        // 调用API删除账号
        const response = await accountApi.deleteAccount(row.id)

        if (response.code === 200) {
          // 从状态管理中删除账号
          accountStore.deleteAccount(row.id)
          ElMessage({
            type: 'success',
            message: 'Đã xóa tài khoản thành công',
          })
        } else {
          ElMessage.error(response.msg || 'Xóa tài khoản thất bại')
        }
      } catch (error) {
        console.error('删除账号失败:', error)
        ElMessage.error('Xóa tài khoản thất bại')
      }
    })
    .catch(() => {
      // 取消删除
    })
}

// 下载Cookie文件
const handleDownloadCookie = (row) => {
  // 从后端获取Cookie文件
  const baseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5409'
  const downloadUrl = `${baseUrl}/downloadCookie?filePath=${encodeURIComponent(row.filePath)}`

  // 创建一个隐藏的链接来触发下载
  const link = document.createElement('a')
  link.href = downloadUrl
  link.download = `${row.name}_cookie.json`
  link.target = '_blank'
  link.style.display = 'none'
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
}

// 上传Cookie文件
const handleUploadCookie = (row) => {
  // 创建一个隐藏的文件输入框
  const input = document.createElement('input')
  input.type = 'file'
  input.accept = '.json'
  input.style.display = 'none'
  document.body.appendChild(input)

  input.onchange = async (event) => {
    const file = event.target.files[0]
    if (!file) return

    // 检查文件类型
    if (!file.name.endsWith('.json')) {
      ElMessage.error('Vui lòng chọn tệp Cookie định dạng JSON (.json)')
      document.body.removeChild(input)
      return
    }

    try {
      // 创建FormData对象
      const formData = new FormData()
      formData.append('file', file)
      formData.append('id', row.id)
      formData.append('platform', row.platform)

      // 使用统一的http封装发送上传请求
      const result = await http.upload('/uploadCookie', formData)

      ElMessage.success('Tải lên tệp Cookie thành công!')
      // 刷新账号列表以显示更新
      fetchAccounts()
    } catch (error) {
      ElMessage.error('Tải lên tệp Cookie thất bại')
    } finally {
      document.body.removeChild(input)
    }
  }

  input.click()
}

// 获取默认头像
const getDefaultAvatar = (name) => {
  // 使用简单的默认头像，可以基于用户名生成不同的颜色
  return `https://ui-avatars.com/api/?name=${encodeURIComponent(name)}&background=random`
}

// SSE事件源对象
let eventSource = null

// 关闭SSE连接
const closeSSEConnection = () => {
  if (eventSource) {
    eventSource.close()
    eventSource = null
  }
}

// 建立SSE连接
const connectSSE = (platform, name) => {
  // 关闭可能存在的连接
  closeSSEConnection()

  // 设置连接状态
  sseConnecting.value = true
  qrCodeData.value = ''
  loginStatus.value = ''

  // 获取平台类型编号
  const platformTypeMap = {
    '小红书': '1',
    '视频号': '2',
    '抖音': '3',
    '快手': '4',
    'Facebook': '5',
    'Instagram': '6',
    'Twitter': '7',
    'Threads': '8',
    'Pinterest': '9',
    'Zalo': '10',
    'YouTube': '11',
    'TikTok': '12'
  }

  const type = platformTypeMap[platform] || '1'

  // 创建SSE连接
  const baseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5409'
  const url = `${baseUrl}/login?type=${type}&id=${encodeURIComponent(name)}`

  eventSource = new EventSource(url)

  // 监听消息
  eventSource.onmessage = (event) => {
    const data = event.data

    // 如果还没有二维码数据，且数据长度较长，认为是二维码
    if (!qrCodeData.value && data.length > 100) {
      try {
        if (data.startsWith('data:image')) {
          qrCodeData.value = data
        } else {
          qrCodeData.value = `data:image/png;base64,${data}`
        }
      } catch (error) {
        // 处理二维码数据出错
      }
    }
    // 如果收到状态码
    else if (data === '200' || data === '500') {
      loginStatus.value = data

      // 如果登录成功
      if (data === '200') {
        setTimeout(() => {
          // 关闭连接
          closeSSEConnection()

          // 1秒后关闭对话框并开始刷新
          setTimeout(() => {
            dialogVisible.value = false
            sseConnecting.value = false

            // 根据是否是重新登录显示不同提示
            ElMessage.success(dialogType.value === 'edit' ? 'Đăng nhập lại thành công' : 'Thêm tài khoản thành công')

            // 显示更新账号信息提示
            ElMessage({
              type: 'info',
              message: 'Đang đồng bộ thông tin tài khoản...',
              duration: 0
            })

            // 触发刷新操作
            fetchAccounts().then(() => {
              // 刷新完成后关闭提示
              ElMessage.closeAll()
              ElMessage.success('Đã cập nhật thông tin tài khoản')
            })
          }, 1000)
        }, 1000)
      } else {
        // 登录失败，关闭连接
        closeSSEConnection()

        // 2秒后重置状态，允许重试
        setTimeout(() => {
          sseConnecting.value = false
          qrCodeData.value = ''
          loginStatus.value = ''
        }, 2000)
      }
    }
  }

  // 监听错误
  eventSource.onerror = (error) => {
    console.error('SSE connection error:', error)
    ElMessage.error('Kết nối máy chủ thất bại, vui lòng thử lại sau')
    closeSSEConnection()
    sseConnecting.value = false
  }
}

// 提交账号表单
const submitAccountForm = () => {
  accountFormRef.value.validate(async (valid) => {
    if (valid) {
      // 将平台名称转换为类型数字
      const platformTypeMap = {
        '小红书': 1,
        '视频号': 2,
        '抖音': 3,
        '快手': 4,
        'Facebook': 5,
        'Instagram': 6,
        'Twitter': 7,
        'Threads': 8,
        'Pinterest': 9,
        'Zalo': 10,
        'YouTube': 11,
        'TikTok': 12
      };
      const type = platformTypeMap[accountForm.platform] || 1;

      if (dialogType.value === 'add') {
        if (accountForm.loginMethod === 'manual') {
          try {
            const res = await http.post('/addAccountManual', {
              name: accountForm.name,
              type: type
            })
            if (res.code === 200) {
              ElMessage.success('Thêm tài khoản thành công! Bạn có thể tải lên file Cookie ngay.')
              dialogVisible.value = false
              fetchAccounts()
            } else {
              ElMessage.error(res.msg || 'Thêm tài khoản thất bại')
            }
          } catch (error) {
            ElMessage.error('Lỗi khi thêm tài khoản')
          }
        } else {
          // 建立SSE连接 mở trình duyệt đăng nhập
          connectSSE(accountForm.platform, accountForm.name)
        }
      } else {
        // 编辑账号逻辑
        try {
          const res = await accountApi.updateAccount({
            id: accountForm.id,
            type: type,
            userName: accountForm.name
          })
          if (res.code === 200) {
            // 更新状态管理中的账号
            const updatedAccount = {
              id: accountForm.id,
              name: accountForm.name,
              platform: accountForm.platform,
              status: accountForm.status // Keep the existing status
            };
            accountStore.updateAccount(accountForm.id, updatedAccount)
            ElMessage.success('Cập nhật thành công')
            dialogVisible.value = false
            // 刷新账号列表
            fetchAccounts()
          } else {
            ElMessage.error(res.msg || 'Cập nhật tài khoản thất bại')
          }
        } catch (error) {
          console.error('Cập nhật tài khoản thất bại:', error)
          ElMessage.error('Cập nhật tài khoản thất bại')
        }
      }
    } else {
      return false
    }
  })
}

// 组件卸载前关闭SSE连接
onBeforeUnmount(() => {
  closeSSEConnection()
})
</script>

<style lang="scss" scoped>
@use '@/styles/variables.scss' as *;

@keyframes rotate {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

.account-management {
  .page-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 24px;
    padding-bottom: 16px;
    border-bottom: 1px solid #ebeef5;
    
    .header-info {
      h1 {
        font-size: 24px;
        font-weight: 600;
        color: $text-primary;
        margin: 0 0 6px 0;
      }
      .subtitle {
        font-size: 14px;
        color: $text-secondary;
        margin: 0;
      }
    }

    .header-actions {
      display: flex;
      gap: 12px;
      align-items: center;
    }
  }
  
  .account-container {
    background-color: #fff;
    border-radius: 8px;
    box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.05);
    padding: 20px;
    
    .toolbar-wrapper {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 20px;
      flex-wrap: wrap;
      gap: 16px;

      .account-tabs-nav {
        flex: 1;
        min-width: 320px;
        
        :deep(.el-tabs__header) {
          margin: 0;
        }
      }

      .search-wrap {
        width: 280px;
      }
    }

    .table-card {
      .empty-data {
        padding: 60px 0;
        text-align: center;
      }
    }
  }
  
  .clickable-status {
    cursor: pointer;
    transition: all 0.3s;

    &:hover {
      transform: scale(1.05);
      box-shadow: 0 0 8px rgba(0, 0, 0, 0.15);
    }
  }

  .qrcode-container {
    margin-top: 20px;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    min-height: 220px;
    background: #f8fafc;
    border-radius: 8px;
    padding: 16px;
    
    .qrcode-wrapper {
      text-align: center;
      
      .qrcode-tip {
        margin-bottom: 15px;
        color: #606266;
        font-size: 14px;
      }
      
      .qrcode-image {
        max-width: 180px;
        max-height: 180px;
        border: 1px solid #ebeef5;
        background-color: black;
      }
    }
    
    .loading-wrapper, .success-wrapper, .error-wrapper {
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      gap: 12px;
      
      .el-icon {
        font-size: 40px;
        
        &.is-loading {
          animation: rotate 1s linear infinite;
        }
      }
      
      span {
        font-size: 15px;
        font-weight: 500;
      }
    }
    
    .success-wrapper .el-icon {
      color: #67c23a;
    }
    
    .error-wrapper .el-icon {
      color: #f56c6c;
    }
  }
}
</style>