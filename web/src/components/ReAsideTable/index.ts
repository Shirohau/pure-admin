import { ref, h } from "vue";
import { type DynamicallyCrudOptions, useMerge } from "@fast-crud/fast-crud";
import asideTable from "./src/index.vue";
import type {
  AsideTableSureContext,
  DialogAsideTableOptions,
  ReAsideTableProps
} from "./types";
import { withInstall } from "@pureadmin/utils";
import { addDialog } from "../ReDialog";
import { ElRadio } from "element-plus";

const { merge } = useMerge();

/** 子表组件 */
export const ReAsideTable = withInstall(asideTable);
/** 子表函数式组件 */
export const dialogAsideTable = (options: DialogAsideTableOptions) => {
  const {
    multiple = true,
    props,
    beforeSure: useBeforeSure,
    ...restOptions
  } = options;
  const tableRef = ref();
  /** 是否多选 */
  const selectDefaults: DynamicallyCrudOptions = multiple
    ? {}
    : {
        table: {
          onCurrentChange: (row: any) => {
            tableRef.value.selectedData = row ? [row] : [];
          }
        },
        columns: {
          $selected: {
            form: { show: false },
            column: {
              title: "单选",
              align: "center",
              width: "55px",
              order: -999,
              show: true,
              columnSetShow: false, //在列设置中不显示该字段
              // 回显读弹窗实例的 selectedData（与确认取数同一数据源）
              cellRender: ({ row }: any) =>
                h(ElRadio, {
                  modelValue: (tableRef.value?.selectedData ?? []).includes(
                    row
                  ),
                  value: true
                })
            }
          },
          $checked: {
            column: { show: false }
          }
        }
      };
  const finalProps: ReAsideTableProps = {
    ...props,
    // 内置默认配置、选择行为配置与调用方覆盖配置深合并，调用方优先
    crudOptionsOverride: merge(
      {
        search: { show: false },
        actionbar: { show: false },
        toolbar: { show: false },
        rowHandle: { show: false }
      },
      selectDefaults,
      props.crudOptionsOverride
    )
  };

  // 包装 beforeSure，注入 selectedData
  const wrappedBeforeSure = (
    done: Function,
    ctx: Omit<AsideTableSureContext, "selectedData">
  ) => {
    const selectedData = tableRef.value?.selectedData ?? [];
    if (useBeforeSure) {
      useBeforeSure(done, { ...ctx, selectedData });
    }
  };
  const defaultProps = {
    width: "70%",
    title: "函数式弹框",
    style: { height: "70vh" },
    contentRenderer: () => h(asideTable, { ...finalProps, ref: tableRef }),
    beforeSure: wrappedBeforeSure
  };
  addDialog(merge(defaultProps, restOptions));
};

export type {
  AsideTableSureContext,
  DialogAsideTableOptions,
  ReAsideTableProps
} from "./types";
export default ReAsideTable;
