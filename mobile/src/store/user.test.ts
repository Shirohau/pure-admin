import { describe, expect, it, vi } from 'vitest'
import { useUserStore } from './user'
import type { IUserInfo } from '@/api/types/login'

// 测试用用户信息（与后端 UserTokenSerializer 输出对齐）
const mockUser: IUserInfo = {
  id: 1,
  username: 'testuser',
  name: 'Test',
  avatar: 'https://example.com/avatar.png',
  roles: [1, 2],
}

describe('useUserStore', () => {
  it('初始状态：id 为 -1，username 为空，avatar 为默认头像', () => {
    const store = useUserStore()
    expect(store.userInfo.id).toBe(-1)
    expect(store.userInfo.username).toBe('')
    expect(store.userInfo.name).toBe('')
    expect(store.userInfo.avatar).toBe('/static/images/default-avatar.png')
    expect(store.userInfo.roles).toEqual([])
  })

  it('setUserInfo：正确更新用户信息', () => {
    const store = useUserStore()
    store.setUserInfo({ ...mockUser })
    expect(store.userInfo.id).toBe(1)
    expect(store.userInfo.username).toBe('testuser')
    expect(store.userInfo.name).toBe('Test')
    expect(store.userInfo.avatar).toBe('https://example.com/avatar.png')
    expect(store.userInfo.roles).toEqual([1, 2])
  })

  it('setUserInfo：avatar 为空字符串时使用默认头像', () => {
    const store = useUserStore()
    store.setUserInfo({ ...mockUser, avatar: '' })
    expect(store.userInfo.avatar).toBe('/static/images/default-avatar.png')
  })

  it('setUserAvatar：正确更新头像', () => {
    const store = useUserStore()
    store.setUserAvatar('https://example.com/new-avatar.png')
    expect(store.userInfo.avatar).toBe('https://example.com/new-avatar.png')
  })

  it('clearUserInfo：重置为初始状态并调用 uni.removeStorageSync', () => {
    const store = useUserStore()
    store.setUserInfo({ ...mockUser })

    store.clearUserInfo()

    expect(store.userInfo.id).toBe(-1)
    expect(store.userInfo.username).toBe('')
    expect(uni.removeStorageSync).toHaveBeenCalledWith('user')
  })

  it('setUserInfo：可直接写入登录接口返回的用户信息（含 roles）', () => {
    const store = useUserStore()
    const loginUserInfo: IUserInfo = {
      id: 42,
      username: 'api_user',
      name: 'API User',
      avatar: 'https://x.com/a.png',
      roles: [3],
    }
    store.setUserInfo(loginUserInfo)
    expect(store.userInfo.id).toBe(42)
    expect(store.userInfo.username).toBe('api_user')
    expect(store.userInfo.name).toBe('API User')
    expect(store.userInfo.avatar).toBe('https://x.com/a.png')
    expect(store.userInfo.roles).toEqual([3])
  })
})
