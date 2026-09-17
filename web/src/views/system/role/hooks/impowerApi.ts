import { CreateApi } from "@/api/base";
import { http } from "@/utils/http";
import { ElMessage } from "element-plus";

/**
 * 角色授权相关 API 模块
 * @description 封装角色菜单按钮（role_menu_button）与角色菜单字段（role_menu_field）
 * 的接口定义与类型，供授权页面（按钮面板 / 字段面板）使用。
 * 同时导出权限等级常量与行数据处理工具，供多个授权面板复用。
 */

// ====== 公共常量 ======

/**
 * 数据权限等级常量（与后端 RoleMenuFieldModel.DataPermission 对齐）
 * 三者互斥：勾选某一等级即取代其余等级；未分配记录时默认全部权限（可读写）。
 */
export const PERMISSION_LEVEL = {
  /** 禁止访问：列与表单均不显示 */
  DENIED: 0,
  /** 只读：列显示、表单只读 */
  READ: 1,
  /** 可读写：列显示、表单可编辑 */
  WRITE: 2
} as const;

/**
 * 访问等级对应的表格行勾选字段名（下标与权限等级一一对应，如 level_1 对应只读）
 */
export const FIELD_LEVEL_KEYS = ["level_0", "level_1", "level_2"] as const;

/** 访问等级勾选字段名类型（"level_0" | "level_1" | "level_2"） */
export type FieldLevelKey = (typeof FIELD_LEVEL_KEYS)[number];

/** 功能权限定义（后端 func_permission_definitions 接口返回） */
export interface FuncPermissionDef {
  /** 功能权限 key（存入 func_permissions JSON 的键名） */
  key: string;
  /** 功能权限显示名 */
  label: string;
}

// ====== 角色菜单按钮 ======
/** 角色菜单按钮行数据 */
export interface RoleMenuButton {
  /** 菜单 ID */
  menu: number;
  /** 菜单按钮 ID */
  menu_button: number;
  /** 菜单按钮名称 */
  menu_button_name: string;
  /** 按钮类型 */
  button_type?: string;
  /** 是否需要数据访问（false 时默认全部数据，不渲染范围选择列） */
  need_data_scope: boolean;
  /** 角色 ID */
  role: number;
  /** 角色菜单按钮记录 ID（未分配权限时为 null） */
  role_menu_button: number | null;
  /** 是否有权限 */
  has_permission: boolean;
  /** 数据权限范围 */
  permission_range: number;
  /** 关联部门 ID 列表 */
  dept: number[];
}

const roleMenuButtonApiPrefix = "/api/system/rolemenubutton/";
/** 角色菜单按钮 API */
export const roleMenuButtonApi = {
  ...CreateApi(roleMenuButtonApiPrefix),
  /**
   * 获取带有权限的按钮列表（角色维度）
   * @param params 查询参数（page/limit/role_id/menu_id）
   */
  async RolesButton(params: object) {
    const res: ApiResponse = await http.get(
      `${roleMenuButtonApiPrefix}roles_button/`,
      {
        params
      }
    );
    return res;
  },
  /**
   * 批量更新按钮权限范围（统一设置模式）
   * @param data { role_id, menu_id, permission_range, dept } 仅作用于已分配权限的按钮
   * @param mes 是否弹出成功提示（默认 true）
   */
  async BatchUpdate(data: object, mes: boolean = true) {
    const res: ApiResponse = await http.post(
      `${roleMenuButtonApiPrefix}batch_update/`,
      {
        data
      }
    );
    if (mes) ElMessage({ message: res.message, type: "success" });
    return res;
  },
  /**
   * 批量开启/关闭按钮权限（表头全量授权开关，单次请求）
   * @param data { role_id, menu_id, has_permission, permission_range?, dept? }
   *        has_permission=true 为未分配按钮批量创建权限记录（已分配的不受影响）；
   *        false 批量删除该角色在该菜单下全部按钮权限记录
   * @param mes 是否弹出成功提示（默认 true）
   */
  async BatchPermission(data: object, mes: boolean = true) {
    const res: ApiResponse = await http.post(
      `${roleMenuButtonApiPrefix}batch_permission/`,
      {
        data
      }
    );
    if (mes) ElMessage({ message: res.message, type: "success" });
    return res;
  }
};

// ====== 角色菜单字段 ======
/** 角色菜单字段行数据 */
export interface RoleMenuField {
  /** 菜单 ID（role_fields 接口返回） */
  menu?: number;
  /** 菜单字段 ID */
  menu_field: number;
  /** 菜单字段显示名（role_fields 接口返回） */
  menu_field_name?: string;
  /** 角色 ID */
  role: number;
  /** 角色名称（field_roles 接口返回） */
  role_name?: string;
  /** 角色菜单字段记录 ID（未分配权限时为 null） */
  role_menu_field?: number;
  /** 是否已分配权限 */
  has_permission?: boolean;
  /** 数据权限等级：0 禁止 / 1 只读 / 2 可读写（未分配时为 null） */
  permission_level?: number | null;
  /** 功能权限集：{功能权限key: bool}（未分配时为 {}） */
  func_permissions?: Record<string, boolean>;

  // UI 绑定字段（由 toFieldRowState 处理后填充）
  /** UI 勾选状态：禁止访问 */
  level_0?: boolean;
  /** UI 勾选状态：只读 */
  level_1?: boolean;
  /** UI 勾选状态：可读写 */
  level_2?: boolean;
}

/**
 * 将接口返回的字段/角色权限行转换为表格行 UI 状态
 * @param item 后端 role_fields / field_roles 接口返回的原始行数据
 * @returns 浅拷贝后的行数据：附 level_0/1/2 勾选状态（按 permission_level 点亮）与独立拷贝的 func_permissions。
 *          仅显式分配了数据等级（permission_level 非 null）才点亮对应等级，
 *          null（未显式分配）不点亮任何等级，保证数据等级与功能权限完全独立。
 */
export const toFieldRowState = <T extends RoleMenuField>(item: T): T => {
  const row: T = { ...item };
  // 初始化三个访问等级勾选状态为 false（互斥：仅一个被点亮）
  FIELD_LEVEL_KEYS.forEach(key => {
    row[key] = false;
  });
  // 功能权限集独立拷贝（避免多行共享同一引用导致响应式串扰）
  row.func_permissions = { ...(row.func_permissions || {}) };
  // 已分配记录且显式设置了数据等级时点亮对应等级（仅 0-2 有效；null 表示未显式分配，不点亮）
  if (row.has_permission && row.permission_level != null) {
    const levelKey = FIELD_LEVEL_KEYS[row.permission_level];
    if (levelKey) {
      row[levelKey] = true;
    }
  }
  return row;
};

const roleMenuFieldApiPrefix = "/api/system/rolemenufield/";
/** 角色菜单字段 API */
export const roleMenuFieldApi = {
  ...CreateApi(roleMenuFieldApiPrefix),
  /**
   * 获取功能权限定义列表（动态渲染功能权限列）
   */
  async GetFuncPermissionDefs() {
    const res: ApiResponse = await http.get(
      `${roleMenuFieldApiPrefix}func_permission_definitions/`
    );
    return res;
  },
  /**
   * 获取带有权限的角色列表（字段维度：菜单字段→分配角色面板）
   * @param params 查询参数（page/limit/menu_field_id）
   */
  async FieldRoles(params: object) {
    const res: ApiResponse = await http.get(
      `${roleMenuFieldApiPrefix}field_roles/`,
      {
        params
      }
    );
    return res;
  },
  /**
   * 获取带有权限的字段列表（角色维度：角色→授权字段面板）
   * @param params 查询参数（page/limit/role_id/menu_id）
   */
  async RoleFields(params: object) {
    const res: ApiResponse = await http.get(
      `${roleMenuFieldApiPrefix}role_fields/`,
      {
        params
      }
    );
    return res;
  },
  /**
   * 单条保存权限（upsert：无记录自动创建，有记录部分更新）
   * @param data { role, menu_field, permission_level?, func_permissions? }
   *        permission_level 与 func_permissions 均不传时删除记录（恢复默认权限）
   */
  async SavePermission(data: object) {
    const res: ApiResponse = await http.post(
      `${roleMenuFieldApiPrefix}save_permission/`,
      {
        data
      }
    );
    return res;
  },
  /**
   * 从角色页面批量更新字段权限（表头全选当前页）
   * @param data { role, menu, field_ids, permission_level?, func_permissions? }
   *        field_ids 为当前页字段 ID 列表；permission_level 与 func_permissions 至少传一个
   */
  async BatchUpdateRoleFields(data: object) {
    const res: ApiResponse = await http.post(
      `${roleMenuFieldApiPrefix}batch_update_role_fields/`,
      {
        data
      }
    );
    return res;
  },
  /**
   * 从菜单字段页面批量更新角色权限（表头全选当前页）
   * @param data { menu_field, role_ids, permission_level?, func_permissions? }
   *        role_ids 为当前页角色 ID 列表；permission_level 与 func_permissions 至少传一个
   */
  async BatchUpdateFieldRoles(data: object) {
    const res: ApiResponse = await http.post(
      `${roleMenuFieldApiPrefix}batch_update_field_roles/`,
      {
        data
      }
    );
    return res;
  },
  /**
   * 批量移除权限（表头取消全选当前页）
   * @param data
   *        角色页面：{ role, menu, field_ids }
   *        菜单字段页面：{ menu_field, role_ids }
   *        后端会保留存在功能权限的记录（重置数据等级为默认可读写），下载权限不丢失
   */
  async BatchDestroy(data: object) {
    return await http.request(
      "delete",
      `${roleMenuFieldApiPrefix}batch_destroy/`,
      {
        data
      }
    );
  }
};
