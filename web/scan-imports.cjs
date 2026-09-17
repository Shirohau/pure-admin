const fs = require("fs");
const path = require("path");
const dir = "e:/code/vue-django-docker/web/src/components/Workflow";
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
  const lines = c.split("\n");
  console.log("===== " + f.replace(/\\/g, "/").replace("E:/code/vue-django-docker/web/src/components/Workflow/", "") + " =====");
  lines.forEach((l, i) => {
    if (/^\s*import\s/.test(l) || /^\s*const\s*\{?\s*proxy/.test(l) || /^import/.test(l)) {
      console.log((i + 1) + ": " + l.replace(/\r$/, ""));
    }
  });
});
