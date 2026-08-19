<template>
  <div class="publish-center">
    <!-- Tab quản lý các bài đăng -->
    <div class="tab-management">
      <div class="tab-header">
        <div class="tab-list">
          <div 
            v-for="tab in tabs" 
            :key="tab.name"
            :class="['tab-item', { active: activeTab === tab.name }]"
            @click="activeTab = tab.name"
          >
            <span>{{ tab.label }}</span>
            <el-icon 
              v-if="tabs.length > 1"
              class="close-icon" 
              @click.stop="removeTab(tab.name)"
            >
              <Close />
            </el-icon>
          </div>
        </div>
        <div class="tab-actions">
          <el-button 
            type="primary" 
            size="small" 
            @click="addTab"
            class="add-tab-btn"
          >
            <el-icon><Plus /></el-icon>
            Thêm Tab
          </el-button>
          <el-button 
            type="success" 
            size="small" 
            @click="batchPublish"
            :loading="batchPublishing"
            class="batch-publish-btn"
          >
            Đăng hàng loạt
          </el-button>
        </div>
      </div>
    </div>

    <!-- Vùng nội dung cấu hình đăng -->
    <div class="publish-content">
      <div class="tab-content-wrapper">
        <div 
          v-for="tab in tabs" 
          :key="tab.name"
          v-show="activeTab === tab.name"
          class="tab-content"
        >
          <!-- Trạng thái đăng -->
          <div v-if="tab.publishStatus" class="publish-status">
            <el-alert
              :title="tab.publishStatus.message"
              :type="tab.publishStatus.type"
              :closable="false"
              show-icon
            />
          </div>

          <!-- Khu vực tải lên Video -->
          <div class="upload-section">
            <h3>Video</h3>
            <div class="upload-options">
              <el-button type="primary" @click="showUploadOptions(tab)" class="upload-btn">
                <el-icon><Upload /></el-icon>
                Tải lên Video
              </el-button>
            </div>
            
            <!-- Danh sách tệp đã tải lên -->
            <div v-if="tab.fileList.length > 0" class="uploaded-files">
              <h4>Tệp đã chọn:</h4>
              <div class="file-list">
                <div v-for="(file, index) in tab.fileList" :key="index" class="file-item">
                  <el-link :href="file.url" target="_blank" type="primary">{{ file.name }}</el-link>
                  <span class="file-size">{{ (file.size / 1024 / 1024).toFixed(2) }}MB</span>
                  <el-button type="danger" size="small" @click="removeFile(tab, index)">Xóa</el-button>
                </div>
              </div>
            </div>
          </div>

          <!-- Dialog chọn nguồn tải lên -->
          <el-dialog
            v-model="uploadOptionsVisible"
            title="Chọn phương thức tải video"
            width="400px"
            class="upload-options-dialog"
          >
            <div class="upload-options-content">
              <el-button type="primary" @click="selectLocalUpload" class="option-btn">
                <el-icon><Upload /></el-icon>
                Tải từ máy tính
              </el-button>
              <el-button type="success" @click="selectMaterialLibrary" class="option-btn">
                <el-icon><Folder /></el-icon>
                Chọn từ Thư viện
              </el-button>
            </div>
          </el-dialog>

          <!-- Dialog tải từ máy tính -->
          <el-dialog
            v-model="localUploadVisible"
            title="Tải video từ máy tính"
            width="600px"
            class="local-upload-dialog"
          >
            <el-upload
              class="video-upload"
              drag
              :auto-upload="true"
              :action="`${apiBaseUrl}/upload`"
              :on-success="(response, file) => handleUploadSuccess(response, file, currentUploadTab)"
              :on-error="handleUploadError"
              multiple
              accept="video/*"
              :headers="authHeaders"
            >
              <el-icon class="el-icon--upload"><Upload /></el-icon>
              <div class="el-upload__text">
                Kéo thả video vào đây, hoặc <em>nhấn để tải lên</em>
              </div>
              <template #tip>
                <div class="el-upload__tip">
                  Hỗ trợ MP4, AVI, MOV... Có thể tải nhiều tệp cùng lúc
                </div>
              </template>
            </el-upload>
          </el-dialog>

          <!-- Dialog tiến trình đăng hàng loạt -->
          <el-dialog
            v-model="batchPublishDialogVisible"
            title="Tiến trình đăng hàng loạt"
            width="500px"
            :close-on-click-modal="false"
            :close-on-press-escape="false"
            :show-close="false"
          >
            <div class="publish-progress">
              <el-progress 
                :percentage="publishProgress"
                :status="publishProgress === 100 ? 'success' : ''"
              />
              <div v-if="currentPublishingTab" class="current-publishing">
                Đang xử lý: {{ currentPublishingTab.label }}
              </div>
              
              <!-- Kết quả đăng -->
              <div class="publish-results" v-if="publishResults.length > 0">
                <div 
                  v-for="(result, index) in publishResults" 
                  :key="index"
                  :class="['result-item', result.status]"
                >
                  <el-icon v-if="result.status === 'success'"><Check /></el-icon>
                  <el-icon v-else-if="result.status === 'error'"><Close /></el-icon>
                  <el-icon v-else><InfoFilled /></el-icon>
                  <span class="label">{{ result.label }}</span>
                  <span class="message">{{ result.message }}</span>
                </div>
              </div>
            </div>
            
            <template #footer>
              <div class="dialog-footer">
                <el-button 
                  @click="cancelBatchPublish" 
                  :disabled="publishProgress === 100"
                >
                  Hủy đăng
                </el-button>
                <el-button 
                  type="primary" 
                  @click="batchPublishDialogVisible = false"
                  v-if="publishProgress === 100"
                >
                  Đóng
                </el-button>
              </div>
            </template>
          </el-dialog>

          <!-- Dialog chọn từ Thư viện tư liệu -->
          <el-dialog
            v-model="materialLibraryVisible"
            title="Chọn video từ Thư viện tư liệu"
            width="800px"
            class="material-library-dialog"
          >
            <div class="material-library-content">
              <el-checkbox-group v-model="selectedMaterials">
                <div class="material-list">
                  <div
                    v-for="material in materials"
                    :key="material.id"
                    class="material-item"
                  >
                    <el-checkbox :label="material.id" class="material-checkbox">
                      <div class="material-info">
                        <div class="material-name">{{ material.filename }}</div>
                        <div class="material-details">
                          <span class="file-size">{{ material.filesize }}MB</span>
                          <span class="upload-time">{{ material.upload_time }}</span>
                        </div>
                      </div>
                    </el-checkbox>
                  </div>
                </div>
              </el-checkbox-group>
            </div>
            <template #footer>
              <div class="dialog-footer">
                <el-button @click="materialLibraryVisible = false">Hủy</el-button>
                <el-button type="primary" @click="confirmMaterialSelection">Xác nhận chọn</el-button>
              </div>
            </template>
          </el-dialog>

          <!-- Chọn Tài khoản -->
          <div class="account-section">
            <h3>Tài khoản đăng</h3>
            <div class="account-display">
              <div class="selected-accounts">
                <el-tag
                  v-for="(account, index) in tab.selectedAccounts"
                  :key="index"
                  closable
                  @close="removeAccount(tab, index)"
                  class="account-tag"
                >
                  {{ getAccountDisplayName(account) }}
                </el-tag>
              </div>
              <el-button 
                type="primary" 
                plain 
                @click="openAccountDialog(tab)"
                class="select-account-btn"
              >
                Chọn tài khoản
              </el-button>
            </div>
          </div>

          <!-- Dialog chọn tài khoản -->
          <el-dialog
            v-model="accountDialogVisible"
            title="Chọn tài khoản đăng"
            width="600px"
            class="account-dialog"
          >
            <div class="account-dialog-content">
              <el-checkbox-group v-model="tempSelectedAccounts">
                <div class="account-list">
                  <el-checkbox
                    v-for="account in availableAccounts"
                    :key="account.id"
                    :label="account.id"
                    class="account-item"
                  >
                    <div class="account-info">
                      <span class="account-name">{{ account.name }}</span>                      
                    </div>
                  </el-checkbox>
                </div>
              </el-checkbox-group>
            </div>

            <template #footer>
              <div class="dialog-footer">
                <el-button @click="accountDialogVisible = false">Hủy</el-button>
                <el-button type="primary" @click="confirmAccountSelection">Xác nhận</el-button>
              </div>
            </template>
          </el-dialog>

          <!-- Chọn Nền tảng -->
          <div class="platform-section">
            <h3>Nền tảng</h3>
            <el-radio-group v-model="tab.selectedPlatform" class="platform-radios">
              <el-radio 
                v-for="platform in platforms" 
                :key="platform.key"
                :label="platform.key"
                class="platform-radio"
              >
                {{ platform.name }}
              </el-radio>
            </el-radio-group>
          </div>

          <!-- Tuyên bố nội dung gốc -->
          <div class="original-section">
            <el-checkbox
              v-model="tab.isOriginal"
              label="Khai báo nội dung gốc (Original)"
              class="original-checkbox"
            />
          </div>

          <!-- Tùy chọn bản nháp WeChat -->
          <div v-if="tab.selectedPlatform === 2" class="draft-section">
            <el-checkbox
              v-model="tab.isDraft"
              label="Chỉ lưu bản nháp trên WeChat (để duyệt/đăng trên điện thoại)"
              class="draft-checkbox"
            />
          </div>

          <!-- Liên kết sản phẩm (TikTok / Douyin Shop) -->
          <div v-if="tab.selectedPlatform === 3" class="product-section">
            <h3>Liên kết sản phẩm Shop</h3>
            <el-input
              v-model="tab.productTitle"
              type="text"
              :rows="1"
              placeholder="Nhập tên sản phẩm"
              maxlength="200"
              class="product-name-input"
            />
            <el-input
              v-model="tab.productLink"
              type="text"
              :rows="1"
              placeholder="Nhập liên kết / link sản phẩm"
              maxlength="200"
              class="product-link-input"
            />
          </div>

          <!-- Nhập Tiêu đề -->
          <div class="title-section">
            <h3>Tiêu đề bài đăng</h3>
            <el-input
              v-model="tab.title"
              type="textarea"
              :rows="3"
              placeholder="Nhập tiêu đề và mô tả video..."
              maxlength="100"
              show-word-limit
              class="title-input"
            />
          </div>

          <!-- Nhập Thẻ Hashtag / Chủ đề -->
          <div class="topic-section">
            <h3>Chủ đề / Hashtag</h3>
            <div class="topic-display">
              <div class="selected-topics">
                <el-tag
                  v-for="(topic, index) in tab.selectedTopics"
                  :key="index"
                  closable
                  @close="removeTopic(tab, index)"
                  class="topic-tag"
                >
                  #{{ topic }}
                </el-tag>
              </div>
              <el-button 
                type="primary" 
                plain 
                @click="openTopicDialog(tab)"
                class="select-topic-btn"
              >
                Thêm Hashtag
              </el-button>
            </div>
          </div>

          <!-- Dialog thêm Hashtag -->
          <el-dialog
            v-model="topicDialogVisible"
            title="Thêm Hashtag / Chủ đề"
            width="600px"
            class="topic-dialog"
          >
            <div class="topic-dialog-content">
              <!-- Nhập Hashtag tùy chỉnh -->
              <div class="custom-topic-input">
                <el-input
                  v-model="customTopic"
                  placeholder="Nhập hashtag tùy chỉnh..."
                  class="custom-input"
                >
                  <template #prepend>#</template>
                </el-input>
                <el-button type="primary" @click="addCustomTopic">Thêm</el-button>
              </div>

              <!-- Gợi ý Hashtag -->
              <div class="recommended-topics">
                <h4>Gợi ý chủ đề phổ biến</h4>
                <div class="topic-grid">
                  <el-button
                    v-for="topic in recommendedTopics"
                    :key="topic"
                    :type="currentTab?.selectedTopics?.includes(topic) ? 'primary' : 'default'"
                    @click="toggleRecommendedTopic(topic)"
                    class="topic-btn"
                  >
                    {{ topic }}
                  </el-button>
                </div>
              </div>
            </div>

            <template #footer>
              <div class="dialog-footer">
                <el-button @click="topicDialogVisible = false">Hủy</el-button>
                <el-button type="primary" @click="confirmTopicSelection">Xong</el-button>
              </div>
            </template>
          </el-dialog>

          <!-- Hẹn giờ đăng bài -->
          <div class="schedule-section">
            <h3>Hẹn giờ đăng bài</h3>
            <div class="schedule-controls">
              <el-switch
                v-model="tab.scheduleEnabled"
                active-text="Hẹn giờ đăng"
                inactive-text="Đăng ngay"
              />
              <div v-if="tab.scheduleEnabled" class="schedule-settings">
                <div class="schedule-item">
                  <span class="label">Số lượng video mỗi ngày:</span>
                  <el-select v-model="tab.videosPerDay" placeholder="Chọn số lượng">
                    <el-option
                      v-for="num in 55"
                      :key="num"
                      :label="num"
                      :value="num"
                    />
                  </el-select>
                </div>
                <div class="schedule-item">
                  <span class="label">Khung giờ đăng mỗi ngày:</span>
                  <el-time-select
                    v-for="(time, index) in tab.dailyTimes"
                    :key="index"
                    v-model="tab.dailyTimes[index]"
                    start="00:00"
                    step="00:30"
                    end="23:30"
                    placeholder="Chọn giờ"
                  />
                  <el-button
                    v-if="tab.dailyTimes.length < tab.videosPerDay"
                    type="primary"
                    size="small"
                    @click="tab.dailyTimes.push('10:00')"
                  >
                    Thêm khung giờ
                  </el-button>
                </div>
                <div class="schedule-item">
                  <span class="label">Bắt đầu từ:</span>
                  <el-select v-model="tab.startDays" placeholder="Chọn ngày bắt đầu">
                    <el-option :label="'Ngày mai'" :value="0" />
                    <el-option :label="'Ngày kia'" :value="1" />
                  </el-select>
                </div>
              </div>
            </div>
          </div>

          <!-- Nút thao tác đăng -->
          <div class="action-buttons">
            <el-button size="small" @click="cancelPublish(tab)">Hủy</el-button>
            <el-button
              size="small"
              type="primary"
              @click="confirmPublish(tab)"
              :loading="tab.publishing || false"
            >
              {{ tab.publishing ? 'Đang đăng bài...' : 'Đăng bài' }}
            </el-button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed } from 'vue'
import { Upload, Plus, Close, Folder } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { useAccountStore } from '@/stores/account'
import { useAppStore } from '@/stores/app'
import { materialApi } from '@/api/material'
import { http } from '@/utils/request'

// API base URL
const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5409'

// Authorization headers
const authHeaders = computed(() => ({
  'Authorization': `Bearer ${localStorage.getItem('token') || ''}`
}))

// 当前激活的tab
const activeTab = ref('tab1')

// tab计数器
let tabCounter = 1

// 获取应用状态管理
const appStore = useAppStore()

// 上传相关状态
const uploadOptionsVisible = ref(false)
const localUploadVisible = ref(false)
const materialLibraryVisible = ref(false)
const currentUploadTab = ref(null)
const selectedMaterials = ref([])
const materials = computed(() => appStore.materials)

// 批量发布相关状态
const batchPublishing = ref(false)
const batchPublishMessage = ref('')
const batchPublishType = ref('info')

// 平台列表 - 对应后端type字段
const platforms = [
  { key: 3, name: 'Douyin (抖音)' },
  { key: 4, name: 'Kuaishou (快手)' },
  { key: 2, name: 'WeChat Channels (视频号)' },
  { key: 1, name: 'Xiaohongshu (小红书)' }
]

const defaultTabInit = {
  name: 'tab1',
  label: 'Bài đăng 1',
  fileList: [], // 后端返回的文件名列表
  displayFileList: [], // 用于显示的文件列表
  selectedAccounts: [], // 选中的账号ID列表
  selectedPlatform: 3, // 选中的平台（单选，mặc định Douyin）
  title: '',
  productLink: '', // 商品链接
  productTitle: '', // 商品名称
  selectedTopics: [], // 话题列表（不带#号）
  scheduleEnabled: false, // 定时发布开关
  videosPerDay: 1, // 每天发布视频数量
  dailyTimes: ['10:00'], // 每天发布时间点列表
  startDays: 0, // 从今天开始计算的发布天数，0表示明天，1表示后天
  publishStatus: null, // 发布状态，包含message和type
  publishing: false, // 发布状态，用于控制按钮loading效果
  isDraft: false, // 是否保存为草稿，仅视频号平台可见
  isOriginal: false // 是否标记为原创
}

// helper to create a fresh deep-copied tab from defaultTabInit
const makeNewTab = () => {
  // prefer structuredClone when available (newer browsers/node), fallback to JSON
  try {
    return typeof structuredClone === 'function' ? structuredClone(defaultTabInit) : JSON.parse(JSON.stringify(defaultTabInit))
  } catch (e) {
    return JSON.parse(JSON.stringify(defaultTabInit))
  }
}

// tab页数据 - 默认只有一个tab (use deep copy to avoid shared refs)
const tabs = reactive([
  makeNewTab()
])

// 账号相关状态
const accountDialogVisible = ref(false)
const tempSelectedAccounts = ref([])
const currentTab = ref(null)

// 获取账号状态管理
const accountStore = useAccountStore()

// 根据选择的平台获取可用账号列表
const availableAccounts = computed(() => {
  const platformMap = {
    3: '抖音',
    2: '视频号',
    1: '小红书',
    4: '快手'
  }
  const currentPlatform = currentTab.value ? platformMap[currentTab.value.selectedPlatform] : null
  return currentPlatform ? accountStore.accounts.filter(acc => acc.platform === currentPlatform || acc.platform === platforms.find(p => p.key === currentTab.value.selectedPlatform)?.name) : []
})

// 话题相关状态
const topicDialogVisible = ref(false)
const customTopic = ref('')

// 推荐话题列表
const recommendedTopics = [
  'Game', 'PhimẢnh', 'ÂmNhạc', 'ẨmThực', 'DuLịch', 'VănHóa',
  'CôngNghệ', 'ĐờiSống', 'GiảiTrí', 'ThểThao', 'GiáoDục', 'NghệThuật',
  'SứcKhỏe', 'ThờiTrang', 'LàmĐẹp', 'NhiếpẢnh', 'ThúCưng', 'XeCộ'
]

// 添加新tab
const addTab = () => {
  tabCounter++
  const newTab = makeNewTab()
  newTab.name = `tab${tabCounter}`
  newTab.label = `Bài đăng ${tabCounter}`
  tabs.push(newTab)
  activeTab.value = newTab.name
}

// 删除tab
const removeTab = (tabName) => {
  const index = tabs.findIndex(tab => tab.name === tabName)
  if (index > -1) {
    tabs.splice(index, 1)
    // 如果删除的是当前激活的tab，切换到第一个tab
    if (activeTab.value === tabName && tabs.length > 0) {
      activeTab.value = tabs[0].name
    }
  }
}

// 处理文件上传成功
const handleUploadSuccess = (response, file, tab) => {
  if (response.code === 200) {
    // 获取文件路径
    const filePath = response.data.path || response.data
    // 从路径中提取文件名
    const filename = filePath.split('/').pop()
    
    // 保存文件信息到fileList，包含文件路径和其他信息
    const fileInfo = {
      name: file.name,
      url: materialApi.getMaterialPreviewUrl(filename), // 使用getMaterialPreviewUrl生成预览URL
      path: filePath,
      size: file.size,
      type: file.type
    }
    
    // 添加到文件列表
    tab.fileList.push(fileInfo)
    
    // 更新显示列表
    tab.displayFileList = [...tab.fileList.map(item => ({
      name: item.name,
      url: item.url
    }))]
    
    ElMessage.success('Tải lên video thành công!')
  } else {
    ElMessage.error(response.msg || 'Tải video lên thất bại')
  }
}

// 处理文件上传失败
const handleUploadError = (error) => {
  ElMessage.error('Tải video lên thất bại')
}

// 删除已上传文件
const removeFile = (tab, index) => {
  // 从文件列表中删除
  tab.fileList.splice(index, 1)
  
  // 更新显示列表
  tab.displayFileList = [...tab.fileList.map(item => ({
    name: item.name,
    url: item.url
  }))]
  
  ElMessage.success('Đã xóa tệp khỏi bài đăng')
}

// 话题相关方法
// 打开添加话题弹窗
const openTopicDialog = (tab) => {
  currentTab.value = tab
  topicDialogVisible.value = true
}

// 添加自定义话题
const addCustomTopic = () => {
  if (!customTopic.value.trim()) {
    ElMessage.warning('Vui lòng nhập nội dung hashtag')
    return
  }
  if (currentTab.value && !currentTab.value.selectedTopics.includes(customTopic.value.trim())) {
    currentTab.value.selectedTopics.push(customTopic.value.trim())
    customTopic.value = ''
    ElMessage.success('Thêm hashtag thành công')
  } else {
    ElMessage.warning('Hashtag này đã được thêm')
  }
}

// 切换推荐话题
const toggleRecommendedTopic = (topic) => {
  if (!currentTab.value) return
  
  const index = currentTab.value.selectedTopics.indexOf(topic)
  if (index > -1) {
    currentTab.value.selectedTopics.splice(index, 1)
  } else {
    currentTab.value.selectedTopics.push(topic)
  }
}

// 删除话题
const removeTopic = (tab, index) => {
  tab.selectedTopics.splice(index, 1)
}

// 确认添加话题
const confirmTopicSelection = () => {
  topicDialogVisible.value = false
  customTopic.value = ''
  currentTab.value = null
  ElMessage.success('Đã cập nhật danh sách Hashtag')
}

// 账号选择相关方法
// 打开账号选择弹窗
const openAccountDialog = (tab) => {
  currentTab.value = tab
  tempSelectedAccounts.value = [...tab.selectedAccounts]
  accountDialogVisible.value = true
}

// 确认账号选择
const confirmAccountSelection = () => {
  if (currentTab.value) {
    currentTab.value.selectedAccounts = [...tempSelectedAccounts.value]
  }
  accountDialogVisible.value = false
  currentTab.value = null
  ElMessage.success('Đã chọn tài khoản thành công')
}

// 删除选中的账号
const removeAccount = (tab, index) => {
  tab.selectedAccounts.splice(index, 1)
}

// 获取账号显示名称
const getAccountDisplayName = (accountId) => {
  const account = accountStore.accounts.find(acc => acc.id === accountId)
  return account ? account.name : accountId
}

// 取消发布
const cancelPublish = (tab) => {
  ElMessage.info('Đã hủy thao tác')
}

// 确认发布
const confirmPublish = async (tab) => {
  // 防止重复点击
  if (tab.publishing) {
    throw new Error('Đang trong quá trình đăng, vui lòng đợi...')
  }

  tab.publishing = true // 设置发布状态为进行中

  // 数据验证
  if (tab.fileList.length === 0) {
    ElMessage.error('Vui lòng tải lên hoặc chọn video trước')
    tab.publishing = false
    throw new Error('Vui lòng tải lên hoặc chọn video trước')
  }
  if (!tab.title.trim()) {
    ElMessage.error('Vui lòng nhập tiêu đề bài đăng')
    tab.publishing = false
    throw new Error('Vui lòng nhập tiêu đề bài đăng')
  }
  if (!tab.selectedPlatform) {
    ElMessage.error('Vui lòng chọn nền tảng đăng')
    tab.publishing = false
    throw new Error('Vui lòng chọn nền tảng đăng')
  }
  if (tab.selectedAccounts.length === 0) {
    ElMessage.error('Vui lòng chọn ít nhất một tài khoản đăng')
    tab.publishing = false
    throw new Error('Vui lòng chọn ít nhất một tài khoản đăng')
  }

  // 构造发布数据，符合后端API格式
  const publishData = {
    type: tab.selectedPlatform,
    title: tab.title,
    tags: tab.selectedTopics, // 不带#号的话题列表
    fileList: tab.fileList.map(file => file.path), // 只发送文件路径
    accountList: tab.selectedAccounts.map(accountId => {
      const account = accountStore.accounts.find(acc => acc.id === accountId)
      return account ? account.filePath : accountId
    }), // 发送账号的文件路径
    enableTimer: tab.scheduleEnabled ? 1 : 0,
    videosPerDay: tab.scheduleEnabled ? tab.videosPerDay || 1 : 1,
    dailyTimes: tab.scheduleEnabled ? tab.dailyTimes || ['10:00'] : ['10:00'],
    startDays: tab.scheduleEnabled ? tab.startDays || 0 : 0,
    category: tab.isOriginal ? 1 : 0, // 1表示原创，0表示非原创
    productLink: tab.productLink.trim() || '',
    productTitle: tab.productTitle.trim() || '',
    isDraft: tab.isDraft
  }

  // 调用后端发布API（使用统一的http封装）
  try {
    const data = await http.post('/postVideo', publishData)
    tab.publishStatus = {
      message: 'Đăng bài thành công!',
      type: 'success'
    }
    // 清空当前tab的数据
    tab.fileList = []
    tab.displayFileList = []
    tab.title = ''
    tab.selectedTopics = []
    tab.selectedAccounts = []
    tab.scheduleEnabled = false
  } catch (error) {
    console.error('发布错误:', error)
    tab.publishStatus = {
      message: `Đăng bài thất bại: ${error.message || 'Vui lòng kiểm tra kết nối'}`,
      type: 'error'
    }
    throw error
  } finally {
    tab.publishing = false
  }
}

// 显示上传选项
const showUploadOptions = (tab) => {
  currentUploadTab.value = tab
  uploadOptionsVisible.value = true
}

// 选择本地上传
const selectLocalUpload = () => {
  uploadOptionsVisible.value = false
  localUploadVisible.value = true
}

// 选择素材库
const selectMaterialLibrary = async () => {
  uploadOptionsVisible.value = false
  
  // 如果素材库为空，先获取素材数据
  if (materials.value.length === 0) {
    try {
      const response = await materialApi.getAllMaterials()
      if (response.code === 200) {
        appStore.setMaterials(response.data)
      } else {
        ElMessage.error('Lấy danh sách tư liệu thất bại')
        return
      }
    } catch (error) {
      console.error('获取素材列表出错:', error)
      ElMessage.error('Lấy danh sách tư liệu thất bại')
      return
    }
  }
  
  selectedMaterials.value = []
  materialLibraryVisible.value = true
}

// 确认素材选择
const confirmMaterialSelection = () => {
  if (selectedMaterials.value.length === 0) {
    ElMessage.warning('Vui lòng chọn ít nhất một tư liệu')
    return
  }
  
  if (currentUploadTab.value) {
    // 将选中的素材添加到当前tab的文件列表
    selectedMaterials.value.forEach(materialId => {
      const material = materials.value.find(m => m.id === materialId)
      if (material) {
        const fileInfo = {
          name: material.filename,
          url: materialApi.getMaterialPreviewUrl(material.file_path.split('/').pop()),
          path: material.file_path,
          size: material.filesize * 1024 * 1024, // 转换为字节
          type: 'video/mp4'
        }
        
        // 检查是否已存在相同文件
        const exists = currentUploadTab.value.fileList.some(file => file.path === fileInfo.path)
        if (!exists) {
          currentUploadTab.value.fileList.push(fileInfo)
        }
      }
    })
    
    // 更新显示列表
    currentUploadTab.value.displayFileList = [...currentUploadTab.value.fileList.map(item => ({
      name: item.name,
      url: item.url
    }))]
  }
  
  const addedCount = selectedMaterials.value.length
  materialLibraryVisible.value = false
  selectedMaterials.value = []
  currentUploadTab.value = null
  ElMessage.success(`Đã thêm ${addedCount} tư liệu vào bài đăng`)
}

// 批量发布对话框状态
const batchPublishDialogVisible = ref(false)
const currentPublishingTab = ref(null)
const publishProgress = ref(0)
const publishResults = ref([])
const isCancelled = ref(false)

// 取消批量发布
const cancelBatchPublish = () => {
  isCancelled.value = true
  ElMessage.info('Đang hủy quá trình đăng...')
}

// 批量发布方法
const batchPublish = async () => {
  if (batchPublishing.value) return
  
  batchPublishing.value = true
  currentPublishingTab.value = null
  publishProgress.value = 0
  publishResults.value = []
  isCancelled.value = false
  batchPublishDialogVisible.value = true
  
  try {
    for (let i = 0; i < tabs.length; i++) {
      if (isCancelled.value) {
        publishResults.value.push({
          label: tabs[i].label,
          status: 'cancelled',
          message: 'Đã hủy'
        })
        continue
      }

      const tab = tabs[i]
      currentPublishingTab.value = tab
      publishProgress.value = Math.floor((i / tabs.length) * 100)
      
      try {
        await confirmPublish(tab)
        publishResults.value.push({
          label: tab.label,
          status: 'success',
          message: 'Đăng thành công'
        })
      } catch (error) {
        publishResults.value.push({
          label: tab.label,
          status: 'error',
          message: error.message
        })
        // 不立即返回，继续显示发布结果
      }
    }
    
    publishProgress.value = 100
    
    // 统计发布结果
    const successCount = publishResults.value.filter(r => r.status === 'success').length
    const failCount = publishResults.value.filter(r => r.status === 'error').length
    const cancelCount = publishResults.value.filter(r => r.status === 'cancelled').length
    
    if (isCancelled.value) {
      ElMessage.warning(`Đã dừng đăng: ${successCount} thành công, ${failCount} thất bại, ${cancelCount} chưa thực hiện`)
    } else if (failCount > 0) {
      ElMessage.error(`Hoàn tất đăng: ${successCount} thành công, ${failCount} thất bại`)
    } else {
      ElMessage.success('Tất cả các bài đăng đã hoàn tất thành công!')
      setTimeout(() => {
        batchPublishDialogVisible.value = false
      }, 1000)
    }
    
  } catch (error) {
    console.error('批量发布出错:', error)
    ElMessage.error('Đăng hàng loạt xảy ra lỗi, vui lòng thử lại')
  } finally {
    batchPublishing.value = false
    isCancelled.value = false
  }
}
</script>

<style lang="scss" scoped>
@use '@/styles/variables.scss' as *;

.publish-center {
  display: flex;
  flex-direction: column;
  height: 100%;
  
  // Tab管理区域
  .tab-management {
    background-color: #fff;
    border-radius: 4px;
    box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
    margin-bottom: 20px;
    padding: 15px 20px;
    
    .tab-header {
      display: flex;
      align-items: flex-start;
      gap: 15px;
      
      .tab-list {
        display: flex;
        flex-wrap: wrap;
        gap: 10px;
        flex: 1;
        min-width: 0;
        
        .tab-item {
           display: flex;
           align-items: center;
           gap: 6px;
           padding: 6px 12px;
           background-color: #f5f7fa;
           border: 1px solid #dcdfe6;
           border-radius: 4px;
           cursor: pointer;
           transition: all 0.3s;
           font-size: 14px;
           height: 32px;
           
           &:hover {
             background-color: #ecf5ff;
             border-color: #b3d8ff;
           }
           
           &.active {
             background-color: #409eff;
             border-color: #409eff;
             color: #fff;
             
             .close-icon {
               color: #fff;
               
               &:hover {
                 background-color: rgba(255, 255, 255, 0.2);
               }
             }
           }
           
           .close-icon {
             padding: 2px;
             border-radius: 2px;
             cursor: pointer;
             transition: background-color 0.3s;
             font-size: 12px;
             
             &:hover {
               background-color: rgba(0, 0, 0, 0.1);
             }
           }
         }
       }
       
      .tab-actions {
        display: flex;
        gap: 10px;
        flex-shrink: 0;
        
        .add-tab-btn,
        .batch-publish-btn {
          display: flex;
          align-items: center;
          gap: 4px;
          height: 32px;
          padding: 6px 12px;
          font-size: 14px;
          white-space: nowrap;
        }
      }
    }
  }
  
  // 批量发布进度对话框样式
  .publish-progress {
    padding: 20px;
    
    .current-publishing {
      margin: 15px 0;
      text-align: center;
      color: #606266;
    }

    .publish-results {
      margin-top: 20px;
      border-top: 1px solid #EBEEF5;
      padding-top: 15px;
      max-height: 300px;
      overflow-y: auto;

      .result-item {
        display: flex;
        align-items: center;
        padding: 8px 0;
        color: #606266;

        .el-icon {
          margin-right: 8px;
        }

        .label {
          margin-right: 10px;
          font-weight: 500;
        }

        .message {
          color: #909399;
        }

        &.success {
          color: #67C23A;
        }

        &.error {
          color: #F56C6C;
        }

        &.cancelled {
          color: #909399;
        }
      }
    }
  }

  .dialog-footer {
    text-align: right;
  }
  
  // 内容区域
  .publish-content {
    flex: 1;
    background-color: #fff;
    border-radius: 4px;
    box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
    padding: 20px;
    
    .tab-content-wrapper {
      display: flex;
      justify-content: center;
      
      .tab-content {
        width: 100%;
        max-width: 800px;
        
        h3 {
          font-size: 16px;
          font-weight: 500;
          color: $text-primary;
          margin: 0 0 10px 0;
        }
        
        .upload-section,
        .account-section,
        .platform-section,
        .title-section,
        .product-section,
        .topic-section,
        .schedule-section {
          margin-bottom: 30px;
        }

        .product-section {
          .product-name-input,
          .product-link-input {
            margin-bottom: 5px;
          }
        }
        
        .video-upload {
          width: 100%;
          
          :deep(.el-upload-dragger) {
            width: 100%;
            height: 180px;
          }
        }
        
        .account-input {
          max-width: 400px;
        }
        
        .platform-buttons {
          display: flex;
          gap: 10px;
          flex-wrap: wrap;
          
          .platform-btn {
            min-width: 80px;
          }
        }
        
        .title-input {
          max-width: 600px;
        }
        
        .topic-display {
          display: flex;
          flex-direction: column;
          gap: 12px;
          
          .selected-topics {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            min-height: 32px;
            
            .topic-tag {
              font-size: 14px;
            }
          }
          
          .select-topic-btn {
            align-self: flex-start;
          }
        }
        
        .schedule-controls {
          display: flex;
          flex-direction: column;
          gap: 15px;

          .schedule-settings {
            margin-top: 15px;
            padding: 15px;
            background-color: #f5f7fa;
            border-radius: 4px;

            .schedule-item {
              display: flex;
              align-items: center;
              margin-bottom: 15px;

              &:last-child {
                margin-bottom: 0;
              }

              .label {
                min-width: 120px;
                margin-right: 10px;
              }

              .el-time-select {
                margin-right: 10px;
              }

              .el-button {
                margin-left: 10px;
              }
            }
          }
        }
        
        .action-buttons {
          display: flex;
          justify-content: flex-end;
          gap: 10px;
          margin-top: 30px;
          padding-top: 20px;
          border-top: 1px solid #ebeef5;
        }

        .draft-section {
          margin: 20px 0;

          .draft-checkbox {
            display: block;
            margin: 10px 0;
          }
        }

        .original-section {
          margin: 10px 0 20px;

          .original-checkbox {
            display: block;
            margin: 10px 0;
          }
        }
      }
    }
  }

  // 已上传文件列表样式
  .uploaded-files {
    margin-top: 20px;
    
    h4 {
      font-size: 16px;
      font-weight: 500;
      margin-bottom: 12px;
      color: #303133;
    }
    
    .file-list {
      display: flex;
      flex-direction: column;
      gap: 10px;
      
      .file-item {
        display: flex;
        align-items: center;
        padding: 10px 15px;
        background-color: #f5f7fa;
        border-radius: 4px;
        
        .el-link {
          margin-right: 10px;
          max-width: 300px;
          overflow: hidden;
          text-overflow: ellipsis;
          white-space: nowrap;
        }
        
        .file-size {
          color: #909399;
          font-size: 13px;
          margin-right: auto;
        }
      }
    }
  }
  
  // 添加话题弹窗样式
  .topic-dialog {
    .topic-dialog-content {
      .custom-topic-input {
        display: flex;
        gap: 12px;
        margin-bottom: 24px;
        
        .custom-input {
          flex: 1;
        }
      }
      
      .recommended-topics {
        h4 {
          margin: 0 0 16px 0;
          font-size: 16px;
          font-weight: 500;
          color: #303133;
        }
        
        .topic-grid {
          display: grid;
          grid-template-columns: repeat(auto-fill, minmax(100px, 1fr));
          gap: 12px;
          
          .topic-btn {
            height: 36px;
            font-size: 14px;
            border-radius: 6px;
            min-width: 100px;
            padding: 0 12px;
            white-space: nowrap;
            text-align: center;
            display: flex;
            align-items: center;
            justify-content: center;
            
            &.el-button--primary {
              background-color: #409eff;
              border-color: #409eff;
              color: white;
            }
          }
        }
      }
    }
    
    .dialog-footer {
      display: flex;
      justify-content: flex-end;
      gap: 12px;
    }
  }
}
</style>
