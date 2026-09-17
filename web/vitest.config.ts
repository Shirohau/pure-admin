import path from "node:path";
import process from "node:process";
import vueJsx from "@vitejs/plugin-vue-jsx";
import { defineConfig } from "vitest/config";

export default defineConfig({
  // jsx、tsx 语法支持（与 build/plugins.ts 保持一致）
  plugins: [vueJsx()],
  test: {
    environment: "jsdom",
    globals: true,
    include: ["test/**/*.{test,spec}.{ts,tsx}"],
    exclude: ["node_modules", "dist"]
  },
  resolve: {
    alias: {
      "@": path.resolve(process.cwd(), "src")
    }
  }
});
