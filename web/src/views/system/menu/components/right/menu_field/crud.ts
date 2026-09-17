import {
  dict,
  type AddReq,
  type DelReq,
  type EditReq,
  type UserPageQuery,
  type CreateCrudOptionsProps,
  type CreateCrudOptionsRet
} from "@fast-crud/fast-crud";

import { addDialog } from "@/components/ReDialog";
import { ElMessage, ElMessageBox } from "element-plus";
import { computed, ref } from "vue";
import { useButtonPerms } from "@/utils/auth";
import XEUtils from "xe-utils";
import { api, apiPrefix } from "./api";
import AutoField from "./components/AutoField.vue";
import SettingRole from "./components/SettingRole.vue";
import { useMenuTree } from "../../../hooks/useMenuTree";
import { useFilter } from "@/components/ReFilter/src/useFilter";
const { selectTreeNode, isSelected } = useMenuTree();

// 定义组件名称
export const componentName = "MenuFieldView";

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
                width: "50%",
                title: "自动匹配模型表",
                props: {
                  // 赋默认值
                  formInline: {
                    name: "",
                    model: "",
                    // search: selectTreeNode.value.title
                    search: ""
                  }
                },
                contentRenderer: () => AutoField,
                closeCallBack: async ({ options, args }) => {
                  // options.props 是响应式的
                  const { formInline } = options.props;
                  if (args?.command === "sure") {
                    const { message } = await api.BatchCreateObj({
                      app_model: formInline.model,
                      menu_id: selectTreeNode.value.id
                    });
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
        width: 120,
        align: "center",
        buttons: {
          view: {
            show: false
          },
          edit: {
            show: false
          },
          setting: {
            order: 4,
            type: "primary",
            icon: "setting",
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
                    menu_field_id: row.id
                  }
                },
                contentRenderer: () => SettingRole
              });
            }
          },
          remove: {
            order: 5,
            icon: "Delete",
            link: true
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
        model: {
          title: "模型表",
          type: "dict-select",
          dict: dict({
            url: `${apiPrefix}app_models/`,
            immediate: false,
            label: "name",
            value: "model"
          }),
          form: {
            col: { span: 8 },
            component: {
              props: {
                filterable: true
              }
            },
            valueChange({ form, value, getComponentRef }) {
              form.verbose_name = ""; // 将“field_name”的值置空
              form.field_name = "";
              if (value) {
                getComponentRef("verbose_name").reloadDict();
              }
            }
          }
        },
        verbose_name: {
          title: "字段显示名",
          type: "dict-select",
          dict: dict({
            url({ form }) {
              if (form && form.model != null) {
                return `${apiPrefix}app_model_fields/?model=${form.model}`;
              }
              return undefined; // 返回undefined 将不加载字典
            },
            label: "verbose_name",
            value: "verbose_name"
          }),
          form: {
            col: { span: 8 },
            component: {
              props: {
                filterable: true,
                allowCreate: true
              }
            },
            valueChange({ form, value, getComponentRef }) {
              form.field_name = ""; // 将“verbose_name”的值置空
              if (value) {
                const fieldNameRef = getComponentRef("verbose_name").getDict();
                const dictMap = fieldNameRef.getDictMap();
                form.field_name = XEUtils.get(dictMap[value], "field_name");
              }
            }
          },
          column: {
            columnSlots: {
              header: createFilterHeader({
                type: "text",
                columnLabel: "字段显示名",
                fieldName: "verbose_name"
              })
            }
          }
        },
        field_name: {
          title: "字段名",
          type: "text",
          form: { col: { span: 8 } },
          column: {
            columnSlots: {
              header: createFilterHeader({
                type: "text",
                columnLabel: "字段名",
                fieldName: "field_name"
              })
            }
          }
        }
      }
    }
  };
}
