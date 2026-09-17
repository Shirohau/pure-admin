import type {
  CreateCrudOptionsProps,
  CreateCrudOptionsRet,
  UserPageQuery
} from "@fast-crud/fast-crud";
import { api } from "./api";

/** 筛选辅助工具（统一管理 filterForm + applyFilter + clearFilter + injectFilterToQuery）*/
import { useFilter } from "@/components/ReFilter/src/useFilter";

// 定义组件名称
export const componentName = "MessageCenterView";

/**
 * 定义一个CrudOptions生成器方法
 */
export default function createCrudOptions({
  crudExpose
}: CreateCrudOptionsProps): CreateCrudOptionsRet {
  /** 筛选 */
  const { createFilterHeader, FilterTags, clearAllFilters } = useFilter({
    crudExpose
  });

  /** 列表查询 */
  const pageRequest = async (query: UserPageQuery) => {
    return await api.GetMyMessages(query);
  };

  return {
    FilterTags,
    crudOptions: {
      // 请求相关配置
      request: {
        pageRequest
      },
      // 表格配置
      table: {
        rowKey: "id"
      },
      // 动作条配置
      actionbar: {
        show: true
      },
      // 工具条配置
      toolbar: {
        show: false
      },
      // 操作列配置
      rowHandle: {
        show: false
      },
      // 查询框配置
      search: {
        show: false,
        buttons: {
          reset: {
            click: context => {
              clearAllFilters();
              context.doReset();
            }
          }
        }
      },
      // 字段复合配置
      columns: {
        id: {
          title: "ID",
          type: "text",
          column: {
            show: false,
            columnSlots: {
              header: createFilterHeader({
                type: "text",
                columnLabel: "ID",
                fieldName: "id"
              })
            }
          }
        },
        title: {
          title: "标题",
          type: "text",
          column: {
            minWidth: 200,
            showOverflowTooltip: true,
            columnSlots: {
              header: createFilterHeader({
                type: "text",
                columnLabel: "标题",
                fieldName: "title"
              })
            }
          }
        },
        content: {
          title: "内容",
          type: "textarea",
          column: {
            minWidth: 300,
            showOverflowTooltip: true,
            columnSlots: {
              header: createFilterHeader({
                type: "text",
                columnLabel: "内容",
                fieldName: "content"
              })
            }
          }
        },
        target_type: {
          title: "目标类型",
          type: "text",
          column: {
            width: 100,
            columnSlots: {
              header: createFilterHeader({
                type: "text",
                columnLabel: "目标类型",
                fieldName: "target_type"
              })
            }
          }
        },
        create_dt: {
          title: "发送时间",
          type: "datetime",
          column: {
            width: 180,
            columnSlots: {
              header: createFilterHeader({
                type: "date",
                columnLabel: "发送时间",
                fieldName: "create_dt"
              })
            }
          }
        }
      }
    }
  };
}
