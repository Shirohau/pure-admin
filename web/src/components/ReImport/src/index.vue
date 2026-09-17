<template>
  <div class="import-workspace">
    <section class="import-config">
      <!-- 顶部操作栏：标题 + 下载模板 -->
      <div class="config-header">
        <div class="header-info">
          <div class="config-title">导入数据</div>
          <div class="config-description">
            请使用最新模板整理数据，支持 XLS 和 XLSX 文件
          </div>
        </div>
        <el-button
          type="primary"
          plain
          :icon="Download"
          @click="downloadTemplate"
        >
          下载模板
        </el-button>
      </div>

      <!-- 主体区域：上传 + 设置 -->
      <div class="import-body">
        <!-- 第一行左侧：文件上传（含自带文件列表） -->
        <div class="upload-area">
          <el-upload
            v-model:file-list="fileList"
            class="file-upload"
            drag
            :auto-upload="false"
            :limit="1"
            accept=".xls,.xlsx"
            :on-change="handleFileChange"
            :on-exceed="handleFileExceed"
            :on-remove="handleFileRemove"
          >
            <div class="upload-content">
              <el-icon class="upload-icon"><UploadFilled /></el-icon>
              <div class="upload-title">拖放 Excel 文件</div>
              <div class="upload-subtitle">
                或 <span class="upload-link">点击选择</span>
              </div>
            </div>
          </el-upload>
        </div>

        <!-- 第一行右侧：导入方式 -->
        <div class="settings-area">
          <div class="mode-card">
            <div class="card-header">
              <el-icon><Setting /></el-icon>
              <span>导入方式</span>
            </div>
            <el-segmented
              v-model="importMode"
              :options="importModeOptions"
              block
              class="mode-selector"
            />
            <div class="mode-tip">
              <el-icon><InfoFilled /></el-icon>
              <span>{{ currentModeDescription }}</span>
            </div>
          </div>
        </div>

        <!-- 第二行左侧：预留文件列表位置 -->
        <div class="file-list-placeholder">
          <!-- el-upload 自带的文件列表会显示在此区域 -->
        </div>

        <!-- 第二行右侧：导入按钮 -->
        <div class="import-btn-area">
          <el-button
            type="primary"
            :icon="Upload"
            :loading="importing"
            :disabled="!selectedFile"
            class="import-btn"
            @click="startImport"
          >
            {{ importMode === "async" ? "创建后台任务" : "开始导入" }}
          </el-button>
        </div>
      </div>
    </section>

    <section class="import-history">
      <fs-crud ref="crudRef" v-bind="crudBinding">
        <template #actionbar-right>
          <div class="history-heading">
            <el-icon><Tickets /></el-icon>
            <span>后台导入记录</span>
          </div>
        </template>
      </fs-crud>
    </section>
  </div>
</template>

<script setup lang="ts">
import { useFs, useFsRef } from "@fast-crud/fast-crud";
import {
  Download,
  InfoFilled,
  Setting,
  Tickets,
  Upload,
  UploadFilled
} from "@element-plus/icons-vue";
import {
  ElMessage,
  ElMessageBox,
  genFileId,
  type UploadFile,
  type UploadFiles,
  type UploadRawFile,
  type UploadUserFile
} from "element-plus";
import { computed, onMounted, ref } from "vue";
import { http } from "@/utils/http";
import createCrudOptions from "./crud";

export interface FormProps {
  formInline?: {
    apiPrefix: string;
    ParentCrudExpose?: any;
  };
}

const props = withDefaults(defineProps<FormProps>(), {
  formInline: () => ({ apiPrefix: "" })
});

const MAX_FILE_SIZE = 20 * 1024 * 1024;
const fileList = ref<UploadUserFile[]>([]);
const selectedFile = ref<File>();
const importMode = ref<"sync" | "async">("sync");
const importing = ref(false);
const importModeOptions = [
  { label: "立即导入", value: "sync" },
  { label: "后台导入", value: "async" }
];
const currentModeDescription = computed(() =>
  importMode.value === "async"
    ? "先在后台解析文件，解析成功后可在记录中确认导入。"
    : "直接校验并写入数据，适合数据量较小的文件。"
);

const { crudRef, crudBinding, crudExpose } = useFsRef();
useFs({
  crudRef,
  crudBinding,
  crudExpose,
  context: { props },
  createCrudOptions
});

const isExcelFile = (file: File) => /\.(xls|xlsx)$/i.test(file.name);

const handleFileChange = (uploadFile: UploadFile, uploadFiles: UploadFiles) => {
  const rawFile = uploadFile.raw;
  if (!rawFile) return;

  if (!isExcelFile(rawFile)) {
    ElMessage.warning("请选择 XLS 或 XLSX 格式的文件");
    clearFile();
    return;
  }
  if (rawFile.size > MAX_FILE_SIZE) {
    ElMessage.warning("文件不能超过 20 MB");
    clearFile();
    return;
  }

  selectedFile.value = rawFile;
  fileList.value = uploadFiles.slice(-1);
};

const handleFileExceed = (files: File[]) => {
  const file = files[0];
  if (!file) return;
  const rawFile = Object.assign(file, { uid: genFileId() }) as UploadRawFile;
  fileList.value = [];
  handleFileChange(
    { name: file.name, size: file.size, raw: rawFile } as UploadFile,
    []
  );
  if (selectedFile.value) {
    fileList.value = [{ name: file.name, size: file.size, raw: rawFile }];
  }
};

const handleFileRemove = () => {
  selectedFile.value = undefined;
};

const clearFile = () => {
  selectedFile.value = undefined;
  fileList.value = [];
};

const formatFileSize = (size: number) => {
  if (size < 1024 * 1024) return `${Math.max(1, Math.round(size / 1024))} KB`;
  return `${(size / 1024 / 1024).toFixed(1)} MB`;
};

/** 格式化导入错误信息（支持行错误与字段错误、截断提示） */
const formatImportErrors = (errorData: any): string => {
  if (!errorData) return "未知错误";

  const lines: string[] = [];

  // 错误摘要（含截断提示）
  if (errorData.error_message) {
    lines.push(errorData.error_message);
  }

  // 行级错误
  if (errorData.row_errors?.length) {
    lines.push("【行级错误】");
    errorData.row_errors.forEach((item: any) => {
      lines.push(`  第 ${item.row} 行: ${item.errors?.join("、") || "未知"}`);
    });
  }

  // 字段级错误
  if (errorData.field_errors?.length) {
    lines.push("【字段级错误】");
    errorData.field_errors.forEach((rowErrors: any, idx: number) => {
      Object.entries(rowErrors).forEach(([field, msg]) => {
        lines.push(`  第 ${idx + 2} 行 [${field}]: ${msg}`);
      });
    });
  }

  // 截断提示（大数据量时仅展示部分错误）
  if (errorData.has_more_errors) {
    lines.push(
      `【提示】共 ${errorData.error_rows_total} 行错误，仅展示前 ${errorData.error_rows_shown} 行`
    );
  }

  // 统计信息
  if (errorData.totals) {
    lines.push("【统计信息】");
    const { new: newCount, update, skip, error, tot } = errorData.totals;
    lines.push(
      `  新增 ${newCount} | 更新 ${update} | 跳过 ${skip} | 错误 ${error} | 总计 ${tot}`
    );
  }

  return lines.join("\n") || "导入失败，请检查文件数据";
};

const downloadTemplate = () => {
  http.downloadFile(`${props.formInline.apiPrefix}import_template/`, {
    filename: "导入模板",
    file_format: "xlsx"
  });
};

const startImport = async () => {
  if (!selectedFile.value || importing.value) return;

  const formData = new FormData();
  formData.append("file", selectedFile.value);
  const url =
    importMode.value === "async"
      ? `${props.formInline.apiPrefix}async_import/start/`
      : `${props.formInline.apiPrefix}sync_import/`;

  importing.value = true;
  try {
    const res: ApiResponse = await http.post(
      url,
      { data: formData },
      { headers: { "Content-Type": "multipart/form-data" }, timeout: -1 }
    );
    ElMessage.success(res.message);
    clearFile();

    if (importMode.value === "async") {
      setTimeout(() => crudExpose.doRefresh(), 800);
    } else {
      props.formInline.ParentCrudExpose?.doRefresh();
    }
  } finally {
    importing.value = false;
  }
};

onMounted(() => crudExpose.doRefresh());
</script>

<style scoped>
/* ==================== 整体布局 ==================== */
.import-workspace {
  display: flex;
  flex-direction: column;
  gap: 12px;
  min-width: 0;
  height: 100%;
}

.import-config {
  flex-shrink: 0;
  padding: 10px;
  background: var(--el-bg-color);
  border: 1px solid var(--el-border-color-light);
  border-radius: 8px;
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

/* ==================== 主体区域 ==================== */
.import-body {
  display: grid;
  grid-template-rows: auto auto;
  grid-template-columns: minmax(180px, 1fr) minmax(180px, 320px);
  gap: 6px 12px;
}

/* ==================== 左侧上传区域 ==================== */
.upload-area {
  position: relative;
  grid-row: 1;
  grid-column: 1;
}

.file-upload {
  width: 100%;
}

.file-upload :deep(.el-upload),
.file-upload :deep(.el-upload-dragger) {
  width: 100%;
}

.file-upload :deep(.el-upload-dragger) {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  min-height: 70px;
  padding: 10px;
  background: var(--el-fill-color-lighter);
  border: 2px dashed var(--el-border-color);
  border-radius: 6px;
  transition:
    border-color 0.2s,
    background-color 0.2s;
}

.file-upload :deep(.el-upload-dragger:hover) {
  background: var(--el-fill-color-light);
  border-color: var(--el-color-primary-light-3);
}

/* 文件列表显示在第二行位置 */
.file-upload :deep(.el-upload-list) {
  position: absolute;
  top: 100%;
  right: 0;
  left: 0;
  margin-top: 6px;
}

.file-upload :deep(.el-upload-list__item) {
  height: 32px;
  padding: 0 8px;
  margin: 0;
  line-height: 32px;
  background: var(--el-fill-color-lighter);
  border-radius: 4px;
}

.upload-content {
  display: flex;
  flex-direction: column;
  gap: 2px;
  align-items: center;
}

.upload-icon {
  font-size: 22px;
  color: var(--el-color-primary);
}

.upload-title {
  font-size: 12px;
  font-weight: 500;
  color: var(--el-text-color-primary);
}

.upload-subtitle {
  font-size: 11px;
  color: var(--el-text-color-secondary);
}

.upload-link {
  color: var(--el-color-primary);
  cursor: pointer;
}

/* 第二行左侧预留位置 */
.file-list-placeholder {
  grid-row: 2;
  grid-column: 1;
  min-height: 38px; /* 文件列表高度 + margin */
}

/* ==================== 右侧设置区域 ==================== */
.settings-area {
  grid-row: 1;
  grid-column: 2;
}

/* 导入方式卡片 */
.mode-card {
  height: 100%;
  padding: 8px 10px;
  background: var(--el-fill-color-lighter);
  border: 1px solid var(--el-border-color-lighter);
  border-radius: 6px;
}

.card-header {
  display: flex;
  gap: 4px;
  align-items: center;
  margin-bottom: 4px;
  font-size: 12px;
  font-weight: 500;
  color: var(--el-text-color-regular);
}

.card-header .el-icon {
  color: var(--el-text-color-secondary);
}

.mode-selector {
  width: 100%;
}

.mode-tip {
  display: flex;
  gap: 4px;
  align-items: flex-start;
  margin-top: 4px;
  font-size: 11px;
  line-height: 1.3;
  color: var(--el-text-color-secondary);
}

.mode-tip .el-icon {
  flex: 0 0 auto;
  margin-top: 1px;
  color: var(--el-color-primary);
}

/* 导入按钮 - 第二行 */
.import-btn-area {
  grid-row: 2;
  grid-column: 2;
}

.import-btn {
  width: 100%;
  height: 32px;
  font-size: 13px;
}

/* ==================== 底部历史记录 ==================== */
.import-history {
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

.import-history :deep(.fs-crud-container) {
  display: flex;
  flex: 1;
  flex-direction: column;
  height: 100%;
  min-height: 0;
}

.import-history :deep(.fs-crud-header) {
  padding: 6px 0;
}

.import-history :deep(.fs-crud-footer) {
  padding-bottom: 0;
}

.import-history :deep(.el-table) {
  --el-table-header-bg-color: var(--el-fill-color-light);
  --el-table-row-hover-bg-color: var(--el-fill-color-lighter);
}

/* ==================== 响应式布局 ==================== */
@media (width <= 800px) {
  .import-body {
    grid-template-columns: 1fr;
  }

  .config-header {
    flex-direction: column;
    gap: 10px;
  }

  .config-header .el-button {
    width: 100%;
  }

  .file-upload :deep(.el-upload-dragger) {
    min-height: 100px;
  }
}
</style>

<!-- 全局样式：导入错误弹窗 -->
<style>
.import-error-dialog {
  max-width: 600px;
}

.import-error-dialog .el-message-box__content {
  max-height: 400px;
  overflow-y: auto;
  font-family: inherit;
  font-size: 13px;
  line-height: 1.6;
  white-space: pre-wrap;
}
</style>
