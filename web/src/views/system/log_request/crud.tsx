import {
  dict,
  type CreateCrudOptionsProps,
  type CreateCrudOptionsRet,
  type UserPageQuery
} from "@fast-crud/fast-crud";
import { api, apiPrefix } from "./api";
import { ref } from "vue";
import { ElMessageBox } from "element-plus";
import { openExportDialog } from "@/components/ReExport";

/** 筛选辅助工具（统一管理 filterForm + applyFilter + clearFilter + injectFilterToQuery）*/
import { useFilter } from "@/components/ReFilter/src/useFilter";
import { createCrudPerms } from "@/utils/crud/createCrudPerms";

// 定义组件名称
export const componentName = "LogRequestView";

/**
 * 定义一个CrudOptions生成器方法
 */
export default function crudOptions({
  crudExpose
}: CreateCrudOptionsProps): CreateCrudOptionsRet {
  /** 按钮权限（懒加载 + 响应式，权限加载完成后自动更新） */
  const hasPerms = createCrudPerms(componentName);

  /** 筛选 */
  const { createFilterHeader, FilterTags, clearAllFilters } = useFilter({
    crudExpose
  });

  /** 列表查询 */
  const pageRequest = async (query: UserPageQuery) => {
    return await api.GetList(query);
  };

  // 选中的数据
  const selectedData = ref([]);
  // 表格选中事件
  const onSelectionChange = (newSelection: any[]) => {
    selectedData.value = newSelection;
  };
  // 批量删除
  const handleBatchDelete = () => {
    const ids = selectedData.value.map(item => item.id);
    ElMessageBox.confirm(
      `确定要批量删除这${selectedData.value.length}条记录吗`,
      "删除提示"
    )
      .then(async () => {
        await api.BatchDelete(ids as any);
        await crudExpose.doRefresh();
        selectedData.value = [];
      })
      .catch(() => {});
  };

  return {
    hasPerms,
    selectedData,
    handleBatchDelete,
    FilterTags,
    crudOptions: {
      // 请求相关配置
      request: {
        pageRequest
      },
      // 表格配置
      table: {
        rowKey: "id", //设置你的主键id， 默认rowKey=id
        onSelectionChange
      },
      // 动作条配置
      actionbar: { show: false },
      // 工具条配置
      toolbar: {
        buttons: {
          export: {
            title: "导出",
            show: hasPerms.export,
            click: () => {
              openExportDialog(apiPrefix, crudExpose);
            }
          }
        }
      },
      // 操作列配置
      rowHandle: { show: false },
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
        username: {
          title: "请求用户",
          type: "text",
          column: {
            width: 120,
            columnSlots: {
              header: createFilterHeader({
                type: "text",
                columnLabel: "请求用户",
                fieldName: "username"
              })
            }
          }
        },
        ip_address: {
          title: "IP地址",
          type: "text",
          column: {
            width: 120,
            columnSlots: {
              header: createFilterHeader({
                type: "text",
                columnLabel: "IP地址",
                fieldName: "ip_address"
              })
            }
          }
        },
        request_time: {
          title: "请求时间",
          type: "datetime",
          column: {
            width: 150,
            columnSlots: {
              header: createFilterHeader({
                type: "date",
                columnLabel: "请求时间",
                fieldName: "request_time"
              })
            }
          }
        },
        method: {
          title: "请求方法",
          type: "dict-select",
          dict: dict({
            data: [
              { value: "GET", label: "GET" },
              { value: "POST", label: "POST" },
              { value: "PUT", label: "PUT" },
              { value: "DELETE", label: "DELETE" }
            ]
          }),
          column: {
            width: 100,
            columnSlots: {
              header: createFilterHeader({
                type: "select",
                columnLabel: "请求方法",
                fieldName: "method",
                selectList: [
                  { value: "GET", label: "GET" },
                  { value: "POST", label: "POST" },
                  { value: "PUT", label: "PUT" },
                  { value: "DELETE", label: "DELETE" }
                ]
              })
            }
          }
        },
        url: {
          title: "请求地址",
          type: "text",
          column: {
            minWidth: 100,
            showOverflowTooltip: true,
            columnSlots: {
              header: createFilterHeader({
                type: "text",
                columnLabel: "请求地址",
                fieldName: "url"
              })
            }
          }
        },
        feedback: {
          title: "请求反馈",
          type: "text",
          column: {
            minWidth: 100,
            showOverflowTooltip: true,
            columnSlots: {
              header: createFilterHeader({
                type: "text",
                columnLabel: "请求反馈",
                fieldName: "feedback"
              })
            }
          }
        },
        query_params: {
          title: "请求参数",
          type: "textarea",
          column: {
            minWidth: 100,
            showOverflowTooltip: true,
            columnSlots: {
              header: createFilterHeader({
                type: "text",
                columnLabel: "请求参数",
                fieldName: "query_params"
              })
            }
          }
        }
      }
    }
  };
}
