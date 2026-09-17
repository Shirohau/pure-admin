<template>
  <el-dialog
    v-model="dialogVisible"
    :title="`授权角色：${roleInfo?.name ?? ''}`"
    width="90%"
    top="5vh"
    append-to-body
    destroy-on-close
    class="authorized-user-dialog"
  >
    <div class="authorized-user-body">
      <!-- 左侧：未授权用户 -->
      <div class="authorized-user-panel authorized-user-panel--left">
        <div class="authorized-user-panel-table">
          <user-table
            ref="leftTableRef"
            class="h-full"
            lookup="id__not_in"
            :ids="ids"
          >
            <template #actionbar-right>
              <div class="authorized-user-panel-header">
                <div class="panel-title">
                  <el-icon class="panel-title__icon"><UserFilled /></el-icon>
                  <span class="panel-title__text">未授权用户</span>
                </div>
                <div class="panel-subtitle">可选择用户加入角色</div>
              </div>
            </template>
          </user-table>
        </div>
      </div>

      <!-- 中间：转移按钮 -->
      <div class="authorized-user-actions">
        <div class="authorized-user-actions__decor">
          <div class="decor-line decor-line--top" />
          <div class="decor-dot" />
          <div class="decor-line decor-line--bottom" />
        </div>
        <div class="authorized-user-action-item">
          <div class="action-button-wrapper">
            <el-button
              :type="actionButtonType"
              :icon="actionButtonIcon"
              circle
              size="large"
              :loading="loading"
              :disabled="!canOperate"
              class="action-button"
              @click="handleAuthorizedUser"
            />
            <div v-if="canOperate" class="action-ripple" />
          </div>
          <div class="authorized-user-action-text">
            <template v-if="isBothAction">
              <span class="action-text__main">
                <span class="action-text__add"
                  >加入 {{ leftSelectedCount }} 位</span
                >
                ，
                <span class="action-text__remove"
                  >移出 {{ rightSelectedCount }} 位</span
                >
              </span>
            </template>
            <template v-else-if="needAdd">
              <span class="action-text__main">
                <span class="action-text__add"
                  >加入 {{ leftSelectedCount }} 位用户</span
                >
              </span>
            </template>
            <template v-else-if="needRemove">
              <span class="action-text__main">
                <span class="action-text__remove"
                  >移出 {{ rightSelectedCount }} 位用户</span
                >
              </span>
            </template>
            <span v-else class="action-text__main action-text__placeholder"
              >请选择用户</span
            >
          </div>
        </div>
      </div>

      <!-- 右侧：已授权用户 -->
      <div class="authorized-user-panel authorized-user-panel--right">
        <div class="authorized-user-panel-table">
          <user-table
            ref="rightTableRef"
            class="h-full"
            lookup="id__in"
            :ids="ids"
          >
            <template #actionbar-right>
              <div class="authorized-user-panel-header">
                <div class="panel-title">
                  <el-icon class="panel-title__icon panel-title__icon--success">
                    <CircleCheckFilled />
                  </el-icon>
                  <span class="panel-title__text">已授权用户</span>
                </div>
                <div class="panel-subtitle">可选择用户移出角色</div>
              </div>
            </template>
          </user-table>
        </div>
      </div>
    </div>
  </el-dialog>
</template>

<script lang="ts" setup>
/**
 * 授权用户弹窗
 * @description 管理当前角色的已授权人员：左侧展示未授权用户、右侧展示已授权用户，
 * 通过中间转移按钮批量新增/移除角色下的用户，操作后回写并刷新两侧表格。
 * 弹窗独立于抽屉渲染（append-to-body），尺寸由固定高度 + flex 布局控制。
 */
import { computed, ref } from "vue";
import {
  ArrowLeft,
  ArrowRight,
  Switch,
  UserFilled,
  CircleCheckFilled,
  Refresh
} from "@element-plus/icons-vue";
import { ElMessage } from "element-plus";
import UserTable from "./asideUserTable/index.vue";
import { useImpowerContext, type RoleInfo } from "../hooks/useImpower";
import { api } from "../api";

const { roleInfo, setRoleInfo } = useImpowerContext();

const props = defineProps<{ dialogVisible: boolean }>();
const emit = defineEmits<{
  (e: "update:dialogVisible", value: boolean): void;
}>();

const dialogVisible = computed({
  get: () => props.dialogVisible,
  set: val => emit("update:dialogVisible", val)
});

const loading = ref(false);

// 表格引用
const leftTableRef = ref();
const rightTableRef = ref();

// 两侧表格的选中数量（用于按钮禁用与数量提示）
const leftSelectedCount = computed(
  () => leftTableRef.value?.selectedData?.length ?? 0
);
const rightSelectedCount = computed(
  () => rightTableRef.value?.selectedData?.length ?? 0
);

// 判断需要执行的操作类型
const needAdd = computed(() => leftSelectedCount.value > 0);
const needRemove = computed(() => rightSelectedCount.value > 0);

// 是否可以执行操作（有任一边选中即可）
const canOperate = computed(() => needAdd.value || needRemove.value);

// 是否同时执行两种操作
const isBothAction = computed(() => needAdd.value && needRemove.value);

// 按钮类型
const actionButtonType = computed(() => {
  if (isBothAction.value) return "primary";
  if (needAdd.value) return "success";
  if (needRemove.value) return "danger";
  return "default";
});

// 按钮图标
const actionButtonIcon = computed(() => {
  if (isBothAction.value) return Switch;
  if (needAdd.value) return ArrowRight;
  if (needRemove.value) return ArrowLeft;
  return ArrowRight;
});

/** 已授权用户 ID 列表 */
const ids = computed(
  () => roleInfo?.users.map(item => item.id).join(",") || ""
);

/**
 * 刷新表格并更新查询参数
 * @param tableRef 表格引用
 * @param lookup 查询关键字（id__in / id__not_in）
 */
const refreshTable = async (
  tableRef: typeof leftTableRef,
  lookup: "id__in" | "id__not_in"
) => {
  if (!tableRef.value) return;
  const crudExpose = tableRef.value.crudExpose;
  // 先覆盖搜索表单数据（mergeForm:false 整体替换，避免旧筛选 key 残留）
  crudExpose.setSearchFormData({
    form: { query: "{id, name, dept_name, role_name}", [lookup]: ids.value },
    mergeForm: false
  });
  // 再清除列头筛选/排序状态（筛选标签、面板输入、图标一并重置），
  // clearAllFilters 内部会同步搜索表单并触发一次刷新，await 等待刷新完成
  await tableRef.value.clearAllFilters?.();
  crudExpose.getBaseTableRef().clearSelection();
};

/**
 * 统一处理用户授权操作
 * @description 一次 API 调用同时处理新增和移除操作：
 * - 左侧选中用户 → 加入角色
 * - 右侧选中用户 → 移出角色
 */
const handleAuthorizedUser = async () => {
  if (!canOperate.value) return;

  loading.value = true;
  try {
    // 构建请求参数
    const requestData: {
      add_user_ids?: number[];
      remove_user_ids?: number[];
    } = {};

    // 左侧选中：要添加的用户
    if (needAdd.value) {
      requestData.add_user_ids = leftTableRef.value!.selectedData.map(
        (item: { id: number }) => item.id
      );
    }

    // 右侧选中：要移除的用户
    if (needRemove.value) {
      requestData.remove_user_ids = rightTableRef.value!.selectedData.map(
        (item: { id: number }) => item.id
      );
    }

    // 一次 API 调用同时处理新增和移除
    const res = await api.AuthorizedUser(roleInfo.id!, requestData);
    // 更新 roleInfo，ids computed 会自动重新计算
    setRoleInfo((res as { data: RoleInfo }).data);

    // 等待 ids computed 更新后，再刷新两侧表格
    await Promise.all([
      refreshTable(leftTableRef, "id__not_in"),
      refreshTable(rightTableRef, "id__in")
    ]);
  } catch (error) {
    console.error(error);
    ElMessage.error("操作失败，请稍后重试");
  } finally {
    loading.value = false;
  }
};
</script>

<style lang="scss">
/* 弹窗通过 append-to-body 渲染到 body，需使用全局样式 */
.authorized-user-dialog {
  display: flex;
  flex-direction: column;
  height: 85vh;

  .el-dialog__header {
    padding: 16px 20px;
    margin-right: 0;
    border-bottom: 1px solid var(--el-border-color-light);
  }

  .el-dialog__body {
    flex: 1;
    min-height: 0;
    padding: 8px;
    overflow: hidden;
    background: var(--el-fill-color-lighter);
  }
}

.authorized-user-body {
  display: flex;
  gap: 8px;
  height: 100%;
}

.authorized-user-panel {
  display: flex;
  flex: 1;
  flex-direction: column;
  min-width: 0;
  height: 100%;
  overflow: hidden;
  background: var(--el-bg-color);
  border-radius: 12px;
  box-shadow: 0 2px 12px rgb(0 0 0 / 4%);
  transition: box-shadow 0.3s ease;

  &:hover {
    box-shadow: 0 4px 16px rgb(0 0 0 / 8%);
  }

  &--left {
    .authorized-user-panel-header {
      background: linear-gradient(
        135deg,
        rgb(64 158 255 / 6%) 0%,
        rgb(64 158 255 / 2%) 100%
      );
    }
  }

  &--right {
    .authorized-user-panel-header {
      background: linear-gradient(
        135deg,
        rgb(103 194 58 / 6%) 0%,
        rgb(103 194 58 / 2%) 100%
      );
    }
  }
}

.authorized-user-panel-header {
  flex: 1;
  min-width: 0;
  padding: 10px 14px;
  border-radius: 12px 12px 0 0;
}

.panel-title {
  display: flex;
  gap: 6px;
  align-items: center;
  font-size: 14px;
  font-weight: 600;
  color: var(--el-text-color-primary);

  &__icon {
    font-size: 18px;
    color: var(--el-color-info);

    &--success {
      color: var(--el-color-success);
    }
  }

  &__text {
    flex: 1;
  }
}

.panel-badge {
  margin-left: auto;

  .el-badge__content {
    font-weight: 600;
    border: none;
  }

  &--success .el-badge__content {
    background: var(--el-color-success);
  }
}

.panel-subtitle {
  margin-top: 2px;
  font-size: 11px;
  color: var(--el-text-color-placeholder);
}

.authorized-user-panel-table {
  flex: 1;
  min-height: 0;
  padding: 4px;
  overflow: hidden;
}

.authorized-user-actions {
  position: relative;
  display: flex;
  flex: none;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  width: 140px;
}

.authorized-user-actions__decor {
  position: absolute;
  top: 0;
  bottom: 0;
  left: 50%;
  z-index: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  pointer-events: none;
  transform: translateX(-50%);

  .decor-line {
    flex: 1;
    width: 2px;
    background: linear-gradient(
      to bottom,
      transparent,
      var(--el-border-color) 20%,
      var(--el-border-color) 80%,
      transparent
    );

    &--top {
      background: linear-gradient(
        to bottom,
        transparent,
        var(--el-border-color)
      );
    }

    &--bottom {
      background: linear-gradient(to top, transparent, var(--el-border-color));
    }
  }

  .decor-dot {
    width: 8px;
    height: 8px;
    margin: 4px 0;
    background: var(--el-color-primary);
    border-radius: 50%;
    opacity: 0.3;
  }
}

.authorized-user-action-item {
  position: relative;
  z-index: 1;
  display: flex;
  flex-direction: column;
  gap: 12px;
  align-items: center;
}

.action-button-wrapper {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
}

.action-button {
  width: 52px !important;
  height: 52px !important;
  font-size: 20px !important;
  box-shadow: 0 4px 12px rgb(0 0 0 / 15%);
  transition: all 0.3s ease;

  &:hover:not(:disabled) {
    box-shadow: 0 6px 20px rgb(0 0 0 / 20%);
    transform: scale(1.08);
  }

  &:active:not(:disabled) {
    transform: scale(0.95);
  }

  &:disabled {
    box-shadow: none;
    opacity: 0.5;
  }
}

.action-ripple {
  position: absolute;
  top: 50%;
  left: 50%;
  width: 68px;
  height: 68px;
  pointer-events: none;
  border: 2px solid var(--el-color-primary);
  border-radius: 50%;
  opacity: 0;
  transform: translate(-50%, -50%);
  animation: ripple 2s ease-out infinite;
}

@keyframes ripple {
  0% {
    opacity: 0.6;
    transform: translate(-50%, -50%) scale(0.8);
  }

  100% {
    opacity: 0;
    transform: translate(-50%, -50%) scale(1.2);
  }
}

.authorized-user-action-text {
  display: flex;
  flex-direction: column;
  gap: 4px;
  align-items: center;
  text-align: center;
}

.action-text__main {
  font-size: 13px;
  font-weight: 500;
  line-height: 1.4;
  color: var(--el-text-color-regular);
  white-space: nowrap;
}

.action-text__add {
  font-weight: 600;
  color: var(--el-color-success);
}

.action-text__remove {
  font-weight: 600;
  color: var(--el-color-danger);
}

.action-text__placeholder {
  color: var(--el-text-color-placeholder);
}

.action-text__sub {
  display: flex;
  gap: 4px;
  align-items: center;
  font-size: 11px;
  color: var(--el-text-color-placeholder);

  .el-icon {
    font-size: 12px;
  }
}
</style>
