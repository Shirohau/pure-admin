<template>
  <div class="h-[calc(100vh-230px)]">
    <fs-crud ref="crudRef" v-bind="crudBinding" />
  </div>
</template>

<script lang="ts" setup>
import { onMounted } from "vue";

import {
  AddReq,
  compute,
  DelReq,
  dict,
  EditReq,
  useFs,
  useFsRef,
  UserPageQuery
} from "@fast-crud/fast-crud";
import { api } from "../api";
import { useCreateComponent } from "../hooks/useCreateComponent";

const { getValueFormComponent, getFormTypeDictData } = useCreateComponent();

const componentName = "FormContentView";
defineOptions({
  name: componentName
});

const props = defineProps({
  parent: { type: Number }
});

// ... (request 函数保持不变) ...
const createCrudOptions = ({ crudExpose }) => {
  const addRequest = async ({ form }: AddReq) => await api.CreateObj(form);
  const pageRequest = async (query: UserPageQuery) => {
    query.parent = props.parent;
    return await api.GetList(query);
  };
  const editRequest = async ({ form, row }: EditReq) => {
    form.id = row.id;
    return await api.UpdateObj(form.id, form);
  };
  const delRequest = async ({ row }: DelReq) => await api.DeleteObj(row.id);

  return {
    crudOptions: {
      request: { pageRequest, addRequest, editRequest, delRequest },
      search: { show: false },
      table: { rowKey: "id" },
      toolbar: { buttons: { export: { show: false } } },
      rowHandle: {
        align: "center",
        width: 150,
        buttons: {
          view: {
            show: false
          },
          remove: {
            show: compute(({ row }) => row.closable)
          }
        }
      },
      columns: {
        parent: {
          title: "上级",
          form: {
            show: false,
            value: props.parent,
            component: { disabled: true }
          },
          column: {
            show: false,
            columnSetShow: false
          }
        },
        key: {
          title: "键",
          type: "el-input",
          editForm: {
            component: {
              disabled: true
            }
          },
          column: {
            width: 150
          }
        },
        title: {
          title: "标题",
          column: {
            width: 150
          }
        },
        form_type: {
          title: "表单类型",
          type: "dict-select",
          dict: dict({
            data: getFormTypeDictData()
          }),
          form: {
            value: "text"
          },
          editForm: {
            component: {
              disabled: true
            }
          },
          column: {
            width: 100
          }
        },
        value: {
          title: "内容",
          form: {
            // 使用 compute 动态计算组件
            component: compute((context: any) => {
              return getValueFormComponent(context);
            })
          },
          column: {
            component: {
              name: compute((context: any) => {
                if (context.row.form_type == "image") return "fs-images-format";
              }),
              style: "width:30px",
              buildUrl(context: any) {
                return context.path;
              }
            }
          }
        },

        setting: {
          title: "配置",
          form: {
            col: { span: 24 },
            component: { name: "fs-json-editor", mode: "code" }
          },
          column: { formatter: ({ value }) => JSON.stringify(value) }
        }
      }
    }
  };
};

const { crudRef, crudBinding, crudExpose } = useFsRef();

useFs({
  crudRef,
  crudBinding,
  crudExpose,
  createCrudOptions
});

onMounted(() => {
  crudExpose.doRefresh();
});
</script>
