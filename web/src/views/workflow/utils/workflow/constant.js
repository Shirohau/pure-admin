/**
 * 审批流程设计器 - 常量定义
 *
 * 来源：AntFlow-Designer（https://gitee.com/ldhnet/AntFlow-Designer）
 * 迁移适配：import 路径由 `@/utils/workflow/` 调整为 `@/views/workflow/utils/workflow/`
 *
 * 本文件集中定义流程设计器涉及的各类枚举常量：
 * - NodeType：节点类型枚举（发起人/条件网关/条件/审批人/并行网关/抄送人/并行审批人）
 * - placeholderList：各节点类型的占位提示文案（发布校验时用于错误提示）
 * - optTypes / opt1s：条件节点比较运算符选项
 * - bizFormMaps：流程编号与自定义表单路径的映射（对接后端自定义表单时使用）
 * - messageSendTypeList：消息发送渠道选项（邮件/短信/app推送/企微/钉钉/飞书）
 */
export const NodeType = Object.freeze({
  StartNode: 1, // 开始节点
  GatewayNode: 2, // 条件网关
  ConditionNode: 3, // 条件节点
  ApproveNode: 4, // 审批人
  ParallelApproveWayNode: 5, // 并行审核网关
  CopyNode: 6, // 抄送人
  ParallelApproveNode: 7, // 并行审核人
});

/** 各节点类型的占位提示文案（节点未配置时显示"请选择xxx"） */
export const placeholderList = Object.freeze({
  [NodeType.StartNode]: "发起人",
  [NodeType.GatewayNode]: "条件", // 网关
  [NodeType.ConditionNode]: "条件",
  [NodeType.ApproveNode]: "审核人",
  [NodeType.ParallelApproveWayNode]: "并行审核人", // 网关
  [NodeType.CopyNode]: "抄送人",
  [NodeType.ParallelApproveNode]: "并行审核人",
});

/** 条件比较运算符选项（conditionDrawer 条件配置使用） */
export let optTypes = [
  { value: 1, label: "小于" },
  { value: 2, label: "大于" },
  { value: 3, label: "小于等于" },
  { value: 4, label: "等于" },
  { value: 5, label: "大于等于" },
  { value: 6, label: "介于两个数之间" },
];

/** 介于两个数之间时的上界运算符选项 */
export let opt1s = [
  { value: "<", label: "<" },
  { value: "≤", label: "≤" },
];

/**
 * 自定义表单路径与 processKey 映射
 * 当流程绑定了自定义表单（非 vForm 动态表单）时，根据流程编号找到对应表单组件路径
 */
export const bizFormMaps = new Map([
  ["DSFZH_WMA", "/forms/form1.vue"],
  ["LEAVE_WMA", "/forms/form2.vue"],
  ["UCARREFUEl_WMA", "/forms/form3.vue"],
  ["PURCHASE_WMA", "/forms/form4.vue"],
  ["BXSP_WMA", "/forms/form5.vue"],
]);

/** 消息发送渠道选项列表（节点消息通知配置使用） */
export const messageSendTypeList = [
  {
    active: false,
    id: 1,
    name: "邮件",
  },
  {
    active: false,
    id: 2,
    name: "短信",
  },
  {
    active: false,
    id: 3,
    name: "app推送",
  },
  {
    active: false,
    id: 5,
    name: "企微",
  },
  {
    active: false,
    id: 6,
    name: "钉钉",
  },
  {
    active: false,
    id: 7,
    name: "飞书",
  },
];
