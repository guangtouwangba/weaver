# Canvas FPS Optimization - Tasks

## Phase 1: Quick Wins (立即生效)

- [x] **1.1 降低节流阈值**
  将 `WHEEL_THROTTLE_MS` 从 16ms 降至 8ms
  - 文件: `app/frontend/src/components/studio/KonvaCanvas.tsx:2319`
  - 验证: FPS Monitor 显示帧率提升
  - 风险: 极低

## Phase 2: 核心优化 (Konva 原生变换)

- [x] **2.1 创建平移状态 ref**
  添加 `wheelRafIdRef` 和 `pendingWheelDeltaRef` 用于 RAF 处理
  - 文件: `KonvaCanvas.tsx`
  - 在 `lastPosRef` 附近添加

- [x] **2.2 修改 handleStageMouseMove**
  使用 Konva `stage.position()` 代替 `onViewportChange`
  - 文件: `KonvaCanvas.tsx:3037-3055`
  - 只更新 stage 位置和调用 `stage.batchDraw()`
  - 不触发 React 状态更新

- [x] **2.3 修改 handleStageMouseUp**
  在平移结束时同步 React 状态
  - 文件: `KonvaCanvas.tsx:3605-3616`
  - 从 `stageRef.current` 读取最终位置
  - 调用 `onViewportChange` 同步状态

- [x] **2.4 修改 handleWheel 使用 RAF**
  用 `requestAnimationFrame` 替代固定节流（仅用于平移）
  - 文件: `KonvaCanvas.tsx:2930-2994`
  - 自动适配显示器刷新率
  - 累积 delta 值后在下一帧处理

## Phase 3: GridBackground 优化

- [x] **3.1 禁用不必要的 Konva 特性**
  - 文件: `app/frontend/src/components/studio/canvas/GridBackground.tsx`
  - 添加 `perfectDrawEnabled={false}` 到 Shape
  - 确保 `listening={false}` 正确设置

- [ ] **3.2 (可选) 实现离屏缓存**
  如果上述优化不够，实现网格的离屏 Canvas 缓存
  - 只在缩放时重绘
  - 平移时只偏移

## Phase 4: 验证与测试

- [ ] **4.1 FPS 基准测试**
  使用 FPS Monitor 记录优化前后帧率
  - 目标: 稳定 ≥ 110 FPS

- [ ] **4.2 功能回归测试**
  - 节点拖拽正常
  - 框选功能正常
  - 连接线绘制正常
  - 缩放功能正常
  - Context menu 正常

- [ ] **4.3 边界测试**
  - 快速连续平移
  - 平移 + 缩放组合
  - 窗口失焦/获焦时状态同步

## 依赖关系

```
1.1 (节流) ─── 独立，可立即实施

2.1 (ref) ──→ 2.2 (移动) ──→ 2.3 (结束) ──→ 2.4 (RAF)
   │                                           │
   └───────────────────────────────────────────┴──→ 4.1, 4.2

3.1 (Grid优化) ─── 独立，可并行

4.3 ─── 最后执行
```

## 验收标准

1. FPS Monitor 显示平移时 ≥ 110 FPS (在 M1/M2/M3 Mac + Chrome)
2. 所有现有功能正常工作
3. 无明显视觉卡顿或闪烁

## 实施记录

### 已完成的更改

1. **KonvaCanvas.tsx**:
   - 将 `WHEEL_THROTTLE_MS` 从 16ms 改为 8ms
   - 添加 `wheelRafIdRef` 和 `pendingWheelDeltaRef` 用于 RAF 平移处理
   - 修改 `handleStageMouseMove` 使用 `stage.position()` + `stage.batchDraw()` 替代 React 状态更新
   - 修改 `handleStageMouseUp` 在平移结束时同步 React 状态
   - 修改 `handleWheel` 使用 RAF 处理平移，累积 delta 值

2. **GridBackground.tsx**:
   - 添加 `perfectDrawEnabled={false}` 优化绘制性能
