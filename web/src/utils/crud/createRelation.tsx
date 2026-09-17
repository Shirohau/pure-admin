import {
  useMerge,
  compute,
  type CreateCrudOptions,
  type ColumnCompositionProps
} from "@fast-crud/fast-crud";
import {
  createTableSelectDict,
  type CreateTableSelectDictOptions
} from "./createTableSelectDict";
import {
  createColumnCellRender,
  type CreateColumnCellRenderOptions
} from "./createColumnCellRender";
import {
  createSearch,
  createValueResolve,
  type ValueResolveConfig
} from "./createSearch";
import { shallowRef } from "vue";
import ReParentForm from "@/components/ReParentForm";
import ReAsideTable, {
  dialogAsideTable,
  type DialogAsideTableOptions
} from "@/components/ReAsideTable";
import ReFsReTableSelect from "@/components/ReFsReTableSelect";

const { merge } = useMerge();

/** 关联模块配置（createRelation 初始化参数，作为四种关联能力的默认配置） */
interface CreateRelationOptions {
  /** 关联记录名称（用于标题与校验文案） */
  title: string;
  /** 关联模块组件标识（子表嵌套与权限标识） */
  componentName: string;
  /** 关联模块数据接口 */
  api: any;
  /** 本模块外键字段名 */
  fkField: string;
  /** 关联模块 CRUD 配置生成器 */
  createCrudOptions: CreateCrudOptions;
  /** 选择器字典默认配置 */
  dictConfig: CreateTableSelectDictOptions;
  /** 搜索值解析默认配置 */
  searchConfig: ValueResolveConfig;
  /** 关联列单元格渲染默认配置 */
  columnCellRenderConfig: CreateColumnCellRenderOptions;
}

/** 调用 createSelect/createForm/createTable 时的可覆盖配置 */
type RelationColumnOptions = ColumnCompositionProps & {
  /** 选择器形态：dialog-弹窗表格选择器（默认）；select-内嵌表格多选选择器 */
  selectType?: "dialog" | "select";
  dictConfig?: CreateTableSelectDictOptions;
  searchConfig?: ValueResolveConfig;
  columnCellRenderConfig?: CreateColumnCellRenderOptions;
};

export function createRelation(config: CreateRelationOptions) {
  const {
    title,
    componentName,
    api,
    fkField,
    createCrudOptions,
    // 工厂级默认配置，可被每次调用的覆盖项按字段合并
    dictConfig: defaultDictConfig,
    searchConfig: defaultSearchConfig,
    columnCellRenderConfig: defaultCellRenderConfig
  } = config;

  /**
   * 合并默认配置与本次覆盖项（覆盖项后置，以最后一次传入为准）
   * @description 以空对象收底：fast-crud merge 会原地修改首参，避免污染模块级共享的默认配置
   */
  const mergeOverride = (defaultConfig: any, override?: any) =>
    merge({}, defaultConfig, override);

  /** 查询区配置：外键多选表格选择器（dict 按 id 回显 + 提交值解析） */
  const buildSearch = (show: boolean, options: RelationColumnOptions) =>
    createSearch({
      title: `${title}高级筛选`,
      show,
      component: {
        createCrudOptions,
        dict: createTableSelectDict(
          mergeOverride(defaultDictConfig, options.dictConfig)
        )
      },
      valueResolve: createValueResolve(
        mergeOverride(defaultSearchConfig, options.searchConfig)
      )
    });

  /** 列表列配置：详情链接单元格渲染，支持整列显示开关 */
  const buildColumn = (show: boolean, options: RelationColumnOptions) => ({
    title,
    show,
    columnSetShow: show,
    cellRender: createColumnCellRender(
      mergeOverride(defaultCellRenderConfig, options.columnCellRenderConfig)
    )
  });

  /** 展示型表单外壳：占整行、无标签、懒加载（只读详情与子表共用） */
  const buildFormShell = (
    formTitle: string,
    component: Record<string, any>
  ) => ({
    title: formTitle,
    show: true,
    lazy: true,
    col: { span: 24 },
    labelWidth: "0px",
    labelPosition: "",
    component
  });

  /**
   * 选择器
   * @description 表单区显示为外键选择器，列表/查询区默认不显示
   */
  const createSelect = (
    options: RelationColumnOptions = {}
  ): ColumnCompositionProps => {
    const { selectType = "dialog" } = options;
    return merge(
      {
        title,
        type: "table-select",
        search: buildSearch(false, options),
        form: {
          title: `${title}选择器`,
          show: true,
          rules: [
            { required: true, trigger: "change", message: `选择${title}` }
          ],
          component: {
            // select=内嵌表格多选选择器；dialog=弹窗表格选择器
            name:
              selectType === "select"
                ? shallowRef(ReFsReTableSelect)
                : "fs-table-select",
            dict: createTableSelectDict(
              mergeOverride(defaultDictConfig, options.dictConfig)
            ),
            multiple: false,
            rowKey: "id", // element-plus 必传
            select: {
              collapseTags: true,
              collapseTagsTooltip: true,
              maxCollapseTags: 5
            },
            createCrudOptions,
            // 单选场景：隐藏行操作与多选列
            crudOptionsOverride: {
              rowHandle: { show: false },
              columns: {
                $checked: {
                  column: { show: false }
                }
              }
            }
          }
        },
        column: buildColumn(false, options)
      },
      options // 列级覆盖项（form/search/column/...）后置优先
    );
  };

  /**
   * 只读表单
   * @description 表单区以 ReParentForm 展示关联记录详情，列表/查询区默认显示
   */
  const createForm = (
    options: RelationColumnOptions = {}
  ): ColumnCompositionProps =>
    merge(
      {
        title,
        width: 130,
        type: ["number", "colspan"],
        search: buildSearch(true, options),
        addForm: { show: false },
        form: buildFormShell(`${title}详情`, {
          name: shallowRef(ReParentForm),
          api,
          id: compute(({ form }) => form?.[fkField]),
          createCrudOptions,
          context: { isNested: true }
        }),
        column: buildColumn(true, options)
      },
      options
    );

  /**
   * 子表嵌套
   * @description 表单区以 ReAsideTable 展示关联子表，列表/查询区默认不显示
   */
  const createTable = (
    options: RelationColumnOptions = {}
  ): ColumnCompositionProps =>
    merge(
      {
        title,
        width: 130,
        type: ["number", "colspan"],
        search: buildSearch(false, options),
        addForm: { show: false },
        form: buildFormShell(`${title}子表`, {
          name: shallowRef(ReAsideTable),
          componentName,
          api,
          style: { height: "calc(100vh - 200px)" },
          createCrudOptions,
          context: { isNested: true },
          // 子表内置工具栏仅保留搜索按钮
          crudOptionsOverride: {
            search: { show: false },
            actionbar: { show: false },
            toolbar: {
              buttons: {
                search: { show: true },
                compact: { show: false },
                columns: { show: true },
                export: { show: false },
                import: { show: false }
              }
            }
          }
        }),
        column: buildColumn(false, options)
      },
      options
    );

  /**
   * 子表弹窗
   * @description 在任意位置以点击形式打开关联子表弹窗，不占用表单区：
   */
  const createDialogTable = (options: DialogAsideTableOptions): void => {
    const { props, ...restOptions } = options;
    const defaultOptions: ColumnCompositionProps = {};
    const crudOptionsOverride = merge(
      defaultOptions,
      props?.crudOptionsOverride
    );
    dialogAsideTable({
      props: {
        ...props,
        componentName,
        createCrudOptions,
        crudOptionsOverride
      },
      ...restOptions
    });
  };

  return { createSelect, createForm, createTable, createDialogTable };
}
