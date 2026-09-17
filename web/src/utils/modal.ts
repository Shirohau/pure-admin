import { ElMessage, ElMessageBox, ElNotification } from "element-plus";

/**
 * 全局 $modal 工具（兼容 AntFlow-Designer 组件对 proxy.$modal 的调用）
 * 用法：proxy.$modal.msgSuccess / msgError / confirm 等
 */
export const Modal = {
  /** 消息提示 */
  msg(msg: string) {
    ElMessage.info(msg);
  },
  /** 错误消息 */
  msgError(msg: string) {
    ElMessage.error(msg);
  },
  /** 成功消息 */
  msgSuccess(msg: string) {
    ElMessage.success(msg);
  },
  /** 警告消息 */
  msgWarning(msg: string) {
    ElMessage.warning(msg);
  },
  /** 通知 */
  notify(content: string) {
    ElNotification.info({ title: "提示", message: content });
  },
  /** 确认框 */
  confirm(content: string, tip: string = "系统提示") {
    return ElMessageBox.confirm(content, tip, {
      confirmButtonText: "确定",
      cancelButtonText: "取消",
      type: "warning"
    });
  },
  /** 提交内容 */
  prompt(content: string, tip: string = "系统提示") {
    return ElMessageBox.prompt(content, tip, {
      confirmButtonText: "确定",
      cancelButtonText: "取消",
      type: "warning"
    });
  }
};
