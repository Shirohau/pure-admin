/**
 * 搜索建议项
 */
interface SuggestionItem {
  label: string;
  value: string;
}

// 获取 views 下所有的 index.vue 文件
const rawFiles = import.meta.glob(
  ["@/views/**/index.vue", "@/views/**/index.tsx"],
  { eager: false }
);

// 过滤掉路径中包含 `/components/` 的项
const filteredRawFiles = Object.fromEntries(
  Object.entries(rawFiles).filter(([path]) => !path.includes("/components/"))
);
// 预处理所有路径（只执行一次）
const allItems: SuggestionItem[] = Object.keys(filteredRawFiles).map(path => {
  let clean = path.replace(/^\.\//, ""); // 去掉 ./
  clean = clean.replace(/\.(vue|tsx)$/i, ""); // 去掉后缀
  const display = clean.replace(/^src\/views\//, ""); // 移除 src/views/ 前缀
  return { label: display, value: display };
});
/**
 * 符合 Element Plus 的 fetch-suggestions 签名：
 * (queryString: string, cb: (items: SuggestionItem[]) => void) => void
 */
const queryComponent = (
  queryString: string,
  cb: (items: SuggestionItem[]) => void
) => {
  const q = queryString.trim().toLowerCase();
  if (!q) {
    // 如果为空，可以返回全部或空（根据需求）
    cb([]);
    return;
  }

  const filtered = allItems.filter(item =>
    item.value.toLowerCase().includes(q)
  );

  cb(filtered);
};
/**
 * 返回用于 el-autocomplete 的 fetch-suggestions 回调函数
 */
export function useFetchSuggestions() {
  return { queryComponent };
}
