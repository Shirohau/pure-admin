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
import { api, apiPrefix, getAreaData } from "./api";
import { ref } from "vue";
import { openExportDialog } from "@/components/ReExport";
import { ElMessage, ElMessageBox } from "element-plus";

/** 筛选辅助工具（统一管理 filterForm + applyFilter + clearFilter + injectFilterToQuery）*/
import { useFilter } from "@/components/ReFilter/src/useFilter";
import { createRelation } from "@/utils/crud/createRelation";
import { createFormAfterSubmit } from "@/utils/crud/createFormAfterSubmit";
import { createFormWrapper } from "@/utils/crud/createFormWrapper";
import { createCrudPerms } from "@/utils/crud/createCrudPerms";

const { merge } = useMerge();
// 定义组件名称
export const componentName = "AreaView";

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
          }
        }
      },
      // 操作列配置
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
      search: {
        show: false,
        initialForm: { level: 1 },
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
              label: "地区管理",
              lazy: true,
              columns: ["name", "code", "enable", "children"]
            },
            example: {
              label: "示例",
              columns: ["area1", "area2", "area3", "area4"]
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
        area1: {
          title: "省",
          type: "dict-cascader",
          dict: getAreaData(1),
          form: {
            col: { span: 12 },
            component: { filterable: true }
          },
          column: {
            show: false
          }
        },
        area2: {
          title: "省市",
          type: "dict-cascader",
          dict: getAreaData(2),
          form: {
            col: { span: 12 },
            helper: {
              render(scope) {
                const str = scope.value
                  ? `['${scope.value.join("', '")}']`
                  : undefined;
                return <span>{str}</span>;
              }
            }
          },
          column: {
            show: false
          }
        },
        area3: {
          title: "省市县",
          type: "dict-cascader",
          dict: getAreaData(3, { value: "name" }),
          form: {
            col: { span: 12 },
            helper: {
              render(scope) {
                const str = scope.value
                  ? `['${scope.value.join("', '")}']`
                  : undefined;
                return <span>{str}</span>;
              }
            }
          },
          column: {
            show: false
          }
        },
        area4: {
          title: "省市县乡",
          type: "dict-cascader",
          form: {
            col: { span: 12 },
            helper: {
              position: "label",
              tooltip: {
                placement: "top-start"
              },
              text: "懒加载"
            },
            component: {
              props: {
                props: {
                  lazy: true,
                  value: "code",
                  label: "name",
                  async lazyLoad(node, resolve) {
                    const { value, level } = node;
                    // 构造请求参数
                    const params = value
                      ? { parent_code: value }
                      : { level: 1, paginate: false };
                    // 获取数据
                    const res = await api.GetList(params);
                    let data = res.data || [];
                    // 如果是第3级，标记为叶子节点（不可再展开）
                    if (level === 3) {
                      data = data.map((item: any) => ({
                        ...item,
                        leaf: true
                      }));
                    }
                    resolve(data);
                  }
                }
              }
            }
          },
          column: {
            show: false
          }
        },
        level: {
          title: "层级",
          type: "dict-select",
          dict: dict({
            data: [
              { value: 1, label: "省份" },
              { value: 2, label: "城市" },
              { value: 3, label: "区县" },
              { value: 4, label: "乡镇" }
            ]
          }),
          search: {
            show: true
          },
          form: {
            show: false
          },
          column: {
            columnSlots: {
              header: createFilterHeader({
                type: "select",
                columnLabel: "层级",
                fieldName: "level",
                selectList: [
                  { value: 1, label: "省份" },
                  { value: 2, label: "城市" },
                  { value: 3, label: "区县" },
                  { value: 4, label: "乡镇" }
                ]
              })
            }
          }
        },
        name: {
          title: "名称",
          type: "text",
          column: {
            columnSlots: {
              header: createFilterHeader({
                type: "text",
                columnLabel: "名称",
                fieldName: "name"
              })
            }
          }
        },
        code: {
          title: "地区编码",
          type: "text",
          column: {
            columnSlots: {
              header: createFilterHeader({
                type: "text",
                columnLabel: "地区编码",
                fieldName: "code"
              })
            }
          }
        },
        pinyin: {
          title: "拼音",
          type: "text",
          form: { show: false },
          column: {
            columnSlots: {
              header: createFilterHeader({
                type: "text",
                columnLabel: "拼音",
                fieldName: "pinyin"
              })
            }
          }
        },
        initials: {
          title: "首字母",
          type: "text",
          form: { show: false },
          column: {
            columnSlots: {
              header: createFilterHeader({
                type: "text",
                columnLabel: "首字母",
                fieldName: "initials"
              })
            }
          }
        },
        enable: {
          title: "是否启用",
          type: "dict-switch",
          dict: dict({
            data: [
              { value: true, label: "启用", color: "success" },
              { value: false, label: "禁止", color: "danger" }
            ]
          }),
          form: { value: true },
          column: {
            columnSlots: {
              header: createFilterHeader({
                type: "select",
                columnLabel: "是否启用",
                fieldName: "enable",
                selectList: [
                  { value: 1, label: "启用" },
                  { value: 0, label: "禁止" }
                ]
              })
            }
          }
        },
        // 子集
        children: areaTable({
          addForm: { show: false },
          form: {
            component: {
              crudOptionsOverride: {
                search: {
                  show: false,
                  initialForm: compute(({ form }) => {
                    return { parent: form?.id, level: form?.level + 1 };
                  })
                },
                form: {
                  initialForm: compute(({ form }) => {
                    return { parent: form?.id, level: form?.level + 1 };
                  })
                },
                columns: {
                  level: {
                    search: { show: false }
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
 * 地区管理 关联组件工厂
 * @description 基于 createRelation 生成关联的三个组件：选择器、只读表单、子表嵌套
 */
const { createTable } = createRelation({
  /** 标题 */
  title: "地区管理",
  /** 组件名称（按钮权限标识，供其他模块复用本模块配置） */
  componentName,
  /** 本模块 CRUD 配置生成器 */
  createCrudOptions,
  /** 本模块接口 */
  api,
  fkField: "area",
  dictConfig: {
    api,
    dictLabel: "name",
    queryFields: ["id", "name"]
  },
  searchConfig: {
    field: "area",
    lookup: "in"
  },
  columnCellRenderConfig: {
    componentName,
    createCrudOptions,
    fkField: "area",
    columnLabel: "area_name",
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
 * 地区管理 子表嵌套
 * @description 默认在表单（form）作为子表 tab 显示。列表（column）不显示，查询区（search）不显示
 */
export const areaTable = (
  options?: ColumnCompositionProps
): ColumnCompositionProps => {
  const defaultOptions: ColumnCompositionProps = {
    form: {
      component: {
        style: { height: "calc(100vh - 270px)" },
        crudOptionsOverride: {
          actionbar: {
            show: true,
            buttons: {
              add: {
                disabled: compute(({ form }) => !form?.id)
              }
            }
          },
          toolbar: {
            buttons: {
              refresh: {
                disabled: compute(({ form }) => !form?.id)
              },
              search: {
                disabled: compute(({ form }) => !form?.id)
              },
              export: { show: false },
              compact: { show: false },
              columns: { show: false }
            }
          },
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
  };
  return createTable(merge(defaultOptions, options));
};
