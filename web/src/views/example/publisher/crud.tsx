import {
  compute,
  useMerge,
  type AddReq,
  type DelReq,
  type EditReq,
  type UserPageQuery,
  type CreateCrudOptionsRet,
  type ColumnCompositionProps,
  type CreateCrudOptionsProps
} from "@fast-crud/fast-crud";
import { api, apiPrefix } from "./api";
import { ref } from "vue";
import { ElMessageBox } from "element-plus";
import { openExportDialog } from "@/components/ReExport";
import { openImportDialog } from "@/components/ReImport";
import { historyTable } from "@/components/ReHistory";
import { AuditField } from "@/plugins/fast-crud";
import { bookSelect, bookTable } from "../book/crud";
import { getAreaData } from "@/views/system/area/api";

/** 筛选辅助工具（统一管理 filterForm + applyFilter + clearFilter + injectFilterToQuery）*/
import { useFilter } from "@/components/ReFilter/src/useFilter";
import { createRowContextmenu } from "@/utils/crud/createRowContextmenu";
import { createFormAfterSubmit } from "@/utils/crud/createFormAfterSubmit";
import { createFormWrapper } from "@/utils/crud/createFormWrapper";
import { createCrudPerms } from "@/utils/crud/createCrudPerms";
import { createRelation } from "@/utils/crud/createRelation";
import type { DialogAsideTableOptions } from "@/components/ReAsideTable/types";

const { merge } = useMerge();

// 定义组件名称
export const componentName = "PublisherView";

/**
 * 定义一个CrudOptions生成器方法
 */
export default function createCrudOptions({
  crudExpose
}: CreateCrudOptionsProps): CreateCrudOptionsRet {
  /** 按钮权限（懒加载 + 响应式，权限加载完成后自动更新） */
  const hasPerms = createCrudPerms(componentName, {
    /** 历史记录恢复权限 */
    historyRecover: "HistoryRecover"
  });

  /** 筛选 */
  const { createFilterHeader, FilterTags, clearAllFilters } = useFilter({
    crudExpose,
    mode: "local"
  });

  /** 分组标签 */
  const groupTab = ref("base");

  /** 列表查询 */
  const pageRequest = async (query: UserPageQuery) => {
    return await api.GetList(query);
  };

  /** 新增 */
  const addRequest = async ({ form }: AddReq) => {
    return await api.CreateObj(form);
  };

  /** 修改 */
  const editRequest = async ({ form }: EditReq) => {
    return await api.UpdateObj(form.id, form);
  };

  /** 删除 */
  const delRequest = async ({ row }: DelReq) => {
    return await api.DeleteObj(row.id);
  };

  // 选中的数据（统一数组口径：单选 0~1 行、多选 0~N 行，消费端保持一致）
  const selectedData = ref<any[]>([]);

  // 多选：复选框列勾选变化 → 整组写入（ReAsideTable 多选也读取该字段）
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

  // 表格右键事件（自动读取 rowHandle 按钮配置）
  const onRowContextmenu = createRowContextmenu(crudExpose);

  /** 区域数据 */
  const areaData = getAreaData(3, { value: "name" });

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
        onSelectionChange,
        onRowContextmenu
      },
      // 查询框配置
      search: {
        show: true,
        buttons: {
          reset: {
            click: context => {
              clearAllFilters();
              context.doReset();
            }
          }
        }
      },
      // 动作条配置
      actionbar: {
        buttons: {
          add: {
            show: hasPerms.add
          }
        }
      },
      // 工具栏配置
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
      // 行操作配置
      rowHandle: {
        fixed: "right",
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
      // 表单配置
      form: {
        // 保存成功后留在抽屉继续编辑：新增转编辑（回写后端返回数据），编辑保持编辑
        afterSubmit: createFormAfterSubmit(crudExpose),
        // 全屏抽屉表单：底部操作按钮仅在 "base" 分组显示，打开时重置到 "base"
        wrapper: createFormWrapper({ groupTab }),
        group: {
          groupType: "tabs",
          onTabChange: (pane: string) => {
            groupTab.value = pane;
          },
          modelValue: "base",
          groups: {
            base: {
              label: "基本信息",
              lazy: true,
              columns: [
                "name",
                "area",
                "area_str",
                "address",
                "phone",
                "email",
                "website",
                "book"
              ]
            },
            bookTable: {
              label: "图书",
              lazy: true,
              columns: ["bookTable"]
            },
            history: {
              label: "历史记录",
              lazy: true,
              columns: ["history"]
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
          title: "出版社名称",
          type: "text",
          column: {
            width: 120,
            showOverflowTooltip: true,
            columnSlots: {
              header: createFilterHeader({
                type: "text",
                columnLabel: "出版社名称",
                fieldName: "name"
              })
            }
          }
        },
        // 图书 选择器
        book: bookSelect({
          search: { show: true },
          form: {
            col: { span: 24 },
            rules: [],
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
            width: 200,
            showOverflowTooltip: true,
            show: true,
            columnSlots: {
              header: createFilterHeader({
                type: "text",
                columnLabel: "关联图书",
                tooltip: "点击可查看详情",
                fieldName: "book__name"
              })
            }
          },
          columnCellRenderConfig: {
            fkField: "publisher",
            crudOptionsOverride: {
              actionbar: { show: true },
              columns: {
                publisher: {
                  form: {
                    component: {
                      disabled: true
                    }
                  }
                }
              }
            }
          }
        }),
        area: {
          title: "省市县",
          type: "dict-cascader",
          dict: areaData,
          column: {
            width: 200,
            showOverflowTooltip: true,
            columnSlots: {
              header: createFilterHeader({
                type: "cascader",
                columnLabel: "省市县",
                fieldName: "area",
                // 可按需覆盖 el-cascader 的 props（字段映射、checkStrictly 等）
                cascaderProps: {
                  value: "name",
                  label: "name",
                  children: "children",
                  emitPath: true,
                  checkStrictly: true
                },
                selectList: () => areaData.data as any[]
              })
            }
          },
          valueResolve({ form }) {
            //value解析，就是把组件的值转化为后台所需要的值
            [form.province, form.city, form.district] = form.area;
          },
          valueBuilder({ row }) {
            //value构建，就是把后台传过来的值转化为前端组件所需要的值
            row.area = [row.province, row.city, row.district];
          }
        },
        address: {
          title: "详细地址",
          type: "text",
          column: {
            width: 100,
            showOverflowTooltip: true,
            columnSlots: {
              header: createFilterHeader({
                type: "text",
                columnLabel: "详细地址",
                fieldName: "address"
              })
            }
          }
        },
        phone: {
          title: "联系电话",
          type: "text",
          column: {
            width: 120,
            showOverflowTooltip: true,
            columnSlots: {
              header: createFilterHeader({
                type: "text",
                columnLabel: "联系电话",
                fieldName: "phone"
              })
            }
          }
        },
        email: {
          title: "邮箱",
          type: "text",
          column: {
            width: 120,
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
        website: {
          title: "官网网址",
          type: "text",
          column: {
            width: 200,
            showOverflowTooltip: true,
            columnSlots: {
              header: createFilterHeader({
                type: "text",
                columnLabel: "官网网址",
                fieldName: "website"
              })
            }
          }
        },

        // 图书 子表
        bookTable: bookTable({
          form: {
            component: {
              crudOptionsOverride: {
                search: {
                  initialForm: compute(({ form }) => {
                    return { publisher__exact: form?.id };
                  })
                },
                form: {
                  initialForm: compute(({ form }) => {
                    return { publisher: form?.id };
                  })
                },
                columns: {
                  publisher: {
                    form: {
                      component: {
                        disabled: true
                      }
                    }
                  }
                }
              }
            }
          }
        }),
        // 添加审计字段
        ...AuditField(
          {
            creator_name: {
              column: { show: true }
            },
            create_dt: {
              column: { show: true }
            },
            dept_belong_name: {
              column: { show: true }
            }
          },
          crudExpose,
          createFilterHeader
        ),
        // 历史记录
        history: historyTable({
          formInline: compute(({ form }) => {
            return {
              apiPrefix: `${apiPrefix}${form?.id}/`,
              restartAuth: hasPerms.historyRecover
            };
          })
        })
      }
    }
  };
}

/**
 * 出版社 关联组件工厂
 * @description 基于 createRelation 生成关联的三个组件：选择器、只读表单、子表嵌套
 */
const { createSelect, createForm, createTable, createDialogTable } =
  createRelation({
    title: "出版社",
    componentName,
    createCrudOptions,
    api,
    fkField: "publisher",
    dictConfig: {
      api,
      dictLabel: "name",
      queryFields: ["id", "name"]
    },
    searchConfig: {
      field: "publisher",
      lookup: "in"
    },
    columnCellRenderConfig: {
      componentName,
      createCrudOptions,
      fkField: "publisher", // 在具体使用的页面，需要重新配置
      columnLabel: "publisher_name"
    }
  });

/**
 * 出版社 选择器
 * @description 默认在表单（form）作为父级字段选择器显示。列表（column）不显示、查询区（search）不显示
 */
export const publisherSelect = (
  options?: ColumnCompositionProps
): ColumnCompositionProps => {
  const defaultOptions: ColumnCompositionProps = {
    // 表单覆盖配置
    form: {
      component: {
        crudOptionsOverride: {
          rowHandle: {
            width: 100,
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
 * 出版社 只读表单
 * @description 默认在表单（form）作为只读表单显示，列表（column）显示，查询区（search）显示
 */
export const publisherForm = (
  options?: ColumnCompositionProps
): ColumnCompositionProps => {
  const defaultOptions: ColumnCompositionProps = {};
  return createForm(merge(defaultOptions, options));
};

/**
 * 出版社 子表嵌套
 * @description 默认在表单（form）作为子表 tab 显示。列表（column）不显示，查询区（search）不显示
 */
export const publisherTable = (
  options?: ColumnCompositionProps
): ColumnCompositionProps => {
  const defaultOptions: ColumnCompositionProps = {};
  return createTable(merge(defaultOptions, options));
};

/**
 * 出版社 子表弹窗
 * @description 任意位置（按钮 click 等）以点击形式打开子表弹窗
 */
export const publisherDialogTable = (
  options: DialogAsideTableOptions
): void => {
  const defaultOptions: DialogAsideTableOptions = {
    props: {
      crudOptionsOverride: {
        actionbar: { show: true },
        toolbar: { show: true },
        rowHandle: { show: true }
      }
    }
  };
  return createDialogTable(merge(defaultOptions, options));
};
