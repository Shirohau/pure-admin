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
import { historyTable } from "@/components/ReHistory";

import { createCrudPerms } from "@/utils/crud/createCrudPerms";
import { AuditField } from "@/plugins/fast-crud";

import dayjs from "dayjs";
import { createRowContextmenu } from "@/utils/crud/createRowContextmenu";

/** 筛选辅助工具（统一管理 filterForm + applyFilter + clearFilter + injectFilterToQuery）*/
import { useFilter } from "@/components/ReFilter/src/useFilter";
import { createFormAfterSubmit } from "@/utils/crud/createFormAfterSubmit";
import { createFormWrapper } from "@/utils/crud/createFormWrapper";
import { publisherForm, publisherSelect } from "../publisher/crud";
import { authorSelect, authorTable } from "../author/crud";
import { createRelation } from "@/utils/crud/createRelation";
import {
  createSummaryMethod,
  type SummaryGroup
} from "@/utils/crud/createSummaryMethod";
import type { DialogAsideTableOptions } from "@/components/ReAsideTable";
const { merge } = useMerge();
// 定义组件名称
export const componentName = "BookView";

/**
 * 表尾分类汇总分组：按出版社归组，每个出版社一行（分页场景仅汇总当前页数据）
 * @param data - 当前表格数据
 * @returns 分组合计行数组（label 为出版社名称，rows 为该出版社的数据行）
 */
function buildPublisherGroups(data: any[]): SummaryGroup[] {
  const groups = new Map<unknown, { label: string; rows: any[] }>();
  for (const row of data) {
    // 未关联出版社的行归入同一组
    const key = row.publisher ?? "unlinked";
    let group = groups.get(key);
    if (!group) {
      group = { label: row.publisher_name || "未关联出版社", rows: [] };
      groups.set(key, group);
    }
    group.rows.push(row);
  }
  return Array.from(groups.values());
}

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

  const groupTab = ref("base");

  /** 筛选 */
  const { createFilterHeader, FilterTags, clearAllFilters } = useFilter({
    crudExpose
  });

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

  // 表格右键事件
  const onRowContextmenu = createRowContextmenu(crudExpose);

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
        onRowContextmenu,
        // 表尾合计：按出版社分类汇总（每个出版社一行），每列可配计算方式与格式；
        // 分页场景仅汇总当前页数据（全量分类汇总需后端 get_summary 下发）
        summaryMethod: createSummaryMethod({
          sumColumns: {
            pages: { aggregate: "sum", format: { type: "integer" } },
            price: { aggregate: "avg", format: { type: "decimal" } }
          },
          buildGroups: buildPublisherGroups,
          firstCellSpan: 2
        }),
        showSummary: true
      },
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
        fixed: "right",
        align: "center",
        width: 180,
        buttons: {
          view: { show: hasPerms.view },
          edit: { show: hasPerms.edit },
          remove: { show: hasPerms.remove }
        }
      },
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
                "publisher",
                "author",
                "name",
                "isbn",
                "publication_time",
                "price",
                "pages",
                "description"
              ]
            },

            publisherForm: {
              label: "出版社详情",
              lazy: true,
              columns: ["publisherForm"]
            },
            authorTable: {
              label: "作者子表",
              lazy: true,
              columns: ["authorTable"]
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
          title: "书名",
          type: "text",
          column: {
            columnSlots: {
              header: createFilterHeader({
                type: "text",
                columnLabel: "书名",
                fieldName: "name"
              })
            }
          }
        },
        // 出版社 只读表单
        publisherForm: publisherForm({
          column: {
            minWidth: 100,
            columnSlots: {
              header: createFilterHeader({
                type: "text",
                columnLabel: "出版社",
                tooltip: "点击可查看详情",
                fieldName: "publisher__name"
              })
            }
          },
          columnCellRenderConfig: {
            fkField: "book",
            crudOptionsOverride: {
              actionbar: { show: true }
            }
          }
        }),
        // 出版社 选择器
        publisher: publisherSelect({
          selectType: "dialog",
          form: {
            helper: {
              position: "label",
              tooltip: {
                placement: "top-start"
              },
              text: "采用dialog弹窗选择"
            },
            component: {
              crudOptionsOverride: {
                columns: {
                  $checked: {
                    column: {
                      show: false
                    }
                  }
                }
              }
            }
          }
        }),
        // 作者 选择器（re-table-select 多选，列配置自动从作者模块列表提取）
        author: authorSelect({
          selectType: "select",
          form: {
            helper: {
              position: "label",
              tooltip: {
                placement: "top-start"
              },
              render: () => (
                <div style={{ color: "red" }}>采用select下拉选择</div>
              )
            },
            component: {
              multiple: true,
              crudOptionsOverride: {
                columns: {
                  $checked: {
                    column: {
                      show: true
                    }
                  },
                  gender: {
                    column: {
                      show: false
                    }
                  }
                }
              }
            }
          }
        }),
        // 作者 子表
        authorTable: authorTable({
          search: { show: true },
          form: {
            component: {
              crudOptionsOverride: {
                search: {
                  initialForm: compute(({ form }) => {
                    return { book__exact: form?.id };
                  })
                },
                form: {
                  initialForm: compute(({ form }) => {
                    return { book: [form?.id] };
                  })
                },
                columns: {
                  book: {
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
            columnSetShow: true,
            width: 120,
            columnSlots: {
              header: createFilterHeader({
                type: "text",
                columnLabel: "作者",
                tooltip: "点击可查看详情",
                fieldName: "author__name"
              })
            }
          },
          columnCellRenderConfig: {
            fkField: "book"
          }
        }),
        isbn: {
          title: "ISBN",
          type: "text",
          column: {
            minWidth: 150,
            showOverflowTooltip: true,
            columnSlots: {
              header: createFilterHeader({
                type: "text",
                columnLabel: "ISBN",
                fieldName: "isbn"
              })
            }
          }
        },
        publication_time: {
          title: "出版日期",
          type: "datetime",
          form: {
            component: {
              //输入值格式
              valueFormat: "YYYY-MM-DD HH:mm:ss"
            },
            valueResolve({ form }) {
              //value解析，就是把组件的值转化为后台所需要的值
              //在form表单点击保存按钮后，提交到后台之前执行转化
              // 所有涉及到日期时间的字段，都需要考虑时区
              if (form.publication_time) {
                form.publication_time = dayjs(form.publication_time).tz();
              }
              //  ↑↑↑↑↑ 注意这里是form，不是row
            }
          },
          column: {
            columnSlots: {
              header: createFilterHeader({
                type: "datetime",
                useTimezone: true,
                columnLabel: "出版日期",
                fieldName: "publication_time"
              })
            }
          }
        },
        price: {
          title: "价格",
          type: "number",
          valueBuilder({ row }) {
            //value构建，就是把后台传过来的值转化为前端组件所需要的值
            //在pageRequest之后执行转化，然后将转化后的数据放到table里面显示
            row.price = Number(row.price);
            //  ↑↑↑↑↑ 注意这里是row，不是form
          },
          column: {
            columnSlots: {
              header: createFilterHeader({
                type: "number",
                columnLabel: "价格",
                fieldName: "price"
              })
            }
          }
        },
        pages: {
          title: "页数",
          type: "number",
          column: {
            columnSlots: {
              header: createFilterHeader({
                type: "number",
                columnLabel: "页数",
                fieldName: "pages"
              })
            }
          }
        },
        description: {
          title: "内容简介",
          type: "textarea",
          column: {
            minWidth: 150,
            showOverflowTooltip: true,
            columnSlots: {
              header: createFilterHeader({
                type: "text",
                columnLabel: "内容简介",
                fieldName: "description"
              })
            }
          }
        },

        // 添加审计字段
        ...AuditField(
          {
            creator_name: {
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
 * 图书 关联组件工厂
 * @description 基于 createRelation 生成关联的组件：选择器、只读表单、子表嵌套、子表弹窗
 */
const { createSelect, createForm, createTable, createDialogTable } =
  createRelation({
    title: "图书",
    componentName,
    createCrudOptions,
    api,
    fkField: "book",
    dictConfig: {
      api,
      dictLabel: "name",
      queryFields: ["id", "name"]
    },
    searchConfig: {
      field: "book",
      lookup: "in"
    },
    columnCellRenderConfig: {
      componentName,
      createCrudOptions,
      fkField: "book", // 在具体使用的页面，需要重新配置
      columnLabel: "book_name"
    }
  });

/**
 * 图书 选择器
 * @description 默认在表单（form）作为父级字段选择器显示。列表（column）不显示、查询区（search）不显示
 */
export const bookSelect = (
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
 * 图书 只读表单
 * @description 默认在表单（form）作为只读表单显示，列表（column）显示，查询区（search）显示
 */
export const bookForm = (
  options?: ColumnCompositionProps
): ColumnCompositionProps => {
  const defaultOptions: ColumnCompositionProps = {};
  return createForm(merge(defaultOptions, options));
};

/**
 * 图书 子表嵌套
 * @description 默认在表单（form）作为子表 tab 显示。列表（column）不显示，查询区（search）不显示
 */
export const bookTable = (
  options?: ColumnCompositionProps
): ColumnCompositionProps => {
  const defaultOptions: ColumnCompositionProps = {};
  return createTable(merge(defaultOptions, options));
};

/**
 * 图书 子表弹窗
 * @description 任意位置（按钮 click 等）以点击形式打开子表弹窗
 */
export const bookDialogTable = (options: DialogAsideTableOptions): void => {
  const defaultOptions: DialogAsideTableOptions = {};
  return createDialogTable(merge(defaultOptions, options));
};
