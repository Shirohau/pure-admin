import { h } from "vue";
import { addDrawer } from "@/components/ReDrawer";
import RoleImpowerContent from "./RoleImpowerContent.vue";

/**
 * 打开角色授权抽屉
 * @description 仿 dialogAsideTable 的函数式抽屉方式，支持从角色列表页（授权按钮）与用户页（关联角色列）复用。
 * 每个抽屉实例通过 props 传入 roleId，内部提供独立状态（provide/inject），可同时打开多个互不干扰。
 * @param role 角色对象（含 id/name）或角色 id
 */
export const dialogRoleImpower = (
  role: { id: number; name?: string } | number
) => {
  const roleId = typeof role === "number" ? role : role.id;
  addDrawer({
    title: "角色授权",
    size: "80%",
    direction: "rtl",
    destroyOnClose: true,
    withHeader: false,
    props: { roleId },
    contentRenderer: () => h(RoleImpowerContent)
  });
};
