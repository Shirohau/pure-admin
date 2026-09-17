<script setup lang="ts">
/**
 * 授权字段面板（角色页面 → 授权字段）
 * @description 展示当前角色在某菜单下的字段权限列表，支持按字段分配权限：
 * 数据权限等级（level_0 禁止 / level_1 只读 / level_2 可读写）三档互斥，
 * 功能权限（func_permissions JSON，如"可下载"）为独立权限，可自由组合。
 * 表头全选为"当前页全选"：勾选某等级/功能权限即对当前页字段批量分配/移除对应权限。
 * 表头全选为派生状态：随当前页数据实时计算（翻页/单条勾选后自动更新）。
 * 通过 useImpowerContext 注入当前抽屉实例的授权上下文（字段列表、分页）
 */
import { computed, onMounted, ref } from "vue";
import { useImpowerContext } from "../hooks/useImpower";
import {
  FIELD_LEVEL_KEYS,
  PERMISSION_LEVEL,
  roleMenuFieldApi,
  type FuncPermissionDef,
  type RoleMenuField
} from "../hooks/impowerApi";

const { roleInfo, menuInfo, menuField, menuFieldPageConfig, getMenuField } =
  useImpowerContext();

/** 功能权限定义列表（接口获取，动态渲染功能权限列） */
const funcPermissionDefs = ref<FuncPermissionDef[]>([]);

/** 当前页字段 ID 列表（表头全选批量操作的作用范围） */
const currentPageFieldIds = computed(() =>
  menuField.value.map(row => row.menu_field)
);

/** 当前页未禁止字段 ID 列表（功能权限批量操作的作用范围：禁止状态字段不参与功能权限批量设置） */
const activeFieldIds = computed(() =>
  menuField.value.filter(row => !row.level_0).map(row => row.menu_field)
);

/**
 * 当前页某数据等级的表头全选状态（派生状态，随当前页数据实时计算）
 * @description 全选当且仅当当前页所有行该等级均为 true；
 * 翻页或单条勾选/取消后自动重算，保证表头始终反映当前页真实状态
 * @param level 数据权限等级（0 禁止 / 1 只读 / 2 可读写）
 */
const levelHeaderChecked = (level: number) => {
  const rows = menuField.value;
  if (rows.length === 0) return false;
  return rows.every(row => !!row[FIELD_LEVEL_KEYS[level]]);
};

/**
 * 当前页某数据等级的表头半选状态（部分行选中时为 true，全选/全不选为 false）
 * @param level 数据权限等级（0 禁止 / 1 只读 / 2 可读写）
 */
const levelHeaderIndeterminate = (level: number) => {
  const rows = menuField.value;
  if (rows.length === 0) return false;
  const checkedCount = rows.filter(
    row => !!row[FIELD_LEVEL_KEYS[level]]
  ).length;
  return checkedCount > 0 && checkedCount < rows.length;
};

/** 当前页功能权限全选状态：仅统计未禁止的字段（禁止状态下功能权限恒为关闭，不参与全选统计） */
const funcHeaderChecked = (key: string) => {
  const rows = menuField.value.filter(row => !row.level_0);
  if (rows.length === 0) return false;
  return rows.every(row => !!row.func_permissions?.[key]);
};

/**
 * 当前页功能权限表头半选状态（仅统计未禁止的字段：部分开启时为 true，全开/全关为 false）
 * @param key 功能权限 key（如 can_download）
 */
const funcHeaderIndeterminate = (key: string) => {
  const rows = menuField.value.filter(row => !row.level_0);
  if (rows.length === 0) return false;
  const checkedCount = rows.filter(row => !!row.func_permissions?.[key]).length;
  return checkedCount > 0 && checkedCount < rows.length;
};

/**
 * 保存失败后的兜底恢复
 * @description 操作失败时重置表头全选状态并重新拉取列表，使 UI 与后端数据保持一致
 */
const restoreAfterFailure = async () => {
  try {
    await getMenuField();
  } catch {
    // 列表刷新失败时忽略，保留现有数据等待用户重试
  }
};

/**
 * 保存单个字段的数据权限等级分配（0 禁止 / 1 只读 / 2 可读写，三者互斥）
 * 特殊规则：勾选"禁止访问"时，强制将全部功能权限置为 false（禁止访问即不允许任何功能），
 * UI 立即同步且随保存一并写入后端。
 * @param value 勾选状态（true 分配 / false 移除）
 * @param row 当前字段行数据
 * @param level 数据权限等级（0 禁止 / 1 只读 / 2 可读写）
 */
const savePermission = async (
  value: string | number | boolean,
  row: RoleMenuField,
  level: number
) => {
  try {
    // 访问等级互斥：勾选当前等级时，取消其他等级的勾选状态（UI 立即同步）
    if (value) {
      FIELD_LEVEL_KEYS.forEach((key, index) => {
        if (index !== level) row[key] = false;
      });
    }
    if (value) {
      // 禁止访问时强制关闭全部功能权限：UI 立即同步，禁用状态随之生效
      if (level === PERMISSION_LEVEL.DENIED) {
        Object.keys(row.func_permissions || {}).forEach(
          key => (row.func_permissions![key] = false)
        );
      }
      // 新增/更新数据权限等级（upsert：无记录自动创建）
      const data: Record<string, string | number | boolean | object> = {
        role: row.role,
        menu_field: row.menu_field,
        permission_level: level
      };
      // 禁止访问时必须同时把所有功能权限置为 false（与 UI 同步写入后端）
      if (level === PERMISSION_LEVEL.DENIED) {
        const funcs: Record<string, boolean> = {};
        funcPermissionDefs.value.forEach(def => (funcs[def.key] = false));
        data.func_permissions = funcs;
      }
      await roleMenuFieldApi.SavePermission(data);
    } else {
      // 取消访问等级：
      // 1) 取消"禁止"（level 0）：保留记录仅清除数据等级（置 null）。
      //    修复说明：勾选"禁止"时会强制把功能权限置 false 并写入后端，若删除记录会导致
      //    can_download=false 等关闭状态丢失（后端恢复"默认全部权限"），UI 与后端不一致；
      // 2) 取消"只读/可读写"（level 1/2）：未修改功能权限，按原逻辑处理——
      //    功能权限集非空（显式配置过，含全 false 的显式关闭状态）则仅清除数据等级，
      //    仅从未配置过功能权限（fp 为空）才删除记录（回到"默认拥有全部权限"语义）
      if (level === PERMISSION_LEVEL.DENIED) {
        await roleMenuFieldApi.SavePermission({
          role: row.role,
          menu_field: row.menu_field,
          permission_level: null
        });
        return;
      }
      // 功能权限集非空即视为"显式配置过"（含全 false 的显式关闭状态，如禁止联动写入的
      // {can_download:false}），必须保留记录仅清除数据等级，否则删除记录会丢失关闭状态；
      // 仅 fp 为空（从未配置过功能权限）才删除记录，回到"默认拥有全部权限"语义
      const hasFuncPermission =
        Object.keys(row.func_permissions || {}).length > 0;
      if (hasFuncPermission) {
        await roleMenuFieldApi.SavePermission({
          role: row.role,
          menu_field: row.menu_field,
          permission_level: null
        });
      } else {
        // 从未分配过功能权限：删除记录（回到"默认拥有全部权限"语义）
        await roleMenuFieldApi.SavePermission({
          role: row.role,
          menu_field: row.menu_field
        });
      }
    }
    await getMenuField();
  } catch {
    // 保存失败：刷新列表，恢复后端真实状态（UI 勾选可能已被本地修改）
    await restoreAfterFailure();
  }
};

/**
 * 保存单个字段的功能权限（可与数据权限等级自由组合，互不影响）
 * @param value 勾选状态（true 开启 / false 关闭）
 * @param row 当前字段行数据
 * @param funcKey 功能权限 key（如 can_download）
 */
const saveFuncPermission = async (
  value: string | number | boolean,
  row: RoleMenuField,
  funcKey: string
) => {
  try {
    const funcs: Record<string, boolean> = {
      ...(row.func_permissions || {})
    };
    funcs[funcKey] = !!value;
    await roleMenuFieldApi.SavePermission({
      role: row.role,
      menu_field: row.menu_field,
      func_permissions: funcs
    });
    await getMenuField();
  } catch {
    await restoreAfterFailure();
  }
};
// ====== 分页点击事件 ======
/** 页码变化时刷新列表 */
const handleCurrentChange = (page: number) => {
  menuFieldPageConfig.page = page;
  getMenuField();
};
/** 每页条数变化时刷新列表 */
const handleSizeChange = (limit: number) => {
  menuFieldPageConfig.limit = limit;
  getMenuField();
};

/**
 * 表头全选：对当前页所有字段批量分配/移除某一数据权限等级（0 禁止 / 1 只读 / 2 可读写）
 * 特殊规则：批量勾选"禁止访问"时，同时批量关闭当前页所有字段的全部功能权限。
 * @param value 勾选状态（true 批量分配 / false 批量移除）
 * @param level 数据权限等级（0 禁止 / 1 只读 / 2 可读写）
 */
const saveAllLevel = async (
  value: string | number | boolean,
  level: number
) => {
  try {
    if (value) {
      const data: Record<string, number | boolean | object> = {
        role: roleInfo.id,
        menu: menuInfo.id,
        field_ids: currentPageFieldIds.value,
        permission_level: level
      };
      // 禁止访问时同时批量关闭全部功能权限（后端按传入的 func_permissions 覆盖）
      if (level === PERMISSION_LEVEL.DENIED) {
        const funcs: Record<string, boolean> = {};
        funcPermissionDefs.value.forEach(def => (funcs[def.key] = false));
        data.func_permissions = funcs;
      }
      await roleMenuFieldApi.BatchUpdateRoleFields(data);
    } else {
      // 取消全选：批量移除当前页字段的访问权限（存在功能权限的记录由后端保留）
      await roleMenuFieldApi.BatchDestroy({
        role: roleInfo.id,
        menu: menuInfo.id,
        field_ids: currentPageFieldIds.value
      });
    }
    await getMenuField();
  } catch {
    await restoreAfterFailure();
  }
};

/**
 * 表头全选：对当前页所有字段批量设置/取消某一功能权限
 * @param value 勾选状态（true 批量开启 / false 批量关闭）
 * @param funcKey 功能权限 key（如 can_download）
 */
const saveAllFuncPermission = async (
  value: string | number | boolean,
  funcKey: string
) => {
  try {
    // 仅对未禁止的字段批量设置功能权限：禁止状态下功能权限必须保持关闭（禁止即不允许任何功能）
    const targetFieldIds = activeFieldIds.value;
    if (targetFieldIds.length === 0) return;
    const funcs: Record<string, boolean> = {};
    funcs[funcKey] = !!value;
    await roleMenuFieldApi.BatchUpdateRoleFields({
      role: roleInfo.id,
      menu: menuInfo.id,
      field_ids: targetFieldIds,
      func_permissions: funcs
    });
    await getMenuField();
  } catch {
    await restoreAfterFailure();
  }
};

// 初始化：加载功能权限定义（列渲染依赖）
onMounted(async () => {
  const { data } = await roleMenuFieldApi.GetFuncPermissionDefs();
  funcPermissionDefs.value = data || [];
});
</script>

<template>
  <div class="authorized-field-wrap">
    <el-alert
      title="若未显式分配权限，则默认拥有全部权限；一旦分配了权限，则仅拥有被分配的权限"
      type="primary"
      :closable="false"
    />
    <!-- 表格区域独立滚动：高度由 flex:1 撑满，滚动条在此容器内，不依赖 el-table 的 height 解析 -->
    <div class="authorized-field-table">
      <el-table :data="menuField">
        <el-table-column
          prop="menu_field_name"
          label="字段名称"
          align="center"
        />
        <el-table-column align="left">
          <template #header="">
            <el-checkbox
              :model-value="levelHeaderChecked(0)"
              :indeterminate="levelHeaderIndeterminate(0)"
              label="禁止访问"
              @change="saveAllLevel($event, 0)"
            />
          </template>
          <template #default="{ row }">
            <el-checkbox
              v-model="row.level_0"
              @change="savePermission($event, row, 0)"
            />
          </template>
        </el-table-column>
        <el-table-column align="left">
          <template #header="">
            <el-checkbox
              :model-value="levelHeaderChecked(1)"
              :indeterminate="levelHeaderIndeterminate(1)"
              label="只读"
              @change="saveAllLevel($event, 1)"
            />
          </template>
          <template #default="{ row }">
            <el-checkbox
              v-model="row.level_1"
              @change="savePermission($event, row, 1)"
            />
          </template>
        </el-table-column>
        <el-table-column align="left">
          <template #header="">
            <el-checkbox
              :model-value="levelHeaderChecked(2)"
              :indeterminate="levelHeaderIndeterminate(2)"
              label="可读写"
              @change="saveAllLevel($event, 2)"
            />
          </template>
          <template #default="{ row }">
            <el-checkbox
              v-model="row.level_2"
              @change="savePermission($event, row, 2)"
            />
          </template>
        </el-table-column>
        <!-- 功能权限列：根据接口定义动态渲染（如"可下载"） -->
        <el-table-column
          v-for="def in funcPermissionDefs"
          :key="def.key"
          :align="'left'"
        >
          <template #header="">
            <el-checkbox
              :model-value="funcHeaderChecked(def.key)"
              :indeterminate="funcHeaderIndeterminate(def.key)"
              :label="def.label"
              :disabled="levelHeaderChecked(0)"
              @change="saveAllFuncPermission($event, def.key)"
            />
          </template>
          <template #default="{ row }">
            <!-- 禁止访问时禁用功能权限：无法勾选，保存时由 savePermission 强制置 false -->
            <el-checkbox
              v-model="row.func_permissions[def.key]"
              :disabled="row.level_0"
              @change="saveFuncPermission($event, row, def.key)"
            />
          </template>
        </el-table-column>
      </el-table>
    </div>

    <!-- 分页器固定在面板底部，不参与表格区域滚动 -->
    <el-pagination
      v-model:current-page="menuFieldPageConfig.page"
      v-model:page-size="menuFieldPageConfig.limit"
      class="authorized-field-pagination"
      background
      layout="total, sizes, prev, pager, next, jumper"
      :total="menuFieldPageConfig.total"
      @size-change="handleSizeChange"
      @current-change="handleCurrentChange"
    />
  </div>
</template>

<style scoped>
.authorized-field-wrap {
  display: flex;
  flex: 1;
  flex-direction: column;
  min-height: 0;
  overflow: hidden;
}

/* 表格区域：flex 撑满剩余高度，表头固定、表体自行滚动 */
.authorized-field-table {
  flex: 1;
  min-height: 0;
  margin-top: 10px;
  overflow: hidden;
}

.authorized-field-table :deep(.el-table) {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.authorized-field-table :deep(.el-table__inner-wrapper) {
  display: flex;
  flex: 1;
  flex-direction: column;
  overflow: hidden;
}

.authorized-field-table :deep(.el-table__header-wrapper) {
  flex-shrink: 0;
}

.authorized-field-table :deep(.el-table__body-wrapper) {
  flex: 1;
  overflow-y: auto;
}

/* 分页器固定贴底，不参与表格区域滚动 */
.authorized-field-pagination {
  flex: none;
  padding: 10px 0 0;
  margin-top: 10px;
}
</style>
