/**
 * 审批流程设计器 - 表单接口（字段权限数据源）
 *
 * 来源：AntFlow-Designer（https://gitee.com/ldhnet/AntFlow-Designer）
 * 迁移适配：
 * 1. import 路径由 @/store/modules/workflow 调整为 @/views/workflow/store/workflow.js
 *
 * 作用：提供"表单字段权限"配置的数据源抽象，便于集成不同的表单系统。
 * 从 Pinia store 中读取 vForm 动态表单设计的字段列表（lowCodeFormField），
 * 转换为 { fieldId, fieldName, perm } 结构的权限列表，供 fieldPerm/index.vue 渲染。
 * showFields/hideFields/disableFields/enableFields 为运行时控制预留接口。
 */
import { ref } from "vue";
import { useWorkflowStore } from "@/views/workflow/store/workflow.js";
let store = useWorkflowStore();
export const formRef = ref(null);
//表单内每个字段ID，与对应字段的配置
export const formItemMap = new Map();
// //表单字段列表
// export const formFields = computed(() => store.lowCodeFormField)

// watch(formFields, () => {
//   getFormPermFields();
// }, {deep: true})

/**
 * 获取表单字段列表
 * @param {string} defaultPerm 默认权限（R 只读 / E 可编辑 / H 隐藏）
 * @returns {Array<{fieldId: string, fieldName: string, perm: string}>} 字段权限列表
 */
export const getFormPermFields = (defaultPerm = "R") => {
  const items = [];
  //formItemMap.clear() //清空map
  const addItem = (item) => {
    items.push({
      fieldId: item.name,
      //key: item.name,
      fieldName: `${item.label}`,
      //required: item.required,
      perm: item.perm ? item.perm : defaultPerm,
    });
  };
  loadFormItem(store.lowCodeFormField, addItem);
  return items;
};

/**
 * 加载表单组件选项
 * @param {Object} obj 表单字段对象（VForm 导出的 { formFields: [] }）
 * @param {Function} addItemFunc 添加的函数
 */
const loadFormItem = (obj, addItemFunc) => {
  if (!obj.formFields) {
    return;
  }
  if (Array.isArray(obj.formFields)) {
    obj.formFields.forEach((item) => {
      addItemFunc(item.options);
    });
  }
  //formItemMap.set(item.id, item)
};
/**
 * 显示表单字段
 * @param {Array} fieldIds 字段id列表
 */
export function showFields(fieldIds) { }

/**
 * 隐藏表单字段
 * @param {Array} fieldIds 字段id列表
 */
export function hideFields(fieldIds) { }

/**
 * 禁用表单字段
 * @param {Array} fieldIds 字段id列表
 */
export function disableFields(fieldIds) { }

/**
 * 允许编辑表单字段
 * @param {Array} fieldIds 字段id列表
 */
export function enableFields(fieldIds) { }
