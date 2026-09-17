import {
  compute,
  useMerge,
  type AddReq,
  type CreateCrudOptionsProps,
  type CreateCrudOptionsRet,
  type ColumnCompositionProps,
  type DelReq,
  type EditReq,
  type UserPageQuery
} from "@fast-crud/fast-crud";
import { api } from "./api";
import { useButtonPerms } from "@/utils/auth";
import ReVueOffice from "@/components/ReVueOffice";
import { shallowRef } from "vue";

/** 筛选辅助工具（统一管理 filterForm + applyFilter + clearFilter + injectFilterToQuery）*/
import { useFilter } from "@/components/ReFilter/src/useFilter";
import { createRelation } from "@/utils/crud/createRelation";
const { merge } = useMerge();
// 附件
export const componentName = "FileView";
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

  /** 新增 */
  const addRequest = async ({ form }: AddReq) => {
    return await api.CreateObj(form);
  };

  /** 列表查询 */
  const pageRequest = async (query: UserPageQuery) => {
    return await api.GetList(query);
  };

  /** 修改 */
  const editRequest = async ({ form }: EditReq) => {
    return await api.UpdateObj(form.id, form);
  };
  /** 删除 */
  const delRequest = async ({ row }: DelReq) => {
    return await api.DeleteObj(row.id);
  };
  return {
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
        rowKey: "id" //设置你的主键id， 默认rowKey=id
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
            show: false
          }
        }
      },
      actionbar: {
        buttons: {
          add: {
            show: true
          }
        }
      },
      rowHandle: {
        align: "center",
        buttons: {
          view: {
            show: true
          },
          edit: {
            show: false
          },
          remove: {
            show: useButtonPerms(`${componentName}:Destroy`)
          }
        }
      },
      form: {
        wrapper: {
          is: "el-drawer",
          size: "100%",
          buttons: {
            ok: { show: false },
            cancel: { show: false },
            reset: { show: false },
            copy: { show: false },
            paste: { show: false }
          }
        }
      },
      columns: {
        path: {
          title: "文件地址",
          addForm: {
            show: false
          },
          form: {
            component: {
              name: "fs-files-format",
              // name: "FsImagesFormat",
              getFileName(value: any) {
                // 创建 URL 对象（自动解析）
                const urlObj = new URL(value);
                // 获取路径部分，例如 "/media/.../%E8%B6%85..."
                const path = urlObj.pathname;
                // 提取最后一段（文件名）
                const encodedFileName = path.substring(
                  path.lastIndexOf("/") + 1
                );
                // 解码 URL 编码（如 %E8%B6%85 → 超）
                const fileName = decodeURIComponent(encodedFileName);
                return fileName;
              },
              async buildUrl(value: any) {
                return value;
              }
            }
          },
          column: {
            component: {
              name: "fs-files-format",
              // name: "FsImagesFormat",
              getFileName(value: any) {
                // 创建 URL 对象（自动解析）
                const urlObj = new URL(value);
                // 获取路径部分，例如 "/media/.../%E8%B6%85..."
                const path = urlObj.pathname;
                // 提取最后一段（文件名）
                const encodedFileName = path.substring(
                  path.lastIndexOf("/") + 1
                );
                // 解码 URL 编码（如 %E8%B6%85 → 超）
                const fileName = decodeURIComponent(encodedFileName);
                return fileName;
              },
              async buildUrl(value: any) {
                return value;
              }
            },
            columnSlots: {
              header: createFilterHeader({
                type: "text",
                columnLabel: "文件名",
                fieldName: "name"
              })
            }
          }
        },
        size: {
          title: "文件大小",
          type: "text",
          addForm: {
            show: false
          },
          column: {
            columnSlots: {
              header: createFilterHeader({
                type: "text",
                columnLabel: "文件大小",
                fieldName: "size"
              })
            }
          }
        },
        file_suffix: {
          title: "文件后缀",
          type: "text",
          form: {
            show: false
          },
          column: {
            columnSlots: {
              header: createFilterHeader({
                type: "text",
                columnLabel: "文件后缀",
                fieldName: "file_suffix"
              })
            }
          }
        },
        related_content_type: {
          title: "模型",
          type: "text",
          addForm: {
            show: false
          },
          column: {
            columnSlots: {
              header: createFilterHeader({
                type: "text",
                columnLabel: "模型",
                fieldName: "related_content_type"
              })
            }
          }
        },
        related_object: {
          title: "对象",
          type: "text",
          addForm: {
            show: false
          },
          column: {
            columnSlots: {
              header: createFilterHeader({
                type: "text",
                columnLabel: "对象",
                fieldName: "related_object"
              })
            }
          }
        },
        file: {
          title: "文件上传",
          type: "file-uploader",
          viewForm: {
            show: false
          },
          form: {
            component: {
              uploader: {
                type: "form"
                // 自定义data，下面是示例
                // data: compute(({ form }) => {
                //   return {
                //     folder: "resume",
                //     content_type: form.content_type_id,
                //     object_id: form.id
                //   };
                // })
              },
              valueType: "row",
              on: {
                success: () => {
                  // 关闭表单
                  const wrapper = crudExpose.getFormWrapperRef();
                  wrapper.close();
                  crudExpose.doRefresh();
                }
              }
            }
          },
          column: {
            show: false
          }
        },
        file_path: {
          title: "文件预览",
          column: {
            show: false
          },
          addForm: {
            show: false
          },
          form: {
            col: { span: 24 },
            component: {
              name: shallowRef(ReVueOffice),
              vModel: "modelValue",
              file_suffix: compute(({ form }) => form.file_suffix)
            }
          }
        }
      }
    }
  };
}

const { createTable } = createRelation({
  title: "附件",
  componentName,
  createCrudOptions,
  api,
  fkField: "file",
  dictConfig: {
    api,
    dictLabel: "name",
    queryFields: ["id", "name"]
  },
  searchConfig: {
    field: "file",
    lookup: "in"
  },
  columnCellRenderConfig: {
    componentName,
    createCrudOptions,
    fkField: "file",
    columnLabel: "file_name"
  }
});

/**
 * 附件 子表嵌套
 * @description 默认在表单（form）作为子表 tab 显示。列表（column）不显示，查询区（search）不显示
 */
export const fileTable = (
  options?: ColumnCompositionProps
): ColumnCompositionProps => {
  const defaultOptions: ColumnCompositionProps = {};
  return createTable(merge(defaultOptions, options));
};
