import { inject, reactive, ref, type InjectionKey, type Ref } from "vue";
import { api } from "../api";
import {
  roleMenuButtonApi,
  roleMenuFieldApi,
  toFieldRowState,
  type RoleMenuButton,
  type RoleMenuField
} from "./impowerApi";

// ====== 角色信息 ======
export interface RoleInfo {
  id: number | undefined;
  name: string;
  users: {
    id: number;
    name: string;
    dept_name: string;
  }[];
  menus: number[];
  [key: string]: any;
}

// ====== 菜单信息 ======
export interface MenuInfo {
  id: number | undefined;
  [key: string]: any;
}

// ====== 授权上下文（每个抽屉实例独立一份） ======
/**
 * 授权上下文
 * @description 承载单个授权抽屉实例的全部状态与方法，
 * 通过 provide/inject 在 RoleImpowerContent 与各授权子组件间共享，
 * 每个抽屉实例独立创建，互不干扰
 */
export interface ImpowerContext {
  /** 当前授权角色信息（由 loadRole 加载） */
  roleInfo: RoleInfo;
  /** 更新角色信息（授权用户/菜单后回写接口返回的最新数据） */
  setRoleInfo: (data: RoleInfo) => void;
  /** 当前选中的菜单节点信息 */
  menuInfo: MenuInfo;
  /** 设置当前选中的菜单节点 */
  setMenuInfo: (data: any) => void;
  /** 当前激活的页签（button 授权按钮 / field 授权字段） */
  activeName: Ref<string>;
  /** 菜单按钮权限列表 */
  menuButton: Ref<RoleMenuButton[]>;
  /** 菜单按钮列表分页配置 */
  menuButtonPageConfig: { page: number; limit: number; total: number };
  /** 菜单字段权限列表 */
  menuField: Ref<RoleMenuField[]>;
  /** 菜单字段列表分页配置 */
  menuFieldPageConfig: { page: number; limit: number; total: number };
  /** 获取当前菜单下的按钮权限列表 */
  getMenuButton: () => Promise<void>;
  /** 获取当前菜单下的字段权限列表 */
  getMenuField: () => Promise<void>;
  /** 根据当前激活页签刷新对应的权限列表 */
  getPermission: () => void;
  /** 加载角色详情并写入 roleInfo */
  loadRole: (roleId: number) => Promise<void>;
}

/** provide/inject 的注入键 */
export const impowerKey: InjectionKey<ImpowerContext> = Symbol("impower");

/**
 * 获取当前授权实例的上下文
 * @description 必须在 RoleImpowerContent 的 provide 作用域内使用（即授权抽屉内的子组件）
 */
export function useImpowerContext(): ImpowerContext {
  const context = inject(impowerKey);
  if (!context) {
    throw new Error(
      "useImpowerContext 必须在 RoleImpowerContent 提供的授权上下文内使用"
    );
  }
  return context;
}

/**
 * 创建每实例授权状态
 * @description 每个授权抽屉独立调用一次，返回互不干扰的状态与方法，
 * 支持同时打开多个授权抽屉。状态随所属组件实例销毁而释放。
 */
export function useImpower(): ImpowerContext {
  const roleInfo = reactive<RoleInfo>({
    id: undefined,
    name: "",
    users: [],
    menus: []
  });
  /* 设置角色信息（Object.assign 合并更新，保留接口返回的扩展字段） */
  const setRoleInfo = (data: RoleInfo) => {
    Object.assign(roleInfo, data);
  };

  /** 加载角色详情（id/name/users/menus 等），供抽屉打开时初始化 */
  const loadRole = async (roleId: number) => {
    const res: ApiResponse = await api.GetObj(roleId);
    setRoleInfo(res.data);
  };

  // ====== 菜单信息 ======
  const menuInfo = reactive<MenuInfo>({ id: undefined });
  /* 设置当前选中的菜单节点（点击菜单树节点时触发） */
  const setMenuInfo = (data: any) => {
    Object.assign(menuInfo, data);
  };

  /** 当前激活页签（button 授权按钮 / field 授权字段），默认按钮页签 */
  const activeName = ref("button");
  /** 根据当前激活页签刷新对应的权限列表（tab 切换时触发） */
  const getPermission = () => {
    if (activeName.value === "button") {
      getMenuButton();
    } else if (activeName.value === "field") {
      getMenuField();
    }
  };

  // ====== 菜单按钮信息 ======
  const menuButton = ref<RoleMenuButton[]>([]);
  const menuButtonPageConfig = reactive({ page: 1, limit: 20, total: 0 });
  /** 获取当前菜单下的按钮权限列表（分页参数取 roleInfo.id + menuInfo.id） */
  const getMenuButton = async () => {
    const params = {
      page: menuButtonPageConfig.page,
      limit: menuButtonPageConfig.limit,
      role_id: roleInfo.id,
      menu_id: menuInfo.id
    };
    const { paginated, data } = await roleMenuButtonApi.RolesButton(params);
    menuButton.value = data;
    menuButtonPageConfig.page = paginated.page ?? 1;
    menuButtonPageConfig.limit = paginated.limit ?? 20;
    menuButtonPageConfig.total = paginated.total ?? 0;
  };

  // ====== 菜单字段信息 ======
  const menuField = ref<RoleMenuField[]>([]);
  const menuFieldPageConfig = reactive({ page: 1, limit: 20, total: 0 });
  /** 获取当前菜单下的字段权限列表，并将 permission_level 映射为 level_x 复选框状态 */
  const getMenuField = async () => {
    const params = {
      page: menuFieldPageConfig.page,
      limit: menuFieldPageConfig.limit,
      role_id: roleInfo.id,
      menu_id: menuInfo.id
    };
    const { paginated, data } = await roleMenuFieldApi.RoleFields(params);
    // 将每行数据转换为带 level_x 勾选状态与独立 func_permissions 的 UI 行
    menuField.value = (data || []).map(item => toFieldRowState(item));
    menuFieldPageConfig.page = paginated.page ?? 1;
    menuFieldPageConfig.limit = paginated.limit ?? 20;
    menuFieldPageConfig.total = paginated.total ?? 0;
  };

  return {
    roleInfo,
    setRoleInfo,
    menuInfo,
    setMenuInfo,
    activeName,
    menuButton,
    menuButtonPageConfig,
    menuField,
    menuFieldPageConfig,
    getMenuButton,
    getMenuField,
    getPermission,
    loadRole
  };
}
