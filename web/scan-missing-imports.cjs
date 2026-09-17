const fs = require("fs");
const path = require("path");
const dir = process.argv[2] || "e:/code/vue-django-docker/web/src/components/Workflow";
const apis = [
  "getCurrentInstance", "useRoute", "useRouter", "computed", "watch",
  "onMounted", "onUnmounted", "onUpdated", "nextTick", "reactive",
  "toRefs", "provide", "inject", "shallowRef", "onBeforeUnmount",
  "watchEffect", "h", "ref"
];
function walk(d) {
  let r = [];
  fs.readdirSync(d).forEach(f => {
    const p = path.join(d, f);
    const s = fs.statSync(p);
    if (s.isDirectory()) r = r.concat(walk(p));
    else if (f.endsWith(".vue") || f.endsWith(".js")) r.push(p);
  });
  return r;
}
walk(dir).forEach(f => {
  const c = fs.readFileSync(f, "utf8");
  const importMatch = c.match(/import\s*\{([^}]+)\}\s*from\s*['"]vue['"]/s);
  const imported = importMatch
    ? importMatch[1].split(",").map(s => s.trim().split(/\s+as\s+/)[0])
    : [];
  const missing = apis.filter(
    a => new RegExp("\\b" + a + "\\b").test(c) && !imported.includes(a)
  );
  if (missing.length) {
    console.log(f.replace(/\\/g, "/") + " : " + missing.join(","));
  }
});
