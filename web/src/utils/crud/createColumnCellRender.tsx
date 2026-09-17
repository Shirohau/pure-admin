/**
 * 关联列详情链接列配置工厂
 * @description 生成"关联列"列表配置：溢出省略 + 点击打开详情弹窗（dialogAsideTable），
 * 手写列配置模块（如 publisher）共用；cellRender 实现收敛在本文件。
 */
import {
  useMerge,
  type CreateCrudOptions,
  type DynamicallyCrudOptions,
  type ScopeContext
} from "@fast-crud/fast-crud";
import { dialogAsideTable } from "@/components/ReAsideTable";

const { merge } = useMerge();

/** 溢出省略样式：超长文本（如合同编号）自动省略，避免撑破单元格 */
const ellipsisStyle = {
  display: "inline-block",
  maxWidth: "100%",
  overflow: "hidden",
  textOverflow: "ellipsis",
  whiteSpace: "nowrap"
};

/** 单元格链接渲染配置（createRelationColumn 内部透传给 createColumnCellRender） */
export interface CreateColumnCellRenderOptions {
  /** 模块标识 */
  componentName: string;
  /** 创建 crud 配置 */
  createCrudOptions: CreateCrudOptions;
  /** 外键字段 */
  fkField: string;
  /** 标签字段 */
  columnLabel: string;
  /** 详情抽屉覆盖配置（columnCrudOptionsOverride） */
  crudOptionsOverride?: DynamicallyCrudOptions;
}

/**
 * 生成"关联记录"单元格点击链接（cellRender 内部实现）
 * @description 单元格渲染为可点击的链接文本，点击后弹出该关联记录所在模块的
 * 详情弹窗（dialogAsideTable，按外键 id 过滤单条记录）。
 * @param config - 链接参数（模块标识 + 外键字段）
 * @returns {(scope: ScopeContext) => JSX.Element} cellRender 渲染函数
 */
export function createColumnCellRender(config: CreateColumnCellRenderOptions) {
  const { componentName, createCrudOptions, fkField, columnLabel } = config;

  return (scope: ScopeContext) => {
    const text = scope.row?.[columnLabel];
    // 行数据中的外键值：数组为多选关联、单个数字为单选关联、null 表示未关联
    const fkValue = scope.row?.id;
    // 未关联任何记录时不渲染可点击链接
    if (fkValue == null) {
      return <span style={ellipsisStyle}>{text}</span>;
    }

    /** 详情弹窗默认覆盖配置：隐藏查询区/动作条/勾选列与行操作，按外键精确过滤单条 */
    const detailDefaults: DynamicallyCrudOptions = {
      search: {
        show: false,
        // 未提供外键字段时不注入过滤条件（由调用方覆盖配置自行指定）
        initialForm:
          fkField != null ? { [`${fkField}__exact`]: fkValue } : undefined
      },
      form: {
        initialForm: fkField != null ? { [fkField]: fkValue } : undefined
      },
      actionbar: { show: false },
      rowHandle: {
        width: 80,
        buttons: {
          view: { show: false },
          remove: { show: false }
        }
      },
      columns: {
        $checked: {
          column: {
            show: false
          }
        }
      }
    };

    return (
      <el-link
        type="primary"
        style={{ fontSize: "inherit" }}
        onClick={() => {
          // 弹出关联记录详情弹窗（复用本模块列表配置，按外键 id 过滤单条；调用方覆盖配置优先）
          dialogAsideTable({
            title: "详情",
            hideFooter: true,
            props: {
              componentName,
              autoSearch: true,
              createCrudOptions,
              crudOptionsOverride: merge(
                {},
                detailDefaults,
                config.crudOptionsOverride
              )
            }
          });
        }}
      >
        <span style={ellipsisStyle}>{text}</span>
      </el-link>
    );
  };
}
