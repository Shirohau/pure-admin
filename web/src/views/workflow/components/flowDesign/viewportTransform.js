/**
 * 审批流程设计器 - 画布视口变换组合式函数
 *
 * 来源：AntFlow-Designer（https://gitee.com/ldhnet/AntFlow-Designer）
 *
 * 作用：为流程设计画布提供缩放（滚轮/按钮）、拖拽平移、视图重置能力，
 * 返回响应式视口状态与操作方法，由 flowDesign/index.vue 使用。
 * 缩放以鼠标指针/视口中心为锚点计算位移，保证缩放时锚点内容不漂移。
 */
import { computed, onMounted, onUnmounted, reactive, ref } from 'vue'

/** 默认缩放配置 */
const DEFAULT_OPTIONS = {
  minScale: 0.4, // 最小缩放比例
  maxScale: 2.5, // 最大缩放比例
  zoomInFactor: 1.1, // 放大倍率
  zoomOutFactor: 0.9 // 缩小倍率
}

/** 滚轮监听选项（passive: false 以便阻止页面默认滚动） */
const wheelListenerOptions = { passive: false }

/** 数值钳制：限制 value 在 [min, max] 范围内 */
const clamp = (value, min, max) => Math.max(min, Math.min(max, value))

/**
 * 视口变换组合式函数
 * @param {import('vue').Ref} viewportRef 画布容器 DOM 引用
 * @param {Object} options 可选配置（覆盖默认缩放参数）
 * @returns {{
 *   viewportViewState: Object, // 响应式视口状态（isDragging/flowTransformStyle/zoomPercent/canZoomIn/canZoomOut）
 *   onMouseDown: Function,     // 鼠标按下（开始拖拽）
 *   zoomIn: Function,          // 放大
 *   zoomOut: Function,         // 缩小
 *   resetView: Function        // 重置视图
 * }}
 */
export function useViewportTransform(viewportRef, options = {}) {
  const config = {
    ...DEFAULT_OPTIONS,
    ...options
  }

  /** 是否正在拖拽 */
  const isDragging = ref(false)

  /** 视口状态：位移 x/y 与缩放比例 scale */
  const viewportState = reactive({
    x: 0,
    y: 0,
    scale: 1
  })

  /** 拖拽状态：记录按下时的起点与视口原点 */
  const dragState = reactive({
    startX: 0,
    startY: 0,
    originX: 0,
    originY: 0
  })

  /** 画布容器的 transform 样式（平移 + 缩放） */
  const flowTransformStyle = computed(() => {
    const x = Math.round(viewportState.x)
    const y = Math.round(viewportState.y)

    return {
      transform: `translate3d(${x}px, ${y}px, 0) scale(${viewportState.scale})`,
      transformOrigin: '0 0'
    }
  })

  /** 缩放百分比显示文本 */
  const zoomPercent = computed(() => `${Math.round(viewportState.scale * 100)}%`)
  /** 是否可以继续放大 */
  const canZoomIn = computed(() => viewportState.scale < config.maxScale)
  /** 是否可以继续缩小 */
  const canZoomOut = computed(() => viewportState.scale > config.minScale)

  /** 获取视口中心坐标（按钮缩放以中心为锚点） */
  const getViewportCenter = () => {
    if (!viewportRef.value) {
      return { x: 0, y: 0 }
    }
    const rect = viewportRef.value.getBoundingClientRect()
    return {
      x: rect.width / 2,
      y: rect.height / 2
    }
  }

  /**
   * 以指定锚点应用新的缩放比例（保持锚点下的内容位置不变）
   * @param {number} newScale 目标缩放比例
   * @param {number} anchorX 锚点 X（视口内坐标）
   * @param {number} anchorY 锚点 Y（视口内坐标）
   */
  const applyScale = (newScale, anchorX, anchorY) => {
    const oldScale = viewportState.scale
    const nextScale = clamp(newScale, config.minScale, config.maxScale)
    if (nextScale === oldScale) {
      return
    }

    // 计算锚点对应的"世界坐标"（缩放前），再反推缩放后的位移
    const worldX = (anchorX - viewportState.x) / oldScale
    const worldY = (anchorY - viewportState.y) / oldScale

    viewportState.scale = nextScale
    viewportState.x = anchorX - worldX * nextScale
    viewportState.y = anchorY - worldY * nextScale
  }

  /** 以视口中心为锚点放大 */
  const zoomIn = () => {
    const center = getViewportCenter()
    applyScale(viewportState.scale * config.zoomInFactor, center.x, center.y)
  }

  /** 以视口中心为锚点缩小 */
  const zoomOut = () => {
    const center = getViewportCenter()
    applyScale(viewportState.scale * config.zoomOutFactor, center.x, center.y)
  }

  /** 重置视图：位移归零、缩放恢复 100% */
  const resetView = () => {
    viewportState.x = 0
    viewportState.y = 0
    viewportState.scale = 1
  }

  /** 鼠标左键按下：记录拖拽起点（绑定在画布容器上） */
  const onMouseDown = (event) => {
    if (event.button !== 0) {
      return
    }
    isDragging.value = true
    dragState.startX = event.clientX
    dragState.startY = event.clientY
    dragState.originX = viewportState.x
    dragState.originY = viewportState.y
  }

  /** 鼠标移动：拖拽平移视口（绑定在 window 上） */
  const onMouseMove = (event) => {
    if (!isDragging.value) {
      return
    }
    viewportState.x = dragState.originX + (event.clientX - dragState.startX)
    viewportState.y = dragState.originY + (event.clientY - dragState.startY)
  }

  /** 鼠标松开：结束拖拽 */
  const onMouseUp = () => {
    isDragging.value = false
  }

  /** 滚轮缩放：以鼠标指针为锚点 */
  const onWheel = (event) => {
    if (!viewportRef.value) {
      return
    }

    // 阻止页面滚动（画布内滚轮仅用于缩放）
    if (event.cancelable) {
      event.preventDefault()
    }

    const rect = viewportRef.value.getBoundingClientRect()
    const pointerX = event.clientX - rect.left
    const pointerY = event.clientY - rect.top
    const zoomFactor = event.deltaY < 0 ? config.zoomInFactor : config.zoomOutFactor
    applyScale(viewportState.scale * zoomFactor, pointerX, pointerY)
  }

  // 挂载：注册全局拖拽监听与画布滚轮监听
  onMounted(() => {
    window.addEventListener('mousemove', onMouseMove)
    window.addEventListener('mouseup', onMouseUp)
    viewportRef.value?.addEventListener('wheel', onWheel, wheelListenerOptions)
  })

  // 卸载：移除监听，防止内存泄漏
  onUnmounted(() => {
    window.removeEventListener('mousemove', onMouseMove)
    window.removeEventListener('mouseup', onMouseUp)
    viewportRef.value?.removeEventListener('wheel', onWheel, wheelListenerOptions)
  })

  /** 暴露给调用方的响应式视口状态 */
  const viewportViewState = {
    isDragging,
    flowTransformStyle,
    zoomPercent,
    canZoomIn,
    canZoomOut
  }

  return {
    viewportViewState,
    onMouseDown,
    zoomIn,
    zoomOut,
    resetView
  }
}
