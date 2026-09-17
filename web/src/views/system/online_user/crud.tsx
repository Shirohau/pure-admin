import type {
  CreateCrudOptionsProps,
  CreateCrudOptionsRet,
  UserPageQuery
} from "@fast-crud/fast-crud";
import { api } from "./api";

// 定义组件名称
export const componentName = "OnlineUserView";

/**
 * 定义一个CrudOptions生成器方法
 */
export default function crudOptions({
  crudExpose
}: CreateCrudOptionsProps): CreateCrudOptionsRet {
  /** 列表查询 */
  const pageRequest = async (query: UserPageQuery) => {
    return await api.GetList(query);
  };

  return {
    crudOptions: {
      // 请求相关配置
      request: {
        pageRequest
      },
      // 表格配置
      table: {
        rowKey: "user_id" //设置你的主键id， 默认rowKey=id
      },
      // 动作条配置
      actionbar: { show: false },
      // 工具条配置
      toolbar: {
        buttons: {
          search: { show: false },
          export: { show: false }
        }
      },
      // 查询
      search: { show: false },
      // 操作列配置
      rowHandle: {
        buttons: {
          view: { show: false },
          edit: { show: false },
          remove: { show: false },
          blacklist: {
            text: "强制下线",
            type: "danger",
            click: async ({ row }) => {
              await api.Blacklist(row.user_id);
              crudExpose.doRefresh();
            }
          }
        }
      },

      // 字段复合配置
      columns: {
        $expand: {
          title: "展开",
          form: { show: false },
          column: {
            type: "expand",
            align: "center",
            width: "55px",
            columnSetDisabled: true //禁止在列设置中选择
          }
        },
        user_id: {
          title: "用户ID",
          type: "text"
        },
        username: {
          title: "账号",
          type: "text"
        },
        name: {
          title: "用户",
          type: "text"
        },
        session_count: {
          title: "会话数",
          type: "text"
        }
      }
    }
  };
}
