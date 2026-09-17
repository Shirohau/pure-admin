import { computed, ref } from "vue";
import { Close } from "@element-plus/icons-vue";
import { resolveIsnullLabel } from "../emptyFilter";
import type { ActiveFilterItem } from "../types";

/**
 * 筛选标签（表格上方 tag 展示）：活跃条件计算 + 渲染函数工厂
 * - createActiveFilters：filterForm → 活跃条件列表（computed）
 * - createFilterTags：渲染函数工厂（模板中 <FilterTags /> 直接使用）
 */

/** 操作符 → 中文标签映射 */
const OPERATOR_LABELS: Record<string, string> = {
  exact: "等于",
  not_exact: "不等于",
  contains: "包含",
  not_contains: "不包含",
  startswith: "开头是",
  endswith: "结尾是",
  gt: "大于",
  gte: "大于等于",
  lt: "小于",
  lte: "小于等于",
  in: "属于",
  isnull: "为空"
};

/** 解析标签操作符文案：isnull 按提交值区分（为空/不为空），其余取 固定描述 > 内置映射 > 原文 */
const resolveOperatorLabel = (
  operator: string,
  value: any,
  fixedOperatorLabel?: string
): string => {
  if (operator === "isnull") return resolveIsnullLabel(value);
  return fixedOperatorLabel || OPERATOR_LABELS[operator] || operator;
};

/**
 * 活跃筛选条件计算（供标签渲染与外部读取）：
 * - 普通筛选 → 单条 tag；区间（gte/lte 配对）→ 合并为一条区间 tag
 * - select 多选 → 以 label 展示（如 "性别 属于 男,女"）；级联 → 路径以 / 连接、路径间以 ；连接
 */
export const createActiveFilters = (context: {
  filterForm: Record<string, any>;
  fieldLabelMap: Record<string, string>;
  tagOperatorLabelMap: Record<string, string>;
}) => {
  const { filterForm, fieldLabelMap, tagOperatorLabelMap } = context;

  return computed<ActiveFilterItem[]>(() => {
    // 收集级联元数据：{ 字段名: 二维 labels[][] }（每个元素是一条选中路径的层级标签）
    const cascaderMeta = new Map<string, any[]>();
    for (const [key, val] of Object.entries(filterForm)) {
      if (key.endsWith("__cascader")) {
        cascaderMeta.set(key.slice(0, -"__cascader".length), val as any[]);
      }
    }
    // 级联字段的值由 __cascader 元数据统一展示（跳过普通分组，避免重复 tag）
    const cascaderFieldSet = new Set(cascaderMeta.keys());

    // 收集 select 选项 label 元数据：{ 字段名: label[] }（提交给后端的是 value）
    const selectMeta = new Map<string, any[]>();
    for (const [key, val] of Object.entries(filterForm)) {
      if (key.endsWith("__select_labels")) {
        selectMeta.set(key.slice(0, -"__select_labels".length), val as any[]);
      }
    }
    const selectFieldSet = new Set(selectMeta.keys());

    const entries = Object.entries(filterForm).filter(
      ([key]) => !key.endsWith("__cascader") && !key.endsWith("__select_labels")
    );

    // 按 fieldName 分组（每组最多两个条件：范围区间的 gte/lte）
    const groups = new Map<
      string,
      { key: string; operator: string; value: any }[]
    >();
    for (const [key, val] of entries) {
      // 取最后一个 __ 分隔字段名与操作符（支持 fieldName 本身含 __，如 book__name）
      const lastSep = key.lastIndexOf("__");
      const fieldName = lastSep === -1 ? key : key.slice(0, lastSep);
      if (cascaderFieldSet.has(fieldName) || selectFieldSet.has(fieldName))
        continue;
      const operator = lastSep === -1 ? "exact" : key.slice(lastSep + 2);
      if (!groups.has(fieldName)) groups.set(fieldName, []);
      groups.get(fieldName)!.push({ key, operator, value: val });
    }

    const rangeStartOps = new Set(["gte", "gt"]);
    const rangeEndOps = new Set(["lte", "lt"]);
    const result: ActiveFilterItem[] = [];

    for (const [fieldName, items] of groups) {
      const fieldLabel = fieldLabelMap[fieldName] || fieldName;
      // 优先使用字段配置的固定操作符描述（如"包含"、"开头是"）
      const fixedOperatorLabel = tagOperatorLabelMap[fieldName];

      // 区间配对（gte + lte）合并为一条区间 tag
      const startItem = items.find(i => rangeStartOps.has(i.operator));
      const endItem = items.find(i => rangeEndOps.has(i.operator));

      if (startItem && endItem) {
        result.push({
          key: startItem.key,
          fieldName,
          fieldLabel,
          operatorLabel: "",
          value: startItem.value,
          endKey: endItem.key,
          endValue: endItem.value
        });
      } else {
        // 单条件（范围只填一边时也走这里）
        const item = items[0];
        result.push({
          key: item.key,
          fieldName,
          fieldLabel,
          operatorLabel: resolveOperatorLabel(
            item.operator,
            item.value,
            fixedOperatorLabel
          ),
          value: item.value
        });
      }
    }

    // 级联筛选：每组生成一条合并 tag（多选路径以 ；连接，路径内层级以 / 连接）
    for (const [fieldName, labels] of cascaderMeta) {
      const fieldLabel = fieldLabelMap[fieldName] || fieldName;
      const labelText = labels
        .map(path => (Array.isArray(path) ? path.join(" / ") : path))
        .join("；");
      result.push({
        key: `${fieldName}__cascader`,
        fieldName,
        fieldLabel,
        operatorLabel: "",
        value: labelText
      });
    }

    // select 选项：以 label 展示（多选逗号连接，如 "性别 属于 男,女"）
    for (const [fieldName, labels] of selectMeta) {
      const fieldLabel = fieldLabelMap[fieldName] || fieldName;
      const fixedOperatorLabel = tagOperatorLabelMap[fieldName];
      result.push({
        key: `${fieldName}__select_labels`,
        fieldName,
        fieldLabel,
        operatorLabel: fixedOperatorLabel || OPERATOR_LABELS["in"] || "in",
        value: labels.join(",")
      });
    }

    return result;
  });
};

/** 筛选标签渲染函数工厂（返回渲染函数，模板中 <FilterTags /> 直接使用） */
export const createFilterTags = (context: {
  /** 获取活跃筛选条件列表 */
  getItems: () => ActiveFilterItem[];
  /** 删除单个筛选条件 */
  onRemove: (item: ActiveFilterItem) => void;
  /** 清除全部筛选与排序 */
  onClearAll: () => void;
}) => {
  const { getItems, onRemove, onClearAll } = context;
  const isHovered = ref(false);
  const isClearBtnHovered = ref(false);

  return () => {
    const items = getItems();
    const hasItems = items.length > 0;
    return (
      <div
        style={{
          marginTop: "10px",
          display: "flex",
          alignItems: "center",
          minHeight: "32px",
          padding: "6px 10px",
          background: "#fafafa",
          border: "1px dashed #d9d9d9",
          borderRadius: "6px",
          transition: "border-color 0.2s"
        }}
        onMouseenter={() => (isHovered.value = true)}
        onMouseleave={() => (isHovered.value = false)}
      >
        <div
          style={{
            display: "flex",
            flex: 1,
            flexWrap: "wrap",
            gap: "8px",
            alignItems: "center"
          }}
        >
          {hasItems &&
            items.map(item => {
              let tagContent: string;
              if (item.endKey !== undefined) {
                // 区间筛选
                tagContent = `${item.fieldLabel} ${item.value} 至 ${item.endValue}`;
              } else if (
                item.operatorLabel === "为空" ||
                item.operatorLabel === "不为空"
              ) {
                // 空值筛选：仅展示列名 + 操作符
                tagContent = `${item.fieldLabel} ${item.operatorLabel}`;
              } else if (item.operatorLabel === "") {
                // 级联筛选等无操作符场景（如"省市县 北京 / 东城区"）
                tagContent = `${item.fieldLabel} ${item.value}`;
              } else {
                tagContent = `${item.fieldLabel} ${item.operatorLabel} ${item.value}`;
              }
              return (
                <el-tag
                  key={item.endKey ? item.key + "_" + item.endKey : item.key}
                  closable
                  size="small"
                  style={{
                    background: "#ecf5ff",
                    borderColor: "#d9ecff",
                    color: "#409eff",
                    borderRadius: "6px"
                  }}
                  onClose={() => onRemove(item)}
                >
                  {tagContent}
                </el-tag>
              );
            })}
        </div>
        {hasItems && isHovered.value && (
          <span
            class="clear-all-btn"
            style={{
              display: "inline-flex",
              alignItems: "center",
              justifyContent: "center",
              width: "15px",
              height: "15px",
              borderRadius: "50%",
              backgroundColor: isClearBtnHovered.value ? "#909399" : "#C0C4CC",
              cursor: "pointer",
              flexShrink: 0,
              transition: "background-color 0.2s"
            }}
            onMouseenter={() => (isClearBtnHovered.value = true)}
            onMouseleave={() => (isClearBtnHovered.value = false)}
            onClick={onClearAll}
            title="清除全部筛选"
          >
            <Close style={{ width: "12px", height: "12px", color: "#fff" }} />
          </span>
        )}
      </div>
    );
  };
};
