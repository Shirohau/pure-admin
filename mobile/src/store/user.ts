import type { IUserInfo } from '@/api/types/login'
import { defineStore } from 'pinia'
import { ref } from 'vue'

// 初始化用户信息（未登录占位）
const userInfoState: IUserInfo = {
  id: -1,
  username: '',
  name: '',
  avatar: '/static/images/default-avatar.png',
  roles: [],
  deptName: null,
}

export const useUserStore = defineStore(
  'user',
  () => {
    // 用户信息
    const userInfo = ref<IUserInfo>({ ...userInfoState })

    /**
     * 设置用户信息
     *
     * 数据来源：登录/刷新接口响应中的用户部分（后端一次返回，无需单独请求用户信息接口）
     *
     * @param val 用户信息
     */
    const setUserInfo = (val: IUserInfo) => {
      console.log('设置用户信息', val)
      // 若头像为空则使用默认头像
      if (!val.avatar) {
        val.avatar = userInfoState.avatar
      }
      userInfo.value = val
    }

    /**
     * 更新用户头像
     * @param avatar 新头像地址
     */
    const setUserAvatar = (avatar: string) => {
      userInfo.value.avatar = avatar
      console.log('设置用户头像', avatar)
      console.log('userInfo', userInfo.value)
    }

    /**
     * 删除用户信息（退出登录时调用）
     */
    const clearUserInfo = () => {
      userInfo.value = { ...userInfoState }
      uni.removeStorageSync('user')
    }

    return {
      userInfo,
      clearUserInfo,
      setUserInfo,
      setUserAvatar,
    }
  },
  {
    persist: true,
  },
)
