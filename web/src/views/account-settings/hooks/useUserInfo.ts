import { useUserStoreHook } from "@/store/modules/user";
import { api } from "../api";
import { ref } from "vue";

const userInfo = ref({
  id: undefined,
  avatar_path: "",
  username: "",
  name: "",
  email: "",
  mobile: "",
  description: ""
});

const get_user_info = async () => {
  const id = useUserStoreHook().id;
  const { data } = await api.GetObj(id);
  userInfo.value = data;
};
const set_avatar_path = (path: string) => {
  userInfo.value.avatar_path = path;
  useUserStoreHook().SET_AVATAR(path);
};
get_user_info();
export function useUserInfo() {
  return {
    userInfo,
    set_avatar_path
  };
}
