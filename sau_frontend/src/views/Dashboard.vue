<template>
  <div class="dashboard">
    <div class="page-header">
      <h1>Tổng quan hệ thống tự động hóa</h1>
    </div>

    <div class="dashboard-content">
      <el-row :gutter="20">
        <!-- Thống kê tài khoản -->
        <el-col :span="8">
          <el-card class="stat-card">
            <div class="stat-card-content">
              <div class="stat-icon">
                <el-icon><User /></el-icon>
              </div>
              <div class="stat-info">
                <div class="stat-value">{{ accountStats.total }}</div>
                <div class="stat-label">Tổng số tài khoản</div>
              </div>
            </div>
            <div class="stat-footer">
              <div class="stat-detail">
                <span>Hoạt động: {{ accountStats.normal }}</span>
                <span>Lỗi/Cần đăng nhập: {{ accountStats.abnormal }}</span>
              </div>
            </div>
          </el-card>
        </el-col>

        <!-- Thống kê nền tảng -->
        <el-col :span="8">
          <el-card class="stat-card">
            <div class="stat-card-content">
              <div class="stat-icon platform-icon">
                <el-icon><Platform /></el-icon>
              </div>
              <div class="stat-info">
                <div class="stat-value">{{ platformStats.total }}</div>
                <div class="stat-label">Nền tảng đã kết nối</div>
              </div>
            </div>
            <div class="stat-footer">
              <div class="stat-detail">
                <el-tooltip content="Facebook" placement="top" v-if="platformStats.fb > 0">
                  <el-tag size="small" type="primary">FB: {{ platformStats.fb }}</el-tag>
                </el-tooltip>
                <el-tooltip content="Instagram" placement="top" v-if="platformStats.insta > 0">
                  <el-tag size="small" type="danger">Insta: {{ platformStats.insta }}</el-tag>
                </el-tooltip>
                <el-tooltip content="Twitter / X" placement="top" v-if="platformStats.twitter > 0">
                  <el-tag size="small" type="info">X: {{ platformStats.twitter }}</el-tag>
                </el-tooltip>
                <el-tooltip content="Threads" placement="top" v-if="platformStats.threads > 0">
                  <el-tag size="small" type="success">Threads: {{ platformStats.threads }}</el-tag>
                </el-tooltip>
                <el-tooltip content="Pinterest" placement="top" v-if="platformStats.pin > 0">
                  <el-tag size="small" type="danger">Pin: {{ platformStats.pin }}</el-tag>
                </el-tooltip>
                <el-tooltip content="Zalo" placement="top" v-if="platformStats.zalo > 0">
                  <el-tag size="small" type="primary">Zalo: {{ platformStats.zalo }}</el-tag>
                </el-tooltip>
                <el-tooltip content="YouTube" placement="top" v-if="platformStats.yt > 0">
                  <el-tag size="small" type="danger">YT: {{ platformStats.yt }}</el-tag>
                </el-tooltip>
                <el-tooltip content="TikTok" placement="top" v-if="platformStats.tk > 0">
                  <el-tag size="small" type="success">TikTok: {{ platformStats.tk }}</el-tag>
                </el-tooltip>
              </div>
            </div>
          </el-card>
        </el-col>

        <!-- Thống kê tư liệu -->
        <el-col :span="8">
          <el-card class="stat-card">
            <div class="stat-card-content">
              <div class="stat-icon content-icon">
                <el-icon><Document /></el-icon>
              </div>
              <div class="stat-info">
                <div class="stat-value">{{ contentStats.total }}</div>
                <div class="stat-label">Tổng số tư liệu</div>
              </div>
            </div>
            <div class="stat-footer">
              <div class="stat-detail">
                <span>Video: {{ contentStats.videos }}</span>
                <span>Hình ảnh: {{ contentStats.images }}</span>
                <span>Khác: {{ contentStats.others }}</span>
              </div>
            </div>
          </el-card>
        </el-col>
      </el-row>

      <!-- Thao tác nhanh -->
      <div class="quick-actions">
        <h2>Thao tác nhanh</h2>
        <el-row :gutter="20">
          <el-col :span="6">
            <el-card class="action-card" @click="navigateTo('/account-management')">
              <div class="action-icon">
                <el-icon><UserFilled /></el-icon>
              </div>
              <div class="action-title">Quản lý tài khoản</div>
              <div class="action-desc">Quản lý tài khoản các nền tảng</div>
            </el-card>
          </el-col>
          <el-col :span="6">
            <el-card class="action-card" @click="navigateTo('/material-management')">
              <div class="action-icon">
                <el-icon><Upload /></el-icon>
              </div>
              <div class="action-title">Quản lý tư liệu</div>
              <div class="action-desc">Tải lên và quản lý video/ảnh</div>
            </el-card>
          </el-col>
          <el-col :span="6">
            <el-card class="action-card" @click="navigateTo('/publish-center')">
              <div class="action-icon">
                <el-icon><Timer /></el-icon>
              </div>
              <div class="action-title">Trung tâm đăng bài</div>
              <div class="action-desc">Đăng nội dung lên các nền tảng</div>
            </el-card>
          </el-col>
          <el-col :span="6">
            <el-card class="action-card" @click="navigateTo('/about')">
              <div class="action-icon">
                <el-icon><DataAnalysis /></el-icon>
              </div>
              <div class="action-title">Giới thiệu</div>
              <div class="action-desc">Xem thông tin hệ thống</div>
            </el-card>
          </el-col>
        </el-row>
      </div>

      <!-- Lịch sử đăng bài gần đây -->
      <div class="recent-tasks" v-if="publishHistory.length > 0" style="margin-bottom: 20px;">
        <div class="section-header">
          <h2>Lịch sử đăng bài gần đây</h2>
          <el-button text @click="navigateTo('/publish-center')">Tạo bài mới</el-button>
        </div>

        <el-table :data="publishHistory.slice(0, 5)" style="width: 100%">
          <el-table-column prop="title" label="Tiêu đề bài đăng" width="280" />
          <el-table-column prop="platform_name" label="Nền tảng" width="160">
            <template #default="scope">
              <el-tag effect="plain" type="primary">{{ scope.row.platform_name }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="file_count" label="Số tệp" width="90" />
          <el-table-column prop="account_count" label="Số tài khoản" width="110" />
          <el-table-column prop="created_at" label="Thời gian gửi" width="180" />
          <el-table-column prop="status" label="Trạng thái" width="120">
            <template #default="scope">
              <el-tag type="success" size="small">{{ scope.row.status }}</el-tag>
            </template>
          </el-table-column>
        </el-table>
      </div>

      <!-- Danh sách tư liệu gần đây -->
      <div class="recent-tasks">
        <div class="section-header">
          <h2>Tư liệu tải lên gần đây</h2>
          <el-button text @click="navigateTo('/material-management')">Xem tất cả</el-button>
        </div>

        <el-table :data="recentMaterials" style="width: 100%" v-loading="loading">
          <el-table-column prop="filename" label="Tên tệp" width="300" />
          <el-table-column prop="filesize" label="Dung lượng" width="120">
            <template #default="scope">
              {{ scope.row.filesize }} MB
            </template>
          </el-table-column>
          <el-table-column prop="upload_time" label="Thời gian tải lên" width="200" />
          <el-table-column label="Loại" width="100">
            <template #default="scope">
              <el-tag
                :type="getFileTypeTag(scope.row.filename)"
                effect="plain"
                size="small"
              >
                {{ getFileType(scope.row.filename) }}
              </el-tag>
            </template>
          </el-table-column>
        </el-table>

        <el-empty v-if="!loading && recentMaterials.length === 0" description="Chưa có dữ liệu tư liệu" />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import {
  User, UserFilled, Platform, Document,
  Upload, Timer, DataAnalysis
} from '@element-plus/icons-vue'
import { accountApi } from '@/api/account'
import { materialApi } from '@/api/material'
import { useAccountStore } from '@/stores/account'
import { useAppStore } from '@/stores/app'

const router = useRouter()
const accountStore = useAccountStore()
const appStore = useAppStore()
const loading = ref(false)

// 账号统计数据 - 从真实数据计算
const accountStats = computed(() => {
  const accounts = accountStore.accounts
  const normal = accounts.filter(a => a.status === '正常' || a.status === 'Hoạt động').length
  const abnormal = accounts.filter(a => a.status !== '正常' && a.status !== 'Hoạt động' && a.status !== '验证中' && a.status !== 'Đang xác thực').length
  return {
    total: accounts.length,
    normal,
    abnormal
  }
})

// 平台统计数据 - 从真实数据计算
const platformStats = computed(() => {
  const accounts = accountStore.accounts
  const fb = accounts.filter(a => a.platform?.toLowerCase().includes('facebook')).length
  const insta = accounts.filter(a => a.platform?.toLowerCase().includes('instagram')).length
  const twitter = accounts.filter(a => a.platform?.toLowerCase().includes('twitter')).length
  const threads = accounts.filter(a => a.platform?.toLowerCase().includes('threads')).length
  const pin = accounts.filter(a => a.platform?.toLowerCase().includes('pinterest')).length
  const zalo = accounts.filter(a => a.platform?.toLowerCase().includes('zalo')).length
  const yt = accounts.filter(a => a.platform?.toLowerCase().includes('youtube')).length
  const tk = accounts.filter(a => a.platform?.toLowerCase().includes('tiktok')).length
  
  const allCounts = [fb, insta, twitter, threads, pin, zalo, yt, tk]
  const total = allCounts.filter(n => n > 0).length
  return { total, fb, insta, twitter, threads, pin, zalo, yt, tk }
})

// 素材统计数据 - 从真实数据计算
const videoExtensions = ['.mp4', '.avi', '.mov', '.wmv', '.flv', '.mkv']
const imageExtensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']

const contentStats = computed(() => {
  const materials = appStore.materials
  const videos = materials.filter(m => videoExtensions.some(ext => m.filename.toLowerCase().endsWith(ext))).length
  const images = materials.filter(m => imageExtensions.some(ext => m.filename.toLowerCase().endsWith(ext))).length
  return {
    total: materials.length,
    videos,
    images,
    others: materials.length - videos - images
  }
})

// 最近上传的素材（最多显示5条）
const recentMaterials = computed(() => {
  return [...appStore.materials]
    .sort((a, b) => new Date(b.upload_time) - new Date(a.upload_time))
    .slice(0, 5)
})

// Lịch sử đăng bài gần đây
const publishHistory = ref([])

// 获取文件类型
const getFileType = (filename) => {
  if (videoExtensions.some(ext => filename.toLowerCase().endsWith(ext))) return 'Video'
  if (imageExtensions.some(ext => filename.toLowerCase().endsWith(ext))) return 'Hình ảnh'
  return 'Khác'
}

// 获取文件类型标签颜色
const getFileTypeTag = (filename) => {
  const type = getFileType(filename)
  return { 'Video': 'success', 'Hình ảnh': 'warning', 'Khác': 'info' }[type] || 'info'
}

// 导航到指定路由
const navigateTo = (path) => {
  router.push(path)
}

// 加载数据
const fetchDashboardData = async () => {
  loading.value = true
  try {
    // 并行获取账号、素材数据和发布历史
    const [accountRes, materialRes, historyRes] = await Promise.allSettled([
      accountApi.getAccounts(),
      materialApi.getAllMaterials(),
      fetch('/getPublishHistory').then(r => r.json())
    ])

    if (accountRes.status === 'fulfilled' && accountRes.value.code === 200) {
      accountStore.setAccounts(accountRes.value.data)
    }
    if (materialRes.status === 'fulfilled' && materialRes.value.code === 200) {
      appStore.setMaterials(materialRes.value.data)
    }
    if (historyRes.status === 'fulfilled' && historyRes.value.code === 200) {
      publishHistory.value = historyRes.value.data || []
    }
  } catch (error) {
    console.error('Lỗi khi tải dữ liệu trang tổng quan:', error)
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  fetchDashboardData()
})
</script>

<style lang="scss" scoped>
@use '@/styles/variables.scss' as *;

.dashboard {
  .page-header {
    margin-bottom: 20px;

    h1 {
      font-size: 24px;
      color: $text-primary;
      margin: 0;
    }
  }

  .dashboard-content {
    .stat-card {
      height: 140px;
      margin-bottom: 20px;

      .stat-card-content {
        display: flex;
        align-items: center;
        margin-bottom: 15px;

        .stat-icon {
          width: 60px;
          height: 60px;
          border-radius: 50%;
          background-color: rgba($primary-color, 0.1);
          display: flex;
          justify-content: center;
          align-items: center;
          margin-right: 15px;

          .el-icon {
            font-size: 30px;
            color: $primary-color;
          }

          &.platform-icon {
            background-color: rgba($success-color, 0.1);

            .el-icon {
              color: $success-color;
            }
          }

          &.content-icon {
            background-color: rgba($info-color, 0.1);

            .el-icon {
              color: $info-color;
            }
          }
        }

        .stat-info {
          .stat-value {
            font-size: 24px;
            font-weight: bold;
            color: $text-primary;
            line-height: 1.2;
          }

          .stat-label {
            font-size: 14px;
            color: $text-secondary;
          }
        }
      }

      .stat-footer {
        border-top: 1px solid $border-lighter;
        padding-top: 10px;

        .stat-detail {
          display: flex;
          justify-content: space-between;
          color: $text-secondary;
          font-size: 13px;

          .el-tag {
            margin-right: 5px;
          }
        }
      }
    }

    .quick-actions {
      margin: 20px 0 30px;

      h2 {
        font-size: 18px;
        margin-bottom: 15px;
        color: $text-primary;
      }

      .action-card {
        height: 160px;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        cursor: pointer;
        transition: all 0.3s;

        &:hover {
          transform: translateY(-5px);
          box-shadow: 0 10px 20px rgba(0, 0, 0, 0.1);
        }

        .action-icon {
          width: 50px;
          height: 50px;
          border-radius: 50%;
          background-color: rgba($primary-color, 0.1);
          display: flex;
          justify-content: center;
          align-items: center;
          margin-bottom: 15px;

          .el-icon {
            font-size: 24px;
            color: $primary-color;
          }
        }

        .action-title {
          font-size: 16px;
          font-weight: bold;
          color: $text-primary;
          margin-bottom: 5px;
        }

        .action-desc {
          font-size: 13px;
          color: $text-secondary;
          text-align: center;
        }
      }
    }

    .recent-tasks {
      margin-top: 30px;

      .section-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 15px;

        h2 {
          font-size: 18px;
          color: $text-primary;
          margin: 0;
        }
      }
    }
  }
}
</style>
