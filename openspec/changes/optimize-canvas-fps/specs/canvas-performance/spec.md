# Canvas Performance Specification

## Overview

定义画布组件的性能要求和优化策略。

## ADDED Requirements

### Requirement: High-refresh-rate panning support

画布平移操作 MUST 支持高刷新率显示器（120Hz+）。

#### Scenario: Panning on 120Hz display

**Given** 用户在 120Hz 显示器上使用画布
**And** 画布上有少于 100 个节点
**When** 用户使用双指或鼠标拖拽进行平移
**Then** 帧率 SHALL 稳定在 110 FPS 以上
**And** 不应有明显的视觉卡顿

#### Scenario: State synchronization after pan

**Given** 用户正在平移画布
**When** 用户停止平移操作（松开鼠标/触摸点）
**Then** React 状态 MUST 立即同步到 Konva Stage 的当前位置
**And** 所有依赖 viewport 的 UI 元素 SHALL 更新

### Requirement: Optimized wheel event handling

滚轮事件处理 MUST 适配高刷新率显示器。

#### Scenario: Wheel throttle frequency

**Given** 显示器刷新率为 120Hz
**When** 用户使用滚轮或触控板进行平移/缩放
**Then** 事件处理频率 SHALL 至少达到 120Hz
**And** SHOULD 使用 requestAnimationFrame 自动适配刷新率

### Requirement: Separated animation and state updates

动画帧更新与 React 状态更新 MUST 分离以提高性能。

#### Scenario: Pan animation performance

**Given** 用户正在平移画布
**When** 每帧 viewport 位置变化
**Then** MUST 使用 Konva 原生 `stage.position()` 更新位置
**And** SHALL NOT 触发 React 组件重渲染
**And** 只在平移结束时 MUST 同步 React 状态

## MODIFIED Requirements

### Requirement: Wheel throttle configuration

滚轮事件节流配置 MUST 支持更高刷新率。

#### Scenario: Default throttle interval

**Given** 默认节流配置
**When** 处理滚轮事件
**Then** 节流间隔 SHALL 为 8ms 或更低（原为 16ms）

## Technical Notes

- 使用 `stage.batchDraw()` 确保高效绘制
- GridBackground SHOULD 设置 `perfectDrawEnabled={false}` 优化性能
- 所有不需要事件监听的元素 SHOULD 设置 `listening={false}`
