import {
  compute,
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
import { api, apiPrefix, getDictData } from "./api";
import { ref } from "vue";
import { Check } from "@element-plus/icons-vue";
import { ElMessage, ElMessageBox } from "element-plus";
import { openExportDialog } from "@/components/ReExport";
import { openImportDialog } from "@/components/ReImport";
// 颜色选择器定制样式（下拉面板 teleport 到 body，需全局样式）
import "./color.scss";

/** 筛选辅助工具（统一管理 filterForm + applyFilter + clearFilter + injectFilterToQuery）*/
import { useFilter } from "@/components/ReFilter/src/useFilter";
import { createRelation } from "@/utils/crud/createRelation";
import { createFormAfterSubmit } from "@/utils/crud/createFormAfterSubmit";
import { createFormWrapper } from "@/utils/crud/createFormWrapper";
import { createCrudPerms } from "@/utils/crud/createCrudPerms";
const { merge } = useMerge();
// 定义组件名称
export const componentName = "DictionaryView";

// 颜色选项类型：value 对应 el-tag 类型
interface ColorOption {
  value: "primary" | "success" | "info" | "warning" | "danger";
  label: string;
  color: string;
}

// 颜色选项：与 element-plus 主题色保持一致
const colorOptions: ColorOption[] = [
  { value: "primary", label: "primary", color: "primary" },
  { value: "success", label: "success", color: "success" },
  { value: "info", label: "info", color: "info" },
  { value: "warning", label: "warning", color: "warning" },
  { value: "danger", label: "danger", color: "danger" }
];

// 颜色值 -> 色值映射，供选中前缀圆点快速取值
const colorHexMap: Record<ColorOption["value"], string> = {
  primary: "#409eff",
  success: "#67c23a",
  info: "#909399",
  warning: "#e6a23c",
  danger: "#f56c6c"
};

/**
 * 定义一个CrudOptions生成器方法
 */
export default function createCrudOptions({
  crudExpose
}: CreateCrudOptionsProps): CreateCrudOptionsRet {
  /** 按钮权限（懒加载 + 响应式，权限加载完成后自动更新） */
  const hasPerms = createCrudPerms(componentName);

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
        fixed: "right",
        align: "center",
        width: 300,
        buttons: {
          view: {
            show: false
          },
          edit: {
            show: hasPerms.edit
          },
          remove: {
            order: 2,
            show: hasPerms.remove
          },
          moveUp: {
            text: "上移",
            show: true,
            click: ({ row }) => {
              api.MoveObj(row.id, "up").then(async () => {
                await crudExpose.doRefresh(); // 刷新表
              });
            }
          },
          moveDown: {
            text: "下移",
            show: true,
            click: ({ row }) => {
              api.MoveObj(row.id, "down").then(async () => {
                await crudExpose.doRefresh(); // 刷新表
              });
            }
          }
        }
      },
      search: {
        initialForm: { level: 1 },
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
        col: { span: 8 },
        initialForm: { level: 1 },
        // 保存成功后留在抽屉继续编辑：新增转编辑，编辑保持编辑
        afterSubmit: createFormAfterSubmit(crudExpose),
        // 全屏抽屉表单：底部操作按钮仅在 "base" 分组显示，打开时重置到 "base"
        wrapper: createFormWrapper({
          groupTab,
          formWrapperOverride: {
            size: "100%",
            buttons: {
              area: {
                text: "表单数据",
                show: compute(
                  () => groupTab.value == "example"
                ) as unknown as boolean,
                click: () => {
                  const form_data = crudExpose.getFormData();
                  ElMessage({ message: form_data, type: "success" });
                  console.log(form_data);
                }
              }
            }
          }
        }),
        group: {
          groupType: "tabs",
          onTabChange: (pane: string) => {
            groupTab.value = pane;
          },
          modelValue: "base",
          groups: {
            base: {
              label: "父级",
              lazy: true,
              columns: ["label", "value", "color", "status", "sort", "remark"]
            },
            children: {
              label: "子集",
              lazy: true,
              columns: ["children"]
            },
            example: {
              label: "示例",
              lazy: true,
              columns: ["gender", "education", "assets_class"]
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
        gender: {
          title: "性别",
          type: "dict-select",
          dict: getDictData("gender"),
          column: {
            show: false
          }
        },
        education: {
          title: "学历",
          code: "education",
          type: "dict-select",
          dict: getDictData("education"),
          column: {
            show: false
          }
        },
        assets_class: {
          title: "资产类别",
          type: "dict-tree",
          dict: getDictData("assets_class", {
            isTree: true
          }),
          form: {
            col: { span: 12 }
          },
          column: {
            show: false
          }
        },
        sort: {
          title: "排序",
          type: "number",
          addForm: { show: false },
          column: {
            columnSlots: {
              header: createFilterHeader({
                type: "number",
                columnLabel: "排序",
                fieldName: "sort"
              })
            }
          }
        },
        label: {
          title: "名称",
          type: "text",
          form: {
            rules: [{ required: true, message: "请输入名称" }]
          },
          column: {
            columnSlots: {
              header: createFilterHeader({
                type: "text",
                columnLabel: "名称",
                fieldName: "label"
              })
            }
          }
        },
        value: {
          title: "值",
          type: "text",
          form: {
            rules: [{ required: true, message: "请输入值" }]
          },
          column: {
            columnSlots: {
              header: createFilterHeader({
                type: "text",
                columnLabel: "值",
                fieldName: "value"
              })
            }
          }
        },
        color: {
          title: "颜色",
          type: "dict-select",
          dict: dict({
            data: colorOptions
          }),
          form: {
            render: ({ form }) => {
              return (
                <el-select
                  v-model={form.color}
                  placeholder="请选择颜色"
                  popper-class="dictionary-color-select"
                >
                  {{
                    // 选中值前缀：展示当前颜色的圆点，便于识别选中颜色
                    prefix: () =>
                      form.color && (
                        <span
                          class="dictionary-color-dot"
                          style={{ backgroundColor: colorHexMap[form.color] }}
                        />
                      ),
                    // 选项内容：el-tag + 选中对勾
                    default: () =>
                      colorOptions.map(item => (
                        <el-option
                          key={item.value}
                          value={item.value}
                          label={item.label}
                        >
                          <div class="dictionary-color-option">
                            <el-tag type={item.value} size="small">
                              {item.label}
                            </el-tag>
                            {form.color === item.value && (
                              <el-icon class="dictionary-color-check">
                                <Check />
                              </el-icon>
                            )}
                          </div>
                        </el-option>
                      ))
                  }}
                </el-select>
              );
            }
          },
          column: {
            columnSlots: {
              header: createFilterHeader({
                type: "select",
                columnLabel: "颜色",
                fieldName: "color",
                selectList: colorOptions
              })
            }
          }
        },
        status: {
          title: "状态",
          type: "dict-switch",
          dict: dict({
            data: [
              { value: true, label: "开启", color: "success" },
              { value: false, label: "关闭", color: "danger" }
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
                  { value: true, label: "开启" },
                  { value: false, label: "关闭" }
                ]
              })
            }
          }
        },
        remark: {
          title: "备注",
          type: "areatext",
          form: {
            col: { span: 24 }
          },
          column: {
            columnSlots: {
              header: createFilterHeader({
                type: "text",
                columnLabel: "备注",
                fieldName: "remark"
              })
            }
          }
        },
        // 子集
        children: dictionaryTable({
          form: {
            component: {
              crudOptionsOverride: {
                actionbar: { show: true },
                search: {
                  initialForm: compute(({ form }) => {
                    return { parent: form?.id, level: form?.level + 1 };
                  })
                },
                form: {
                  afterSubmit() {
                    return true;
                  },
                  initialForm: compute(({ form }) => {
                    return { parent: form?.id, level: form?.level + 1 };
                  })
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
 * 字典表 关联组件工厂
 * @description 基于 createRelation 生成关联的三个组件：选择器、只读表单、子表嵌套
 */
const { createTable } = createRelation({
  /** 标题 */
  title: "字典表",
  /** 组件名称（按钮权限标识，供其他模块复用本模块配置） */
  componentName,
  /** 本模块 CRUD 配置生成器 */
  createCrudOptions,
  /** 本模块接口 */
  api,
  fkField: "dictionary",
  dictConfig: {
    api,
    dictLabel: "name",
    queryFields: ["id", "name"]
  },
  searchConfig: {
    field: "dictionary",
    lookup: "in"
  },
  columnCellRenderConfig: {
    componentName,
    createCrudOptions,
    fkField: "dictionary",
    columnLabel: "dictionary_label"
  }
});

/**
 * 字典表 子表嵌套
 * @description 默认在表单（form）作为子表 tab 显示。列表（column）不显示，查询区（search）不显示
 */
export const dictionaryTable = (
  options?: ColumnCompositionProps
): ColumnCompositionProps => {
  const defaultOptions: ColumnCompositionProps = {};
  return createTable(merge(defaultOptions, options));
};
