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
  type CreateCrudOptionsRet
} from "@fast-crud/fast-crud";
import { api } from "./api";
import { ref } from "vue";
import { ElMessageBox } from "element-plus";
import { useButtonPerms } from "@/utils/auth";
import { periodicTaskTable } from "@/views/system/celery/periodic_task/crud";
import { createRelation } from "@/utils/crud/createRelation";
const { merge } = useMerge();

// 定义组件名称
export const componentName = "IntervalScheduleView";

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
        wrapper: {
          is: "el-drawer",
          size: "100%"
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

        every: {
          title: "周期数",
          type: "number",
          form: {
            col: { span: 12 },
            component: { min: 1, precision: 0 },
            rules: [{ required: true, message: "请选择周期数" }],
            helper: "再次执行任务之前要等待的间隔周期数"
          }
        },
        period: {
          title: "间隔周期",
          type: "dict-select",
          dict: dict({
            data: [
              { label: "天", value: "days" },
              { label: "小时", value: "hours" },
              { label: "分钟", value: "minutes" },
              { label: "秒", value: "seconds", disabled: true },
              { label: "毫秒", value: "microseconds", disabled: true }
            ]
          }),
          form: {
            col: { span: 12 },
            rules: [{ required: true, message: "请选择间隔周期" }],
            helper: "任务每次执行之间的时间间隔类型（例如：天）"
          }
        },
        described: {
          title: "描述",
          type: "text",
          form: {
            component: {
              disabled: true
            }
          },
          addForm: { show: false }
        },
        periodic_task: periodicTaskTable({
          form: {
            labelPosition: "top",
            component: {
              crudOptionsOverride: {
                table: {
                  show: true
                },
                search: {
                  initialForm: compute(({ form }) => {
                    return { interval__exact: form?.id };
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
                      value: "interval",
                      component: {
                        disabled: true
                      }
                    }
                  },
                  interval: {
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
 * 间隔触发器 关联组件工厂
 * @description 基于 createRelation 生成关联的三个组件：选择器、只读表单、子表嵌套
 */
const { createSelect, createForm, createTable } = createRelation({
  /** 标题 */
  title: "间隔触发器",
  /** 组件名称（按钮权限标识，供其他模块复用本模块配置） */
  componentName,
  /** 本模块 CRUD 配置生成器 */
  createCrudOptions,
  /** 本模块接口 */
  api,
  fkField: "interval",
  dictConfig: {
    api,
    dictLabel: "name",
    queryFields: ["id", "name"]
  },
  searchConfig: {
    field: "interval",
    lookup: "in"
  },
  columnCellRenderConfig: {
    componentName,
    createCrudOptions,
    fkField: "interval",
    columnLabel: "interval_name",
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
 * 间隔触发器 选择器
 * @description 默认在表单（form）作为父级字段选择器显示。列表（column）不显示、查询区（search）不显示
 */
export const intervalSelect = (
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
 * 间隔触发器 只读表单
 * @description 默认在表单（form）作为只读表单显示，列表（column）显示，查询区（search）显示
 */
export const intervalForm = (
  options?: ColumnCompositionProps
): ColumnCompositionProps => {
  const defaultOptions: ColumnCompositionProps = {};
  return createForm(merge(defaultOptions, options));
};

/**
 * 间隔触发器 子表嵌套
 * @description 默认在表单（form）作为子表 tab 显示。列表（column）不显示，查询区（search）不显示
 */
export const intervalTable = (
  options?: ColumnCompositionProps
): ColumnCompositionProps => {
  const defaultOptions: ColumnCompositionProps = {};
  return createTable(merge(defaultOptions, options));
};
