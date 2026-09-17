<template>
  <div class="export-workspace">
    <section class="export-config">
      <!-- 顶部：说明 + 格式选择 -->
      <div class="config-header">
        <div class="header-info">
          <div class="config-title">导出数据</div>
          <div class="config-description">
            选择导出格式和字段，支持 CSV 和 Excel 格式
          </div>
        </div>
        <el-segmented v-model="file_format" :options="formatOptions" />
      </div>

      <!-- 主体区域：左右布局 -->
      <div class="export-body">
        <!-- 左侧列 -->
        <div class="left-column">
          <!-- 第一行：字段模板（标题与按钮同行） -->
          <div class="template-card">
            <div class="template-header">
              <div class="card-header">
                <el-icon><DocumentChecked /></el-icon>
                <span>字段模板</span>
              </div>
              <div class="template-actions">
                <el-button :icon="Plus" size="small" @click="createTemplate">
                  新建
                </el-button>

                <el-button
                  :icon="DocumentChecked"
                  size="small"
                  :disabled="!selectedTemplateId"
                  @click="updateTemplateFields"
                >
                  保存
                </el-button>

                <el-button
                  :icon="Edit"
                  size="small"
                  :disabled="!selectedTemplateId"
                  @click="renameTemplate"
                >
                  重命名
                </el-button>

                <el-button
                  :icon="Delete"
                  size="small"
                  :disabled="!selectedTemplateId"
                  @click="deleteTemplate"
                >
                  删除
                </el-button>
              </div>
            </div>
            <el-select
              v-model="selectedTemplateId"
              clearable
              placeholder="选择已保存模板"
              class="template-select"
              @change="applyTemplate"
            >
              <el-option
                v-for="template in templates"
                :key="template.id"
                :label="template.name"
                :value="template.id"
              />
            </el-select>
          </div>

          <!-- 第二行：导出字段选择 -->
          <div class="fields-card">
            <div class="card-header">
              <el-icon><Setting /></el-icon>
              <span>导出字段</span>
              <span class="field-count"
                >{{ fields.length }}/{{ fields_options.length }}</span
              >
            </div>
            <el-select
              v-model="fields"
              clearable
              multiple
              collapse-tags
              collapse-tags-tooltip
              :max-collapse-tags="5"
              placeholder="选择导出字段"
              class="fields-select"
            >
              <el-option
                v-for="item in fields_options"
                :key="item.value"
                :label="item.label"
                :value="item.value"
              />
            </el-select>
          </div>
        </div>

        <!-- 右侧列：导出方式（整块） -->
        <div class="right-column">
          <div class="mode-card">
            <div class="card-header">
              <el-icon><Setting /></el-icon>
              <span>导出方式</span>
            </div>
            <el-segmented
              v-model="exportMode"
              :options="exportModeOptions"
              block
              class="mode-selector"
            />
            <div class="mode-tip">
              <el-icon><InfoFilled /></el-icon>
              <span>{{ currentModeDescription }}</span>
            </div>
            <el-button
              type="primary"
              :icon="Download"
              :loading="asyncExporting"
              class="export-btn"
              @click="handleExport"
            >
              {{ exportMode === "async" ? "创建后台任务" : "开始导出" }}
            </el-button>
          </div>
        </div>
      </div>
    </section>

    <section class="export-history">
      <fs-crud ref="crudRef" v-bind="crudBinding">
        <template #actionbar-right>
          <div class="history-heading">
            <el-icon><Tickets /></el-icon>
            <span>后台导出记录</span>
          </div>
        </template>
      </fs-crud>
    </section>
  </div>
</template>

<script setup lang="ts">
import { useFs, useFsRef } from "@fast-crud/fast-crud";
import { computed, onMounted, ref } from "vue";
import createCrudOptions from "./crud";
import { http } from "@/utils/http";
import {
  Delete,
  DocumentChecked,
  Download,
  Edit,
  InfoFilled,
  Plus,
  Refresh,
  Setting,
  Tickets
} from "@element-plus/icons-vue";
import { ElMessage, ElMessageBox } from "element-plus";

/** 后端 export_fields 接口返回的可导出字段。 */
interface ExportFieldOption {
  value: string;
  label: string;
}

/** 当前用户保存的一条字段模板。 */
interface ExportFieldTemplate {
  id: number;
  name: string;
  api_path: string;
  fields: string[];
}
/** 打开导出弹窗时由业务页面传入的上下文。 */
export interface FormProps {
  formInline?: {
    apiPrefix: string;
    query_params?: object;
  };
}

/** 未传业务上下文时使用空前缀，保证组件初始化过程稳定。 */
const props = withDefaults(defineProps<FormProps>(), {
  formInline: () => ({ apiPrefix: "" })
});
const templateApiPrefix = "/api/system/export_field_template/";

// ---------- 导出配置状态 ----------
const fields_options = ref<ExportFieldOption[]>([]);
const file_format = ref("csv");
const formatOptions = [
  { label: "CSV", value: "csv" },
  { label: "Excel", value: "xlsx" }
];
const fields = ref<string[]>([]);
const templates = ref<ExportFieldTemplate[]>([]);
const selectedTemplateId = ref<number>();
const asyncExporting = ref(false);
const exportMode = ref<"sync" | "async">(
  (props.formInline as any)?.defaultExportMode === "async" ? "async" : "sync"
);
const exportModeOptions = [
  { label: "立即导出", value: "sync" },
  { label: "后台导出", value: "async" }
];
const currentModeDescription = computed(() =>
  exportMode.value === "async"
    ? "先在后台生成文件，生成完成后可在记录中下载。"
    : "直接生成并下载文件，适合数据量较小的场景。"
);

// FastCrud 暴露对象负责后台导出记录的查询、分页和刷新。
const { crudRef, crudBinding, crudExpose } = useFsRef();

/** 当前选择字段转换为后端导出接口约定的逗号分隔字符串。 */
const selected_fields = computed(() => {
  return fields.value.length > 0
    ? fields.value.join(",")
    : fields_options.value.map(item => item.value).join(",");
});

/** 当前选中的模板对象，供保存、重命名和删除操作复用。 */
const currentTemplate = computed(() =>
  templates.value.find(item => item.id === selectedTemplateId.value)
);

// 初始化后台导出记录表，并把业务 API 前缀传给 CRUD 配置生成器。
useFs({
  crudRef,
  crudBinding,
  crudExpose,
  context: { props, file_format, selected_fields },
  createCrudOptions
});

// ---------- 初始化数据 ----------

/**
 * 获取当前用户有权限导出的字段。
 * 首次加载默认全选，模板应用后再替换为模板中的有效字段。
 */
const get_export_fields = async () => {
  const { data }: ApiResponse = await http.get(
    `${props.formInline.apiPrefix}export_fields/`
  );
  fields_options.value = data;
  fields.value = fields_options.value.map(item => item.value);
};

/** 获取当前用户在当前业务接口下保存的全部字段模板。 */
const getTemplates = async () => {
  const { data }: ApiResponse = await http.get(templateApiPrefix, {
    params: {
      paginate: false,
      api_path: props.formInline.apiPrefix
    }
  });
  templates.value = data;
};

// ---------- 模板管理 ----------

/**
 * 应用字段模板。
 * 模板字段会与最新字段权限取交集，防止旧模板恢复已失去权限的字段。
 */
const applyTemplate = (templateId?: number) => {
  if (!templateId) return;
  const template = templates.value.find(item => item.id === templateId);
  if (!template) return;

  const availableFields = new Set(fields_options.value.map(item => item.value));
  const permittedFields = template.fields.filter(field =>
    availableFields.has(field)
  );
  if (permittedFields.length === 0) {
    ElMessage.error("该模板已没有当前可导出的字段");
    return;
  }
  fields.value = permittedFields;
  if (permittedFields.length !== template.fields.length) {
    ElMessage.warning("模板中的部分字段当前不可导出，已自动忽略");
  }
};

/** 打开模板名称输入框，并在提交前完成空值和长度校验。 */
const promptTemplateName = async (defaultValue = "") => {
  const { value } = await ElMessageBox.prompt("请输入模板名称", "字段模板", {
    inputValue: defaultValue,
    inputPlaceholder: "例如：财务常用字段",
    inputValidator: value => {
      const name = value.trim();
      if (!name) return "模板名称不能为空";
      if (name.length > 50) return "模板名称不能超过 50 个字符";
      return true;
    }
  });
  return value.trim();
};

/** 所有保存和导出动作共用的字段非空校验。 */
const requireFields = () => {
  if (fields.value.length > 0) return true;
  ElMessage.warning("请至少选择一个导出字段");
  return false;
};

/** 使用当前字段选择创建一个新的用户模板。 */
const createTemplate = async () => {
  if (!requireFields()) return;
  try {
    const name = await promptTemplateName();
    const { data }: ApiResponse = await http.post(templateApiPrefix, {
      data: {
        name,
        api_path: props.formInline.apiPrefix,
        fields: fields.value
      }
    });
    await getTemplates();
    selectedTemplateId.value = data.id;
    ElMessage.success("模板已创建");
  } catch (error: any) {
    if (error !== "cancel" && error !== "close") throw error;
  }
};

/** 更新当前模板，并在成功后刷新模板列表。 */
const updateTemplate = async (data: Partial<ExportFieldTemplate>) => {
  if (!currentTemplate.value) return;
  await http.request(
    "put",
    `${templateApiPrefix}${currentTemplate.value.id}/`,
    {
      data: {
        name: currentTemplate.value.name,
        api_path: currentTemplate.value.api_path,
        fields: currentTemplate.value.fields,
        ...data
      }
    }
  );
  await getTemplates();
};

/** 将当前字段选择覆盖保存到已选模板。 */
const updateTemplateFields = async () => {
  if (!requireFields() || !currentTemplate.value) return;
  await updateTemplate({ fields: [...fields.value] });
  ElMessage.success("模板字段已保存");
};

/** 修改当前模板名称，保留模板字段和业务接口不变。 */
const renameTemplate = async () => {
  if (!currentTemplate.value) return;
  try {
    const name = await promptTemplateName(currentTemplate.value.name);
    await updateTemplate({ name });
    ElMessage.success("模板已重命名");
  } catch (error: any) {
    if (error !== "cancel" && error !== "close") throw error;
  }
};

/** 删除当前模板；删除后清空选择，避免继续引用已删除记录。 */
const deleteTemplate = async () => {
  if (!currentTemplate.value) return;
  try {
    await ElMessageBox.confirm(
      `确定删除模板“${currentTemplate.value.name}”吗？`,
      "删除模板",
      { type: "warning" }
    );
    await http.request(
      "delete",
      `${templateApiPrefix}${currentTemplate.value.id}/`
    );
    selectedTemplateId.value = undefined;
    await getTemplates();
    ElMessage.success("模板已删除");
  } catch (error: any) {
    if (error !== "cancel" && error !== "close") throw error;
  }
};

// ---------- 导出动作 ----------

/** 根据当前导出模式执行对应的导出操作。 */
const handleExport = async () => {
  if (!requireFields()) return;
  if (exportMode.value === "async") {
    await startAsyncExport();
  } else {
    startSyncExport();
  }
};

/** 创建后台异步导出任务，并在任务入队后刷新记录表。 */
const startAsyncExport = async () => {
  asyncExporting.value = true;
  try {
    const res: ApiResponse = await http.post(
      `${props.formInline.apiPrefix}async_export/start/`,
      {
        params: props.formInline.query_params,
        data: {
          file_format: file_format.value,
          selected_fields: selected_fields.value
        }
      }
    );
    ElMessage.success(res.message);
    setTimeout(() => crudExpose.doRefresh(), 1000);
  } finally {
    asyncExporting.value = false;
  }
};

/** 直接下载当前筛选条件和字段配置对应的导出文件。 */
const startSyncExport = () => {
  http.downloadFile(`${props.formInline.apiPrefix}sync_export/`, {
    file_format: file_format.value,
    selected_fields: selected_fields.value,
    ...props.formInline.query_params
  });
};

/** 手动刷新后台导出记录。 */
const refreshHistory = () => {
  crudExpose.doRefresh();
};

/** 组件挂载时并行加载记录、字段权限和用户模板。 */
onMounted(() => {
  crudExpose.doRefresh();
  Promise.all([get_export_fields(), getTemplates()]);
});
</script>

<style scoped>
/* ==================== 整体布局 ==================== */
.export-workspace {
  display: flex;
  flex-direction: column;
  gap: 12px;
  min-width: 0;
  height: 100%;
}

.export-config {
  flex-shrink: 0;
  padding: 10px;
  background: var(--el-bg-color);
  border: 1px solid var(--el-border-color-light);
  border-radius: 8px;
}

/* ==================== 主体区域：左右布局 ==================== */
.export-body {
  display: flex;
  gap: 12px;
}

.left-column {
  display: flex;
  flex: 1.4;
  flex-direction: column;
  gap: 8px;
  min-width: 0;
}

.right-column {
  display: flex;
  flex: 0.8;
  flex-direction: column;
  min-width: 0;
}

/* ==================== 顶部操作栏 ==================== */
.config-header {
  display: flex;
  gap: 10px;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
}

.header-info {
  flex: 1;
  min-width: 0;
}

.config-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--el-text-color-primary);
}

.config-description {
  margin-top: 2px;
  font-size: 12px;
  color: var(--el-text-color-secondary);
}

/* ==================== 卡片通用样式 ==================== */
.template-card,
.fields-card,
.mode-card {
  padding: 8px 10px;
  background: var(--el-fill-color-lighter);
  border: 1px solid var(--el-border-color-lighter);
  border-radius: 6px;
}

.card-header {
  display: flex;
  gap: 4px;
  align-items: center;
  font-size: 12px;
  font-weight: 500;
  color: var(--el-text-color-regular);
}

.card-header .el-icon {
  color: var(--el-text-color-secondary);
}

/* ==================== 左侧：模板相关 ==================== */
.template-header {
  display: flex;
  gap: 8px;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 6px;
}

.template-select {
  width: 100%;
}

.template-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.template-actions :deep(.el-button + .el-button) {
  margin-left: 0;
}

/* ==================== 左侧：字段选择 ==================== */
.field-count {
  margin-left: auto;
  font-size: 11px;
  font-variant-numeric: tabular-nums;
  color: var(--el-color-primary);
}

.fields-select {
  width: 100%;
}

/* ==================== 右侧：导出方式卡片 ==================== */
.mode-card {
  display: flex;
  flex: 1;
  flex-direction: column;
}

.mode-selector {
  width: 100%;
  margin-bottom: 4px;
}

.mode-tip {
  display: flex;
  gap: 4px;
  align-items: flex-start;
  margin-bottom: 10px;
  font-size: 11px;
  line-height: 1.3;
  color: var(--el-text-color-secondary);
}

.mode-tip .el-icon {
  flex: 0 0 auto;
  margin-top: 1px;
  color: var(--el-color-primary);
}

.export-btn {
  width: 100%;
  height: 36px;
  margin-top: auto;
  font-size: 13px;
}

/* ==================== 底部历史记录 ==================== */
.export-history {
  display: flex;
  flex: 1;
  flex-direction: column;
  min-height: 0;
}

.history-heading {
  display: flex;
  gap: 6px;
  align-items: center;
  font-size: 13px;
  font-weight: 600;
  color: var(--el-text-color-primary);
}

.export-history :deep(.fs-crud-container) {
  display: flex;
  flex: 1;
  flex-direction: column;
  height: 100%;
  min-height: 0;
}

.export-history :deep(.fs-crud-header) {
  padding: 6px 0;
}

.export-history :deep(.fs-crud-footer) {
  padding-bottom: 0;
}

.export-history :deep(.el-table) {
  --el-table-header-bg-color: var(--el-fill-color-light);
  --el-table-row-hover-bg-color: var(--el-fill-color-lighter);
}

/* ==================== 响应式布局 ==================== */
@media (width <= 800px) {
  .export-body {
    flex-direction: column;
  }
}
</style>
