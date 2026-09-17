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
import { api } from "./api";
import { ref } from "vue";
import { ElMessageBox } from "element-plus";
import { useButtonPerms } from "@/utils/auth";
import { periodicTaskTable } from "@/views/system/celery/periodic_task/crud";
import dayjs from "dayjs";
import { createRelation } from "@/utils/crud/createRelation";
const { merge } = useMerge();

// 定义组件名称
export const componentName = "ClockedScheduleView";

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
          size: "80%"
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

        clocked_time: {
          title: "定时时间",
          type: "datetime",
          form: {
            valueResolve({ form }) {
              // 所有涉及到时间的字段，都需要考虑时区
              if (form.clocked_time) {
                form.clocked_time = dayjs(form.clocked_time).tz();
              }
            }
          },
          column: {
            align: "center",
            width: "anto"
          }
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
                    return { clocked__exact: form?.id };
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
                      value: "clocked",
                      component: {
                        disabled: true
                      }
                    }
                  },
                  clocked: {
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
 * 定时触发器 关联组件工厂
 * @description 基于 createRelation 生成关联的三个组件：选择器、只读表单、子表嵌套
 */
const { createSelect, createForm, createTable } = createRelation({
  /** 标题 */
  title: "定时触发器",
  /** 组件名称（按钮权限标识，供其他模块复用本模块配置） */
  componentName,
  /** 本模块 CRUD 配置生成器 */
  createCrudOptions,
  /** 本模块接口 */
  api,
  fkField: "clocked",
  dictConfig: {
    api,
    dictLabel: "name",
    queryFields: ["id", "name"]
  },
  searchConfig: {
    field: "clocked",
    lookup: "in"
  },
  columnCellRenderConfig: {
    componentName,
    createCrudOptions,
    fkField: "clocked",
    columnLabel: "clocked_name",
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
 * 定时触发器 选择器
 * @description 默认在表单（form）作为父级字段选择器显示。列表（column）不显示、查询区（search）不显示
 */
export const clockedSelect = (
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
 * 定时触发器 只读表单
 * @description 默认在表单（form）作为只读表单显示，列表（column）显示，查询区（search）显示
 */
export const clockedForm = (
  options?: ColumnCompositionProps
): ColumnCompositionProps => {
  const defaultOptions: ColumnCompositionProps = {};
  return createForm(merge(defaultOptions, options));
};

/**
 * 定时触发器 子表嵌套
 * @description 默认在表单（form）作为子表 tab 显示。列表（column）不显示，查询区（search）不显示
 */
export const clockedTable = (
  options?: ColumnCompositionProps
): ColumnCompositionProps => {
  const defaultOptions: ColumnCompositionProps = {};
  return createTable(merge(defaultOptions, options));
};
