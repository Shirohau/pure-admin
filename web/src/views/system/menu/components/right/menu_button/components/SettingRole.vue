<script setup lang="ts">
import { onMounted, reactive, ref, watch } from "vue";
import { api as dept_api } from "@/views/system/dept/api";
import XEUtils from "xe-utils";
import { http } from "@/utils/http";
import { CreateApi } from "@/api/base";
import { ElMessage } from "element-plus";

// ====== 类型定义 ======
interface RoleMenuButton {
  /* 角色*/
  role: number;
  /* 角色名称 */
  role_name: string;
  /* 菜单按钮*/
  menu_button: number;
  /* 角色菜单按钮（未分配权限时为 null）*/
  role_menu_button: number | null;
  /* 是否有权限*/
  has_permission: boolean;
  /* 权限范围*/
  permission_range: number;
  /* 权限部门*/
  dept: number[];
  /* 是否需要数据访问（false 时默认全部数据，不渲染范围选择列）*/
  need_data_scope: boolean;
}

// 声明 props 类型
export interface FormProps {
  formInline?: {
    menu_button_id: number | undefined;
    menu_button_type: string | undefined;
  };
}

// 声明 props 默认值
// 推荐阅读：https://cn.vuejs.org/guide/typescript/composition-api.html#typing-component-props
const props = withDefaults(defineProps<FormProps>(), {
  formInline: () => ({ menu_button_id: undefined, menu_button_type: "" })
});

// ====== API ======
const apiPrefix = "/api/system/rolemenubutton/";
const api = {
  ...CreateApi(apiPrefix),
  /**
   * 获取带有权限的角色列表
   */
  async GetButtonRoles(params: object) {
    const res: ApiResponse = await http.get(`${apiPrefix}button_roles/`, {
      params
    });
    return res;
  },
  /**
   * 批量开启/关闭角色权限（表头全量授权开关，单次请求）
   * @param data { menu_button_id, has_permission, permission_range?, dept? }
   *        has_permission=true 为未分配角色批量创建权限记录（已分配的不受影响）；
   *        false 批量删除该按钮下全部角色权限记录
   * @param mes 是否弹出成功提示（默认 true）
   */
  async BatchButtonPermission(data: object, mes: boolean = true) {
    const res: ApiResponse = await http.post(
      `${apiPrefix}batch_button_permission/`,
      {
        data
      }
    );
    if (mes) ElMessage({ message: res.message, type: "success" });
    return res;
  },
  /**
   * 统一设置模式批量更新角色权限范围（单次请求）
   * @param data { menu_button_id, permission_range, dept? }
   *        仅更新该按钮下已分配权限的角色记录，未分配的角色仅本地同步
   * @param mes 是否弹出成功提示（默认 true）
   */
  async BatchButtonUpdate(data: object, mes: boolean = true) {
    const res: ApiResponse = await http.post(
      `${apiPrefix}batch_button_update/`,
      {
        data
      }
    );
    if (mes) ElMessage({ message: res.message, type: "success" });
    return res;
  }
};

// ====== 数据 ======
const dataOptions = [
  { value: 0, label: "仅本人" },
  { value: 1, label: "本部门" },
  { value: 2, label: "本部门及以下" },
  { value: 3, label: "自定义部门" },
  { value: 4, label: "全部" }
];

const roles = ref<RoleMenuButton[]>([]);
const deptTree = ref<any[]>([]);
const switchValue = ref(false);
const globalPermissionRange = ref(0);
const globalSelectedDepts = ref<number[]>([]);
/** 表头批量授权开关（true=当前按钮所有角色均已授权；切换即全量授权/取消，单次请求） */
const unifiedPermission = ref(false);
/** 批量授权请求进行中标记（期间禁用行内开关，避免并发修改） */
const batchLoading = ref(false);
const pageConfig = reactive({ page: 1, limit: 10, total: 10 });
// 当前按钮是否需要数据访问（false 时不渲染范围选择列，权限默认全部数据）
const needDataScope = ref(true);

/**
 * 构建权限提交数据
 * @param row 当前角色行数据
 * @returns { permission_range, dept } 提交给后端创建/更新接口的数据
 * @description 按钮无需数据访问（need_data_scope=false）时不做范围设置，默认全部数据(4)；
 * 否则统一设置模式下取全局范围与全局部门，单独设置模式取行内数据；
 * 权限范围为自定义部门(3)时携带关联部门列表，其他范围部门置空
 */
const buildPermissionData = (row: RoleMenuButton) => {
  // 无需数据访问的按钮：默认全部数据，不携带部门
  if (!needDataScope.value) {
    return { permission_range: 4, dept: [] };
  }
  const permissionRange = switchValue.value
    ? globalPermissionRange.value
    : row.permission_range;
  return {
    permission_range: permissionRange,
    dept:
      permissionRange === 3
        ? switchValue.value
          ? [...globalSelectedDepts.value]
          : (row.dept ?? [])
        : []
  };
};

/**
 * 保存单个角色的权限分配
 * @param row 当前角色行数据
 * @description 权限开关打开时调用创建接口新增权限，关闭时调用删除接口移除权限；
 * 创建成功后回写服务端生成的记录 ID 与最新权限范围/部门数据
 */
const savePermission = async (row: RoleMenuButton) => {
  if (row.has_permission) {
    // 新增权限：携带角色 / 按钮 / 权限范围 / 关联部门
    const res = await api.CreateObj({
      role: row.role,
      menu_button: props.formInline.menu_button_id,
      ...buildPermissionData(row)
    });
    Object.assign(row, {
      role_menu_button: res.data.id,
      permission_range: res.data.permission_range,
      dept: res.data.dept
    });
  } else {
    // 删除（关闭开关时必有已分配记录，记录 ID 非空）
    await api.DeleteObj(row.role_menu_button!);
  }
};

/**
 * 更新单个角色的权限范围
 * @param row 当前角色行数据
 * @description 选择关联部门（自定义部门模式下）或切换范围离开自定义部门时触发：
 * 1. 权限已分配（role_menu_button 存在）→ 调用更新接口持久化，并回写服务端最新数据；
 * 2. 权限未分配 → 仅本地生效，待开启权限开关创建时一并携带最新范围
 */
const updatePermission = async (row: RoleMenuButton) => {
  if (!row.has_permission || !row.role_menu_button) return;
  const res = await api.UpdateObj(
    row.role_menu_button,
    buildPermissionData(row)
  );
  Object.assign(row, {
    permission_range: res.data.permission_range,
    dept: res.data.dept
  });
};

/**
 * 行内数据权限范围变更
 * @param row 当前角色行数据
 * @description 切到"自定义部门"(3) 时仅本地切换、不调用接口，待选择部门时由部门选择器提交；
 * 切到其他范围时立即更新（同时清空关联部门，避免残留自定义部门数据）
 */
const handlePermissionRangeChange = async (row: RoleMenuButton) => {
  if (row.permission_range === 3) return;
  await updatePermission(row);
};

/**
 * 统一设置：将全局权限范围/关联部门批量应用到当前按钮下所有角色
 * @description 选择全局关联部门或切换范围离开自定义部门时触发，单次调用后端批量更新接口，
 * 仅持久化已分配权限的角色；未分配的行仅本地同步（开启权限时创建会携带最新范围）
 */
const updateAllPermission = async () => {
  const permissionRange = globalPermissionRange.value;
  const deptIds = permissionRange === 3 ? [...globalSelectedDepts.value] : [];
  // 单次批量接口：更新该按钮下所有已分配角色的权限范围
  await api.BatchButtonUpdate({
    menu_button_id: props.formInline.menu_button_id,
    permission_range: permissionRange,
    dept: deptIds
  });
  // 本地同步显示值（已分配的行由接口持久化，未分配的行仅本地生效）
  roles.value.forEach(row => {
    row.permission_range = permissionRange;
    row.dept = deptIds;
  });
};

/**
 * 统一设置：全局数据权限范围变更
 * @description 切到"自定义部门"(3) 时仅本地切换、不调用接口，待选择部门时由部门选择器批量提交；
 * 切到其他范围时立即批量更新（同时清空关联部门）
 */
const handleUnifiedRangeChange = () => {
  if (globalPermissionRange.value === 3) return;
  updateAllPermission();
};

// ====== 表头批量授权 ======
/**
 * 同步表头开关状态：全部角色已授权才显示开启，否则显示关闭（部分授权时点击即全量开启）
 */
const syncUnifiedPermission = () => {
  unifiedPermission.value =
    roles.value.length > 0 && roles.value.every(row => row.has_permission);
};

/**
 * 表头批量授权开关切换
 * @param val 切换后的目标值
 * @description 单次调用后端批量接口完成全量授权/取消：
 * 开启时仅创建未分配角色的权限记录（已分配的不受影响），关闭时删除该按钮下全部角色权限记录；
 * 成功后在本地回写行数据，失败时按实际行数据回滚开关状态
 */
const handleUnifiedPermissionChange = async (val: boolean) => {
  batchLoading.value = true;
  try {
    // 批量开启的新记录：统一设置模式取全局范围/部门，否则默认仅本人（与行内未分配时的显示值一致）
    const permissionRange = switchValue.value ? globalPermissionRange.value : 0;
    const deptIds = permissionRange === 3 ? [...globalSelectedDepts.value] : [];
    const res = await api.BatchButtonPermission({
      menu_button_id: props.formInline.menu_button_id,
      has_permission: val,
      permission_range: permissionRange,
      dept: deptIds
    });
    if (val) {
      // 批量开启：按后端返回的创建结果回写各行（已分配的行不在返回列表内，保持不变）
      const createdMap = new Map<number, any>(
        (res.data?.created ?? []).map((item: any) => [item.role, item])
      );
      roles.value.forEach(row => {
        const created = createdMap.get(row.role);
        if (!created) return;
        row.has_permission = true;
        row.role_menu_button = created.role_menu_button;
        row.permission_range = created.permission_range;
        row.dept = created.dept;
      });
    } else {
      // 批量关闭：重置所有行为未授权状态
      roles.value.forEach(row => {
        row.has_permission = false;
        row.role_menu_button = null;
        row.permission_range = 0;
        row.dept = [];
      });
    }
  } catch {
    // 请求失败：按实际行数据回滚表头开关状态
    syncUnifiedPermission();
  } finally {
    batchLoading.value = false;
  }
};

// 行内开关变化 / 重新加载后，联动同步表头开关状态
watch(
  () => roles.value.map(row => row.has_permission),
  () => syncUnifiedPermission()
);
// ====== 分页点击事件 ======
const handleCurrentChange = (page: number) => {
  pageConfig.page = page;
  getRole();
};
const handleSizeChange = (limit: number) => {
  pageConfig.limit = limit;
  getRole();
};
// 获取角色列表
const getRole = async () => {
  const params = {
    page: pageConfig.page,
    limit: pageConfig.limit,
    menu_button_id: props.formInline.menu_button_id
  };
  const { paginated, data }: ApiResponse = await api.GetButtonRoles(params);
  roles.value = data;
  // 同一按钮的所有行 need_data_scope 相同，取首行判断是否渲染范围选择列
  needDataScope.value = data[0]?.need_data_scope ?? true;
  pageConfig.page = paginated.page ?? 1;
  pageConfig.limit = paginated.limit ?? 10;
  pageConfig.total = paginated.total ?? 0;
};
// 获取部门树
const getDeptTree = async () => {
  const { data } = await dept_api.GetList();
  deptTree.value = XEUtils.toArrayTree(data, {
    key: "path",
    parentKey: "parent_path"
  });
};
// 初始化数据
onMounted(async () => {
  await Promise.all([getRole(), getDeptTree()]);
});
</script>

<template>
  <div>
    <el-table :data="roles" height="400">
      <el-table-column prop="role_name" label="角色名称">
        <template #header>
          <el-switch
            v-model="switchValue"
            inline-prompt
            style="
              --el-switch-on-color: #13ce66;
              --el-switch-off-color: #409eff;
            "
            active-text="统一设置"
            inactive-text="单独设置"
          />
        </template>
      </el-table-column>
      <!-- 无需数据访问的按钮不渲染范围选择列（权限默认全部数据）-->
      <el-table-column
        v-if="props.formInline.menu_button_type == 'api' && needDataScope"
        prop="permission_range"
        label="数据权限范围"
        min-width="180"
      >
        <template #header="">
          <el-select
            v-model="globalPermissionRange"
            :disabled="!switchValue"
            @change="handleUnifiedRangeChange"
          >
            <el-option
              v-for="item in dataOptions"
              :key="item.value"
              :value="item.value"
              :label="item.label"
            />
          </el-select>
        </template>
        <template #default="{ row }">
          <el-select
            v-model="row.permission_range"
            :disabled="switchValue"
            @change="handlePermissionRangeChange(row)"
          >
            <el-option
              v-for="item in dataOptions"
              :key="item.value"
              :value="item.value"
              :label="item.label"
            />
          </el-select>
        </template>
      </el-table-column>
      <el-table-column
        v-if="props.formInline.menu_button_type == 'api' && needDataScope"
        prop="dept"
        label="关联部门"
        min-width="180"
      >
        <template #header>
          <el-tree-select
            v-model="globalSelectedDepts"
            :data="deptTree"
            :disabled="!switchValue || globalPermissionRange != 3"
            :props="{ label: 'name', children: 'children' }"
            node-key="id"
            clearable
            multiple
            show-checkbox
            check-strictly
            check-on-click-node
            @change="updateAllPermission"
          />
        </template>
        <template #default="{ row }">
          <el-tree-select
            v-model="row.dept"
            :disabled="switchValue || row.permission_range != 3"
            :data="deptTree"
            :props="{ label: 'name', children: 'children' }"
            node-key="id"
            clearable
            multiple
            show-checkbox
            check-strictly
            check-on-click-node
            @change="updatePermission(row)"
          />
        </template>
      </el-table-column>
      <!-- 权限分配列：表头为批量授权开关（全开/全关，单次请求），行内为单角色开关 -->
      <el-table-column prop="has_permission" label="权限分配" align="center">
        <template #header>
          <el-tooltip
            content="批量开启/关闭当前按钮下所有角色权限"
            placement="top"
          >
            <el-switch
              v-model="unifiedPermission"
              :disabled="batchLoading"
              @change="handleUnifiedPermissionChange"
            />
          </el-tooltip>
        </template>
        <template #default="{ row }">
          <el-switch
            v-model="row.has_permission"
            :disabled="batchLoading"
            @change="savePermission(row)"
          />
        </template>
      </el-table-column>
    </el-table>

    <el-pagination
      v-model:current-page="pageConfig.page"
      v-model:page-size="pageConfig.limit"
      style="margin-top: 10px"
      background
      layout="total, sizes, prev, pager, next, jumper"
      :total="pageConfig.total"
      @size-change="handleSizeChange"
      @current-change="handleCurrentChange"
    />
  </div>
</template>
