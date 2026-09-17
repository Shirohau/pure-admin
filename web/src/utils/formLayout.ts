/**
 * fast-crud 表单网格布局辅助工具
 *
 * groups.columns 配置中，只需按行组织字段名即可。
 * 字段实际占用的宽度由各字段 column 定义中的 form.col.span 控制。
 *
 * 用法示例：
 * ```ts
 * groups: {
 *   base: {
 *     columns: formRows(
 *       ["field1", "field2"],           // 第1行：2个字段（各 span 12）
 *       ["field3"],                      // 第2行：1个字段（需设 span 24 才能满行）
 *       ["field4", "field5", "field6"], // 第3行：3个字段（各 span 8）
 *     )
 *   }
 * }
 * ```
 */

/**
 * 将多个行数组展平为一维 columns 数组。
 * 纯粹为了按行组织的可读性，不影响字段 span。
 */
export function formRows(...rows: string[][]): string[] {
  return rows.flat();
}

/**
 * 与 formRows 相同，别名，语义更贴近网格布局。
 */
export const formGrid = formRows;
