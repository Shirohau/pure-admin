import {
  compute,
  dict,
  type CreateCrudOptionsProps,
  type CreateCrudOptionsRet,
  type UserPageQuery
} from "@fast-crud/fast-crud";
import { ElButton, ElMessage, ElMessageBox } from "element-plus";
import { h } from "vue";
import { http } from "@/utils/http";

/** 创建后台导入任务记录表；文件选择与提交动作统一由 index.vue 管理。 */
export default function ({
  crudExpose,
  context: { props }
}: CreateCrudOptionsProps): CreateCrudOptionsRet {
  const apiPrefix = props.formInline.apiPrefix;

  const pageRequest = async (params: UserPageQuery) => {
    return await http.get(`${apiPrefix}async_import/`, { params });
  };

  const confirmImport = async (ctx: any) => {
    try {
      await ElMessageBox.confirm(
        "文件已解析完成，确认后将正式写入数据。是否继续？",
        "确认导入",
        { type: "warning", confirmButtonText: "确认导入" }
      );
      const res: ApiResponse = await http.post(
        `${apiPrefix}async_import/${ctx.row.id}/confirm/`
      );
      ElMessage.success(res.message);
      crudExpose.doRefresh();
      props.formInline.ParentCrudExpose?.doRefresh();
    } catch (error: any) {
      if (error !== "cancel" && error !== "close") throw error;
    }
  };

  const cancelImport = async (ctx: any) => {
    try {
      await ElMessageBox.confirm("确定取消该后台导入任务吗？", "取消任务", {
        type: "warning",
        confirmButtonText: "确定取消"
      });
      const res: ApiResponse = await http.post(
        `${apiPrefix}async_import/${ctx.row.id}/cancel/`
      );
      ElMessage.success(res.message);
      crudExpose.doRefresh();
    } catch (error: any) {
      if (error !== "cancel" && error !== "close") throw error;
    }
  };

  const fileName = (value?: string) => {
    if (!value) return "-";
    try {
      const url = new URL(value, window.location.origin);
      return decodeURIComponent(url.pathname.split("/").pop() || value);
    } catch {
      return value;
    }
  };

  return {
    crudOptions: {
      request: { pageRequest },
      search: { show: false },
      actionbar: { show: true, buttons: { add: { show: false } } },
      toolbar: {
        show: true,
        buttons: {
          search: { show: false },
          compact: { show: false },
          export: { show: false },
          columns: { show: false }
        }
      },
      rowHandle: {
        fixed: "right",
        width: 132,
        align: "center",
        buttons: {
          view: { show: false },
          edit: { show: false },
          remove: { show: false },
          confirm: {
            text: "确认导入",
            type: "primary",
            link: true,
            show: compute(ctx => ctx.row.import_status === "PARSED"),
            click: confirmImport
          },
          cancel: {
            text: "取消",
            type: "danger",
            link: true,
            show: compute(ctx =>
              ["CREATED", "PARSING", "CONFIRMED", "IMPORTING"].includes(
                ctx.row.import_status
              )
            ),
            click: cancelImport
          }
        }
      },
      columns: {
        id: {
          title: "ID",
          type: "text",
          column: { width: 50, align: "center", show: false }
        },
        created: {
          title: "创建时间",
          column: {
            width: 140,
            align: "center",
            formatter: ({ value }) => value || "-"
          }
        },
        import_status: {
          title: "状态",
          type: "dict-select",
          dict: dict({
            data: [
              { value: "CREATED", label: "等待解析", color: "info" },
              { value: "PARSING", label: "解析中", color: "info" },
              { value: "PARSED", label: "待确认", color: "primary" },
              { value: "INPUT_ERROR", label: "数据错误", color: "warning" },
              { value: "PARSE_ERROR", label: "解析错误", color: "danger" },
              { value: "CONFIRMED", label: "已确认", color: "primary" },
              { value: "IMPORTING", label: "导入中", color: "primary" },
              { value: "IMPORTED", label: "导入成功", color: "success" },
              { value: "IMPORT_ERROR", label: "导入错误", color: "warning" },
              { value: "CANCELLED", label: "已取消", color: "info" }
            ]
          }),
          column: { width: 108, align: "center" }
        },
        "import_params.data_file": {
          title: "源文件",
          column: {
            minWidth: 300,
            showOverflowTooltip: true,
            cellRender({ value }) {
              if (!value) return "-";
              return h(
                ElButton,
                {
                  link: true,
                  type: "primary",
                  onClick: () => window.open(value, "_blank")
                },
                { default: () => fileName(value) }
              );
            }
          }
        },
        import_started: {
          title: "开始时间",
          column: {
            width: 140,
            align: "center",
            formatter: ({ value }) => value || "-"
          }
        },
        import_finished: {
          title: "完成时间",
          column: {
            width: 140,
            align: "center",
            formatter: ({ value }) => value || "-"
          }
        },
        input_errors_file: {
          title: "错误明细",
          column: {
            width: 96,
            align: "center",
            cellRender({ value }) {
              if (!value) return "-";
              return h(
                ElButton,
                {
                  link: true,
                  type: "danger",
                  onClick: () => window.open(value, "_blank")
                },
                { default: () => "下载明细" }
              );
            }
          }
        },
        error_message: {
          title: "错误描述",
          column: {
            minWidth: 180,
            showOverflowTooltip: true,
            formatter: ({ value }) => value || "-"
          }
        }
      }
    }
  };
}
