import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useAccountStore = defineStore('account', () => {
  // 存储所有账号信息
  const accounts = ref([])
  
  // 平台类型映射
  const platformTypes = {
    5: 'Facebook',
    6: 'Instagram',
    7: 'Twitter',
    8: 'Threads',
    9: 'Pinterest',
    10: 'Zalo',
    11: 'YouTube',
    12: 'TikTok'
  }
  
  // 设置账号列表
  const setAccounts = (accountsData) => {
    // 转换后端返回的数据格式为前端使用的格式
    accounts.value = accountsData.map(item => {
      const typeId = Number(item[1])
      return {
        id: item[0],
        type: typeId,
        filePath: item[2],
        name: item[3],
        status: item[4] === -1 ? 'Đang xác thực' : (item[4] === 1 ? 'Hoạt động' : 'Chưa có Cookie'),
        platform: platformTypes[typeId] || item[1] || 'Facebook'
      }
    })
  }
  
  // 添加账号
  const addAccount = (account) => {
    accounts.value.push(account)
  }
  
  // 更新账号
  const updateAccount = (id, updatedAccount) => {
    const index = accounts.value.findIndex(acc => acc.id === id)
    if (index !== -1) {
      accounts.value[index] = { ...accounts.value[index], ...updatedAccount }
    }
  }
  
  // 删除账号
  const deleteAccount = (id) => {
    accounts.value = accounts.value.filter(acc => acc.id !== id)
  }
  
  // 根据平台获取账号
  const getAccountsByPlatform = (platform) => {
    return accounts.value.filter(acc => acc.platform === platform)
  }
  
  return {
    accounts,
    setAccounts,
    addAccount,
    updateAccount,
    deleteAccount,
    getAccountsByPlatform
  }
})