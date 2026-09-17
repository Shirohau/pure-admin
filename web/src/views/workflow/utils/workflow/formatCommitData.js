/**
 * 审批流程设计器 - 提交数据格式化
 *
 * 来源：AntFlow-Designer（https://gitee.com/ldhnet/AntFlow-Designer）
 * 迁移适配：import 路径由 `@/utils/workflow/constant.js` 调整为 `@/views/workflow/utils/workflow/constant.js`
 *
 * 作用：与 formatDisplayData 相反，发布流程时将设计器的**树形节点结构**
 * 还原为后端存储所需的**扁平节点列表**（nodes 数组 + nodeFrom/nodeTo 关联关系），
 * 并将各节点 nodeProperty 对象序列化为 JSON 字符串。
 */
import { NodeType } from "@/views/workflow/utils/workflow/constant.js";
// import { NodeUtils } from '@/utils/nodeUtils'

/** 空值判断 */
const isEmpty = (data) => data === null || data === undefined || data === "";
/** 空数组判断 */
const isEmptyArray = (data) => (Array.isArray(data) ? data.length === 0 : true);

export class FormatUtils {
  /**
   * 对基础设置、高级设置等设置页内容进行格式化（树 → 扁平列表）
   * @param {Object} param 树形流程节点数据（发起人节点为树根）
   * @returns {Array} 扁平节点列表（nodeProperty 已序列化为字符串）
   */
  static formatSettings(param) {
    const cloneParam = JSON.parse(JSON.stringify(param));
    console.log("cloneParam===", { ...cloneParam });
    const treeList = this.flattenMapTreeToList(cloneParam);
    const combinationList = this.getEndpointNodeId(treeList);
    const finalList = this.cleanNodeList(combinationList);
    return finalList;
  }

  /**
   * 展平树结构：递归遍历节点树，补充 nodeFrom/nodeTo 关系，删除 childNode
   * @param {Object} treeData - 树形节点数据
   * @returns {Array} 节点数组
   */
  static flattenMapTreeToList(treeData) {
    const nodeData = [];
    function traverse(node) {
      // 条件网关：条件分支挂 conditionNodes，其余子节点挂 childNode
      if (node.nodeType == NodeType.GatewayNode) {
        if (node.childNode) {
          node.childNode.nodeFrom = node.nodeId;
          traverse(node.childNode);
        }
        // 条件节点数组：设置 nodeFrom，并写入网关的 nodeTo
        if (!isEmptyArray(node.nodeProperty?.conditionNodes)) {
          for (const child of node.nodeProperty?.conditionNodes) {
            child.nodeFrom = node.nodeId;
            traverse(child);
          }
          node.nodeTo = node.nodeProperty?.conditionNodes.map(
            (item) => item.nodeId,
          );
          delete node.nodeProperty?.conditionNodes;
        }
      } else if (node.nodeType == NodeType.ParallelApproveWayNode) {
        // 并行网关：并行审批分支挂 parallelNodes，其余子节点挂 childNode
        if (node.childNode) {
          node.childNode.nodeFrom = node.nodeId;
          traverse(node.childNode);
        }
        if (!isEmptyArray(node.nodeProperty?.parallelNodes)) {
          for (const child of node.nodeProperty?.parallelNodes) {
            child.nodeFrom = node.nodeId;
            traverse(child);
          }
          node.nodeTo = node.nodeProperty?.parallelNodes.map(
            (item) => item.nodeId,
          );
          delete node.nodeProperty?.parallelNodes;
        }
      } else if (node.childNode) {
        // 普通节点：串联 childNode
        node.nodeTo = [node.childNode.nodeId];
        node.childNode.nodeFrom = node.nodeId;
        traverse(node.childNode);
      }
      delete node.childNode;
      nodeData.push(node);
    }
    traverse(treeData);
    return nodeData;
  }

  /**
   * 递归处理网关节点下属子节点的 nodeTo 数据
   * 使网关各条件分支的"末端节点"指向网关汇聚后的公共子节点（comNode）
   * @param {Array} parmData - 节点关系数组
   * @returns {Array}
   */
  static getEndpointNodeId(parmData) {
    if (isEmptyArray(parmData)) return parmData;

    // 找出所有条件网关节点
    const getwayList = parmData.filter((c) => {
      return c.nodeType == NodeType.GatewayNode;
    });

    if (isEmptyArray(getwayList)) return parmData;

    // 按 nodeFrom 分组
    const nodesGroup = {};
    for (const t of parmData) {
      if (nodesGroup.hasOwnProperty(t.nodeFrom)) {
        nodesGroup[t.nodeFrom].push(t);
      } else {
        nodesGroup[t.nodeFrom] = [t];
      }
    }
    for (const getway of getwayList) {
      if (nodesGroup.hasOwnProperty(getway.nodeId)) {
        const itemNodes = nodesGroup[getway.nodeId];
        // 网关后的公共子节点（非条件节点的那个）
        const comNode = itemNodes.find((c) => {
          return c.nodeType != NodeType.ConditionNode;
        });
        if (!comNode) continue;
        // 各条件分支
        const conditionList = itemNodes.filter((c) => {
          return c.nodeId != comNode.nodeId;
        });
        for (const itemNode of conditionList) {
          // 递归找到每个条件分支的末端节点，将 nodeTo 指向公共子节点
          function internalTraverse(info) {
            if (info) {
              if (!nodesGroup[info.nodeId]) {
                info.nodeTo = [comNode.nodeId];
              } else {
                const tempNode = nodesGroup[info.nodeId];
                if (Array.isArray(tempNode)) {
                  for (const t_item of tempNode) {
                    internalTraverse(t_item);
                  }
                } else {
                  internalTraverse(tempNode);
                }
              }
            }
          }
          internalTraverse(itemNode);
        }
      }
    }
    return parmData;
  }

  /**
   * 清理节点数据：nodeTo 去重、过滤无效 id、nodeProperty 对象序列化为 JSON 字符串
   * @param {Array} arr - 节点数组
   * @returns {Array}
   */
  static cleanNodeList(arr) {
    const nodeIds = arr.map((c) => {
      return c.nodeId;
    });
    for (const node of arr) {
      node.nodeTo = Array.from(new Set(node.nodeTo));
      // 过滤掉不在节点列表中的 nodeTo（防止悬挂引用）
      if (!isEmptyArray(node.nodeTo)) {
        node.nodeTo = node.nodeTo.filter((key) => {
          return nodeIds.indexOf(key) > -1;
        });
      }
      // 对象序列化为 JSON 字符串（与后端存储格式一致）
      if (
        !isEmpty(node.nodeProperty) &&
        typeof node.nodeProperty === "object"
      ) {
        node.nodeProperty = JSON.stringify(node.nodeProperty);
      }
    }
    return arr;
  }
}
