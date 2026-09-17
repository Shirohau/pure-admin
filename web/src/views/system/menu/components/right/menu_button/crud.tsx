import {
  compute,
  dict,
  type ValueBuilderContext,
  type AddReq,
  type CreateCrudOptionsProps,
  type CreateCrudOptionsRet,
  type DelReq,
  type EditReq,
  type UserPageQuery
} from "@fast-crud/fast-crud";
import { api, apiPrefix } from "./api";
import { computed, ref, shallowRef } from "vue";
import { ElMessageBox } from "element-plus";
import { useButtonPerms } from "@/utils/auth";

import { addDialog } from "@/components/ReDialog";
import AutoApi from "./components/AutoApi.vue";
import SettingRole from "./components/SettingRole.vue";
import { ElMessage } from "element-plus";
import { useMenuTree } from "../../../hooks/useMenuTree";
import ReTableSelect from "@/components/ReTableSelect";
const { selectTreeNode, isSelected } = useMenuTree();
import { useFilter } from "@/components/ReFilter/src/useFilter";
// 定义组件名称
export const componentName = "MenuButtonView";

/**
 * 定义一个CrudOptions生成器方法
 */
export default function ({
  crudExpose
}: CreateCrudOptionsProps): CreateCrudOptionsRet {
  /** 权限控制 */
  const hasPerms = {
    /** 批量删除权限 */
    batchDestroy: useButtonPerms(`${componentName}:BatchDestroy`)
  };

  /** 筛选 */
  const { createFilterHeader, FilterTags, clearAllFilters } = useFilter({
    crudExpose
  });

  /** 新增 */
  const addRequest = async ({ form }: AddReq) => {
    form.menu = selectTreeNode.value?.id;
    return await api.CreateObj(form);
  };

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
  const onSelectionChange = changed => {
    selectedData.value = changed;
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
      actionbar: {
        buttons: {
          add: {
            disabled: computed(() => selectTreeNode.value == null)
          },
          batchAdd: {
            text: "自动匹配",
            type: "primary",
            disabled: computed(() => selectTreeNode.value == null),
            click: async () => {
              addDialog({
                title: "自动匹配API接口",
                props: {
                  // 赋默认值
                  formInline: {
                    tags: "",
                    // search: selectTreeNode.value.title
                    search: ""
                  }
                },
                contentRenderer: () => AutoApi,
                closeCallBack: async ({ options, args }) => {
                  // options.props 是响应式的
                  const { formInline } = options.props;
                  if (args?.command === "sure") {
                    const data = {
                      menu_id: selectTreeNode.value.id,
                      search: formInline.tags
                    };

                    const { message }: ApiResponse =
                      await api.BatchCreateObj(data);
                    ElMessage.success(message);
                    await crudExpose.doRefresh(); // 刷新表
                  }
                }
              });
            }
          }
        }
      },
      toolbar: {
        buttons: {
          refresh: {
            disabled: computed(() => !isSelected.value)
          },
          search: {
            show: true,
            disabled: computed(() => !isSelected.value)
          },
          export: {
            show: false
          }
        }
      },
      rowHandle: {
        fixed: "right",
        width: 150,
        align: "center",
        dropdown: {
          more: {
            link: true,
            size: "small",
            icon: "Setting"
          }
        },
        buttons: {
          view: {
            order: 1,
            icon: "View",
            dropdown: true,
            link: true
          },
          edit: {
            order: 3,
            icon: "Edit",
            dropdown: true,
            link: true
          },
          remove: {
            order: 4,
            icon: "Delete",
            dropdown: true,
            link: true
          },
          setting: {
            order: 5,
            type: "primary",
            link: true,
            text: "配置",
            click: async ({ row }) => {
              addDialog({
                title: "分配角色",
                hideFooter: true,
                appendToBody: true,
                props: {
                  // 赋默认值
                  formInline: {
                    menu_button_id: row.id,
                    menu_button_type: row.button_type
                  }
                },
                contentRenderer: () => SettingRole
              });
            }
          },
          moveUp: {
            text: "上移",
            link: true,
            click: async ({ row }) => {
              await api.MoveObj(row.id, "up");
              await crudExpose.doRefresh(); // 刷新表
            }
          },
          moveDown: {
            link: true,
            text: "下移",
            click: async ({ row }) => {
              await api.MoveObj(row.id, "down");
              await crudExpose.doRefresh(); // 刷新表
            }
          }
        }
      },
      columns: {
        $checked: {
          title: "选择",
          form: { show: false },
          column: {
            type: "selection",
            align: "center",
            width: "55px",
            columnSetShow: false //在列设置中不显示该字段
          }
        },
        button_type: {
          title: "按钮类型",
          type: "dict-select",
          dict: dict({
            data: [
              { value: "api", label: "接口", color: "success" },
              { value: "button", label: "按钮", color: "info" }
            ]
          }),
          form: {
            value: "api",
            col: { span: 9 },
            component: {
              clearable: false
            }
          },
          column: {
            width: 100,
            columnSlots: {
              header: createFilterHeader({
                type: "select",
                columnLabel: "按钮类型",
                fieldName: "button_type",
                selectList: [
                  { value: "api", label: "接口" },
                  { value: "button", label: "按钮" }
                ]
              })
            }
          }
        },
        api: {
          title: "接口地址",
          type: "text",
          form: {
            blank: compute(({ form }) => {
              return form.button_type === "button";
            }),
            col: { span: 15 },
            component: {
              name: shallowRef(ReTableSelect),
              vModel: "modelValue",
              tableConfig: {
                url: `${apiPrefix}api_list/`,
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
                  form.name = tableSelect.summary;
                  form.key = `${selectTreeNode.value.name}:${tableSelect.function}`;
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
                columnLabel: "接口地址",
                fieldName: "api"
              })
            }
          },
          valueResolve(context: ValueBuilderContext) {
            if (context.form.button_type === "button") {
              delete context.form.api;
              delete context.form.method;
            }
          }
        },
        name: {
          title: "名称",
          type: "text",
          form: {
            col: { span: 9 },
            rules: [{ required: true, message: "请输入名称" }],
            component: {
              props: {
                disabled: compute(({ form }) => {
                  return form.button_type === "api";
                })
              }
            }
          },
          column: {
            align: "left",
            columnSlots: {
              header: createFilterHeader({
                type: "text",
                columnLabel: "名称",
                fieldName: "name"
              })
            }
          }
        },
        key: {
          title: "权限值",
          type: "text",
          form: {
            col: { span: 9 },
            rules: [{ required: true, message: "请输入权限值" }],
            component: {
              props: {
                disabled: compute(({ form }) => {
                  return form.button_type === "api";
                })
              },
              slots: {
                prefix: ({ form }) => {
                  if (form.button_type === "button") {
                    return <el-text>{selectTreeNode.value.name}:</el-text>;
                  }
                }
              }
            },
            valueResolve({ form }: ValueBuilderContext) {
              if (form.button_type === "button") {
                form.key = `${selectTreeNode.value.name}:${form.key}`;
              }
            }
          },
          column: {
            columnSlots: {
              header: createFilterHeader({
                type: "text",
                columnLabel: "权限值",
                fieldName: "key"
              })
            }
          }
        },
        method: {
          title: "请求方法",
          type: "dict-select",
          form: {
            blank: compute(({ form }) => {
              return form.button_type === "button";
            }),
            col: { span: 6 },
            component: {
              props: {
                disabled: true
              }
            }
          },
          dict: dict({
            data: [
              { value: "GET", label: "GET", color: "primary" },
              { value: "POST", label: "POST", color: "success" },
              { value: "PUT", label: "PUT", color: "warning" },
              { value: "DELETE", label: "DELETE", color: "danger" }
            ]
          }),
          column: {
            align: "left",

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
        sort: {
          title: "排序",
          type: "text",
          form: {
            show: false
          },
          column: {
            columnSlots: {
              header: createFilterHeader({
                type: "text",
                columnLabel: "排序",
                fieldName: "sort"
              })
            }
          }
        }
      }
    }
  };
}
