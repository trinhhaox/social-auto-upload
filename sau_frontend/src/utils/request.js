import axios from 'axios'
import { ElMessage } from 'element-plus'

// 创建axios实例
const request = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:5409',
  headers: {
    'Content-Type': 'application/json'
  }
})

// 请求拦截器
request.interceptors.request.use(
  (config) => {
    // 可以在这里添加token等认证信息
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    console.error('请求错误:', error)
    return Promise.reject(error)
  }
)

// 响应拦截器
request.interceptors.response.use(
  (response) => {
    const { data } = response
    
    // 根据后端接口规范处理响应
    if (data.code === 200 || data.success) {
      return data
    } else {
      ElMessage.error(data.msg || data.message || 'Yêu cầu thất bại')
      return Promise.reject(new Error(data.msg || data.message || 'Yêu cầu thất bại'))
    }
  },
  (error) => {
    console.error('Lỗi phản hồi HTTP:', error)
    
    // 处理HTTP错误状态码
    if (error.response) {
      const { status } = error.response
      switch (status) {
        case 401:
          ElMessage.error('Chưa được xác thực, vui lòng thử lại')
          break
        case 403:
          ElMessage.error('Từ chối quyền truy cập')
          break
        case 404:
          ElMessage.error('Địa chỉ API không tồn tại')
          break
        case 500:
          ElMessage.error('Lỗi máy chủ nội bộ')
          break
        default:
          ElMessage.error('Lỗi mạng kết nối')
      }
    } else {
      ElMessage.error('Kết nối mạng thất bại')
    }
    
    return Promise.reject(error)
  }
)

// 封装常用的请求方法
export const http = {
  get(url, params) {
    return request.get(url, { params })
  },
  
  post(url, data, config = {}) {
    return request.post(url, data, config)
  },
  
  put(url, data, config = {}) {
    return request.put(url, data, config)
  },
  
  delete(url, params) {
    return request.delete(url, { params })
  },
  
  upload(url, formData, onUploadProgress) {
    return request.post(url, formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      },
      onUploadProgress
    })
  }
}

export default request