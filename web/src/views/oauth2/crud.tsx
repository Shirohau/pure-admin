import {
  compute,
  useMerge,
  type AddReq,
  type DelReq,
  type EditReq,
  type UserPageQuery,
  type ColumnCompositionProps,
  type CreateCrudOptionsProps,
  type CreateCrudOptionsRet
} from "@fast-crud/fast-crud";
import { api, apiPrefix } from "./api";
import { ref } from "vue";
import { ElMessageBox } from "element-plus";
import { openExportDialog } from "@/components/ReExport";
import { openImportDialog } from "@/components/ReImport";
import { useButtonPerms } from "@/utils/auth";
const { merge } = useMerge();

/** 筛选辅助工具（统一管理 filterForm + applyFilter + clearFilter + injectFilterToQuery）*/
import { useFilter } from "@/components/ReFilter/src/useFilter";
import { createRelation } from "@/utils/crud/createRelation";

// 定义组件名称
export const componentName = "UserOAuthView";

/**
 * 定义一个CrudOptions生成器方法
 */
export default function createCrudOptions({
  crudExpose
}: CreateCrudOptionsProps): CreateCrudOptionsRet {
  /** 权限控制 */
  const hasPerms = {
    /** 新增权限 */
    add: useButtonPerms(`${componentName}:Create`),
    /** 批量删除权限 */
    batchDestroy: useButtonPerms(`${componentName}:BatchDestroy`),
    /** 导出权限 */
    export: useButtonPerms(`${componentName}:SyncExport`),
    /** 导入权限 */
    import: useButtonPerms(`${componentName}:SyncImport`)
  };

  const groupTab = ref("base");

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
      // 请求相关配置
      request: {
        pageRequest,
        addRequest,
        editRequest,
        delRequest
      },
      // 表格配置
      table: {
        rowKey: "id", //设置你的主键id， 默认rowKey=id
        onSelectionChange
      },
      // 动作条配置
      actionbar: {
        buttons: {
          add: {
            show: hasPerms.add
          }
        }
      },
      // 工具条配置
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
      // 操作列配置
      rowHandle: {
        show: false
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
      // 表单基本配置
      form: {
        wrapper: {
          is: "el-drawer",
          size: "100%",
          appendToBody: true,
          buttons: {
            ok: { show: compute(() => groupTab.value == "base") },
            cancel: { show: compute(() => groupTab.value == "base") },
            reset: { show: compute(() => groupTab.value == "base") },
            copy: { show: compute(() => groupTab.value == "base") },
            paste: { show: compute(() => groupTab.value == "base") }
          },
          onOpen() {
            groupTab.value = "base";
          }
        },
        group: {
          groupType: "tabs",
          onTabChange: (pane: string) => {
            groupTab.value = pane;
          },
          modelValue: "base",
          groups: {
            base: {
              label: "第三方认证",
              lazy: true,
              columns: ["user", "platform", "uname", "create_dt"]
            }
          }
        }
      },
      // 字段复合配置
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
        username: {
          title: "用户",
          type: "text",
          column: {
            columnSlots: {
              header: createFilterHeader({
                type: "text",
                columnLabel: "用户",
                fieldName: "user__name"
              })
            }
          }
        },
        platform_display: {
          title: "第三方平台",
          type: "text",
          column: {
            columnSlots: {
              header: createFilterHeader({
                type: "text",
                columnLabel: "第三方平台",
                fieldName: "platform"
              })
            }
          }
        },
        uname: {
          title: "第三方平台用户名",
          type: "text",
          column: {
            columnSlots: {
              header: createFilterHeader({
                type: "text",
                columnLabel: "第三方平台用户名",
                fieldName: "uname"
              })
            }
          }
        },
        create_dt: {
          title: "创建时间",
          type: "datetime",
          column: {
            columnSlots: {
              header: createFilterHeader({
                type: "date",
                columnLabel: "创建时间",
                fieldName: "create_dt"
              })
            }
          }
        }
      }
    }
  };
}

/**
 * 第三方认证 关联组件工厂
 * @description 基于 createRelation 生成关联的三个组件：选择器、只读表单、子表嵌套
 */
const { createSelect, createForm, createTable } = createRelation({
  /** 标题 */
  title: "第三方认证",
  /** 组件名称（按钮权限标识，供其他模块复用本模块配置） */
  componentName,
  /** 本模块 CRUD 配置生成器 */
  createCrudOptions,
  /** 本模块接口 */
  api,
  fkField: "oauth",
  dictConfig: {
    api,
    dictLabel: "name",
    queryFields: ["id", "name"]
  },
  searchConfig: {
    field: "oauth",
    lookup: "in"
  },
  columnCellRenderConfig: {
    componentName,
    createCrudOptions,
    fkField: "oauth",
    columnLabel: "oauth_name",
    crudOptionsOverride: {
      rowHandle: {
        width: 150,
        buttons: {
          view: { show: false },
          remove: { show: false },
          history: { show: false }
        }
      }
    }
  }
});

/**
 * 第三方认证 选择器
 * @description 默认在表单（form）作为父级字段选择器显示。列表（column）不显示、查询区（search）不显示
 */
export const oauth2Select = (
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
              remove: { show: false },
              history: { show: false }
            }
          }
        }
      }
    }
  };
  return createSelect(merge(defaultOptions, options));
};

/**
 * 第三方认证 只读表单
 * @description 默认在表单（form）作为只读表单显示，列表（column）显示，查询区（search）显示
 */
export const oauth2Form = (
  options?: ColumnCompositionProps
): ColumnCompositionProps => {
  const defaultOptions: ColumnCompositionProps = {};
  return createForm(merge(defaultOptions, options));
};

/**
 * 第三方认证 子表嵌套
 * @description 默认在表单（form）作为子表 tab 显示。列表（column）不显示，查询区（search）不显示
 */
export const oauth2Table = (
  options?: ColumnCompositionProps
): ColumnCompositionProps => {
  const defaultOptions: ColumnCompositionProps = {};
  return createTable(merge(defaultOptions, options));
};
