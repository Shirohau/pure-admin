import { addDialog } from "../ReDialog";
import reImport from "./src/index.vue";
import { withInstall } from "@pureadmin/utils";
export const openImportDialog = (
  apiPrefix: string,
  ParentCrudExpose: any = undefined
) => {
  addDialog({
    width: "min(1180px, 92vw)",
    title: "导入",
    hideFooter: true,
    style: { height: "78vh" },
    props: {
      // 赋默认值
      formInline: {
        apiPrefix,
        ParentCrudExpose
      }
    },
    contentRenderer: () => ReImport
  });
};
/** 导入组件 */
export const ReImport = withInstall(reImport);

export default ReImport;
