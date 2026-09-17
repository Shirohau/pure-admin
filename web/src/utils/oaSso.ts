import { createBrowserAdapter, createElectronAdapter, createOaSdk } from "@oa/jsapi";
import type { UserResult } from "@/api/user";

// 只在 OA 工作台启动时启用，普通打开应用仍使用原登录页。
const electronAdapter = createElectronAdapter();
const hasTicket = new URL(window.location.href).searchParams.has("oa_ticket");
export const hasOaLaunch = Boolean(electronAdapter) || hasTicket;
let attempted = false;

async function request<T>(action: string, data?: object): Promise<T> {
  const base = (import.meta.env.VITE_API_URL || "").replace(/\/$/, "");
  const url = new URL(`${base}/api/oa-sso/${action}/`, window.location.origin);
  if (url.origin !== window.location.origin || url.protocol !== "https:") {
    throw new Error("OA 免登需要应用页面与后台接口使用同源 HTTPS");
  }
  const response = await fetch(url, {
    method: data === undefined ? "GET" : "POST",
    credentials: "include",
    cache: "no-store",
    headers: data === undefined ? {} : { "Content-Type": "application/json" },
    body: data === undefined ? undefined : JSON.stringify(data),
    signal: AbortSignal.timeout(45000)
  });
  const result = await response.json();
  if (!response.ok || !result.success) {
    throw new Error(result.message || "OA 免登未完成，请从工作台重新打开");
  }
  return result.data as T;
}

export async function loginFromOa(): Promise<UserResult["data"] | undefined> {
  if (!hasOaLaunch || attempted) return;
  attempted = true;
  // issuer 来自本应用后台部署配置，不接受查询参数传入。
  const { issuer } = await request<{ issuer: string }>("config");
  const adapter = electronAdapter ?? createBrowserAdapter({ platformOrigin: issuer });
  const sdk = createOaSdk(adapter);
  const { requestId } = await request<{ requestId: string }>("prepare", {});
  const result = await sdk.requestAuthCode({ requestId });
  const account = await request<UserResult["data"]>("complete", {
    code: result.code,
    requestId: result.requestId
  });
  return account;
}

export async function logoutFromOa(localRefreshToken?: string): Promise<void> {
  // 此解码仅判断是否需要请求 OA 退出；后台仍独立验证会话与请求来源。
  // 不依赖标签页标记，避免普通密码登录继承此前 OA 登录的退出行为。
  try {
    const segment = localRefreshToken?.split(".")[1];
    if (!segment) return;
    const payload = JSON.parse(atob(segment.replace(/-/g, "+").replace(/_/g, "/")));
    if (!payload.oa_sso) return;
  } catch {
    return;
  }
  await request("logout", {});
}
