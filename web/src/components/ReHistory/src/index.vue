<!--
 * @description 历史记录组件（ReHistory）
 *   - 基于 django-simple-history 后端接口，展示对象的历史变更时间线（时间倒序）
 *   - 支持分页查询、按历史版本一键恢复数据
 *   - 列表高度默认自适应内容（超出 calc(100vh - 200px) 上限时内部滚动），也可通过 formInline.height 传固定高度
 *   - 通过 formInline 注入接口前缀与恢复权限，兼容 fast-crud 子表展开与独立弹窗两种使用方式
 -->
<template>
  <div class="re-history">
    <!-- 分页器：始终显示固定占位，避免单页/多页切换时高度变化导致滚动区域挤压出现新滚动条 -->
    <div class="re-history__pagination">
      <el-pagination
        background
        :current-page="historyList.page"
        :page-size="DEFAULT_PAGE_SIZE"
        layout="total, prev, pager, next"
        :total="historyList.total"
        @current-change="handlePageChange"
      />
    </div>

    <!-- 历史时间线区域：默认自适应内容高度，传入 height 时固定高度滚动 -->
    <el-scrollbar
      v-loading="loading"
      :height="scrollbarHeight"
      :max-height="scrollbarMaxHeight"
    >
      <!-- 空数据占位 -->
      <el-empty
        v-if="!loading && historyList.data.length === 0"
        description="暂无历史记录"
        :image-size="80"
      />
      <!-- 历史记录时间线（新 → 旧） -->
      <el-timeline v-else>
        <el-timeline-item
          v-for="(item, index) in historyList.data"
          :key="item.history_id"
          placement="top"
          :type="getHistoryStyle(item.history_type)"
          :timestamp="item.history_date"
        >
          <!-- 单条历史卡片 -->
          <div class="re-history__card">
            <!-- 卡片头部：操作者信息（左），恢复按钮（右） -->
            <div class="re-history__card-header">
              <span class="re-history__operator-name">
                <el-icon><User /></el-icon>
                <el-text tag="b">{{ formatOperator(item) }}</el-text>
              </span>
              <!-- 恢复按钮：需开启恢复权限、非删除记录且非最新一条（最新即当前状态，无需恢复） -->
              <el-button
                v-if="
                  index > 0 &&
                  options.restartAuth &&
                  item.history_type !== HISTORY_TYPE.DELETE
                "
                size="small"
                type="primary"
                text
                bg
                :icon="RefreshRight"
                @click="recoverHistory(item.history_id)"
              >
                恢复
              </el-button>
            </div>
            <!-- 字段变更明细列表 -->
            <ul
              v-if="Object.keys(item.changed_fields).length > 0"
              class="re-history__changes"
            >
              <li
                v-for="(change, field) in item.changed_fields"
                :key="field"
                class="re-history__changes-item"
              >
                <span class="re-history__changes-field">【{{ field }}】</span>
                <span>从</span>
                <span
                  class="re-history__changes-value re-history__changes-value--old"
                >
                  {{ change.old }}
                </span>
                <span>改为</span>
                <span
                  class="re-history__changes-value re-history__changes-value--new"
                >
                  {{ change.new }}
                </span>
              </li>
            </ul>
            <!-- 无字段变更占位：新增为首条记录，修改可能因未改动字段直接提交产生 -->
            <el-text v-else size="small" type="info">
              {{ getEmptyChangesText(item.history_type) }}
            </el-text>
          </div>
        </el-timeline-item>
      </el-timeline>
    </el-scrollbar>
  </div>
</template>

<script lang="ts" setup>
import { computed, onMounted, reactive, ref } from "vue";
import { RefreshRight, User } from "@element-plus/icons-vue";
import { ElMessage, ElMessageBox } from "element-plus";
import { http } from "@/utils/http";

/**
 * 组件对外配置（由 historyTable / openHistoryDialog 通过 formInline 注入）
 */
export interface FormProps {
  /** 历史记录配置项 */
  formInline?: {
    /** 接口前缀（含对象主键，如 `/api/v1/publisher/1/`） */
    apiPrefix: string;
    /** 是否允许恢复历史版本，默认 false */
    restartAuth: boolean;
    /** 列表区域高度：默认 auto 自适应内容（上限 calc(100vh - 200px) 可滚动），可传 "70vh"、"400px" 等固定值 */
    height?: string;
  };
}

/** 变更类型中文文案（与后端 HISTORY_TYPE_CHOICES 保持一致） */
const HISTORY_TYPE = {
  /** 新增 */
  CREATE: "新增",
  /** 修改 */
  UPDATE: "修改",
  /** 删除 */
  DELETE: "删除"
} as const;

/** 每页展示条数（与后端分页 limit 保持一致） */
const DEFAULT_PAGE_SIZE = 10;
/** 自适应高度模式下的最大高度上限，内容超出后内部滚动 */
const AUTO_MAX_HEIGHT = "calc(100vh - 240px)";

/** 变更类型 → 时间线节点颜色映射（保留操作类型的视觉区分） */
const HISTORY_TYPE_STYLE: Record<string, "success" | "primary" | "danger"> = {
  [HISTORY_TYPE.CREATE]: "success",
  [HISTORY_TYPE.UPDATE]: "primary",
  [HISTORY_TYPE.DELETE]: "danger"
};

/** 单条历史记录数据（与后端 HistorySerializer 输出结构一致） */
interface HistoricalData {
  /** 历史记录主键 */
  history_id: number;
  /** 变更时间（后端已格式化为 yyyy-MM-dd HH:mm:ss） */
  history_date: string;
  /** 变更者账号 */
  history_user: string | null;
  /** 变更者显示名称（用户被删除时可能为空） */
  history_user_name: string | null;
  /** 变更类型（新增 / 修改 / 删除） */
  history_type: string;
  /** 字段变更明细：字段名 -> { old: 旧值, new: 新值 }，首次创建记录为空对象 */
  changed_fields: Record<string, { old: string; new: string }>;
}

/** 历史列表数据状态 */
interface HistoryListState {
  /** 当前页码 */
  page: number;
  /** 记录总数 */
  total: number;
  /** 当前页记录 */
  data: HistoricalData[];
}

const props = withDefaults(defineProps<FormProps>(), {
  // 默认配置：接口前缀为空、不允许恢复、高度自适应
  formInline: () => ({ apiPrefix: "", restartAuth: false, height: "auto" })
});

/** 合并默认值与外部传入值，避免部分属性缺失导致 undefined */
const options = computed(() => ({
  apiPrefix: "",
  restartAuth: false,
  height: "auto",
  ...props.formInline
}));

/** 滚动区域高度：默认 auto 时不设固定高度（内容自适应），传入具体值时固定高度滚动 */
const scrollbarHeight = computed(() =>
  options.value.height === "auto" ? undefined : options.value.height
);
/** 滚动区域最大高度：仅自适应模式设置上限，内容超出后内部滚动 */
const scrollbarMaxHeight = computed(() =>
  options.value.height === "auto" ? AUTO_MAX_HEIGHT : undefined
);

/** 历史列表数据 */
const historyList = reactive<HistoryListState>({
  page: 1,
  total: 0,
  data: []
});
/** 列表加载状态 */
const loading = ref(false);

/** 事件：恢复成功后回传最新数据，供外部（父 crud 表）联动刷新 */
const emit = defineEmits<{
  (e: "update:modelValue", value: any): void;
}>();

/** 获取变更类型对应的时间线节点颜色，未知类型回退为主色 */
const getHistoryStyle = (type: string): "success" | "primary" | "danger" =>
  HISTORY_TYPE_STYLE[type] ?? "primary";

/**
 * 格式化操作者显示文本
 * @description 优先展示「名称(账号)」；用户被删除时名称为空，回退为账号或占位文案
 */
const formatOperator = (item: HistoricalData): string => {
  if (item.history_user_name && item.history_user) {
    return `${item.history_user_name}(${item.history_user})`;
  }
  return item.history_user_name ?? item.history_user ?? "未知用户";
};

/**
 * 查询历史记录列表
 * @description 按当前页码请求 history_list 接口，成功后写入数据与总数
 */
const fetchHistoryList = async () => {
  loading.value = true;
  try {
    const { data, paginated }: ApiResponse<HistoricalData[]> = await http.get(
      `${options.value.apiPrefix}history_list/`,
      { params: { page: historyList.page } }
    );
    historyList.data = data ?? [];
    historyList.total = paginated?.total ?? 0;
  } catch {
    ElMessage.error("历史记录加载失败");
  } finally {
    loading.value = false;
  }
};

/**
 * 获取无字段变更时的占位文案
 * @description 新增记录无上一版本可比对；修改记录可能因未改动字段直接提交而变更集为空；删除记录无变更明细
 */
const getEmptyChangesText = (type: string): string => {
  switch (type) {
    case HISTORY_TYPE.CREATE:
      return "首次创建，无字段变更";
    case HISTORY_TYPE.UPDATE:
      return "未修改任何字段";
    case HISTORY_TYPE.DELETE:
      return "删除记录，无字段变更";
    default:
      return "无字段变更";
  }
};

/** 页码切换：更新当前页码并重新查询 */
const handlePageChange = (page: number) => {
  historyList.page = page;
  fetchHistoryList();
};

/**
 * 恢复指定历史版本
 * @param historyId 目标历史记录 id
 * @description 二次确认后调用 history_recover 接口，成功后回传最新数据并刷新列表
 */
const recoverHistory = async (historyId: number) => {
  try {
    // 二次确认，用户取消则直接结束
    await ElMessageBox.confirm("确定要恢复到此版本吗？", "恢复确认", {
      confirmButtonText: "确定",
      cancelButtonText: "取消",
      type: "warning"
    });
  } catch {
    return;
  }
  try {
    // 注意：http.post 第二参为 axios 配置，请求体需放在 data 字段中
    const { data }: ApiResponse = await http.post(
      `${options.value.apiPrefix}history_recover/`,
      { data: { history_id: historyId } }
    );
    ElMessage.success("恢复成功");
    // 回传最新数据，通知外部父级 crud 同步刷新
    emit("update:modelValue", data);
    await fetchHistoryList();
  } catch {
    ElMessage.error("恢复失败，请稍后重试");
  }
};

// 组件挂载后加载首屏历史记录
onMounted(() => {
  fetchHistoryList();
});
</script>

<style lang="scss" scoped>
.re-history {
  /* 分页器容器：水平居中 */
  &__pagination {
    display: flex;
    justify-content: center;
    padding-bottom: 12px;
  }

  /* 单条历史记录卡片 */
  &__card {
    padding: 10px 14px;
    border: 1px solid var(--el-border-color-lighter);
    border-radius: 8px;
    background-color: var(--el-fill-color-light);
    transition:
      border-color 0.2s,
      box-shadow 0.2s;

    /* 悬停轻微高亮，增强可感知性 */
    &:hover {
      border-color: var(--el-border-color);
      box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
    }
  }

  /* 卡片头部：操作者信息与恢复按钮两端对齐，右侧按钮不参与压缩 */
  &__card-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 8px;

    .el-button {
      flex-shrink: 0;
    }
  }

  /* 用户名：用户图标 + 名称 */
  &__operator-name {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    font-size: 13px;
    color: var(--el-text-color-primary);

    .el-icon {
      font-size: 14px;
      color: var(--el-text-color-secondary);
    }
  }

  /* 字段变更明细列表 */
  &__changes {
    margin: 8px 0 0;
    padding: 0;
    list-style: none;
  }

  /* 单条字段变更：行内紧凑排版，支持换行 */
  &__changes-item {
    display: flex;
    align-items: center;
    flex-wrap: wrap;
    gap: 4px;
    font-size: 13px;
    line-height: 1.9;
    color: var(--el-text-color-regular);
  }

  /* 变更字段名：加粗强调 */
  &__changes-field {
    font-weight: 600;
    color: var(--el-text-color-primary);
  }

  /* 变更值：旧值危险色 + 删除线，新值主色加粗 */
  &__changes-value {
    padding: 0 2px;
    border-radius: 4px;

    &--old {
      color: var(--el-color-danger);
      text-decoration: line-through;
    }

    &--new {
      font-weight: 600;
      color: var(--el-color-primary);
    }
  }

  /* 时间线整体留白微调，与卡片间距更舒适 */
  :deep(.el-timeline) {
    padding-left: 4px;
  }
}
</style>
