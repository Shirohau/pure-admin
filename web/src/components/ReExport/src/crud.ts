import {
  compute,
  dict,
  type CreateCrudOptionsProps,
  type CreateCrudOptionsRet,
  type UserPageQuery
} from "@fast-crud/fast-crud";

import { http } from "@/utils/http";

/**
 * 创建后台导出记录表配置。
 * 此文件只负责记录查询与表格展示；模板管理和导出动作统一留在 index.vue。
 */
export default function ({
  context: { props }
}: CreateCrudOptionsProps): CreateCrudOptionsRet {
  /** 按 FastCrud 分页参数查询当前业务的后台导出任务。 */
  const pageRequest = async (params: UserPageQuery) => {
    return await http.get(`${props.formInline.apiPrefix}async_export/`, {
      params
    });
  };

  return {
    crudOptions: {
      // 在这里自定义你的crudOptions配置
      request: {
        pageRequest
      },
      // 导出记录仅需分页列表，不显示搜索表单和新增入口。
      search: { show: false },
      actionbar: { show: true, buttons: { add: { show: false } } },
      toolbar: {
        show: true,
        buttons: {
          search: {
            show: false
          },
          compact: {
            show: false
          },
          export: {
            show: false
          },
          columns: {
            show: false
          }
        }
      },
      rowHandle: {
        fixed: "right",
        width: 96,
        align: "center",
        buttons: {
          view: {
            show: false
          },
          edit: {
            show: false
          },
          remove: {
            show: false
          },
          download: {
            // 只有任务成功后才显示下载入口，避免打开空文件地址。
            show: compute(ctx => {
              return ctx.row.export_status === "EXPORTED";
            }),
            text: "下载文件",
            type: "primary",
            link: true,
            click: ctx => window.open(ctx.row.data_file, "_blank")
          }
        }
      },
      columns: {
        // ID 保留给 FastCrud 作为行标识，不在表格中占用空间。
        id: {
          title: "ID",
          type: "text",
          column: {
            width: 50,
            align: "center",
            show: false
          }
        },
        export_status: {
          title: "状态",
          type: "dict-select",
          dict: dict({
            data: [
              { value: "CREATED", label: "等待处理", color: "info" },
              { value: "EXPORTING", label: "导出中", color: "primary" },
              { value: "EXPORT_ERROR", label: "导出错误", color: "danger" },
              { value: "EXPORTED", label: "导出成功", color: "success" },
              { value: "CANCELLED", label: "已取消", color: "info" }
            ]
          }),
          column: {
            width: 108,
            align: "center"
          }
        },
        data_file: {
          title: "文件地址",
          column: {
            minWidth: 220,
            showOverflowTooltip: true,
            formatter({ value }) {
              if (!value) return "-";
              // 同时兼容绝对媒体地址与相对媒体地址。
              const url = new URL(value, window.location.origin);
              const encodedName = url.pathname.split("/").pop() || "";
              return decodeURIComponent(encodedName);
            }
          }
        },

        export_started: {
          title: "开始时间",
          column: {
            width: 168,
            align: "center"
          }
        },
        export_finished: {
          title: "完成时间",
          column: {
            width: 168,
            align: "center"
          }
        },
        error_message: {
          title: "错误描述",
          column: {
            minWidth: 180,
            showOverflowTooltip: true,
            formatter({ value }) {
              return value || "-";
            }
          }
        }
      }
    }
  };
}
