import {
  compute,
  dict,
  useMerge,
  type AddReq,
  type DelReq,
  type EditReq,
  type UserPageQuery,
  type ColumnCompositionProps,
  type CreateCrudOptionsProps,
  type CreateCrudOptionsRet,
  type ValueBuilderContext
} from "@fast-crud/fast-crud";
import { api, apiPrefix } from "./api";
import { ref } from "vue";
import { ElMessageBox } from "element-plus";
import { useButtonPerms } from "@/utils/auth";
import { clockedSelect } from "@/views/system/celery/schedule/clocked/crud";
import { intervalSelect } from "@/views/system/celery/schedule/interval/crud";
import { crontabSelect } from "@/views/system/celery/schedule/crontab/crud";
import { taskResultTable } from "../task_result/crud";
import dayjs from "dayjs";
import { createRelation } from "@/utils/crud/createRelation";

const { merge } = useMerge();

// 定义组件名称
export const componentName = "PeriodicTaskView";

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

  const groupTab = ref("base");

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
        show: false,
        rowKey: "id", //设置你的主键id， 默认rowKey=id
        onSelectionChange
      },
      // 动作条配置
      actionbar: {
        buttons: {
          add: {
            show: true
          }
        }
      },
      // 工具条配置
      toolbar: {
        buttons: {
          export: { show: false },
          compact: { show: false },
          columns: { show: false }
        }
      },
      // 操作列配置
      rowHandle: {
        fixed: "right",
        align: "center",
        buttons: {
          view: { show: true },
          edit: { show: false },
          remove: { show: false }
        }
      },
      // 表单基本配置
      form: {
        col: { span: 24 },
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
              label: "任务",
              show: true,
              columns: [
                "name",
                "task",
                "enabled",
                "description",
                "schedule",
                "clocked",
                "interval",
                "crontab",
                "start_time",
                "expires",
                "expire_seconds",
                "one_off",
                "last_run_at",
                "total_run_count",
                "date_changed"
              ]
            },
            arguments: {
              label: "参数",
              show: true,
              columns: ["args", "kwargs"]
            },
            execution: {
              label: "其他配置",
              columns: [
                "queue",
                "exchange",
                "routing_key",
                "priority",
                "headers"
              ]
            },
            task_result: {
              label: "执行记录",
              lazy: true,
              columns: ["task_result"]
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
        enabled: {
          title: "状态",
          type: "dict-switch",
          form: {
            show: false,
            value: false
          },
          column: {
            width: 80,
            fixed: "left", //固定列
            component: {
              name: "fs-dict-switch",
              activeText: "",
              inactiveText: "",
              style:
                "--el-switch-on-color: var(--el-color-primary); --el-switch-off-color: #dcdfe6",
              onChange: compute(({ row }) => {
                return () => {
                  // 构造一个 JS 对象
                  const kwargsObj = { periodic_task_id: row.id };
                  // 转为标准 JSON 字符串（双引号）
                  row.kwargs = JSON.stringify(kwargsObj);
                  api.UpdateObj(row.id, row);
                };
              })
            }
          },
          dict: dict({})
        },
        name: {
          title: "任务名称",
          type: "text",
          form: {
            col: { span: 8 },
            helper: "该任务的简短说明",
            rules: [{ required: true, message: "任务名称必填" }],
            component: {
              placeholder: "请输入任务名称"
            }
          },
          column: {
            minWidth: 120,
            fixed: "left" //固定列
          }
        },
        task: {
          title: "执行函数",
          type: "dict-select",
          dict: dict({
            url: apiPrefix + "job_list/",
            value: "value",
            label: "label"
          }),
          search: { show: true },
          form: {
            col: { span: 16 },
            rules: [{ required: true, message: "执行任务必填" }],
            component: {
              placeholder: "输入执行任务"
            }
          },
          column: {
            minWidth: 300,
            // sortable: 'custom',
            columnSetDisabled: true
          },
          valueBuilder(context) {
            const { row, key } = context;
            return row[key];
          }
        },
        description: {
          title: "描述",
          type: "textarea",
          form: {
            helper: "有关此任务的详细信息"
          }
        },
        schedule: {
          title: "触发器",
          type: "dict-select",
          dict: dict({
            data: [
              { label: "周期", value: "crontab" },
              { label: "间隔", value: "interval" },
              { label: "定时", value: "clocked" }
            ]
          }),
          form: {
            col: { span: 8 },
            rules: [{ required: true, message: "请选择触发器" }],
            value: "crontab",
            component: {
              clearable: false
            },
            valueChange: {
              immediate: true, //是否立即执行一次
              handle({ form }) {
                form.one_off = form.schedule === "clocked";
              }
            }
          },
          valueBuilder(context: ValueBuilderContext) {
            const { row } = context;
            if (row.clocked) {
              row.schedule = "clocked";
            } else if (row.interval) {
              row.schedule = "interval";
            } else if (row.crontab) {
              row.schedule = "crontab";
            }
          }
        },
        clocked: clockedSelect({
          column: { show: false },
          form: {
            col: { span: 16 },
            show: compute(({ form }) => form.schedule === "clocked") as any
          }
        }),

        interval: intervalSelect({
          column: { show: false },
          form: {
            col: { span: 16 },
            show: compute(({ form }) => form.schedule === "interval") as any
          }
        }),
        crontab: crontabSelect({
          column: { show: false },
          form: {
            col: { span: 16 },
            show: compute(({ form }) => form.schedule === "crontab") as any
          }
        }),
        start_time: {
          title: "开始时间",
          type: "datetime",
          form: {
            col: { span: 8 },
            helper: "触发器开始触发任务执行的时刻",
            component: {
              valueFormat: "YYYY-MM-DD HH:mm",
              format: "YYYY-MM-DD HH:mm"
            },
            valueResolve({ form }) {
              if (form.start_time) {
                form.start_time = dayjs(form.start_time).tz();
              }
            }
          }
        },
        expires: {
          title: "过期时刻",
          type: "datetime",
          form: {
            col: { span: 8 },
            helper: "触发器将在此时刻后不再触发任务执行",
            component: {
              valueFormat: "YYYY-MM-DD HH:mm",
              format: "YYYY-MM-DD HH:mm"
            },
            valueResolve({ form }) {
              if (form.expires) {
                form.expires = dayjs(form.expires).tz();
              }
              console.log(form.expires);
            }
          }
        },
        expire_seconds: {
          title: "过期时间间隔",
          type: "number",
          form: {
            col: { span: 8 },
            helper: "再过该秒后，不再触发任务执行"
          }
        },
        one_off: {
          title: "一次任务",
          type: "dict-switch",
          dict: dict({
            data: [
              {
                label: "是",
                value: true,
                color: "success",
                effect: "dark"
              },
              {
                label: "否",
                value: false,
                effect: "dark"
              }
            ]
          }),
          form: {
            helper: "如果为True，则计划将仅运行任务一次",
            component: {
              disabled: compute(({ form }) => {
                return form.schedule === "clocked";
              })
            }
          }
        },
        last_run_at: {
          title: "上次运行时刻",
          type: "datetime",
          form: {
            col: { span: 8 },
            component: {
              disabled: true,
              component: { valueFormat: "YYYY-MM-DD HH:mm:ss" }
            }
          }
        },
        total_run_count: {
          title: "总运行次数",
          type: "number",
          form: {
            col: { span: 8 },
            component: {
              disabled: true
            }
          }
        },
        date_changed: {
          title: "最后修改",
          type: "datetime",
          form: {
            col: { span: 8 },
            component: {
              disabled: true
            }
          }
        },
        args: {
          title: "位置参数",
          type: "textarea"
        },
        kwargs: {
          title: "关键字参数",
          type: "textarea",
          form: {
            component: {
              disabled: true
            }
          }
        },

        queue: {
          title: "队列覆盖",
          type: "text",
          form: {
            col: { span: 12 },
            helper: "在 CELERY_TASK_QUEUES 定义的队列。保留空以进行默认排队"
          }
        },
        exchange: {
          title: "交换机",
          type: "text",
          form: {
            col: { span: 12 },
            helper: "覆盖交换机以进行低层级AMQP路由"
          }
        },
        routing_key: {
          title: "路由键",
          type: "text",
          form: {
            col: { span: 12 },
            helper: "覆盖路由键以进行低层级AMQP路由"
          }
        },
        priority: {
          title: "优先级",
          type: "number",
          form: {
            col: { span: 12 },
            helper:
              "优先级数字，介于0和255之间。支持者：RabbitMQ，Redis（优先级颠倒，0是最高）"
          }
        },
        headers: {
          title: "Amqp消息头",
          type: "textarea",
          form: {
            helper: "AMQP消息的JSON编码消息头。"
          }
        },

        task_result: taskResultTable({
          form: {
            component: {
              crudOptionsOverride: {
                search: {
                  initialForm: compute(({ form }) => {
                    // 构造一个 JS 对象
                    const task_kwargs = `"{'periodic_task_id': ${form.id}}"`;
                    return { task_kwargs__exact: task_kwargs };
                  })
                },
                toolbar: {
                  show: true
                },
                columns: {
                  task_id: { column: { show: false } },
                  periodic_task_name: { column: { show: false } },
                  task_name: { column: { show: false } }
                }
              }
            }
          },
          column: { show: false }
        })
      }
    }
  };
}

/**
 * 定时任务 关联组件工厂
 * @description 基于 createRelation 生成关联的三个组件：选择器、只读表单、子表嵌套
 */
const { createSelect, createForm, createTable } = createRelation({
  /** 标题 */
  title: "定时任务",
  /** 组件名称（按钮权限标识，供其他模块复用本模块配置） */
  componentName,
  /** 本模块 CRUD 配置生成器 */
  createCrudOptions,
  /** 本模块接口 */
  api,
  fkField: "periodic_task",
  dictConfig: {
    api,
    dictLabel: "name",
    queryFields: ["id", "name"]
  },
  searchConfig: {
    field: "periodic_task",
    lookup: "in"
  },
  columnCellRenderConfig: {
    componentName,
    createCrudOptions,
    fkField: "periodic_task",
    columnLabel: "periodic_task_name",
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
 * 定时任务 选择器
 * @description 默认在表单（form）作为父级字段选择器显示。列表（column）不显示、查询区（search）不显示
 */
export const periodicTaskSelect = (
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
 * 定时任务 只读表单
 * @description 默认在表单（form）作为只读表单显示，列表（column）显示，查询区（search）显示
 */
export const periodicTaskForm = (
  options?: ColumnCompositionProps
): ColumnCompositionProps => {
  const defaultOptions: ColumnCompositionProps = {};
  return createForm(merge(defaultOptions, options));
};

/**
 * 定时任务 子表嵌套
 * @description 默认在表单（form）作为子表 tab 显示。列表（column）不显示，查询区（search）不显示
 */
export const periodicTaskTable = (
  options?: ColumnCompositionProps
): ColumnCompositionProps => {
  const defaultOptions: ColumnCompositionProps = {};
  return createTable(merge(defaultOptions, options));
};
