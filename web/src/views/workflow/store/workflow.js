/**
 * 审批流程设计器 - Pinia 全局状态
 *
 * 来源：AntFlow-Designer（https://gitee.com/ldhnet/AntFlow-Designer）
 *
 * 作用：跨组件共享设计器运行时状态：
 * - 各节点配置抽屉（审批人/抄送人/条件）的打开状态与待编辑配置
 * - 动态表单（vForm）设计过程中同步的字段列表（lowCodeFormField，供条件配置引用）
 * 组件中通过 `useWorkflowStore()` 获取实例。
 */
import { defineStore } from "pinia";

export const useWorkflowStore = defineStore("workflowStore", {
  state: () => ({
    /** 当前操作人 id（预留，对接后端后使用） */
    userId: "",
    /** 发起人节点配置抽屉可见性 */
    promoterDrawer: false,
    /** 发起人节点配置（预留） */
    promoterConfig: {},
    /** 审批人节点配置抽屉可见性 */
    approverDrawer: false,
    /** 当前正在编辑的审批人节点配置 */
    approverConfig: {},
    /** 抄送人节点配置抽屉可见性 */
    copyerDrawer: false,
    /** 当前正在编辑的抄送人节点配置 */
    copyerConfig: {},
    /** 条件节点配置抽屉可见性 */
    conditionDrawer: false,
    /** 当前正在编辑的条件节点配置 */
    conditionsConfig: {},
    /** vForm 动态表单设计过程中的字段列表（条件配置的数据源） */
    lowCodeFormField: {},
  }),
  actions: {
    /** 设置当前操作人 id */
    setUserId(payload) {
      this.userId = payload;
    },
    /** 设置发起人抽屉可见性 */
    setPromoter(payload) {
      this.promoterDrawer = payload;
    },
    /** 设置发起人节点配置 */
    setPromoterConfig(payload) {
      this.promoterConfig = payload;
    },
    /** 设置审批人抽屉可见性 */
    setApprover(payload) {
      this.approverDrawer = payload;
    },
    /** 设置当前编辑的审批人节点配置 */
    setApproverConfig(payload) {
      this.approverConfig = payload;
    },
    /** 设置抄送人抽屉可见性 */
    setCopyer(payload) {
      this.copyerDrawer = payload;
    },
    /** 设置当前编辑的抄送人节点配置 */
    setCopyerConfig(payload) {
      this.copyerConfig = payload;
    },
    /** 设置条件抽屉可见性 */
    setCondition(payload) {
      this.conditionDrawer = payload;
    },
    /** 设置当前编辑的条件节点配置 */
    setConditionsConfig(payload) {
      this.conditionsConfig = payload;
    },
    /** 同步 vForm 动态表单字段列表 */
    setLowCodeFormField(payload) {
      this.lowCodeFormField = payload;
    },
  },
});
