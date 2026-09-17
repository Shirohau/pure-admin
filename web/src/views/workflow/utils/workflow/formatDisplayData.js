/**
 * 审批流程设计器 - 显示数据格式化
 *
 * 来源：AntFlow-Designer（https://gitee.com/ldhnet/AntFlow-Designer）
 * 迁移适配：import 路径由 `@/utils/workflow/constant.js` 调整为 `@/views/workflow/utils/workflow/constant.js`
 *
 * 作用：将后端返回的**扁平节点列表**（nodes 数组 + nodeFrom/nodeTo 关联关系）
 * 转换为设计器画布渲染所需的**树形结构**（nodeConfig，发起人节点作为树根），
 * 并解析各节点 nodeProperty 中的 JSON 字符串为对象。
 */
import { NodeType as NodeTypeEnum } from "@/views/workflow/utils/workflow/constant.js";

/** 空值判断（仅 null/undefined/空串） */
const isEmpty = (data) => data === null || data === undefined || data === "";
/** 空数组判断 */
const isEmptyArray = (data) => (Array.isArray(data) ? data.length === 0 : true);

export class FormatDisplayUtils {
  /**
   * 格式化显示数据：扁平列表 → 树形结构
   * @param {Array} parmData 后端返回的流程定义对象（含 nodes 扁平列表）
   * @returns {Object} 含 nodeConfig（树）及流程基础字段的对象
   */
  static getToTree(parmData) {
    const node = this.createNodeDisplay(parmData);
    const formatList = this.formatDisplayStructNodeList(node.nodes);
    node.nodeConfig = this.depthConverterToTree(formatList);
    const { nodes, ...result } = node; // 移除 nodes 属性
    return result;
  }

  /**
   * 创建节点展示数据（保留基础字段，新增 nodeConfig 属性占位）
   * @param {Object} nodeData - 源节点数据
   * @returns {Object}
   */
  static createNodeDisplay(nodeData) {
    const displayObj = {
      ...nodeData,
      nodeConfig: {},
    };
    return displayObj;
  }

  /**
   * 扁平列表转换为树形结构
   * 依据 nodeFrom → nodeId 的父子关系建树；
   * 网关（GatewayNode）下的条件节点挂到 nodeProperty.conditionNodes，
   * 并行网关（ParallelApproveWayNode）下的并行审批节点挂到 nodeProperty.parallelNodes，
   * 其余节点通过 childNode 串联。
   * @param {Array} parmData 扁平节点列表
   * @returns {Object} 树根节点（发起人节点）
   */
  static depthConverterToTree(parmData) {
    if (isEmptyArray(parmData)) return;
    let nodesGroup = {},
      startNode = {};
    // 按 nodeFrom 分组，建立"父节点 id → 子节点列表"的映射
    for (const t of parmData) {
      if (nodesGroup.hasOwnProperty(t.nodeFrom)) {
        nodesGroup[t.nodeFrom].push(t);
      } else {
        nodesGroup[t.nodeFrom] = [t];
      }
    }
    for (const node of parmData) {
      // 找到发起人节点作为树根
      if (NodeTypeEnum.StartNode == node.nodeType) {
        startNode = node;
      }
      // 网关节点初始化 conditionNodes 容器
      if (NodeTypeEnum.GatewayNode == node.nodeType) {
        Object.assign(node, { nodeProperty: { conditionNodes: [] } });
      }
      // 并行网关节点初始化 parallelNodes 容器
      if (NodeTypeEnum.ParallelApproveWayNode == node.nodeType) {
        Object.assign(node, { nodeProperty: { parallelNodes: [] } });
      }
      // 将该节点的所有子节点挂载到对应位置
      const currNodeId = node.nodeId;
      if (nodesGroup.hasOwnProperty(currNodeId)) {
        const itemNodes = nodesGroup[currNodeId];
        for (const itemNode of itemNodes) {
          if (NodeTypeEnum.ConditionNode == itemNode.nodeType) {
            node.nodeProperty.conditionNodes.push(itemNode);
          } else {
            Object.assign(node, { childNode: itemNode });
            //node.childNode = itemNode;
          }
        }
      }
    }
    return startNode;
  }

  /**
   * 解析节点列表中的 nodeProperty JSON 字符串为对象
   * （后端存储的 nodeProperty 为字符串，设计器需要对象）
   * @param {Array} nodeList 扁平节点列表
   * @returns {Array}
   */
  static formatDisplayStructNodeList(nodeList) {
    if (isEmptyArray(nodeList)) return nodeList;
    for (const node of nodeList) {
      if (node && node.nodeProperty) {
        if (
          !isEmpty(node.nodeProperty) &&
          typeof node.nodeProperty !== "object"
        ) {
          node.nodeProperty = JSON.parse(node.nodeProperty);
        }
      }
    }
    return nodeList;
  }
}
