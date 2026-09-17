import {
  compute,
  useMerge,
  type AddReq,
  type DelReq,
  type EditReq,
  type UserPageQuery,
  type ColumnCompositionProps,
  type CreateCrudOptionsProps,
  type CreateCrudOptionsRet,
  type ValueBuilderContext,
  type FormScopeContext
} from "@fast-crud/fast-crud";
import { api } from "./api";
import { ref, shallowRef } from "vue";
import { ElMessageBox } from "element-plus";
import { useButtonPerms } from "@/utils/auth";

import { periodicTaskTable } from "@/views/system/celery/periodic_task/crud";
import {
  CrontabDay,
  CrontabHour,
  CrontabMin,
  CrontabMonth,
  CrontabWeek
} from "./component";
import cronstrue from "cronstrue";
import "cronstrue/locales/zh_CN";
import { createRelation } from "@/utils/crud/createRelation";
const { merge } = useMerge();

// 定义组件名称
export const componentName = "CrontabScheduleView";

/**
 * 定义一个CrudOptions生成器方法
 */
export default function createCrudOptions({
  crudExpose
}: CreateCrudOptionsProps): CreateCrudOptionsRet {
  /** 权限控制 */
  const hasPerms = {
    /** 批量删除权限 */
    batchDestroy: useButtonPerms(`${componentName}:BatchDestroy`)
  };

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

      // 工具条配置
      toolbar: {
        buttons: {
          export: { show: false },
          search: { show: false },
          compact: { show: false },
          columns: { show: false }
        }
      },
      search: {
        show: false
      },
      // 操作列配置
      rowHandle: {
        fixed: "right",
        align: "center"
      },
      // 表单基本配置
      form: {
        col: { span: 24 },
        labelWidth: "110px",
        wrapper: {
          is: "el-drawer",
          size: "80%"
        },
        group: {
          groupType: "tabs", //collapse  tabs
          accordion: false,
          groups: {
            minute: {
              label: "分钟",
              columns: ["minute"]
            },
            hour: {
              label: "小时",
              columns: ["hour"]
            },
            day_of_month: {
              label: "日期",
              columns: ["day_of_month"]
            },
            month_of_year: {
              label: "月份",
              columns: ["month_of_year"]
            },
            day_of_week: {
              label: "星期",
              columns: ["day_of_week"]
            },
            periodic_task: {
              label: "任务",
              columns: ["periodic_task"]
            }
          }
        },
        watch(context: FormScopeContext) {
          const { form } = context;
          form.expression = `${form.minute} ${form.hour} ${form.day_of_month} ${form.month_of_year} ${form.day_of_week}`;
          form.described = cronstrue.toString(form.expression, {
            locale: "zh_CN"
          });
        }
      },
      // 字段复合配置
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
        minute: {
          title: "分钟",
          type: "text",
          form: {
            value: "*",
            labelWidth: "0px",
            component: {
              name: shallowRef(CrontabMin),
              vModel: "modelValue",
              defaultValue: compute(({ row }) => {
                return row ? row.minute : "*";
              })
            }
          }
        },
        hour: {
          title: "小时",
          type: "text",
          form: {
            value: "*",
            labelWidth: "0px",
            component: {
              name: shallowRef(CrontabHour),
              vModel: "modelValue",
              defaultValue: compute(({ row }) => {
                return row ? row.hour : "*";
              })
            }
          }
        },
        day_of_month: {
          title: "日期",
          type: "text",
          form: {
            value: "*",
            labelWidth: "0px",
            component: {
              name: shallowRef(CrontabDay),
              vModel: "modelValue",
              defaultValue: compute(({ row }) => {
                return row ? row.day_of_month : "*";
              })
            }
          }
        },
        month_of_year: {
          title: "月份",
          type: "text",
          form: {
            value: "*",
            labelWidth: "0px",
            component: {
              name: shallowRef(CrontabMonth),
              vModel: "modelValue",
              defaultValue: compute(({ row }) => {
                return row ? row.month_of_year : "*";
              })
            }
          }
        },
        day_of_week: {
          title: "星期",
          type: "text",
          form: {
            value: "*",
            labelWidth: "0px",
            component: {
              name: shallowRef(CrontabWeek),
              vModel: "modelValue",
              defaultValue: compute(({ row }) => {
                return row ? row.day_of_week : "*";
              })
            }
          }
        },
        timezone: {
          title: "时区",
          type: "text",
          form: { show: false }
        },
        described: {
          title: "表达式描述",
          type: "textarea",
          form: {
            show: false
          },
          column: {
            align: "left", //对齐方式
            minWidth: 200, //最小列宽
            showOverflowTooltip: true
          },
          valueBuilder(context: ValueBuilderContext) {
            //value构建，就是把后台传过来的值转化为前端组件所需要的值
            const { row } = context;
            row.expression = `${row.minute} ${row.hour} ${row.day_of_month} ${row.month_of_year} ${row.day_of_week}`;
            row.described = cronstrue.toString(row.expression, {
              locale: "zh_CN"
            });
          }
        },
        periodic_task: periodicTaskTable({
          form: {
            component: {
              crudOptionsOverride: {
                table: {
                  show: true
                },
                search: {
                  initialForm: compute(({ form }) => {
                    return { crontab__exact: form?.id };
                  })
                },
                actionbar: {
                  buttons: {
                    add: {
                      show: true
                    }
                  }
                },
                toolbar: {
                  show: true
                },
                columns: {
                  schedule: {
                    form: {
                      value: "crontab",
                      component: {
                        disabled: true
                      }
                    }
                  },
                  crontab: {
                    form: {
                      value: compute(({ form }) => form.id),
                      component: {
                        disabled: true
                      }
                    }
                  }
                }
              }
            }
          }
        })
      }
    }
  };
}

/**
 * 周期触发器 关联组件工厂
 * @description 基于 createRelation 生成关联的三个组件：选择器、只读表单、子表嵌套
 */
const { createSelect, createForm, createTable } = createRelation({
  /** 标题 */
  title: "周期触发器",
  /** 组件名称（按钮权限标识，供其他模块复用本模块配置） */
  componentName,
  /** 本模块 CRUD 配置生成器 */
  createCrudOptions,
  /** 本模块接口 */
  api,
  fkField: "crontab",
  dictConfig: {
    api,
    dictLabel: "name",
    queryFields: ["id", "name"]
  },
  searchConfig: {
    field: "crontab",
    lookup: "in"
  },
  columnCellRenderConfig: {
    componentName,
    createCrudOptions,
    fkField: "crontab",
    columnLabel: "crontab_name",
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
 * 周期触发器 选择器
 * @description 默认在表单（form）作为父级字段选择器显示。列表（column）不显示、查询区（search）不显示
 */
export const crontabSelect = (
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
 * 周期触发器 只读表单
 * @description 默认在表单（form）作为只读表单显示，列表（column）显示，查询区（search）显示
 */
export const crontabForm = (
  options?: ColumnCompositionProps
): ColumnCompositionProps => {
  const defaultOptions: ColumnCompositionProps = {};
  return createForm(merge(defaultOptions, options));
};

/**
 * 周期触发器 子表嵌套
 * @description 默认在表单（form）作为子表 tab 显示。列表（column）不显示，查询区（search）不显示
 */
export const crontabTable = (
  options?: ColumnCompositionProps
): ColumnCompositionProps => {
  const defaultOptions: ColumnCompositionProps = {};
  return createTable(merge(defaultOptions, options));
};
