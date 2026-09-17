/**
 * 审批流程设计器 - 通用工具函数
 *
 * 来源：AntFlow-Designer（https://gitee.com/ldhnet/AntFlow-Designer）
 *
 * 提供空值判断、深拷贝、对象比较、随机编码生成等通用工具，
 * 被表单设计（dynamicForm 字段变更检测）与节点配置等模块复用。
 */

/** 判断数据是否为空（null/undefined/""/{}/[]/"null" 等均视为空） */
export const isEmpty = (data) =>
  data === null ||
  data === undefined ||
  data == "" ||
  data == {} ||
  data == "{}" ||
  data == "[]" ||
  data == "null";

/** 判断数组（或对象）是否为空，非数组且为空值时同样返回 true */
export const isEmptyArray = (data) =>
  Array.isArray(data)
    ? data.length === 0
    : data === null ||
      data === undefined ||
      data == "" ||
      data == [] ||
      data == "{}" ||
      data == "null"
    ? true
    : false;

/** 深拷贝（JSON 序列化方式，简单对象/数组适用） */
export const deepClone = (source) => {
  // if (typeof structuredClone === "function") {
  //   return structuredClone(source);
  // }
  return JSON.parse(JSON.stringify(source));
};

/**
 * 检查对象中指定属性是否有空值
 * @param {*} obj 目标对象
 * @param {*} props 属性名数组
 * @returns {boolean} true 表示存在空值
 */
export const hasEmptyValue = (obj, props) => {
  if (isEmpty(obj)) {
    return Object.values(obj).some((value) => {
      return isEmpty(value);
    });
  } else {
    return props.some((prop) => {
      const value = obj[prop];
      return isEmpty(value);
    });
  }
};

/**
 * 判断字段是否为"真"（兼容布尔值与字符串/数字形式）
 * @param {*} val
 * @returns {boolean}
 */
export const isTrue = (val) => {
  return (
    val === true ||
    val === "true" ||
    val === "True" ||
    val === "TRUE" ||
    val === 1 ||
    val === "1"
  );
};

/**
 * 字符串中间部分隐藏（脱敏显示）
 * @param {*} str
 * @returns 长度小于等于 18 时原样返回，否则中间替换为 ******
 */
export function substringHidden(str) {
  let frontLen = 6;
  let endLen = 6;
  if (str == null || str == undefined || str == "") {
    return str;
  }
  if (str.length <= 18) {
    return str;
  }
  var xing = "******";
  return str.substring(0, frontLen) + xing + str.substring(str.length - endLen);
}

/**
 * 将对象中的布尔值转换为字符串 "true" 或 "false"（递归处理嵌套对象/数组）
 * @param {*} obj
 * @returns
 */
export function boolToString(obj) {
  if (Array.isArray(obj)) {
    return obj.map(boolToString);
  } else if (obj && typeof obj === "object") {
    const newObj = {};
    for (const key in obj) {
      if (typeof obj[key] === "boolean") {
        newObj[key] = obj[key] ? "true" : "false";
      } else if (typeof obj[key] === "object") {
        newObj[key] = boolToString(obj[key]);
      } else {
        newObj[key] = obj[key];
      }
    }
    return newObj;
  }
  return obj;
}

/**
 * 比较两个对象是否相等（递归比较，支持嵌套对象/数组）
 * @param {*} source
 * @param {*} comparison
 * @returns {boolean} true 表示不相等，false 表示相等
 */
export const isObjectChanged = (source, comparison) => {
  if (!iterable(source)) {
    throw new Error(
      `source should be a Object or Array , but got ${getDataType(source)}`
    );
  }
  if (getDataType(source) !== getDataType(comparison)) {
    return true;
  }
  const sourceKeys = Object.keys(source);
  const comparisonKeys = Object.keys({ ...source, ...comparison });
  if (sourceKeys.length !== comparisonKeys.length) {
    return true;
  }
  return comparisonKeys.some((key) => {
    if (iterable(source[key])) {
      return isObjectChanged(source[key], comparison[key]);
    } else {
      return source[key] !== comparison[key];
    }
  });
};

/**
 * 简单比较两个对象是否相等（JSON 序列化方式，性能较好但忽略键顺序）
 * @param {*} source
 * @param {*} comparison
 * @returns {boolean} true 表示不相等，false 表示相等
 */
export const isObjectChangedSimple = (source, comparison) => {
  const _source = JSON.stringify(source);
  const _comparison = JSON.stringify({ ...source, ...comparison });
  return _source !== _comparison;
};

/* ------------------------------ 以下为私有方法 ------------------------------ */

/**
 * 获取数据的类型名称（如 Object / Array / String / Number）
 * @param {*} data
 * @returns {string}
 */
export const getDataType = (data) => {
  const temp = Object.prototype.toString.call(data);
  const type = temp.match(/\b\w+\b/g);
  return type.length < 2 ? "Undefined" : type[1];
};

/**
 * 判断数据是否为可迭代对象（Object 或 Array）
 * @param {*} data
 * @returns {boolean}
 */
export const iterable = (data) => {
  return ["Object", "Array"].includes(getDataType(data));
};

/**
 * 生成 9 位不重复的大写字母数字组合
 * 优先使用浏览器安全随机数（crypto.getRandomValues），不可用时退化为 Math.random
 * @returns {string} 9 位不重复随机字符串
 */
export const getRandomUniqueCode = () => {
  // 字符池：数字 + 大写字母
  const chars = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ";

  // 优先使用浏览器安全随机数，退化时再使用 Math.random
  const randomValues =
    typeof crypto !== "undefined" && typeof crypto.getRandomValues === "function"
      ? crypto.getRandomValues(new Uint32Array(9))
      : Array.from({ length: 9 }, () => Math.floor(Math.random() * 0x100000000));

  let result = "";
  for (const value of randomValues) {
    result += chars[value % chars.length];
  }
  return result;
};
