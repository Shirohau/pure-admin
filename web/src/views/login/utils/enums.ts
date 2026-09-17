import { $t } from "@/plugins/i18n";

const operates = [
  {
    title: $t("login.purePhoneLogin")
  },
  // {
  //   title: $t("login.pureQRCodeLogin")
  // },
  {
    title: $t("login.pureEmailLogin")
  },
  {
    title: $t("login.pureRegister")
  }
];

export type ThirdParty = {
  title: string;
  icon: string;
  platform: string;
  color?: string;
};

const thirdParty: ThirdParty[] = [
  {
    title: $t("login.pureWeComLogin"),
    icon: "tdesign:logo-wecom",
    platform: "wecom"
    // color: "#397BFF" // 企业微信蓝
  },
  {
    title: $t("login.pureWeiBoLogin"),
    icon: "ri:weibo-fill",
    platform: "weibo"
    // color: "#E6162D" // 微博红
  },
  {
    title: $t("login.pureGithubLogin"),
    icon: "ri:github-fill",
    platform: "github",
    color: "#C71D23" // GitHub 红
  },
  {
    title: $t("login.pureGiteeLogin"),
    icon: "ri:gitee-fill",
    platform: "gitee",
    color: "#C71D23" // Gitee 红
  },
  {
    title: $t("login.pureWeChatLogin"),
    icon: "ri:wechat-fill",
    platform: "wechat"
    // color: "#07C160" // 微信绿
  },

  {
    title: $t("login.pureAlipayLogin"),
    icon: "ri:alipay-fill",
    platform: "alipay"
    // color: "#1677FF" // 支付宝蓝
  },
  {
    title: $t("login.pureQQLogin"),
    icon: "ri:qq-fill",
    platform: "qq"
    // color: "#12B7F5" // QQ 蓝
  }
];

export { operates, thirdParty };
