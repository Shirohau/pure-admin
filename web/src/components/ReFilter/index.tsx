import reFilter from "./src/index.vue";
import { withInstall } from "@pureadmin/utils";

/**
 * 表格列头排序与筛选组件（配合 useFilter 组合式函数使用）
 * - 后端筛选：useFilter({ crudExpose })，模板中 <template #header-bottom><FilterTags /></template>
 * - 前端筛选：useFilter({ mode: "local", crudExpose })
 * - 内置 text / number / select / date / datetime / cascader 六种类型（新增类型见 registry/index.ts）
 * - 列配置：columns: { name: { column: { columnSlots: { header: createFilterHeader(...) } } } }
 */
export const ReFilter = withInstall(reFilter);

export default ReFilter;
