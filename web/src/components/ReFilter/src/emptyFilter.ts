/**
 * 空值筛选（为空 / 不为空）公共语义（FilterArea 提交与 useFilter 标签展示共用）
 * - 为空 → field__isnull=true：后端匹配 NULL 或空字符串
 * - 不为空 → field__isnull=false：后端匹配非 NULL 且非空字符串
 * （后端逻辑见 backend/extends/drf/filters/base.py 的 _build_isnull_q）
 */

/** 空值筛选模式（"" 未选择；"isnull" 为空；"notnull" 不为空） */
export type EmptyFilterMode = "" | "isnull" | "notnull";

/** 点击空值标签后的下一个模式（互斥 + 可取消） */
export const resolveNextEmptyMode = (
  current: EmptyFilterMode | undefined,
  clicked: Exclude<EmptyFilterMode, "">
): EmptyFilterMode => (current === clicked ? "" : clicked);

/** 与后端 parse_isnull_flag 一致的真值集合（表示"为空"） */
const TRUTHY_ISNULL_VALUES = new Set(["true", "1", "是"]);

/** 解析 isnull 提交值是否为"为空"（布尔值直接返回，字符串按后端真值集合判断） */
export const parseIsnullFlag = (value: any): boolean => {
  if (typeof value === "boolean") return value;
  return TRUTHY_ISNULL_VALUES.has(String(value).toLowerCase());
};

/** 空值筛选模式 → 筛选结果荷载（isnull=true 为空 / isnull=false 不为空） */
export const toIsnullResult = (mode: Exclude<EmptyFilterMode, "">) => ({
  cond1Operator: "isnull",
  cond1Value: mode === "isnull"
});

/** isnull 提交值 → 标签文案（为空 / 不为空） */
export const resolveIsnullLabel = (value: any): string =>
  parseIsnullFlag(value) ? "为空" : "不为空";
