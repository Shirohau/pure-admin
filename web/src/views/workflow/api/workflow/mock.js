/**
 * 审批流程设计器 - Mock 数据接口
 *
 * 来源：AntFlow-Designer（https://gitee.com/ldhnet/AntFlow-Designer）
 * 迁移适配：
 * 1. 原实现基于 axios 请求 public/mock/*.json，此处改为原生 fetch（后端暂不实现，无需引入额外依赖）
 * 2. 返回结构与原版一致（fetch 直接返回 json 内容，等同 axios 响应拦截器解包后的 response.data），
 *    因此组件内的调用方式（res.data / res.total）无需任何修改
 *
 * 对接后端指引：后续实现后端接口时，仅需将各函数体替换为对真实 API 的请求
 * （如使用项目 `@/utils/request`），保持函数签名与返回结构不变即可。
 */
// 静态数据文件所在目录（public 目录下的资源路径）
const mockBaseUrl = `${import.meta.env.BASE_URL}mock/`;

/**
 * 请求 public/mock 下的 JSON 静态文件
 * @param {string} fileName 文件名（不含路径）
 * @returns {Promise<any>} 解析后的 JSON 内容
 */
function getMockJson(fileName) {
  return fetch(`${mockBaseUrl}${fileName}`).then((res) => res.json());
}

/**
 * 获取流程定义详情（设计器初始化数据）
 * 返回结构：{ code: 200, data: { flowCode, name, frmValue, nodes: [...] } }
 * @param {Object} data 查询参数（预留，如流程 id）
 * @returns {Promise<Object>}
 */
export function getWorkFlowData(data) {
  return getMockJson("data.json");
}

/**
 * 获取职员列表（审批人/抄送人选择对话框使用）
 * 返回结构：{ code: "200", msg, total, data: [{ id, employeeName }] }
 * @param {Object} data 分页/搜索参数
 * @returns {Promise<Object>}
 */
export function getEmployees(data) {
  return getMockJson("employees.json");
}

/**
 * 获取角色列表（审批人选择"角色"类型时使用）
 * 返回结构：{ code: "200", msg, data: [{ roleId, roleName }] }
 * @returns {Promise<Object>}
 */
export function getRoleList() {
  return getMockJson("roles.json");
}

/**
 * 获取条件字段列表（条件节点配置的可用字段）
 * 返回结构：{ isDefault, groupRelation, groupConditions: [...] }
 * @param {Object} data 查询参数（预留）
 * @returns {Promise<Object>}
 */
export function getConditions(data) {
  return getMockJson("conditions.json");
}

/**
 * 保存/发布流程定义（当前仅打印数据，不调后端）
 * @param {Object} data 格式化后的流程定义（含 frmValue、nodes）
 * @returns {Promise<{ code: number }>} 模拟成功返回
 */
export function setWorkFlowData(data) {
  console.log("【AntFlow】保存流程定义（Mock 模式，未提交后端）：", JSON.stringify(data));
  return Promise.resolve({ code: 200 });
}
