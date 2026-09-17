import {
  dict,
  type AddReq,
  type CreateCrudOptionsProps,
  type CreateCrudOptionsRet,
  type DelReq,
  type EditReq,
  type UserPageQuery
} from "@fast-crud/fast-crud";
import { api, apiPrefix } from "./api";
import { ref, shallowRef } from "vue";
import { ElMessageBox } from "element-plus";
import ReTableSelect from "@/components/ReTableSelect";
import { useButtonPerms } from "@/utils/auth";
import { openExportDialog } from "@/components/ReExport";
import { openImportDialog } from "@/components/ReImport";

/** 筛选辅助工具（统一管理 filterForm + applyFilter + clearFilter + injectFilterToQuery）*/
import { useFilter } from "@/components/ReFilter/src/useFilter";

// 定义组件名称
export const componentName = "ApiWhiteView";

/**
 * 定义一个CrudOptions生成器方法
 */
export default function ({
  crudExpose
}: CreateCrudOptionsProps): CreateCrudOptionsRet {
  /** 权限控制 */
  const hasPerms = {
    /** 新增权限 */
    add: useButtonPerms(`${componentName}:Create`),
    /** 查看权限 */
    view: useButtonPerms(`${componentName}:Retrieve`),
    /** 修改权限 */
    edit: useButtonPerms(`${componentName}:Update`),
    /** 删除权限 */
    remove: useButtonPerms(`${componentName}:Destroy`),
    /** 批量删除权限 */
    batchDestroy: useButtonPerms(`${componentName}:BatchDestroy`),
    /** 导出权限 */
    export: useButtonPerms(`${componentName}:SyncExport`),
    /** 导入权限 */
    import: useButtonPerms(`${componentName}:SyncImport`)
  };

  /** 新增 */
  const addRequest = async ({ form }: AddReq) => {
    return await api.CreateObj(form);
  };

  /** 筛选 */
  const { createFilterHeader, FilterTags, clearAllFilters } = useFilter({
    crudExpose
  });

  /** 列表查询 */
  const pageRequest = async (query: UserPageQuery) => {
    return await api.GetList(query);
  };

  /** 修改 */
  const editRequest = async ({ form, row }: EditReq) => {
    form.id = row.id;
    return await api.UpdateObj(form.id, form);
  };
  /** 删除 */
  const delRequest = async ({ row }: DelReq) => {
    return await api.DeleteObj(row.id);
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
      // 在这里自定义你的crudOptions配置
      request: {
        pageRequest,
        addRequest,
        editRequest,
        delRequest
      },
      table: {
        rowKey: "id", //设置你的主键id， 默认rowKey=id
        onSelectionChange
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
      toolbar: {
        buttons: {
          export: {
            title: "导出",
            show: hasPerms.export,
            click: () => {
              openExportDialog(apiPrefix, crudExpose);
            }
          },
          import: {
            title: "导入",
            show: hasPerms.import,
            circle: true,
            order: 4,
            icon: "Download",
            type: "primary",
            click: () => {
              openImportDialog(apiPrefix);
            }
          }
        }
      },
      actionbar: {
        buttons: {
          add: {
            show: hasPerms.add
          }
        }
      },
      rowHandle: {
        align: "center",
        buttons: {
          view: {
            show: hasPerms.view
          },
          edit: {
            show: hasPerms.edit
          },
          remove: {
            show: hasPerms.remove
          }
        }
      },
      columns: {
        $checked: {
          title: "选择",
          form: { show: false },
          column: {
            show: hasPerms.batchDestroy,
            type: "selection",
            align: "center",
            width: "55px",
            columnSetShow: false //在列设置中不显示该字段
          }
        },
        name: {
          title: "描述",
          type: "text",
          form: {
            col: { span: 8 },
            component: {
              props: {
                disabled: true
              }
            }
          },
          column: {
            columnSlots: {
              header: createFilterHeader({
                type: "text",
                columnLabel: "描述",
                fieldName: "name"
              })
            }
          }
        },
        method: {
          title: "请求方法",
          type: "dict-select",
          search: {
            show: true,
            component: {
              props: {
                disabled: false
              }
            }
          },
          form: {
            col: { span: 8 },
            component: {
              props: {
                disabled: true
              }
            }
          },
          dict: dict({
            data: [
              { value: "GET", label: "GET" },
              { value: "POST", label: "POST" },
              { value: "PUT", label: "PUT" },
              { value: "PATCH", label: "PATCH" },
              { value: "DELETE", label: "DELETE" }
            ]
          }),
          column: {
            columnSlots: {
              header: createFilterHeader({
                type: "select",
                columnLabel: "请求方法",
                fieldName: "method",
                selectList: [
                  { value: "GET", label: "GET" },
                  { value: "POST", label: "POST" },
                  { value: "PUT", label: "PUT" },
                  { value: "PATCH", label: "PATCH" },
                  { value: "DELETE", label: "DELETE" }
                ]
              })
            }
          }
        },
        api: {
          title: "地址",
          type: "text",
          form: {
            col: { span: 24 },
            component: {
              name: shallowRef(ReTableSelect),
              vModel: "modelValue",
              search: "",
              tableConfig: {
                url: `/api/system/menubutton/api_list/`,
                label: "path",
                value: "path",
                columns: [
                  { prop: "tags", label: "标签", width: 80 },
                  { prop: "summary", label: "概要", width: 100 },
                  { prop: "function", label: "函数名" },
                  { prop: "method", label: "请求方法", width: 80 },
                  { prop: "path", label: "API地址" },
                  { prop: "description", label: "详细说明" }
                ]
              },
              on: {
                onSelectChange: ({ $event: tableSelect, form }) => {
                  form.name = `${tableSelect.tags}${tableSelect.summary}`;
                  form.method = tableSelect.method;
                }
              }
            }
          },
          column: {
            showOverflowTooltip: true,
            columnSlots: {
              header: createFilterHeader({
                type: "text",
                columnLabel: "地址",
                fieldName: "api"
              })
            }
          }
        },
        status: {
          title: "状态",
          type: "dict-switch",
          dict: dict({
            data: [
              { value: true, label: "启用", color: "success" },
              { value: false, label: "禁用", color: "info" }
            ]
          }),
          form: {
            col: { span: 8 },
            value: true
          },
          column: {
            columnSlots: {
              header: createFilterHeader({
                type: "select",
                columnLabel: "状态",
                fieldName: "status",
                selectList: [
                  { value: 1, label: "启用" },
                  { value: 0, label: "禁用" }
                ]
              })
            }
          }
        }
      }
    }
  };
}
