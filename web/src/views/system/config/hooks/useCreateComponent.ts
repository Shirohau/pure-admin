import { useMerge } from "@fast-crud/fast-crud";
import { api as file_api } from "@/views/system/file/api";
import { api } from "../api";
/**
 * [策略映射表]
 */
const VALUE_COMPONENT_MAP: Record<string, () => any> = {
  text: () => ({
    label: "单行文本",
    name: "el-input",
    props: {
      type: "text",
      clearable: true,
      placeholder: "请输入内容"
    }
  }),
  textarea: () => ({
    label: "多行文本",
    name: "el-input",
    props: {
      type: "textarea",
      rows: 5,
      clearable: true,
      showWordLimit: true,
      maxlength: 2000
    }
  }),
  number: () => ({
    label: "数字",
    name: "el-input-number",
    props: { style: { width: "100%" }, precision: 2 }
  }),
  date: () => ({
    label: "日期",
    name: "el-date-picker",
    props: {
      type: "date",
      style: { width: "100%" },
      valueFormat: "YYYY-MM-DD"
    }
  }),
  time: () => ({
    label: "时间",
    name: "el-time-picker",
    props: {
      style: { width: "100%" },
      valueFormat: "hh:mm:ss"
    }
  }),
  switch: () => ({
    label: "开关",
    name: "el-switch",
    props: {
      activeText: "开启",
      inactiveText: "关闭"
    }
  }),
  select: () => ({
    label: "选择",
    name: "fs-dict-select",
    props: {
      style: { width: "100%" },
      options: [
        // { value: "CREATED", label: "创建成功" },
        // { value: "EXPORTING", label: "导出中" },
        // { value: "EXPORT_ERROR", label: "导出错误" },
        // { value: "EXPORTED", label: " 导出成功" },
        // { value: "CANCELLED", label: " 已取消" }
      ]
    }
  }),
  image: () => ({
    label: "图片",
    name: "fs-file-uploader",
    listType: "picture-card",
    accept: ".png,.jpeg,.jpg,.ico,.bmp,.gif,.webp,.svg",
    limit: 1,
    uploader: {
      type: "form",
      data: {
        folder: "config"
      }
    },
    valueType: "row",
    on: {
      change: (context: any) => {
        if (context.value != null) {
          // 新增
          context.form.image_id = context.value.id;
        } else {
          // 删除
          file_api.DeleteObj(context.row.value.id);
          api.UpdateObj(context.row.id, { value: null }, false);
        }
      }
    }
  })
};

/**
 * 根据 VALUE_COMPONENT_MAP 动态生成下拉字典数据
 */
const getFormTypeDictData = () => {
  return Object.keys(VALUE_COMPONENT_MAP).map(key => {
    const config = VALUE_COMPONENT_MAP[key](); // 执行工厂函数获取配置
    return {
      label: config.label || key, // 优先使用配置的 label，如果没有则用 key
      value: key // key 就是 form_type 的值 (如 "text", "number")
    };
  });
};

/**
 * 清洗配置对象：移除所有以数字开头的 key，防止 Vue 渲染时报 DOMException
 */
const sanitizeSetting = (obj: any): any => {
  if (!obj || typeof obj !== "object" || Array.isArray(obj)) {
    return obj;
  }

  const result: any = {};

  for (const key in obj) {
    if (Object.prototype.hasOwnProperty.call(obj, key)) {
      // 【核心逻辑】如果 key 以数字开头，直接跳过（不拷贝到结果中）
      if (/^\d/.test(key)) {
        console.warn(
          `[ConfigSanitize] 检测到非法配置项 "${key}"，已自动忽略以防止渲染报错。`,
          obj[key]
        );
        continue;
      }

      // 递归处理嵌套对象 (例如 setting.props 内部也可能有非法 key)
      if (typeof obj[key] === "object" && obj[key] !== null) {
        result[key] = sanitizeSetting(obj[key]);
      } else {
        result[key] = obj[key];
      }
    }
  }

  return result;
};
/**
 * 获取组件配置
 */
const getValueFormComponent = (context: any) => {
  const { form } = context;
  const generator =
    VALUE_COMPONENT_MAP[form.form_type] || VALUE_COMPONENT_MAP["text"];

  const { merge } = useMerge();
  const baseConfig = generator();
  const userConfig = merge(baseConfig, sanitizeSetting(form.setting));
  if (form.form_type === "image") {
    // 添加 buildUrl
    userConfig.buildUrl = () => {
      return context.form.value.path;
    };
  }

  // 合并配置
  return userConfig;
};

export function useCreateComponent() {
  return {
    getValueFormComponent,
    getFormTypeDictData
  };
}
