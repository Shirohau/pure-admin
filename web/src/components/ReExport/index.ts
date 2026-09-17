import { addDialog } from "../ReDialog";
import reExport from "./src/index.vue";
import { withInstall } from "@pureadmin/utils";
import type { CrudExpose } from "@fast-crud/fast-crud";

/**
 * 打开导出组件弹窗
 * @param apiPrefix API前缀，用于指定导出接口的路径
 * @param crudExpose fast-crud 的 crudExpose 实例，内部自动获取搜索参数并执行 valueResolve 转换
 * @param options 额外配置，如 defaultExportMode 指定默认导出模式（"sync" | "async"）
 */
export const openExportDialog = (
  apiPrefix: string,
  crudExpose?: CrudExpose,
  options?: { defaultExportMode?: "sync" | "async" }
) => {
  // getSearchFormData 返回原始表单数据，尚未执行日期范围、级联选择等 valueResolve 转换。
  let query_params = {};
  if (crudExpose) {
    const rawForm = crudExpose.getSearchFormData();
    query_params = { ...rawForm };
    // 必须显式传入搜索列配置；默认表格列配置无法找到搜索字段的 valueResolve。
    crudExpose.doValueResolve(
      { form: query_params },
      crudExpose.crudBinding.value.search.columns
    );
  }

  // 使用视口约束宽度，在常规桌面和窄屏设备上都保留安全边距。
  addDialog({
    width: "min(1320px, 92vw)",
    title: "导出",
    hideFooter: true,
    style: { height: "78vh" },
    props: {
      formInline: {
        apiPrefix,
        query_params,
        defaultExportMode: options?.defaultExportMode
      }
    },
    contentRenderer: () => ReExport
  });
};
/** 导出组件 */
export const ReExport = withInstall(reExport);

export default ReExport;
