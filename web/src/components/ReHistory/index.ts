import { shallowRef } from "vue";
import reHistory from "./src/index.vue";
import { withInstall } from "@pureadmin/utils";
import { addDialog } from "../ReDialog";

/**
 * 历史记录组件配置项（与组件内 FormProps.formInline 结构保持一致）
 */
export interface HistoryOptions {
  /** 接口前缀（含对象主键，如 `/api/v1/publisher/1/`） */
  apiPrefix: string;
  /** 是否允许恢复历史版本，默认 false */
  restartAuth?: boolean;
  /** 列表区域高度：默认 auto（自适应内容，上限 calc(100vh - 200px) 可滚动），可传 "70vh"、"400px" 等固定值 */
  height?: string;
}

/**
 * 生成「操作记录」子表列配置（嵌入 fast-crud 列表，点击行展开显示历史时间线）
 * @param options 配置项，formInline 支持静态对象或 fast-crud 的 compute 动态计算
 */
// formInline 经 fast-crud 透传，运行时可能是 compute 动态计算值，故类型放宽为 any
export const historyTable = ({ formInline }: { formInline: any }) => {
  return {
    title: "操作记录",
    width: 130,
    type: ["number", "colspan"],
    addForm: { show: false },
    form: {
      labelWidth: "0px",
      col: { span: 24 },
      component: {
        name: shallowRef(reHistory),
        vModel: "modelValue",
        formInline
      }
    },

    column: {
      show: false,
      // 在列设置中不显示该字段
      columnSetShow: false
    }
  };
};

/**
 * 打开历史记录弹窗
 * @param options 历史记录配置（apiPrefix 必填，restartAuth / height 可选）
 */
export const openHistoryDialog = (options: HistoryOptions) => {
  const { apiPrefix, restartAuth, height } = options;
  addDialog({
    width: "70%",
    title: "历史记录",
    hideFooter: true,
    props: {
      // 统一以 formInline 形式注入组件配置（组件内会合并默认值）
      formInline: {
        apiPrefix,
        restartAuth,
        height
      }
    },
    contentRenderer: () => ReHistory
  });
};

/** 历史记录组件（支持按需安装） */
export const ReHistory = withInstall(reHistory);
export default ReHistory;
