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
import { ref } from "vue";
import { ElMessageBox } from "element-plus";
import { openExportDialog } from "@/components/ReExport";
import { openImportDialog } from "@/components/ReImport";
/** 筛选辅助工具（统一管理 filterForm + applyFilter + clearFilter + injectFilterToQuery）*/
import { useFilter } from "@/components/ReFilter/src/useFilter";
import { dialogRoleImpower } from "./components/dialogRoleImpower";
import { createRelation } from "@/utils/crud/createRelation";
import { createCrudPerms } from "@/utils/crud/createCrudPerms";
import { userTable } from "../user/crud";
const { merge } = useMerge();
// 定义组件名称
export const componentName = "RoleView";

/**
 * 定义一个CrudOptions生成器方法
 */
export default function createCrudOptions({
  crudExpose
}: CreateCrudOptionsProps): CreateCrudOptionsRet {
  /** 按钮权限（懒加载 + 响应式，权限加载完成后自动更新） */
  const hasPerms = createCrudPerms(componentName, {
    /** 授权权限 */
    impower: "Impower",
    /** 移动权限 */
    move: "Move"
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
        onSelectionChange,
        height: "100%",
        highlightCurrentRow: true
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
      actionbar: {
        buttons: {
          add: {
            show: hasPerms.add
          }
        }
      },
      toolbar: {
        buttons: {
          export: {
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
              openImportDialog(apiPrefix, crudExpose);
            }
          }
        }
      },
      rowHandle: {
        fixed: "right",
        align: "center",
        dropdown: {
          more: {
            icon: "Setting"
          }
        },
        buttons: {
          view: {
            order: 1,
            icon: "View",
            dropdown: true,
            link: true,
            show: hasPerms.view
          },
          edit: {
            order: 3,
            icon: "Edit",
            dropdown: true,
            link: true,
            show: hasPerms.edit
          },
          remove: {
            order: 4,
            icon: "Delete",
            dropdown: true,
            link: true,
            show: hasPerms.remove
          },
          impower: {
            order: 5,
            type: "success",
            text: "授权",
            show: hasPerms.impower,
            click: ({ row }) => {
              dialogRoleImpower(row);
            }
          },
          moveUp: {
            text: "上移",
            show: hasPerms.move,
            click: ({ row }) => {
              api.MoveObj(row.id, "up").then(async () => {
                await crudExpose.doRefresh(); // 刷新表
              });
            }
          },
          moveDown: {
            text: "下移",
            show: hasPerms.move,
            click: ({ row }) => {
              api.MoveObj(row.id, "down").then(async () => {
                await crudExpose.doRefresh(); // 刷新表
              });
            }
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
          title: "名称",
          type: "text",
          column: {
            columnSlots: {
              header: createFilterHeader({
                type: "text",
                columnLabel: "名称",
                fieldName: "name"
              })
            }
          }
        },
        code: {
          title: "编号",
          type: "text",
          column: {
            columnSlots: {
              header: createFilterHeader({
                type: "text",
                columnLabel: "编号",
                fieldName: "code"
              })
            }
          }
        },
        status: {
          title: "状态",
          search: { show: true },
          type: "dict-switch",
          dict: dict({
            data: [
              { value: true, label: "启用", color: "success" },
              { value: false, label: "禁用", color: "info" }
            ]
          }),
          form: {
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
        },
        user_count: userTable({
          form: { show: false },
          column: { show: true, title: "用户数" },
          columnCellRenderConfig: {
            fkField: "role",
            columnLabel: "user_count"
          }
        }),
        sort: {
          title: "显示排序",
          type: "number",
          addForm: {
            show: false
          },
          column: {
            columnSlots: {
              header: createFilterHeader({
                type: "number",
                columnLabel: "显示排序",
                fieldName: "sort"
              })
            }
          }
        }
      }
    }
  };
}

/**
 * 角色 关联组件工厂
 * @description 基于 createRelation 生成关联的三个组件：选择器、只读表单、子表嵌套
 */
const { createSelect } = createRelation({
  /** 标题 */
  title: "角色",
  /** 组件名称（按钮权限标识，供其他模块复用本模块配置） */
  componentName,
  /** 本模块 CRUD 配置生成器 */
  createCrudOptions,
  /** 本模块接口 */
  api,
  fkField: "role",
  dictConfig: {
    api,
    dictLabel: "name",
    queryFields: ["id", "name"]
  },
  searchConfig: {
    field: "role",
    lookup: "in"
  },
  columnCellRenderConfig: {
    componentName,
    createCrudOptions,
    fkField: "role",
    columnLabel: "role_name",
    crudOptionsOverride: {
      rowHandle: {
        show: true,
        width: 120,
        buttons: {
          view: { show: false },
          edit: { show: false },
          remove: { show: false },
          moveUp: { show: false },
          moveDown: { show: false }
        }
      }
    }
  }
});

/**
 * 角色 选择器
 * @description 默认在表单（form）作为父级字段选择器显示。列表（column）不显示、查询区（search）不显示
 */
export const roleSelect = (
  options?: ColumnCompositionProps
): ColumnCompositionProps => {
  const defaultOptions: ColumnCompositionProps = {
    // 表单覆盖配置
    form: {
      component: {
        crudOptionsOverride: {
          rowHandle: {
            width: 120,
            buttons: {
              view: { show: false },
              edit: { show: false },
              remove: { show: false },
              moveUp: { show: false },
              moveDown: { show: false }
            }
          }
        }
      }
    }
  };
  return createSelect(merge(defaultOptions, options));
};
