<script setup lang="ts">
/**
 * 授权按钮面板
 * @description 展示当前角色在某菜单下的按钮权限列表，支持：
 * 1. 单个按钮的权限分配（has_permission 开关：打开创建 / 关闭删除）
 * 2. 数据权限范围设置（仅本人/本部门/本部门及以下/自定义部门/全部）
 * 3. 头部"统一设置"模式：一次批量设置所有按钮的数据权限范围与关联部门
 * 4. 已分配权限的按钮修改范围即时持久化；切到"自定义部门"时不发请求，选择部门时才提交
 * 通过 useImpowerContext 注入当前抽屉实例的授权上下文（按钮列表 / 分页状态 / 角色与菜单信息）
 */
import { onMounted, ref, watch } from "vue";
import { api as deptApi } from "@/views/system/dept/api";
import XEUtils from "xe-utils";

import { useImpowerContext } from "../hooks/useImpower";
import { roleMenuButtonApi, type RoleMenuButton } from "../hooks/impowerApi";

/** 数据权限范围：自定义部门（值为 3 时需携带关联部门列表） */
const PERMISSION_RANGE_CUSTOM_DEPT = 3;
/** 数据权限范围：全部（按钮无需数据访问时的默认范围） */
const PERMISSION_RANGE_ALL = 4;

// 注入当前授权抽屉实例的上下文（角色信息 / 菜单信息 / 按钮列表 / 分页状态）
const { menuButton, menuButtonPageConfig, getMenuButton, roleInfo, menuInfo } =
  useImpowerContext();

// ====== 数据 ======
/** 数据权限范围下拉选项（与后端 DATASCOPE_CHOICES 一一对应） */
const permissionRangeOptions = [
  { value: 0, label: "仅本人" },
  { value: 1, label: "本部门" },
  { value: 2, label: "本部门及以下" },
  { value: 3, label: "自定义部门" },
  { value: 4, label: "全部" }
];

/** 部门树数据（用于自定义部门的多选树） */
const deptTree = ref<any[]>([]);
/** 是否启用"统一设置"模式（表头批量设置所有按钮的权限范围与部门） */
const unifiedMode = ref(false);
/** 统一设置模式下的全局数据权限范围 */
const unifiedPermissionRange = ref(0);
/** 统一设置模式下的全局选中部门 ID 列表 */
const unifiedSelectedDepts = ref<number[]>([]);
/** 表头批量授权开关（true=当前菜单所有按钮均已授权；切换即全量授权/取消，单次请求） */
const unifiedPermission = ref(false);
/** 批量授权请求进行中标记（期间禁用行内开关，避免并发修改） */
const batchLoading = ref(false);

/** 部门树选择器公共配置（行内与全局表头共用，避免重复声明） */
const deptTreeSelectProps = {
  props: { label: "name", children: "children" },
  nodeKey: "id",
  clearable: true,
  multiple: true,
  showCheckbox: true,
  checkStrictly: true,
  checkOnClickNode: true
};

/**
 * 构建按钮权限提交数据
 * @param row 当前按钮行数据
 * @returns { permission_range, dept } 提交给后端创建/更新接口的数据
 * @description 按钮无需数据访问（need_data_scope=false）时不做范围设置，默认全部数据(4)；
 * 否则统一设置模式下取全局范围与全局部门，单独设置模式取行内数据；
 * 权限范围为自定义部门(3)时携带关联部门列表，其他范围部门置空
 */
const buildPermissionData = (row: RoleMenuButton) => {
  // 无需数据访问的按钮：默认全部数据，不携带部门
  if (!row.need_data_scope) {
    return { permission_range: PERMISSION_RANGE_ALL, dept: [] };
  }
  const permissionRange = unifiedMode.value
    ? unifiedPermissionRange.value
    : row.permission_range;
  return {
    permission_range: permissionRange,
    dept:
      permissionRange === PERMISSION_RANGE_CUSTOM_DEPT
        ? unifiedMode.value
          ? unifiedSelectedDepts.value
          : (row.dept ?? [])
        : []
  };
};

/**
 * 保存单个按钮的权限分配
 * @param row 当前按钮行数据
 * @description 权限开关打开时调用创建接口新增权限，关闭时调用删除接口移除权限；
 * 创建成功后回写服务端生成的记录 ID 与最新权限范围/部门数据
 */
const savePermission = async (row: RoleMenuButton) => {
  if (row.has_permission) {
    // 新增权限：携带角色 / 按钮 / 权限范围 / 关联部门
    const res = await roleMenuButtonApi.CreateObj({
      role: row.role,
      menu_button: row.menu_button,
      ...buildPermissionData(row)
    });
    Object.assign(row, {
      role_menu_button: res.data.id,
      permission_range: res.data.permission_range,
      dept: res.data.dept
    });
  } else {
    // 移除权限（关闭开关时必有已分配记录，记录 ID 非空）
    await roleMenuButtonApi.DeleteObj(row.role_menu_button!);
  }
};

/**
 * 更新单个按钮的权限范围
 * @param row 当前按钮行数据
 * @description 选择关联部门（自定义部门模式下）或切换范围离开自定义部门时触发：
 * 1. 权限已分配（role_menu_button 存在）→ 调用更新接口持久化，并回写服务端最新数据；
 * 2. 权限未分配 → 仅本地生效，待开启权限开关创建时一并携带最新范围
 */
const updatePermission = async (row: RoleMenuButton) => {
  if (!row.has_permission || !row.role_menu_button) return;
  const res = await roleMenuButtonApi.UpdateObj(
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
 * @param row 当前按钮行数据
 * @description 切到"自定义部门"(3) 时仅本地切换、不调用接口，待选择部门时由部门选择器提交；
 * 切到其他范围时立即更新（同时清空关联部门，避免残留自定义部门数据）
 */
const handlePermissionRangeChange = async (row: RoleMenuButton) => {
  if (row.permission_range === PERMISSION_RANGE_CUSTOM_DEPT) return;
  await updatePermission(row);
};

/**
 * 统一设置：将全局权限范围/关联部门批量应用到当前菜单下所有按钮
 * @description 选择全局关联部门或切换范围离开自定义部门时触发，单次调用后端批量更新接口，
 * 仅持久化已分配权限的按钮；未分配的行仅本地同步（开启权限时创建会携带最新范围）
 */
const updateAllPermission = async () => {
  const permissionRange = unifiedPermissionRange.value;
  const deptIds =
    permissionRange === PERMISSION_RANGE_CUSTOM_DEPT
      ? [...unifiedSelectedDepts.value]
      : [];
  // 单次批量接口：更新该角色在当前菜单下所有已分配按钮的权限范围
  await roleMenuButtonApi.BatchUpdate({
    role_id: roleInfo.id,
    menu_id: menuInfo.id,
    permission_range: permissionRange,
    dept: deptIds
  });
  // 本地同步显示值（已分配的行由接口持久化，未分配的行仅本地生效）；
  // 无需数据访问的按钮不参与范围设置（默认全部数据）
  menuButton.value.forEach(row => {
    if (!row.need_data_scope) return;
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
  if (unifiedPermissionRange.value === PERMISSION_RANGE_CUSTOM_DEPT) return;
  updateAllPermission();
};

// ====== 表头批量授权 ======
/**
 * 同步表头开关状态：全部按钮已授权才显示开启，否则显示关闭（部分授权时点击即全量开启）
 */
const syncUnifiedPermission = () => {
  const rows = menuButton.value;
  unifiedPermission.value =
    rows.length > 0 && rows.every(row => row.has_permission);
};

/**
 * 表头批量授权开关切换
 * @param val 切换后的目标值
 * @description 单次调用后端批量接口完成全量授权/取消：
 * 开启时仅创建未分配按钮的权限记录（已分配的不受影响），关闭时删除该角色在该菜单下全部按钮权限记录；
 * 成功后在本地回写行数据，失败时按实际行数据回滚开关状态
 */
const handleUnifiedPermissionChange = async (val: boolean) => {
  batchLoading.value = true;
  try {
    // 批量开启的新记录：统一设置模式取全局范围/部门，否则默认仅本人（与行内未分配时的显示值一致）
    const permissionRange = unifiedMode.value
      ? unifiedPermissionRange.value
      : 0;
    const deptIds =
      permissionRange === PERMISSION_RANGE_CUSTOM_DEPT
        ? [...unifiedSelectedDepts.value]
        : [];
    const res = await roleMenuButtonApi.BatchPermission({
      role_id: roleInfo.id,
      menu_id: menuInfo.id,
      has_permission: val,
      permission_range: permissionRange,
      dept: deptIds
    });
    if (val) {
      // 批量开启：按后端返回的创建结果回写各行（已分配的行不在返回列表内，保持不变）
      const createdMap = new Map<number, any>(
        (res.data?.created ?? []).map((item: any) => [item.menu_button, item])
      );
      menuButton.value.forEach(row => {
        const created = createdMap.get(row.menu_button);
        if (!created) return;
        row.has_permission = true;
        row.role_menu_button = created.role_menu_button;
        row.permission_range = created.permission_range;
        row.dept = created.dept;
      });
    } else {
      // 批量关闭：重置所有行为未授权状态
      menuButton.value.forEach(row => {
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

// 行内开关变化 / 切换菜单重新加载后，联动同步表头开关状态
watch(
  () => menuButton.value.map(row => row.has_permission),
  () => syncUnifiedPermission()
);

// ====== 分页事件 ======
/** 页码变化时刷新按钮权限列表 */
const handleCurrentChange = (page: number) => {
  menuButtonPageConfig.page = page;
  getMenuButton();
};
/** 每页条数变化时刷新按钮权限列表 */
const handleSizeChange = (limit: number) => {
  menuButtonPageConfig.limit = limit;
  getMenuButton();
};

/** 获取部门树数据（用于"自定义部门"权限范围的选择） */
const getDeptTree = async () => {
  const { data } = await deptApi.GetList();
  // 扁平列表按 path / parent_path 转为树形结构
  deptTree.value = XEUtils.toArrayTree(data, {
    key: "path",
    parentKey: "parent_path"
  });
};

// 初始化：加载部门树
onMounted(async () => {
  await getDeptTree();
});
</script>

<template>
  <div class="authorized-btn-wrap">
    <!-- 表格区域独立滚动：高度由 flex:1 撑满，滚动条在此容器内，不依赖 el-table 的 height 解析 -->
    <div class="authorized-btn-table">
      <el-table :data="menuButton">
        <!-- 按钮名称列：表头为"统一设置"模式开关 -->
        <el-table-column
          prop="menu_button_name"
          label="按钮名称"
          min-width="70"
        >
          <template #header>
            <el-switch
              v-model="unifiedMode"
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

        <!-- 数据权限范围列：表头为全局范围选择器（统一设置模式），行内为单按钮范围选择器 -->
        <el-table-column
          prop="permission_range"
          label="数据权限范围"
          min-width="180"
        >
          <template #header>
            <el-select
              v-model="unifiedPermissionRange"
              :disabled="!unifiedMode"
              @change="handleUnifiedRangeChange"
            >
              <el-option
                v-for="item in permissionRangeOptions"
                :key="item.value"
                :value="item.value"
                :label="item.label"
              />
            </el-select>
          </template>
          <template #default="{ row }">
            <!-- 仅 api 类型且需要数据访问的按钮渲染范围选择器 -->
            <el-select
              v-if="row.button_type === 'api' && row.need_data_scope"
              v-model="row.permission_range"
              :disabled="unifiedMode"
              @change="handlePermissionRangeChange(row)"
            >
              <el-option
                v-for="item in permissionRangeOptions"
                :key="item.value"
                :value="item.value"
                :label="item.label"
              />
            </el-select>
            <!-- 无需数据访问/非接口按钮：权限固定为全部数据，不做范围设置 -->
            <el-text v-else size="small" type="info" />
          </template>
        </el-table-column>

        <!-- 关联部门列：表头为全局部门树（统一设置模式），行内为单按钮部门树 -->
        <el-table-column prop="dept" label="关联部门" min-width="180">
          <template #header>
            <el-tree-select
              v-model="unifiedSelectedDepts"
              :data="deptTree"
              :disabled="
                !unifiedMode ||
                unifiedPermissionRange !== PERMISSION_RANGE_CUSTOM_DEPT
              "
              v-bind="deptTreeSelectProps"
              @change="updateAllPermission"
            />
          </template>
          <template #default="{ row }">
            <!-- 仅 api 类型且需要数据访问、范围为自定义部门时可选部门 -->
            <el-tree-select
              v-if="row.button_type === 'api' && row.need_data_scope"
              v-model="row.dept"
              :disabled="
                unifiedMode ||
                row.permission_range !== PERMISSION_RANGE_CUSTOM_DEPT
              "
              :data="deptTree"
              v-bind="deptTreeSelectProps"
              @change="updatePermission(row)"
            />
            <!-- 无需数据访问/非接口按钮：无关联部门概念 -->
            <el-text v-else size="small" type="info" />
          </template>
        </el-table-column>

        <!-- 权限分配列：表头为批量授权开关（全开/全关，单次请求），行内为单按钮开关 -->
        <el-table-column
          prop="has_permission"
          label="权限分配"
          align="center"
          width="90"
        >
          <template #header>
            <el-tooltip
              content="批量开启/关闭当前菜单下所有按钮权限"
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
    </div>

    <!-- 分页器固定在面板底部，不参与表格区域滚动 -->
    <el-pagination
      v-model:current-page="menuButtonPageConfig.page"
      v-model:page-size="menuButtonPageConfig.limit"
      class="authorized-btn-pagination"
      background
      layout="total, sizes, prev, pager, next, jumper"
      :total="menuButtonPageConfig.total"
      @size-change="handleSizeChange"
      @current-change="handleCurrentChange"
    />
  </div>
</template>

<style scoped>
.authorized-btn-wrap {
  display: flex;
  flex: 1;
  flex-direction: column;
  min-height: 0;
  overflow: hidden;
}

/* 表格区域：flex 撑满剩余高度，表头固定、表体自行滚动 */
.authorized-btn-table {
  flex: 1;
  min-height: 0;
  overflow: hidden;
}

.authorized-btn-table :deep(.el-table) {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.authorized-btn-table :deep(.el-table__inner-wrapper) {
  display: flex;
  flex: 1;
  flex-direction: column;
  overflow: hidden;
}

.authorized-btn-table :deep(.el-table__header-wrapper) {
  flex-shrink: 0;
}

.authorized-btn-table :deep(.el-table__body-wrapper) {
  flex: 1;
  overflow-y: auto;
}

/* 分页器固定贴底，不参与表格区域滚动 */
.authorized-btn-pagination {
  flex: none;
  padding: 10px 0 0;
  margin-top: 10px;
}
</style>
