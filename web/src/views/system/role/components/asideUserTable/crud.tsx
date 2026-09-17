import type {
  CreateCrudOptionsProps,
  CreateCrudOptionsRet,
  UserPageQuery
} from "@fast-crud/fast-crud";
import { api } from "./api";

import { ref } from "vue";

/** 筛选辅助工具（统一管理 filterForm + applyFilter + clearFilter + injectFilterToQuery）*/
import { useFilter } from "@/components/ReFilter/src/useFilter";

// 用户
export const componentName = "UserView";
/**
 * 定义一个CrudOptions生成器方法
 */
export default function createCrudOptions({
  crudExpose,
  context: { queryParams }
}: CreateCrudOptionsProps): CreateCrudOptionsRet {
  /** 筛选 */
  const { createFilterHeader, FilterTags, clearAllFilters } = useFilter({
    crudExpose
  });

  /** 列表查询 */
  const pageRequest = async (query: UserPageQuery) => {
    if (query["id__in"]?.length === 0) {
      // 返回空数据结构
      return { paginated: { page: 1, limit: 20, total: 0 }, data: [] };
    }
    return await api.GetList(query);
  };

  // 选中的数据
  const selectedData = ref([]);
  // 表格选中事件
  const onSelectionChange = (newSelection: any[]) => {
    selectedData.value = newSelection;
  };

  return {
    selectedData,
    FilterTags,
    clearAllFilters,
    crudOptions: {
      // 在这里自定义你的crudOptions配置
      request: {
        pageRequest
      },
      table: {
        rowKey: "id", //设置你的主键id， 默认rowKey=id
        onSelectionChange
      },
      search: {
        show: false,
        initialForm: {
          query: "{id, name, dept_name, role_name}",
          ...queryParams.value
        }
      },
      toolbar: {
        buttons: {
          search: { show: false },
          export: { show: false },
          import: { show: false },
          compact: { show: false },
          columns: { show: false }
        }
      },
      actionbar: {
        buttons: {
          add: { show: false }
        }
      },
      rowHandle: {
        show: false
      },
      columns: {
        $checked: {
          title: "选择",
          form: { show: false },
          column: {
            type: "selection",
            align: "center",
            width: "55px",
            reserveSelection: true,
            columnSetShow: false //在列设置中不显示该字段
          }
        },
        name: {
          title: "姓名",
          type: "text",
          form: {
            rules: [{ required: true, message: "请输入姓名" }]
          },
          column: {
            width: 100,
            columnSlots: {
              header: createFilterHeader({
                type: "text",
                columnLabel: "姓名",
                fieldName: "name"
              })
            }
          }
        },
        dept_name: {
          title: "关联部门",
          type: "text",
          column: {
            columnSlots: {
              header: createFilterHeader({
                type: "text",
                columnLabel: "关联部门",
                fieldName: "dept__name"
              })
            }
          }
        },
        // 关联角色
        role_name: {
          title: "关联角色",
          type: "text",
          column: {
            columnSlots: {
              header: createFilterHeader({
                type: "text",
                columnLabel: "关联角色",
                fieldName: "role__name"
              })
            }
          }
        }
      }
    }
  };
}
