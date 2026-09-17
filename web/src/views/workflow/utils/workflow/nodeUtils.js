/**
 * 审批流程设计器 - 节点工厂工具
 *
 * 来源：AntFlow-Designer（https://gitee.com/ldhnet/AntFlow-Designer）
 * 迁移适配：import 路径由 `@/utils/workflow/constant.js` 调整为 `@/views/workflow/utils/workflow/constant.js`
 *
 * 作用：提供流程节点的统一创建工厂方法，
 * 包括节点 id 生成、各类节点（发起人/审批人/抄送人/条件网关/并行网关等）的默认数据结构。
 */
//import {  NodeUtils } from '@/utils/nodeUtils'

import { version } from "vue";
import { NodeType as NodeTypeEnum } from "@/views/workflow/utils/workflow/constant.js";

export class NodeUtils {
  /**
   * 根据时间戳自增数生成 64 进制 id（全局唯一节点 id）
   * @returns {string} 64 进制 id 字符串
   */
  static idGenerator() {
    let qutient = new Date() - new Date("2024-05-01");
    qutient += Math.ceil(Math.random() * 1000); // 防止重复
    const chars =
      "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz";
    const charArr = chars.split("");
    const radix = chars.length;
    const res = [];
    do {
      let mod = qutient % radix;
      qutient = (qutient - mod) / radix;
      res.push(charArr[mod]);
    } while (qutient);
    return res.join("").toUpperCase();
  }

  /**
   * 初始化流程数据（新建流程时的默认值，含发起人起始节点）
   * @returns {Object} 流程定义对象
   */
  static initNode() {
    const initNodesObj = {
      name: "请假申请流程",
      key: "BIZ_RTWHMN",
      flowCode: "BIZ_QA",
      frmType: 1,
      frmValue:
        '{"widgetList":[],"formConfig":{"modelName":"formData","refName":"vForm","rulesName":"rules","labelWidth":80,"labelPosition":"left","size":"","labelAlign":"label-left-align","cssCode":"","customClass":[],"functions":"","layoutType":"PC","jsonVersion":3,"onFormCreated":"","onFormMounted":"","onFormDataChange":""}}',
      frmUrl: "",
      distinctType: 1,
      isActive: true,
      version: "1.0",
      Remark: "",
      formData: null,
      nodes: [
        {
          nodeId: "Gb2",
          nodeName: "发起人",
          nodeDisplayName: "发起人",
          nodeType: NodeTypeEnum.StartNode,
          nodeFrom: "",
          nodeTo: ["4FIHMN"],
          nodeWeight: 0,
          nodeProperty: null,
          error: false,
        },
      ],
    };
    return initNodesObj;
  }

  /**
   * 创建基础节点（各节点公共字段）
   * @param {Object} param0 节点字段（名称/类型/权重/子节点等）
   * @returns {Object} 基础节点对象
   */
  static createBaseNode({
    nodeName = "",
    nodeDisplayName = nodeName,
    nodeType,
    nodeFrom = "",
    nodeTo = [],
    nodeWeight = 0,
    childNode = null,
    error = true,
  }) {
    return {
      nodeId: this.idGenerator(),
      nodeName,
      nodeDisplayName,
      nodeType,
      nodeFrom,
      nodeTo,
      nodeWeight,
      childNode,
      error,
    };
  }

  /**
   * 创建审批人基础节点（含默认属性：审批方式/会签方式/字段权限/按钮权限）
   * @param {Object} param0 nodeType 节点类型、childNode 后继节点
   * @returns {Object} 审批人节点对象
   */
  static createApproveBaseNode({ nodeType, childNode }) {
    const approveNode = {
      ...this.createBaseNode({
        nodeName: "审核人",
        nodeDisplayName: "审核人",
        nodeType: nodeType || NodeTypeEnum.ApproveNode,
        childNode: childNode,
      }),
      nodeProperty: {
        assigneeType: 1, // 审批人类型（1 指定人员）
        signType: 1, // 会签方式（1 或签 / 2 会签 / 3 顺序会签）
        noHeaderAction: 1,
        directorLevel: 0, // 主管层级 1、直属主管 2、上级主管 3、最高主管
        IsDistinct: 0, // 是否去重 1、去重 0、不去重
        sort: 0,
        assigneeList: [], // 审批人列表
        fieldPrems: [], // 字段权限
        buttons: {
          startPage: [1],
          approvalPage: [3, 4],
          viewPage: [0],
        },
      },
    };
    return approveNode;
  }

  /**
   * 创建审批人节点（普通审批）
   * @param {Object} child 后继节点
   * @returns {Object}
   */
  static createApproveNode(child) {
    const approveNode = {
      ...this.createApproveBaseNode({
        nodeType: NodeTypeEnum.ApproveNode,
        childNode: child,
      }),
    };
    return approveNode;
  }

  /**
   * 创建并行审批人节点（并行网关下的审批分支节点）
   * @param {Object} child 后继节点
   * @returns {Object}
   */
  static createParallelApproveNode(child) {
    const approveNode = {
      ...this.createApproveBaseNode({
        nodeType: NodeTypeEnum.ParallelApproveNode,
        childNode: child,
      }),
    };
    return approveNode;
  }

  /**
   * 创建并行网关节点（默认含两个并行审批分支）
   * @param {Object} child 后继节点
   * @returns {Object} 并行网关节点对象
   */
  static createParallelWayNode(child) {
    const parallelwayNode = {
      ...this.createBaseNode({
        nodeName: "并行审核网关",
        nodeType: NodeTypeEnum.ParallelApproveWayNode,
        nodeWeight: 1,
        childNode: this.createParallelApproveNode(null),
        error: false,
      }),
      nodeProperty: {
        parallelNodes: [
          this.createParallelApproveNode(child),
          this.createParallelApproveNode(null),
        ],
        assigneeType: 1,
        signType: 1,
        noHeaderAction: 1,
        directorLevel: 0, // 主管层级 1、直属主管 2、上级主管 3、最高主管
        IsDistinct: 0, // 是否去重 1、去重 0、不去重
        sort: 0,
        assigneeList: [],
        fieldPrems: [], // 字段权限
        buttons: {
          startPage: [1],
          approvalPage: [3, 4],
          viewPage: [0],
        },
      },
    };
    return parallelwayNode;
  }

  /**
   * 创建抄送人节点
   * @param {Object} child 后继节点
   * @returns {Object} 抄送人节点对象
   */
  static createCopyNode(child) {
    const copyNode = {
      ...this.createBaseNode({
        nodeName: "抄送人",
        nodeDisplayName: "抄送人",
        nodeType: NodeTypeEnum.CopyNode,
        childNode: child,
      }),
      nodeProperty: {
        assigneeType: 1,
        ccFlag: 0, // 抄送标志
        fieldPrems: [], // 字段权限
        assigneeList: [],
        buttons: {
          startPage: [],
          approvalPage: [],
          viewPage: [],
        },
      },
    };
    return copyNode;
  }

  /**
   * 创建条件网关节点（默认含"条件1"与"默认条件分支"两个分支）
   * @param {Object} child 后继节点
   * @returns {Object} 网关节点对象
   */
  static createGatewayNode(child) {
    const gatewayNode = {
      ...this.createBaseNode({
        nodeName: "网关",
        nodeType: NodeTypeEnum.GatewayNode,
        nodeWeight: 1,
        error: false,
      }),
      nodeProperty: {
        groupRelation: false, // 审批组关系 true 且 false 或
        isDefault: 0, // 是否默认分支 1、默认 0、非默认
        sort: 0,
        conditionNodes: [
          this.createConditionNode("条件1", child, 1, 0),
          this.createConditionNode("默认条件分支", null, 2, 1),
        ],
      },
    };
    return gatewayNode;
  }

  /**
   * 创建动态网关对象（预留，暂未实现）
   * @returns {Object} 空对象
   */
  static createDynamicConditionWayNode(child) {
    const dynamicGatewayNode = {};
    return dynamicGatewayNode;
  }

  /**
   * 创建条件并行网关对象（预留，暂未实现）
   * @returns {Object} 空对象
   */
  static createParallelConditionWayNode(child) {
    const gatewayNode = {};
    return gatewayNode;
  }

  /**
   * 创建条件节点（网关分支）
   * @param {string} name 条件名称
   * @param {Object} childNode 后继节点
   * @param {number} nodeWeight 优先级权重
   * @param {number} isDefault 是否默认分支（1 默认）
   * @returns {Object} 条件节点对象
   */
  static createConditionNode(name, childNode, nodeWeight, isDefault) {
    const conditionNode = {
      ...this.createBaseNode({
        nodeName: name || "条件1",
        nodeDisplayName: name || "条件1",
        nodeType: NodeTypeEnum.ConditionNode,
        nodeWeight,
        childNode: childNode,
        error: isDefault !== 1, // 默认分支无需配置条件，非默认分支需要配置
      }),
      nodeProperty: {
        groupRelation: false, // 审批组关系 true 且 false 或
        isDefault: isDefault || 0,
        groupConditions: [
          {
            groupId: "groupid1",
            condRelation: true, // 条件关系 true 且 false 或
            sort: 0,
            conditionList: [],
          },
        ],
      },
    };
    return conditionNode;
  }

  /**
   * 创建条件判断对象（条件表达式单条记录）
   * @param {string} key 字段 key
   * @param {string} label 显示名称
   * @param {string} type 字段类型
   * @param {string} columnDbName DB 字段名称
   * @param {string} columnType DB 字段类型
   * @param {string} fixedDownBoxValue 固定下拉选项值
   * @returns {Object} 条件判断对象
   */
  static createJudgeNode(
    key,
    label,
    type,
    columnDbName,
    columnType,
    fixedDownBoxValue,
  ) {
    const judgeNode = {
      key: key,
      label: label,
      type: type,
      optType: "=", // 比较运算符
      zdy1: "", // 自定义值 1
      opt1: "<",
      zdy2: "", // 自定义值 2（介于两数之间时使用）
      opt2: "<",
      columnDbName: columnDbName,
      columnType: columnType,
      fixedDownBoxValue: fixedDownBoxValue,
    };
    return judgeNode;
  }
}

/**
 * 添加模拟数据（预留方法）
 */
export function getMockData() {
  const startNode = ""; //NodeUtils.createNode("start", "");
  return startNode;
}
