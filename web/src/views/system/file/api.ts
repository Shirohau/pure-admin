import { CreateApi } from "@/api/base";
import { http } from "@/utils/http";
import { useFileDialog } from "@vueuse/core";
import { ElMessage } from "element-plus";

export const apiPrefix = "/api/system/file/";
export const api = {
  ...CreateApi(apiPrefix)
};

const { open, onChange, reset } = useFileDialog({
  accept: ".csv, .xls, .xlsx",
  directory: false // 如果设置为 true，则选择目录而不是文件
});

onChange(files => {
  /** 处理文件 */
  if (!files?.length) return;

  // 创建 FormData 实例
  const formData = new FormData();
  formData.append("file", files[0]);

  http
    .post(
      apiPrefix,
      { data: formData },
      {
        headers: {
          "Content-Type": "multipart/form-data"
        }
      }
    )
    .then((res: ApiResponse) => {
      ElMessage.success(res.message);
    });
  reset(); // 重置文件选择
});

export const openFile = open;
