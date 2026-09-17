import { useMerge, type SearchItemProps } from "@fast-crud/fast-crud";

const { merge } = useMerge();

/**
 * 生成查询区多选表格选择器配置（createSearch 内部实现）
 * @param config - 外键字段与模块依赖配置
 * @returns 查询区字段配置
 */
export function createSearch(options: SearchItemProps): SearchItemProps {
  const defaultOptions: SearchItemProps = {
    show: true,
    col: { span: 8 },
    component: {
      name: "fs-table-select",
      style: { height: "auto" }, // 自动高度
      multiple: true, // 开启多选
      crossPage: true, // 是否跨页选中
      rowKey: "id", // element-plus 必传
      dict: options.dict, // 字典配置 必传
      // 选择器配置
      select: {
        collapseTags: true, // 是否折叠标签
        collapseTagsTooltip: true, // 是否显示折叠标签的 tooltip
        maxCollapseTags: 2 // 最大折叠标签数
      },
      createCrudOptions: options.createCrudOptions, // 创建 crud 配置 必传
      // 搜索弹窗列表默认显示多选框、隐藏行操作，调用方 crudOptionsOverride 优先
      crudOptionsOverride: {
        search: { show: false },
        actionbar: { show: false },
        toolbar: {
          buttons: {
            search: { show: true },
            compact: { show: false },
            columns: { show: false },
            export: { show: false },
            import: { show: false }
          }
        },
        rowHandle: { show: false },
        columns: {
          $checked: {
            column: {
              show: true
            }
          }
        }
      }
    }
  };
  return merge(defaultOptions, options);
}

export interface ValueResolveConfig {
  /** 目标字段名   */
  field?: string;
  /** 查询方式后缀，对应后端过滤器的 lookup 表达式 */
  lookup?: string;
}
/**
 * 创建搜索字段的 valueResolve 方法
 *
 * @description
 * 仅生成值解析函数，不包含任何 UI 配置（show、component、autoSearchTrigger 等）。
 * 调用方需自行在搜索字段配置中组装其余属性，实现值解析逻辑与 UI 配置的彻底解耦。
 *
 * @param config - 值解析配置，所有选项均可选，缺省时使用合理默认值
 * @returns 符合 fast-crud SearchItemProps["valueResolve"] 签名的回调函数
 *
 * @example
 * ```ts
 * // 基本用法：模糊查询
 * valueResolve: createValueResolve({ field: "username", lookup: "contains" })
 *
 * // 多选 in 查询
 * valueResolve: createValueResolve({ lookup: "in" })
 *
 * // 使用默认配置（等同于 field=当前key, lookup="contains"）
 * valueResolve: createValueResolve()
 * ```
 */
export const createValueResolve = (
  config: ValueResolveConfig = {}
): NonNullable<SearchItemProps["valueResolve"]> => {
  // 解构配置，lookup 默认为 "contains"
  const { field, lookup = "contains" } = config;
  return ({ key, value, form }) => {
    // 空值守卫：null / undefined / 空字符串均跳过，避免向后端发送无意义的查询参数
    if (value == null || value === "") return;
    // 确定最终使用的字段名：优先取 config.field，否则回退到当前 key
    const targetField = String(field || key);
    // 确认最终使用的值：如果 lookup 为 "in"，则将值 join 为逗号分隔字符串
    const targetValue = lookup === "in" ? value.join(",") : value;
    form[`${targetField}__${lookup}`] = targetValue;
    // 删除原始 key，防止同一字段以两种命名同时提交给后端
    delete form[key];
  };
};
