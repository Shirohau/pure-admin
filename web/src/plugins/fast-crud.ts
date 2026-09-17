// 引入fast-crud
//  设置日志级别 日志级别包括: debug | info | warn | error
import {
  type ColumnCompositionProps,
  type CompositionColumns,
  type CrudExpose,
  FastCrud,
  setLogger,
  useMerge
} from "@fast-crud/fast-crud";
import "@fast-crud/fast-crud/dist/style.css";
// element
import ui from "@fast-crud/ui-element";

import type { App } from "vue";
import { i18n } from "./i18n";

import {
  FsExtendsEditor,
  FsExtendsJson,
  FsExtendsUploader,
  type FsUploaderFormRequestOptions
} from "@fast-crud/fast-extends";
import "@fast-crud/fast-extends/dist/style.css";

import { FsEditorCode } from "@fast-crud/editor-code";
import "@fast-crud/editor-code/dist/style.css";
import { TABLE_SUMMARY_KEY } from "@/utils/crud/createSummaryMethod";
import { http } from "@/utils/http";

setLogger({ level: "error" });

export function useFastCrud(app: App) {
  // 安装 UI 组件库
  app.use(ui);

  // 安装 FastCrud 插件
  app.use(FastCrud, {
    i18n,
    async dictRequest(dict): Promise<any[]> {
      //通过字段组件中配置的dict.url获取远程字典数据
      const { data }: ApiResponse = await http.get(dict.url);
      return data;
    },
    //公共crud配置
    commonOptions() {
      return {
        table: {
          remove: { showSuccessNotification: false }
        },
        request: {
          // 转换分页查询参数
          transformQuery: ({ page, form, sort }) => {
            // 根据你后端实际需要的结构调整
            if (sort.asc !== undefined) {
              form["ordering"] = `${sort.asc ? "" : "-"}${sort.prop}`;
            }
            //转换为你 pageRequest 所需要的请求参数结构
            return { page: page.currentPage, limit: page.pageSize, ...form };
          },
          // 转换接口响应数据结构
          transformRes: ({ res }) => {
            // 后端返回结构为：{ data: { data, total, page, limit } }
            //return {records,currentPage,pageSize,total};
            const { paginated, data, summary } = res;
            const records: any[] = data || [];
            // 表尾合计直传：挂到 records 上供 createSummaryMethod 自动读取
            // （fast-crud 只消费 records/分页字段，响应中的 summary 会被丢弃）
            if (summary != null) {
              records[TABLE_SUMMARY_KEY] = summary;
            }
            return {
              records,
              currentPage: paginated?.page || 1,
              pageSize: paginated?.limit || 10,
              total: paginated?.total || 0
            };
          }
        }
      };
    },
    logger: { off: { tableColumns: false } }
  });
  // 安装 文件上传 组件
  app.use(FsExtendsUploader, {
    defaultType: "form",
    form: {
      action: `/api/system/file/`,
      name: "file",
      uploadRequest: async (props: FsUploaderFormRequestOptions) => {
        const data = new FormData();
        data.append("file", props.file);
        for (const key in props.data) {
          if (key !== "file") {
            data.append(key, props.data[key]);
          }
        }
        return await http.request("post", props.action, {
          data,
          timeout: 0,
          headers: {
            "Content-Type": "multipart/form-data"
          },
          onUploadProgress: (p: any) => {
            props.onProgress({
              percent: Math.round((p.loaded / p.total) * 100)
            });
          }
        });
      },
      successHandle(res: any) {
        // 上传完成后的结果处理， 此处应返回格式为{url:xxx,key:xxx}
        return Promise.resolve({
          url: res.data.path,
          key: res.data.id + "",
          row: res.data
        });
      }
    }
  });
  //安装editor
  app.use(FsExtendsEditor, {
    //编辑器的公共配置
    wangEditor: {
      editorConfig: {
        MENU_CONF: {}
      },
      toolbarConfig: {}
    }
  });
  app.use(FsExtendsJson);
  // 安装editor code
  app.use(FsEditorCode);
}

const { merge } = useMerge();

/**
 * 审计字段
 *
 * 提供创建者、创建时间、更新者、更新时间、数据归属部门五个审计字段的列配置，
 * 均支持列头筛选（text/date）；创建时间（create_dt）的日期筛选带时区参数。
 *
 * @param options 自定义覆盖配置（与默认配置深合并）
 * @param crudExpose CRUD 实例（提供 doRefresh 触发列表刷新）
 * @param createFilterHeader 列头筛选创建函数（来自 useFilter 的 createFilterHeader）
 * @returns 审计字段列配置
 */
export const AuditField = (
  options?: CompositionColumns,
  crudExpose?: CrudExpose,
  createFilterHeader?: (options: any) => any
): CompositionColumns => {
  // 未传入 createFilterHeader / crudExpose 时不渲染列头筛选，保证调用方向后兼容
  const hasFilter = !!(createFilterHeader && crudExpose);

  // 创建者
  const creator_name: ColumnCompositionProps = {
    title: "创建者",
    type: "text",
    form: { show: false },
    column: {
      show: false,
      showOverflowTooltip: true,
      minWidth: 100,
      ...(hasFilter
        ? {
            columnSlots: {
              header: createFilterHeader!({
                type: "text",
                columnLabel: "创建者",
                fieldName: "creator__name"
              })
            }
          }
        : {})
    }
  };

  // 创建时间（日期筛选带时区参数 useTimezone: true）
  const create_dt: ColumnCompositionProps = {
    title: "创建时间",
    type: "text",
    form: { show: false },
    column: {
      show: false,
      showOverflowTooltip: true,
      minWidth: 150,
      ...(hasFilter
        ? {
            columnSlots: {
              header: createFilterHeader!({
                type: "datetime",
                columnLabel: "创建时间",
                fieldName: "create_dt",
                useTimezone: true
              })
            }
          }
        : {})
    }
  };

  // 更新者
  const updater_name: ColumnCompositionProps = {
    title: "更新者",
    type: "text",
    form: { show: false },
    column: {
      show: false,
      showOverflowTooltip: true,
      minWidth: 100,
      ...(hasFilter
        ? {
            columnSlots: {
              header: createFilterHeader!({
                type: "text",
                columnLabel: "更新者",
                fieldName: "updater__name"
              })
            }
          }
        : {})
    }
  };

  // 更新时间
  const update_dt: ColumnCompositionProps = {
    title: "更新时间",
    type: "text",
    form: { show: false },
    column: {
      show: false,
      showOverflowTooltip: true,
      minWidth: 150,
      ...(hasFilter
        ? {
            columnSlots: {
              header: createFilterHeader!({
                type: "datetime",
                columnLabel: "更新时间",
                fieldName: "update_dt",
                useTimezone: true
              })
            }
          }
        : {})
    }
  };

  // 数据归属部门
  const dept_belong_name: ColumnCompositionProps = {
    title: "数据归属部门",
    type: "text",
    form: { show: false },
    column: {
      show: false,
      showOverflowTooltip: true,
      minWidth: 150,
      ...(hasFilter
        ? {
            columnSlots: {
              header: createFilterHeader!({
                type: "text",
                columnLabel: "数据归属部门",
                fieldName: "dept_belong__name"
              })
            }
          }
        : {})
    }
  };

  // 默认配置，可覆盖
  const defaultOptions: CompositionColumns = {
    creator_name,
    create_dt,
    updater_name,
    update_dt,
    dept_belong_name
  };
  return merge(defaultOptions, options);
};
