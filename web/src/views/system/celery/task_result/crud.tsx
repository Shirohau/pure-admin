import {
  useMerge,
  type AddReq,
  type DelReq,
  type EditReq,
  type UserPageQuery,
  type ColumnCompositionProps,
  type CreateCrudOptionsRet
} from "@fast-crud/fast-crud";
import { api } from "./api";
import { ref } from "vue";
import { createRelation } from "@/utils/crud/createRelation";

const { merge } = useMerge();

// 定义组件名称
export const componentName = "TaskResultView";

/**
 * 定义一个CrudOptions生成器方法
 */
export default function createCrudOptions(): CreateCrudOptionsRet {
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

  return {
    selectedData,
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
        show: false
      },
      // 工具条配置
      toolbar: {
        buttons: {
          export: { show: false },
          compact: { show: false },
          columns: { show: false }
        }
      },
      search: { show: false },
      // 操作列配置
      rowHandle: {
        fixed: "right",
        align: "center",
        width: 80,
        buttons: {
          view: { show: true },
          edit: { show: false },
          remove: { show: false }
        }
      },
      // 表单基本配置
      form: {
        col: { span: 24 },
        labelWidth: "110px",
        wrapper: {
          is: "el-drawer",
          size: "100%"
        }
      },
      // 字段复合配置
      columns: {
        search: {
          title: "关键词",
          column: {
            show: false,
            columnSetShow: false //在列设置中不显示该字段
          },
          search: {
            show: true,
            component: {
              props: {
                clearable: true
              },
              placeholder: "请输入关键词"
            }
          },
          form: {
            show: false
          }
        },
        task_id: {
          title: "任务ID",
          type: "text",
          form: {
            col: { span: 8 }
          },
          column: {
            showOverflowTooltip: true,
            minWidth: 200, //最小列宽
            align: "left" //对齐方式
          }
        },
        periodic_task_name: {
          title: "任务名称",
          type: "text",
          form: {
            col: { span: 8 }
          },
          column: {
            showOverflowTooltip: true,
            minWidth: 200, //最小列宽
            align: "left" //对齐方式
          }
        },
        task_name: {
          title: "工作函数名称",
          type: "text",
          form: {
            col: { span: 8 }
          },
          column: {
            showOverflowTooltip: true,
            minWidth: 200, //最小列宽
            align: "left" //对齐方式
          }
        },
        status: {
          title: "状态",
          type: "select",
          form: {
            col: { span: 8 }
          },
          column: {
            showOverflowTooltip: true,
            width: 100, //最小列宽
            align: "left" //对齐方式
          }
        },
        date_created: {
          title: "开始时间",
          type: "datetime",
          form: {
            col: { span: 8 }
          },
          column: {
            showOverflowTooltip: true,
            minWidth: 200, //最小列宽
            align: "left" //对齐方式
          }
        },
        date_done: {
          title: "完成时间",
          type: "datetime",
          form: {
            col: { span: 8 }
          },
          column: {
            showOverflowTooltip: true,
            minWidth: 200, //最小列宽
            align: "left" //对齐方式
          }
        },
        worker: {
          title: "任务队列",
          type: "text",
          form: {
            col: { span: 8 }
          },
          column: {
            showOverflowTooltip: true,
            minWidth: 200, //最小列宽
            align: "left" //对齐方式
          }
        },
        content_type: {
          title: "结果内容类型",
          type: "text",
          form: {
            col: { span: 8 }
          },
          column: {
            showOverflowTooltip: true,
            minWidth: 200, //最小列宽
            align: "left" //对齐方式
          }
        },
        content_encoding: {
          title: "结果内容编码",
          type: "text",
          form: {
            col: { span: 8 }
          },
          column: {
            showOverflowTooltip: true,
            minWidth: 200, //最小列宽
            align: "left" //对齐方式
          }
        },
        task_args: {
          title: "位置参数",
          type: "textarea",
          column: {
            showOverflowTooltip: true,
            minWidth: 200, //最小列宽
            align: "left" //对齐方式
          }
        },
        task_kwargs: {
          title: "关键字参数",
          type: "textarea",
          column: {
            showOverflowTooltip: true,
            minWidth: 200, //最小列宽
            align: "left" //对齐方式
          }
        },
        result: {
          title: "返回值",
          type: "textarea",
          column: {
            showOverflowTooltip: true,
            minWidth: 200, //最小列宽
            align: "left" //对齐方式
          }
        },
        traceback: {
          title: "回溯文本",
          type: "textarea",
          column: {
            showOverflowTooltip: true,
            minWidth: 200, //最小列宽
            align: "left" //对齐方式
          }
        },
        meta: {
          title: "任务元信息",
          type: "textarea",
          column: {
            showOverflowTooltip: true,
            minWidth: 200, //最小列宽
            align: "left" //对齐方式
          }
        }
      }
    }
  };
}

/**
 * 任务结果 关联组件工厂
 * @description 基于 createRelation 生成关联的三个组件：选择器、只读表单、子表嵌套
 */
const { createSelect, createForm, createTable } = createRelation({
  /** 标题 */
  title: "任务结果",
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
 * 任务结果 选择器
 * @description 默认在表单（form）作为父级字段选择器显示。列表（column）不显示、查询区（search）不显示
 */
export const taskResultSelect = (
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
 * 任务结果 只读表单
 * @description 默认在表单（form）作为只读表单显示，列表（column）显示，查询区（search）显示
 */
export const taskResultForm = (
  options?: ColumnCompositionProps
): ColumnCompositionProps => {
  const defaultOptions: ColumnCompositionProps = {};
  return createForm(merge(defaultOptions, options));
};

/**
 * 任务结果 子表嵌套
 * @description 默认在表单（form）作为子表 tab 显示。列表（column）不显示，查询区（search）不显示
 */
export const taskResultTable = (
  options?: ColumnCompositionProps
): ColumnCompositionProps => {
  const defaultOptions: ColumnCompositionProps = {};
  return createTable(merge(defaultOptions, options));
};
