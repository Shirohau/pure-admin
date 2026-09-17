import {
  dict,
  useMerge,
  type AddReq,
  type CreateCrudOptionsProps,
  type CreateCrudOptionsRet,
  type ColumnCompositionProps,
  type DelReq,
  type EditReq,
  type UserPageQuery
} from "@fast-crud/fast-crud";
import { api, apiPrefix } from "./api";
import { api as dept_api } from "../dept/api";
import { api as file_api } from "../file/api";
import { ref } from "vue";
import { ElMessageBox } from "element-plus";

import { openExportDialog } from "@/components/ReExport";
import { openImportDialog } from "@/components/ReImport";
import XEUtils from "xe-utils";
import { getDictData } from "../dictionary/api";
import { dialogAsideTable } from "@/components/ReAsideTable";
import oauth2CreateCrudOptions from "@/views/oauth2/crud";

/** 筛选辅助工具（统一管理 filterForm + applyFilter + clearFilter + injectFilterToQuery）*/
import { useFilter } from "@/components/ReFilter/src/useFilter";
import { createRelation } from "@/utils/crud/createRelation";
import { roleSelect } from "../role/crud";
import { createCrudPerms } from "@/utils/crud/createCrudPerms";
const { merge } = useMerge();
// 用户
export const componentName = "UserView";
/**
 * 定义一个CrudOptions生成器方法
 */
export default function createCrudOptions({
  crudExpose
}: CreateCrudOptionsProps): CreateCrudOptionsRet {
  /** 按钮权限（懒加载 + 响应式，权限加载完成后自动更新） */
  const hasPerms = createCrudPerms(componentName, {
    /** 重置密码权限 */
    resetPassword: "ResetPassword",
    /** 权限管理 */
    permissions: "Permissions"
  });

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
  /** 性别字典（提取为变量，方便在 columnSlots 中复用 data，避免重复请求）*/
  const genderDict = getDictData("gender");

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
        width: 250,
        buttons: {
          view: {
            dropdown: true,
            show: hasPerms.view
          },
          edit: {
            show: hasPerms.edit
          },
          remove: {
            dropdown: true,
            show: hasPerms.remove
          },
          password: {
            order: 5,
            show: hasPerms.resetPassword,
            text: "重置密码",
            click: ({ loadingRef, row }) => {
              loadingRef.value = true;
              api.ResetPassword(row.id).finally(() => {
                loadingRef.value = false;
              });
            }
          },
          oauth2: {
            text: "第三方账号",
            dropdown: true,
            show: true,
            click: async ({ row }) => {
              const initialForm = row?.oauth2?.length
                ? { id__in: row.oauth2.join(",") }
                : { platform__exact: "A" };
              dialogAsideTable({
                title: "第三方账号",
                props: {
                  componentName: componentName,
                  autoSearch: true,
                  createCrudOptions: oauth2CreateCrudOptions,
                  crudOptionsOverride: {
                    search: {
                      show: false,
                      initialForm: initialForm
                    },
                    actionbar: { show: false },
                    toolbar: { show: false },
                    columns: {
                      $checked: {
                        column: {
                          show: false
                        }
                      }
                    }
                  }
                }
              });
            }
          }
        },
        dropdown: {
          more: {
            text: "操作",
            icon: "Setting"
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
        username: {
          title: "账号",
          type: "text",
          form: {
            rules: [{ required: true, message: "请输入账号" }]
          },
          column: {
            columnSlots: {
              header: createFilterHeader({
                type: "text",
                columnLabel: "账号",
                fieldName: "username"
              })
            }
          }
        },
        name: {
          title: "姓名",
          type: "text",
          form: {
            rules: [{ required: true, message: "请输入姓名" }]
          },
          column: {
            columnSlots: {
              header: createFilterHeader({
                type: "text",
                columnLabel: "姓名",
                fieldName: "name"
              })
            }
          }
        },
        email: {
          title: "邮箱",
          type: "text",
          form: {
            rules: [
              { required: true, message: "请输入邮箱" },
              {
                type: "email",
                message: "请输入有效的邮箱地址",
                trigger: "blur"
              }
            ]
          },
          column: {
            width: 150,
            showOverflowTooltip: true,
            columnSlots: {
              header: createFilterHeader({
                type: "text",
                columnLabel: "邮箱",
                fieldName: "email"
              })
            }
          }
        },
        mobile: {
          title: "电话",
          type: "text",
          column: {
            width: 100,
            showOverflowTooltip: true,
            columnSlots: {
              header: createFilterHeader({
                type: "text",
                columnLabel: "电话",
                fieldName: "mobile"
              })
            }
          }
        },
        avatar_path: {
          title: "头像",
          type: "cropper-uploader",
          form: {
            component: {
              uploader: {
                type: "form",
                data: {
                  folder: "avatar"
                }
              },
              valueType: "row",
              buildUrl(context: any) {
                return context.path || context;
              },
              on: {
                change: (context: any) => {
                  if (context.value) {
                    // 新增
                    context.form.avatar_id = context.value.id;
                  } else {
                    // 删除
                    file_api.DeleteObj(context.form.avatar_id);
                    context.form.avatar_id = null;
                  }
                }
              }
            }
          }
        },
        gender: {
          title: "性别",
          type: "dict-select",
          dict: genderDict,
          column: {
            columnSlots: {
              header: createFilterHeader({
                type: "select",
                columnLabel: "性别",
                fieldName: "gender",
                selectList: () => genderDict.data ?? []
              })
            }
          }
        },

        dept: {
          title: "关联部门",
          type: "dict-tree",
          search: { show: true, component: { clearable: true } },
          dict: dict({
            isTree: true,
            async getData() {
              const params = {
                paginate: false,
                status: true,
                query: "{id, name, path, parent_path}"
              };
              const { data } = await dept_api.GetList(params);
              return XEUtils.toArrayTree(data, {
                key: "path",
                parentKey: "parent_path"
              });
            }
          }),
          form: {
            rules: [{ required: true, message: "请关联部门" }],
            component: {
              placeholder: "请选择",
              props: {
                checkStrictly: true,
                filterable: true,
                props: {
                  value: "id",
                  label: "name"
                }
              }
            }
          },
          column: {
            minWidth: 120,
            formatter({ row }) {
              return row.dept_name;
            },
            columnSlots: {
              header: createFilterHeader({
                type: "text",
                columnLabel: "关联部门",
                fieldName: "dept__name"
              })
            }
          }
        },
        dept_full_path: {
          title: "部门全路径",
          form: { show: false },
          column: {
            width: 200,
            showOverflowTooltip: true
          }
        },
        // 角色 选择器（开启多选）
        role: roleSelect({
          search: { show: true },
          form: {
            component: {
              multiple: true,
              crossPage: true,
              crudOptionsOverride: {
                columns: {
                  $checked: {
                    column: {
                      show: true
                    }
                  }
                }
              }
            }
          },
          column: {
            show: true,
            width: 120,
            columnSlots: {
              header: createFilterHeader({
                type: "text",
                columnLabel: "角色名称",
                tooltip: "点击可查看详情",
                fieldName: "role__name"
              })
            }
          },
          columnCellRenderConfig: {
            fkField: "user"
          }
        }),
        timezone: {
          title: "时区",
          type: "dict-select",
          form: {
            value: "Asia/Shanghai"
          },
          dict: dict({
            data: [
              { value: "Asia/Shanghai", label: "中国 上海" },
              { value: "Europe/Moscow", label: "俄罗斯 莫斯科" },
              { value: "Asia/Tokyo", label: "日本 东京" },
              { value: "Asia/Singapore", label: "新加坡" },
              { value: "Asia/Kolkata", label: "印度 孟买" },
              { value: "Europe/London", label: "英国 伦敦" },
              { value: "Europe/Paris", label: "法国 巴黎" },
              { value: "America/New_York", label: "美国 纽约" },
              { value: "UTC", label: "UTC（世界协调时间）" }
            ]
          }),
          column: {
            show: false
          }
        },
        is_active: {
          title: "有效状态",
          type: "dict-switch",
          form: {
            value: true
          },
          dict: dict({
            data: [
              { value: true, label: "是", color: "success" },
              { value: false, label: "否", color: "danger" }
            ]
          }),
          column: {
            minWidth: 100,
            columnSlots: {
              header: createFilterHeader({
                type: "select",
                columnLabel: "有效状态",
                fieldName: "is_active",
                selectList: [
                  { value: 1, label: "是" },
                  { value: 0, label: "否" }
                ]
              })
            }
          }
        }
      }
    }
  };
}

/**
 * 用户 关联组件工厂
 * @description 基于 createRelation 生成关联的三个组件：选择器、只读表单、子表嵌套
 */
const { createSelect, createForm, createTable } = createRelation({
  /** 标题 */
  title: "用户",
  /** 组件名称（按钮权限标识，供其他模块复用本模块配置） */
  componentName,
  /** 本模块 CRUD 配置生成器 */
  createCrudOptions,
  /** 本模块接口 */
  api,
  fkField: "user",
  dictConfig: {
    api,
    dictLabel: "name",
    queryFields: ["id", "name"]
  },
  searchConfig: {
    field: "user",
    lookup: "in"
  },
  columnCellRenderConfig: {
    componentName,
    createCrudOptions,
    fkField: "user",
    columnLabel: "user_name",
    crudOptionsOverride: {
      rowHandle: { show: false },
      columns: {
        username: { column: { show: false } },
        avatar_path: { column: { show: false } },
        role: { column: { show: false } },
        timezone: { column: { show: false } },
        is_active: { column: { show: false } }
      }
    }
  }
});

/**
 * 用户 选择器
 * @description 默认在表单（form）作为父级字段选择器显示。列表（column）不显示、查询区（search）不显示
 */
export const userSelect = (
  options?: ColumnCompositionProps
): ColumnCompositionProps => {
  const defaultOptions: ColumnCompositionProps = {
    // 表单覆盖配置
    form: {
      component: {
        crudOptionsOverride: {
          rowHandle: { show: false },
          search: { initialForm: { is_active: true } },
          columns: {
            username: { column: { show: false } },
            avatar_path: { column: { show: false } },
            role: { column: { show: false } },
            timezone: { column: { show: false } },
            is_active: { column: { show: false } }
          }
        }
      }
    }
  };
  return createSelect(merge(defaultOptions, options));
};

/**
 * 用户 只读表单
 * @description 默认在表单（form）作为只读表单显示，列表（column）显示，查询区（search）显示
 */
export const userForm = (
  options?: ColumnCompositionProps
): ColumnCompositionProps => {
  const defaultOptions: ColumnCompositionProps = {};
  return createForm(merge(defaultOptions, options));
};

/**
 * 用户 子表嵌套
 * @description 默认在表单（form）作为子表 tab 显示。列表（column）不显示，查询区（search）不显示
 */
export const userTable = (
  options?: ColumnCompositionProps
): ColumnCompositionProps => {
  const defaultOptions: ColumnCompositionProps = {};
  return createTable(merge(defaultOptions, options));
};
