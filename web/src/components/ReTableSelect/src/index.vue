<template>
  <el-select
    ref="selectRef"
    v-model="displayValue"
    clearable
    filterable
    remote
    fit-input-width
    :remote-method="remoteMethod"
    :loading="loading"
    :placeholder="placeholder"
    :disabled="disabled"
    @clear="onClear"
  >
    <!-- 自定义下拉面板：搜索结果表格 + 分页（搜索直接在 el-select 自带输入框中进行） -->
    <template #empty>
      <div class="option">
        <el-table
          row-key="id"
          :height="TABLE_HEIGHT"
          border
          highlight-current-row
          :data="tableData"
          :row-class-name="tableConfig.rowClassName"
          @row-click="handleRowClick"
        >
          <el-table-column
            v-for="(col, idx) in tableConfig.columns"
            :key="idx"
            show-overflow-tooltip
            :prop="col.prop"
            :label="col.label"
            :width="col.width"
          />
        </el-table>

        <!-- 远程数据分页：总条数超过每页条数时才展示 -->
        <el-pagination
          v-if="showPagination"
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.limit"
          style="margin-top: 10px"
          background
          layout="prev, pager, next"
          :total="pagination.total"
          @current-change="handlePageChange"
        />
      </div>
    </template>
  </el-select>
</template>

<script setup lang="ts">
import { ref, reactive, computed, watch } from "vue";
import { http } from "@/utils/http";

// ===== 组件 Props =====
// modelValue：外部 v-model 绑定的值（值字段，如 id）
// modelLabel：外部回显的显示文本（编辑回显时传入，如名称）
// search：初始搜索关键词（仅首次加载生效）
// tableConfig：表格数据与展示配置
const props = defineProps({
  modelValue: null,
  modelLabel: null,
  search: {
    type: String,
    default: ""
  },
  tableConfig: {
    type: Object,
    default: () => ({
      url: null, // 远程数据接口地址（与 data 二选一）
      params: {}, // 附加请求参数
      label: "label", // 显示字段，如 name
      value: "id", // 值字段，如 id
      data: [], // 静态数据（配置后优先使用，不走接口）
      columns: [] // 表格列配置
    })
  },
  placeholder: { type: String, default: "请选择" },
  disabled: { type: Boolean, default: false }
});

// ===== 组件事件 =====
// update:modelValue：选中/清除时向外写入值字段
// select-change：点击表格行选中时，向外传出完整行数据
const emit = defineEmits<{
  "update:modelValue": [value: any];
  "select-change": [row: any];
}>();

// ===== 内部状态 =====
const selectRef = ref(); // el-select 实例（用于选择后收起下拉）
const searchKeyword = ref(""); // 当前搜索关键词（来自 el-select 自带输入框）
const loading = ref(false); // 远程请求加载中状态
const tableData = ref<any[]>([]); // 表格数据（静态或远程）
const selectedRow = ref<any>(null); // 当前选中的行（驱动输入框显示 label）
const pagination = reactive({
  page: 1, // 当前页码
  limit: 10, // 每页条数
  total: 0 // 总条数
});

// 面板内表格的固定展示高度
const TABLE_HEIGHT = 300;

// 初始关键词是否已应用：props.search 仅在首次加载时生效，之后以用户输入为准
let initialSearchApplied = false;

// ===== 派生状态 =====
// 输入框显示文本：已选中时展示选中行的 label 字段；
// 未选中时回显外部值（优先 modelLabel，其次 modelValue）
const displayValue = computed({
  get: () => {
    const labelField = props.tableConfig.label;
    if (selectedRow.value) {
      return selectedRow.value[labelField];
    }
    return props.modelLabel || (props.modelValue ?? "");
  },
  set: val => emit("update:modelValue", val)
});

// 远程数据且总条数大于每页条数时才展示分页
const showPagination = computed(() => pagination.total > pagination.limit);

// ===== 数据加载 =====
// 加载表格数据：静态数据直接使用，远程数据携带关键词与分页参数请求接口
const fetchData = async () => {
  const { url, params = {}, data: staticData } = props.tableConfig;

  // 静态数据：直接赋值，不走接口
  if (staticData?.length) {
    tableData.value = staticData;
    return;
  }

  // 未配置数据源：清空表格
  if (!url) {
    tableData.value = [];
    return;
  }

  // 远程数据：请求接口
  loading.value = true;
  try {
    const { paginated, data }: ApiResponse = await http.get(url, {
      params: {
        page: pagination.page,
        limit: pagination.limit,
        search: searchKeyword.value.trim(),
        ...params
      }
    });
    pagination.page = paginated.page ?? 1;
    pagination.limit = paginated.limit ?? 10;
    pagination.total = paginated.total ?? 0;
    tableData.value = data || [];
  } catch {
    // 请求失败时清空表格，避免残留旧数据
    tableData.value = [];
  } finally {
    loading.value = false;
  }
};

// 重置到第一页并重新加载（搜索词变化时使用）
const reload = () => {
  pagination.page = 1;
  fetchData();
};

// ===== 远程搜索 =====
// el-select 自带输入框输入时触发（组件内部内置 300ms 防抖），
// 每次展开下拉也会以空关键词触发一次，因此首次加载无需额外处理
const remoteMethod = (query: string) => {
  // 首次触发且未输入关键词时，使用 props.search 作为初始搜索词
  searchKeyword.value = initialSearchApplied ? query : query || props.search;
  initialSearchApplied = true;
  reload();
};

// ===== 用户交互 =====
// 点击表格行：记录选中行、向外写入选中值并收起下拉
const handleRowClick = (row: any) => {
  const valueField = props.tableConfig.value;
  selectedRow.value = row; // 记录选中行，驱动输入框显示该行 label
  displayValue.value = row[valueField]; // 触发 set → 外部 modelValue 更新
  emit("select-change", row);
  selectRef.value?.blur();
};

// 点击清除按钮：清空选中行与外部值
const onClear = () => {
  selectedRow.value = null;
  displayValue.value = null;
};

// 分页切换：更新页码并重新加载
const handlePageChange = (page: number) => {
  pagination.page = page;
  fetchData();
};

// 外部 modelValue 变化（清空/重置/回显）时，同步清理内部选中行，避免输入框显示残留
watch(
  () => props.modelValue,
  val => {
    const valueField = props.tableConfig.value;
    if (selectedRow.value && val !== selectedRow.value[valueField]) {
      selectedRow.value = null;
    }
  }
);
</script>

<style scoped>
.option {
  padding: 5px;
  background-color: #fff;
}
</style>
