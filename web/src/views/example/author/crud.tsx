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
import { api, apiPrefix } from "./api";
import { ref } from "vue";
import { ElMessageBox } from "element-plus";
import { openExportDialog } from "@/components/ReExport";
import { openImportDialog } from "@/components/ReImport";
import { historyTable, openHistoryDialog } from "@/components/ReHistory";

import { createCrudPerms } from "@/utils/crud/createCrudPerms";

import { createRowContextmenu } from "@/utils/crud/createRowContextmenu";

import { api as bookApi } from "../book/api";
import { bookDialogTable, bookSelect, bookTable } from "../book/crud";

/** 筛选辅助工具（统一管理 filterForm + applyFilter + clearFilter + injectFilterToQuery）*/
import { useFilter } from "@/components/ReFilter/src/useFilter";
import { getDictData } from "@/views/system/dictionary/api";
import { createFormAfterSubmit } from "@/utils/crud/createFormAfterSubmit";
import { createFormWrapper } from "@/utils/crud/createFormWrapper";
import { createRelation } from "@/utils/crud/createRelation";
import { getAreaData } from "@/views/system/area/api";
import { createSummaryMethod } from "@/utils/crud/createSummaryMethod";
import { publisherDialogTable } from "../publisher/crud";
const { merge } = useMerge();
// 定义组件名称
export const componentName = "AuthorView";
/**
 * 定义一个CrudOptions生成器方法
 */
export default function createCrudOptions({
  crudExpose,
  context
}: CreateCrudOptionsProps): CreateCrudOptionsRet {
  /** 是否处于嵌套模式   */
  const isNested = Boolean(context?.isNested);
  console.log("是否处于子表嵌套模式", isNested);

  /** 按钮权限（懒加载 + 响应式，权限加载完成后自动更新） */
  const hasPerms = createCrudPerms(componentName, {
    /** 打印权限 */
    print: "Print",
    /** 历史记录恢复权限 */
    historyRecover: "HistoryRecover"
  });

  /** 筛选 */
  const { createFilterHeader, FilterTags, clearAllFilters } = useFilter({
    crudExpose
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

  // 批量删除（单选/多选通用：按选中行 id 批量删除）
  const handleBatchDelete = () => {
    const ids = selectedData.value.map(item => item.id);
    ElMessageBox.confirm(
      `确定要批量删除这${selectedData.value.length}条记录吗`,
      "删除提示"
    )
      .then(async () => {
        await api.BatchDelete(ids);
        await crudExpose.doRefresh();
        selectedData.value = [];
      })
      .catch(() => {});
  };

  // 表格右键事件
  const onRowContextmenu = createRowContextmenu(crudExpose);

  /** 性别字典（提取为变量，方便在 columnSlots 中复用 data，避免重复请求）*/
  const genderDict = getDictData("gender");
  const educationDict = getDictData("education");
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
        highlightCurrentRow: true,
        onSelectionChange,
        onRowContextmenu,
        // 表尾合计：每列可配计算方式与格式；
        summaryMethod: createSummaryMethod({
          sumText: "平均年龄",
          sumColumns: {
            age: { aggregate: "avg", format: { type: "integer" } }
          },
          firstCellSpan: 2
        }),
        showSummary: true
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
      // 左侧动作条配置
      actionbar: {
        buttons: {
          add: {
            show: hasPerms.add
          },
          publisherDialogTable: {
            text: "出版社弹窗 单选",
            click: () => {
              publisherDialogTable({
                title: "出版社 子表弹窗 单选",
                width: "60%",
                multiple: false,
                props: {
                  crudOptionsOverride: {
                    search: { show: true }
                  }
                },
                beforeSure: (done, { selectedData }) => {
                  console.log(selectedData);
                  done();
                }
              });
            }
          },
          bookDialogTable: {
            text: "图书弹窗 多选",
            click: () => {
              bookDialogTable({
                title: "图书 子表弹窗 多选",
                width: "60%",
                props: {
                  showBatchDelete: false
                },
                beforeSure: (done, { selectedData }) => {
                  console.log(selectedData);
                  done();
                }
              });
            }
          }
        }
      },
      // 右侧工具条配置
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
        fixed: "right",
        align: "center",
        width: 330,
        buttons: {
          view: {
            order: 1,
            text: "查看",
            show: hasPerms.view
          },
          edit: {
            order: 2,
            text: "编辑",
            show: hasPerms.edit
          },
          remove: {
            order: 3,
            text: "删除",
            show: hasPerms.remove
          },
          history: {
            order: 4,
            text: "历史记录",
            click: ({ row }) => {
              openHistoryDialog({
                apiPrefix: `${apiPrefix}${row.id}/`,
                restartAuth: hasPerms.historyRecover.value,
                height: "calc(100vh - 300px)"
              });
            }
          },
          print: {
            order: 5,
            text: "打印",
            show: hasPerms.print,
            click: async ({ row }) => {
              const [{ data }, { print }] = await Promise.all([
                bookApi.GetList({ author: row?.id, limit: 1000 }),
                import("./print")
              ]);
              row["books"] = data;
              print(row);
            }
          }
        }
      },
      // 表单基本配置
      form: {
        // 保存成功后留在抽屉继续编辑：新增转编辑，编辑保持编辑
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
                "gender",
                "age",
                "birth_date",
                "education",
                "area",
                "address",
                "nationality",
                "biography",
                "email",
                "date_time",
                "book"
              ]
            },
            bookTable: {
              label: "图书子表",
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
        name: {
          title: "作者姓名",
          type: "text",
          column: {
            minWidth: 100,
            columnSlots: {
              header: createFilterHeader({
                type: "text",
                columnLabel: "姓名",
                tooltip: "文本筛选",
                fieldName: "name"
              })
            }
          }
        },
        // 图书 子表
        bookTable: bookTable({
          search: { show: true },
          form: {
            component: {
              crudOptionsOverride: {
                search: {
                  initialForm: compute(({ form }) => {
                    return { author__exact: form?.id };
                  })
                },
                form: {
                  initialForm: compute(({ form }) => {
                    return { author: [form?.id] };
                  })
                },
                columns: {
                  author: {
                    form: {
                      component: {
                        disabled: true
                      }
                    }
                  }
                }
              }
            }
          },
          column: {
            show: true,
            minWidth: 150,
            showOverflowTooltip: true,
            columnSlots: {
              header: createFilterHeader({
                type: "text",
                columnLabel: "关联图书",
                tooltip: "关联表快捷筛选，也可在顶部使用高级筛选",
                fieldName: "book__name"
              })
            }
          },
          columnCellRenderConfig: {
            fkField: "author"
          }
        }),
        // 图书 选择器(开启多选)
        book: bookSelect({
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
          }
        }),
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
                tooltip: "选择筛选",
                selectList: () => genderDict.data ?? []
              })
            }
          }
        },
        age: {
          title: "年龄",
          type: "number",
          column: {
            columnSlots: {
              header: createFilterHeader({
                type: "number",
                columnLabel: "年龄",
                tooltip: "数字筛选",
                fieldName: "age"
              })
            }
          }
        },
        birth_date: {
          title: "出生日期",
          type: "date",
          form: {
            component: {
              //输入输出值格式化
              valueFormat: "YYYY-MM-DD"
            }
          },
          column: {
            columnSlots: {
              header: createFilterHeader({
                type: "date",
                columnLabel: "出生日期",
                tooltip: "日期筛选",
                fieldName: "birth_date"
              })
            }
          }
        },
        education: {
          title: "学历",
          type: "dict-select",
          dict: educationDict,
          column: {
            minWidth: 100,
            columnSlots: {
              header: createFilterHeader({
                type: "select",
                columnLabel: "学历",
                tooltip: "选择筛选",
                fieldName: "education",
                selectList: () => educationDict.data ?? []
              })
            }
          }
        },
        area: {
          title: "省市县",
          type: "dict-cascader",
          dict: areaData,
          column: {
            minWidth: 150,
            showOverflowTooltip: true,
            columnSlots: {
              header: createFilterHeader({
                type: "cascader",
                columnLabel: "省市县",
                tooltip: "级联筛选，需要后端单独写筛选方法",
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
            minWidth: 150,
            showOverflowTooltip: true,
            columnSlots: {
              header: createFilterHeader({
                type: "text",
                columnLabel: "详细地址",
                tooltip: "文本筛选",
                fieldName: "address"
              })
            }
          }
        },
        biography: {
          title: "简介",
          type: "textarea",
          column: {
            showOverflowTooltip: true,
            columnSlots: {
              header: createFilterHeader({
                type: "text",
                columnLabel: "简介",
                tooltip: "文本筛选",
                fieldName: "biography"
              })
            }
          }
        },
        creator_name: {
          title: "创建者",
          type: "text",
          form: { show: false },
          column: {
            show: true,
            showOverflowTooltip: true,
            width: 100,
            columnSlots: {
              header: createFilterHeader!({
                type: "text",
                columnLabel: "创建者",
                tooltip: "跨表筛选",
                fieldName: "creator__name"
              })
            }
          }
        },
        create_dt: {
          title: "创建时间",
          type: "text",
          form: { show: false },
          column: {
            show: true,
            width: 150,
            columnSlots: {
              header: createFilterHeader!({
                type: "datetime",
                columnLabel: "创建时间",
                tooltip: "日期时间筛选",
                fieldName: "create_dt"
              })
            }
          }
        },
        updater_name: {
          title: "更新者",
          type: "text",
          form: { show: false },
          column: {
            show: true,
            showOverflowTooltip: true,
            width: 100,
            columnSlots: {
              header: createFilterHeader!({
                type: "text",
                columnLabel: "更新者",
                tooltip: "跨表筛选",
                fieldName: "updater__name"
              })
            }
          }
        },
        update_dt: {
          title: "修改时间",
          type: "text",
          form: { show: false },
          column: {
            show: true,
            showOverflowTooltip: true,
            width: 150,
            columnSlots: {
              header: createFilterHeader!({
                type: "datetime",
                columnLabel: "更新时间",
                tooltip: "日期时间筛选",
                fieldName: "update_dt"
              })
            }
          }
        },

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
 * 作者 关联组件工厂
 * @description 基于 createRelation 生成关联的三个组件：选择器、只读表单、子表嵌套
 */
const { createSelect, createForm, createTable } = createRelation({
  title: "作者",
  componentName,
  createCrudOptions,
  api,
  fkField: "author",
  dictConfig: {
    api,
    dictLabel: "name",
    queryFields: ["id", "name"]
  },
  searchConfig: {
    field: "author",
    lookup: "in"
  },
  columnCellRenderConfig: {
    componentName,
    createCrudOptions,
    fkField: "author",
    columnLabel: "author_name",
    crudOptionsOverride: {
      rowHandle: {
        buttons: {
          print: { show: false },
          history: { show: false }
        }
      }
    }
  }
});

/**
 * 作者 选择器
 * @description 默认在表单（form）作为父级字段选择器显示。列表（column）不显示、查询区（search）不显示。
 */
export const authorSelect = (
  options?: ColumnCompositionProps
): ColumnCompositionProps => {
  const defaultOptions: ColumnCompositionProps = {
    form: {
      component: {
        crudOptionsOverride: {
          toolbar: {
            show: false
          }
        },
        // 选中后回写上级外键
        on: {
          selectedChange({ $event: selectList, form }) {
            if (selectList) {
              const selectRow = selectList[0];
              console.log(selectRow, form);
              // form.sales_customer = selectRow.sales_customer;
              // form.sales_contract = selectRow.sales_contract;
              // form.sales_project = selectRow.sales_project;
              // form.sales_job = selectRow.sales_job;
              // form.job_quotation = selectRow.job_quotation;
            }
          }
        }
      }
    }
  };
  return createSelect(merge(defaultOptions, options));
};

/**
 * 作者 只读表单
 * @description 默认在表单（form）作为只读表单显示，列表（column）显示，查询区（search）显示
 */
export const authorForm = (
  options?: ColumnCompositionProps
): ColumnCompositionProps => {
  const defaultOptions: ColumnCompositionProps = {};
  return createForm(merge(defaultOptions, options));
};

/**
 * 作者 子表嵌套
 * @description 默认在表单（form）作为子表 tab 显示。列表（column）不显示，查询区（search）不显示
 */
export const authorTable = (
  options?: ColumnCompositionProps
): ColumnCompositionProps => {
  const defaultOptions: ColumnCompositionProps = {};
  return createTable(merge(defaultOptions, options));
};
