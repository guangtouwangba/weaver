# Optimize Canvas FPS to 120Hz

## Status
Applied

## Why

当前白板画布在双指移动（平移）时 FPS 只有 54，远低于 120Hz 的目标。即使在 M1/M2/M3 MacBook Pro 上只有不到 10 个节点时也会出现这个问题，说明性能瓶颈在于**核心渲染循环**而非节点数量。

### 问题根源分析

1. **事件节流过于保守**: `WHEEL_THROTTLE_MS = 16` (~60fps) 人为限制了更新频率
2. **React 状态更新开销**: 每次平移触发 `onViewportChange` 导致 React reconciliation
3. **同步渲染**: viewport 变化同步触发整个组件树重渲染
4. **GridBackground 重绘**: 网格在每次移动时都完全重绘

### 目标

- 达到 120 FPS 稳定帧率（~8.3ms per frame）
- 保持现有功能完整性
- 不降低画布交互体验

## What Changes

优化 Konva 画布的平移性能，使其能在 120Hz 显示器上流畅运行。

### 核心策略

1. **分离动画帧与 React 状态**: 使用 `requestAnimationFrame` 和 Konva 原生变换
2. **降低节流阈值**: 将 `WHEEL_THROTTLE_MS` 从 16ms 降至 8ms
3. **延迟状态同步**: 平移结束后才同步 React 状态
4. **优化 GridBackground**: 使用增量绘制或 Canvas 模式

### 不包含在本次优化

- 节点渲染优化（当前节点数量不是瓶颈）
- 边连接线优化
- 图片加载优化

## Related

- `openspec/changes/add-fps-monitor/` - FPS 监控工具（已完成）

## Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2024-01-15 | 优先优化核心平移循环 | 少量节点下 FPS 低说明问题在渲染循环 |
| 2024-01-15 | 使用 Konva 原生变换 | 避免 React reconciliation 开销 |
