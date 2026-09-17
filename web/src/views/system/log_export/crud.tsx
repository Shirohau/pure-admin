import {
  compute,
  dict,
  type CreateCrudOptionsProps,
  type CreateCrudOptionsRet,
  type UserPageQuery
} from "@fast-crud/fast-crud";
import { api } from "./api";
import { ref } from "vue";
import { ElMessageBox } from "element-plus";

/** 筛选辅助工具（统一管理 filterForm + applyFilter + clearFilter + injectFilterToQuery）*/
import { useFilter } from "@/components/ReFilter/src/useFilter";
import { createCrudPerms } from "@/utils/crud/createCrudPerms";

// 定义组件名称
export const componentName = "LogExportView";

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
          export: { show: false }
        }
      },
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
      // 操作列配置
      rowHandle: {
        fixed: "right",
        width: 120,
        align: "center",
        buttons: {
          view: {
            show: false
          },
          edit: {
            show: false
          },
          remove: {
            show: false
          },
          download: {
            show: compute(ctx => {
              return ctx.row.export_status === "EXPORTED";
            }),
            text: "下载文件",
            type: "warning",
            link: true,
            click: ctx => window.open(ctx.row.data_file, "_blank")
          }
        }
      },
      // 字段复合配置
      columns: {
        id: {
          title: "ID",
          type: "text",
          column: {
            width: 50,
            align: "center",
            show: false
          }
        },
        model_verbose_name: {
          title: "模型",
          type: "text",
          column: {
            columnSlots: {
              header: createFilterHeader({
                type: "text",
                columnLabel: "模型",
                fieldName: "model_verbose_name",
                lookup: "exact",
                hideEmpty: true,
                tagOperatorLabel: "包含"
              })
            }
          }
        },
        export_status: {
          title: "状态",
          type: "dict-select",
          dict: dict({
            data: [
              { value: "CREATED", label: "创建成功" },
              { value: "EXPORTING", label: "导出中" },
              { value: "EXPORT_ERROR", label: "导出错误" },
              { value: "EXPORTED", label: " 导出成功" },
              { value: "CANCELLED", label: " 已取消" }
            ]
          }),
          column: {
            width: 120,
            align: "center",
            columnSlots: {
              header: createFilterHeader({
                type: "select",
                columnLabel: "状态",
                fieldName: "export_status",
                selectList: [
                  { value: "CREATED", label: "创建成功" },
                  { value: "EXPORTING", label: "导出中" },
                  { value: "EXPORT_ERROR", label: "导出错误" },
                  { value: "EXPORTED", label: "导出成功" },
                  { value: "CANCELLED", label: "已取消" }
                ]
              })
            }
          }
        },
        data_file: {
          title: "文件地址",
          column: {
            showOverflowTooltip: true,
            formatter({ value }) {
              if (!value) return "";
              const urlObj = new URL(value);
              const filenameEncoded = urlObj.pathname.split("/").pop(); // 获取路径最后一段
              const filename = decodeURIComponent(filenameEncoded);
              return filename;
            },
            columnSlots: {
              header: createFilterHeader({
                type: "text",
                columnLabel: "文件地址",
                fieldName: "data_file"
              })
            }
          }
        },

        export_started: {
          title: "开始时间",
          column: {
            align: "center",
            columnSlots: {
              header: createFilterHeader({
                type: "date",
                columnLabel: "开始时间",
                fieldName: "export_started"
              })
            }
          }
        },
        export_finished: {
          title: "完成时间",
          column: {
            align: "center",
            columnSlots: {
              header: createFilterHeader({
                type: "date",
                columnLabel: "完成时间",
                fieldName: "export_finished"
              })
            }
          }
        },
        error_message: {
          title: "错误描述",
          column: {
            showOverflowTooltip: true,
            columnSlots: {
              header: createFilterHeader({
                type: "text",
                columnLabel: "错误描述",
                fieldName: "error_message"
              })
            }
          }
        },
        created_by: {
          title: "创建人",
          column: {
            align: "center",
            columnSlots: {
              header: createFilterHeader({
                type: "text",
                columnLabel: "创建人",
                fieldName: "created_by__name"
              })
            }
          }
        }
      }
    }
  };
}
