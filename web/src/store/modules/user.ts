import { defineStore } from "pinia";
import { logoutFromOa } from "@/utils/oaSso";
import { ElMessage } from "element-plus";
import {
  type userType,
  store,
  router,
  resetRouter,
  routerArrays,
  storageLocal
} from "../utils";
import {
  type UserResult,
  type RefreshTokenResult,
  getLogin,
  refreshTokenApi,
  verifyTokenApi
} from "@/api/user";
import { useMultiTagsStoreHook } from "./multiTags";
import {
  type DataInfo,
  getToken,
  setToken,
  removeToken,
  userKey,
  resetPagePerms
} from "@/utils/auth";

export const useUserStore = defineStore("pure-user", {
  state: (): userType => ({
    // id
    id: storageLocal().getItem<DataInfo<number>>(userKey)?.id ?? undefined,
    // 头像
    avatar: storageLocal().getItem<DataInfo<number>>(userKey)?.avatar ?? "",
    // 用户名
    username: storageLocal().getItem<DataInfo<number>>(userKey)?.username ?? "",
    // 昵称
    name: storageLocal().getItem<DataInfo<number>>(userKey)?.name ?? "",
    // 页面级别权限
    roles: storageLocal().getItem<DataInfo<number>>(userKey)?.roles ?? [],
    // 按钮级别权限（按页面增量加载，不再从 localStorage 初始化）
    permissions: [] as string[],
    // 字段级别权限（按页面 componentName 增量缓存）
    fieldPerms: {} as Record<
      string,
      Array<{
        field_name: string;
        permission_level: number;
        func_permissions?: Record<string, boolean>;
      }>
    >,
    // 前端生成的验证码（按实际需求替换）
    verifyCode: "",
    // 判断登录页面显示哪个组件（0：登录（默认）、1：手机登录、2：邮箱登录、3：注册、4：忘记密码）
    currentPage: 0,
    // 是否勾选了登录页的免登录
    isRemembered: false,
    // 登录页的免登录存储几天，默认7天
    loginDay: 7
  }),
  actions: {
    /** 存储ID */
    SET_ID(id: number) {
      this.id = id;
    },
    /** 存储头像 */
    SET_AVATAR(avatar: string) {
      this.avatar = avatar;
    },
    /** 存储用户名 */
    SET_USERNAME(username: string) {
      this.username = username;
    },
    /** 存储昵称 */
    SET_NICKNAME(name: string) {
      this.name = name;
    },
    /** 存储角色 */
    SET_ROLES(roles: Array<string>) {
      this.roles = roles;
    },
    /** 存储按钮级别权限 */
    SET_PERMS(permissions: Array<string>) {
      this.permissions = permissions;
    },
    /** 增量合并按钮权限（去重） */
    MERGE_PERMS(keys: Array<string>) {
      const existing = new Set(this.permissions);
      keys.forEach(k => existing.add(k));
      this.permissions = Array.from(existing);
    },
    /** 存储页面字段权限（按 componentName 缓存） */
    SET_FIELD_PERMS(
      componentName: string,
      fields: Array<{
        field_name: string;
        permission_level: number;
        func_permissions?: Record<string, boolean>;
      }>
    ) {
      this.fieldPerms[componentName] = fields;
    },
    /** 存储前端生成的验证码 */
    SET_VERIFYCODE(verifyCode: string) {
      this.verifyCode = verifyCode;
    },
    /** 存储登录页面显示哪个组件 */
    SET_CURRENTPAGE(value: number) {
      this.currentPage = value;
    },
    /** 存储是否勾选了登录页的免登录 */
    SET_ISREMEMBERED(bool: boolean) {
      this.isRemembered = bool;
    },
    /** 设置登录页的免登录存储几天 */
    SET_LOGINDAY(value: number) {
      this.loginDay = Number(value);
    },
    /** 登入 */
    async loginByUsername(data) {
      return new Promise<UserResult>((resolve, reject) => {
        getLogin(data)
          .then(data => {
            if (data?.success) setToken(data.data);
            resolve(data);
          })
          .catch(error => {
            reject(error);
          });
      });
    },
    /** 第三方登录 */
    async loginByPlatform(data) {
      return new Promise<UserResult>((resolve, reject) => {
        verifyTokenApi(data)
          .then(data => {
            if (data?.success) setToken(data.data);
            resolve(data);
          })
          .catch(error => {
            reject(error);
          });
      });
    },
    /** OA 登录先结束本应用授权；普通登录保持原清理流程。 */
    async logOut() {
      try {
        await logoutFromOa(getToken()?.refreshToken);
      } catch (error) {
        ElMessage.error(error instanceof Error ? error.message : "退出未完成，请重试");
        return;
      }
      this.id = undefined;
      this.username = "";
      this.roles = [];
      this.permissions = [];
      this.fieldPerms = {};
      resetPagePerms();
      removeToken();
      useMultiTagsStoreHook().handleTags("equal", [...routerArrays]);
      resetRouter();
      router.push("/login");
    },
    /** 刷新`token` */
    async handRefreshToken(data) {
      return new Promise<RefreshTokenResult>((resolve, reject) => {
        refreshTokenApi(data)
          .then(data => {
            if (data) {
              setToken(data.data);
              resolve(data);
            }
          })
          .catch(error => {
            reject(error);
          });
      });
    }
  }
});

export function useUserStoreHook() {
  return useUserStore(store);
}
