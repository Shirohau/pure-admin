import type { CSSProperties, VNode, Component } from "vue";

type DoneFn = (cancel?: boolean) => void;

interface DrawerOptions {
  /** `Drawer` 的显示与隐藏 */
  visible?: boolean;
  /** `Drawer` 的标题 */
  title?: string;
  /** `Drawer` 的尺寸（水平方向为宽度，垂直方向为高度），默认 `30%` */
  size?: string | number;
  /** `Drawer` 打开的方向，默认 `rtl` */
  direction?: "rtl" | "ltr" | "ttb" | "btt";
  /** 是否为 `Drawer` 添加遮罩层，默认 `true` */
  modal?: boolean;
  /** `Drawer` 自身是否插入至 `body` 元素上，默认 `false` */
  appendToBody?: boolean;
  /** 是否在关闭 `Drawer` 时销毁其中的元素，默认 `false` */
  destroyOnClose?: boolean;
  /** 是否显示 `Drawer` 的标题栏，默认 `true`。置为 `false` 隐藏标题栏时，关闭按钮不再内置于头部，`ReDrawer` 会自动在内容区右上角渲染浮动关闭按钮（可用 `showClose` 控制） */
  withHeader?: boolean;
  /** `Drawer` 的自定义类名 */
  class?: string;
  /** `Drawer` 的自定义样式 */
  style?: CSSProperties;
  /** `Drawer` 打开的延时时间，单位毫秒，默认 `0` */
  openDelay?: number;
  /** `Drawer` 关闭的延时时间，单位毫秒，默认 `200` */
  closeDelay?: number;
  /** 是否可以通过点击 `modal` 关闭 `Drawer`，默认 `true` */
  closeOnClickModal?: boolean;
  /** 是否可以通过按下 `ESC` 关闭 `Drawer`，默认 `true` */
  closeOnPressEscape?: boolean;
  /** 是否显示关闭按钮，默认 `true` */
  showClose?: boolean;
  /** 关闭前的回调，会暂停 `Drawer` 的关闭。回调函数内执行 `done` 参数方法的时候才是真正关闭的时候 */
  beforeClose?: (done: DoneFn) => void;
  /** 内容区组件的 `props`，可通过 `defineProps` 接收 */
  props?: any;
  /** 自定义 `Drawer` 标题的内容渲染器 */
  headerRenderer?: ({
    close,
    titleId,
    titleClass
  }: {
    close: Function;
    titleId: string;
    titleClass: string;
  }) => VNode | Component;
  /** 自定义内容渲染器 */
  contentRenderer: ({
    options,
    index
  }: {
    options: DrawerOptions;
    index: number;
  }) => VNode | Component;
  /** `Drawer` 打开后的回调 */
  open?: ({
    options,
    index
  }: {
    options: DrawerOptions;
    index: number;
  }) => void;
  /** `Drawer` 关闭后的回调 */
  close?: ({
    options,
    index
  }: {
    options: DrawerOptions;
    index: number;
  }) => void;
  /** `Drawer` 关闭后的回调。 `args` 返回的 `command` 值：`close` 点击右上角关闭按钮或空白页或按下了esc键 */
  closeCallBack?: ({
    options,
    index,
    args
  }: {
    options: DrawerOptions;
    index: number;
    args: any;
  }) => void;
  /** 其他额外配置 */
  [key: string]: any;
}

export type { DrawerOptions };
