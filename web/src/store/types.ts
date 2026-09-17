import type { RouteRecordName } from "vue-router";

export type cacheType = {
  mode: string;
  name?: RouteRecordName;
};

export type positionType = {
  startIndex?: number;
  length?: number;
};

export type appType = {
  sidebar: {
    opened: boolean;
    withoutAnimation: boolean;
    // 判断是否手动点击Collapse
    isClickCollapse: boolean;
  };
  layout: string;
  device: string;
  viewportSize: { width: number; height: number };
};

export type multiType = {
  path: string;
  name: string;
  meta: any;
  query?: object;
  params?: object;
};

export type setType = {
  title: string;
  fixedHeader: boolean;
  hiddenSideBar: boolean;
};

export type userType = {
  id?: number;
  avatar?: string;
  username?: string;
  name?: string;
  roles?: Array<string>;
  permissions?: Array<string>;
  /** 字段级别权限（按页面 componentName 缓存，增量加载）
   * permission_level: 0 禁止访问 / 1 只读 / 2 可读写
   * func_permissions: 功能权限集（动态扩展，如 can_download 可下载 / can_print 可打印） */
  fieldPerms?: Record<
    string,
    Array<{
      field_name: string;
      permission_level: number;
      func_permissions?: Record<string, boolean>;
    }>
  >;
  verifyCode?: string;
  currentPage?: number;
  isRemembered?: boolean;
  loginDay?: number;
};
