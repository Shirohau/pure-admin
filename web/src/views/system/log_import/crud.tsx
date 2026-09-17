import {
  dict,
  type CreateCrudOptionsProps,
  type CreateCrudOptionsRet,
  type UserPageQuery
} from "@fast-crud/fast-crud";
import { api } from "./api";
import { h, ref } from "vue";
import { ElMessageBox } from "element-plus";

import { ElButton } from "element-plus";

/** 筛选辅助工具（统一管理 filterForm + applyFilter + clearFilter + injectFilterToQuery）*/
import { useFilter } from "@/components/ReFilter/src/useFilter";
import { createCrudPerms } from "@/utils/crud/createCrudPerms";

// 定义组件名称
export const componentName = "LogImportView";

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
        rowKey: "id",
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
        import_status: {
          title: "状态",
          type: "dict-select",
          dict: dict({
            data: [
              { value: "CREATED", label: "创建成功" },
              { value: "PARSING", label: "解析中" },
              { value: "PARSED", label: "解析成功" },
              { value: "INPUT_ERROR", label: "输入数据错误" },
              { value: "PARSE_ERROR", label: "解析错误" },
              { value: "CONFIRMED", label: "导入已确认" },
              { value: "IMPORTING", label: "导入中" },
              { value: "IMPORTED", label: "导入成功" },
              { value: "IMPORT_ERROR", label: "导入错误" },
              { value: "CANCELLED", label: "已取消" }
            ]
          }),
          column: {
            width: 120,
            align: "center",
            columnSlots: {
              header: createFilterHeader({
                type: "select",
                columnLabel: "状态",
                fieldName: "import_status",
                selectList: [
                  { value: "CREATED", label: "创建成功" },
                  { value: "PARSING", label: "解析中" },
                  { value: "PARSED", label: "解析成功" },
                  { value: "INPUT_ERROR", label: "输入数据错误" },
                  { value: "PARSE_ERROR", label: "解析错误" },
                  { value: "CONFIRMED", label: "导入已确认" },
                  { value: "IMPORTING", label: "导入中" },
                  { value: "IMPORTED", label: "导入成功" },
                  { value: "IMPORT_ERROR", label: "导入错误" },
                  { value: "CANCELLED", label: "已取消" }
                ]
              })
            }
          }
        },
        "import_params.data_file": {
          title: "文件地址",
          column: {
            width: 100,
            align: "center",
            cellRender({ value }) {
              if (!value) return "";
              return h(
                ElButton,
                {
                  link: true,
                  type: "warning",
                  onClick: () => window.open(value, "_blank")
                },
                {
                  default: () => "下载文件"
                }
              );
            },
            columnSlots: {
              header: createFilterHeader({
                type: "text",
                columnLabel: "文件地址",
                fieldName: "import_params.data_file"
              })
            }
          }
        },
        input_errors_file: {
          title: "错误文件地址",
          column: {
            width: 150,
            align: "center",
            cellRender({ value }) {
              if (!value) return "";
              return h(
                ElButton,
                {
                  link: true,
                  type: "warning",
                  onClick: () => window.open(value, "_blank")
                },
                {
                  default: () => "下载文件"
                }
              );
            },
            columnSlots: {
              header: createFilterHeader({
                type: "text",
                columnLabel: "错误文件地址",
                fieldName: "input_errors_file"
              })
            }
          }
        },
        import_started: {
          title: "开始时间",
          column: {
            align: "center",
            columnSlots: {
              header: createFilterHeader({
                type: "date",
                columnLabel: "开始时间",
                fieldName: "import_started"
              })
            }
          }
        },
        import_finished: {
          title: "完成时间",
          column: {
            align: "center",
            columnSlots: {
              header: createFilterHeader({
                type: "date",
                columnLabel: "完成时间",
                fieldName: "import_finished"
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
