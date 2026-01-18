# Canvas FPS Optimization - Technical Design

## Architecture Overview

当前的平移流程：
```
TouchMove Event
    ↓
handleStageMouseMove (每次触发)
    ↓
onViewportChange (React setState)
    ↓
React Reconciliation
    ↓
Re-render KonvaCanvas + children
    ↓
useViewportCulling 重计算
    ↓
GridBackground 重绘
    ↓
所有 visible nodes 重渲染
```

优化后的平移流程：
```
TouchMove Event
    ↓
handleStageMouseMove
    ↓
Konva Stage.position() (原生变换)  ← 绕过 React
    ↓
RAF throttle (~120fps capable)
    |
    └──→ (平移结束后) onViewportChange (同步 React 状态)
```

## 核心优化方案

### 1. 使用 Konva 原生变换 (最高优先级)

**问题**: 当前每次 viewport 变化都触发 React 状态更新：

```typescript
// 当前实现 (每帧 ~16ms 开销)
onViewportChange({
  ...viewport,
  x: viewport.x + dx,
  y: viewport.y + dy,
});
```

**解决方案**: 使用 Konva Stage 的原生 `position()` 方法直接变换：

```typescript
// 优化后 (每帧 <1ms 开销)
const stage = stageRef.current;
stage.position({
  x: stage.x() + dx,
  y: stage.y() + dy,
});
stage.batchDraw();
```

只在平移结束时同步回 React 状态：

```typescript
const handleStageMouseUp = () => {
  if (isPanning) {
    const stage = stageRef.current;
    // 只在结束时同步一次
    onViewportChange({
      ...viewport,
      x: stage.x(),
      y: stage.y(),
    });
  }
  setIsPanning(false);
};
```

### 2. 降低节流阈值

**问题**: `WHEEL_THROTTLE_MS = 16` 人为限制在 60fps

**解决方案**:
```typescript
const WHEEL_THROTTLE_MS = 8; // ~120fps capable
```

或使用 `requestAnimationFrame` 自动适配显示器刷新率：

```typescript
const rafIdRef = useRef<number | null>(null);

const handleWheel = (e: WheelEvent) => {
  e.preventDefault();

  if (rafIdRef.current === null) {
    rafIdRef.current = requestAnimationFrame(() => {
      // 执行实际的平移/缩放
      rafIdRef.current = null;
    });
  }
};
```

### 3. GridBackground 优化

**当前问题**: 每次 viewport 变化都完全重绘网格点

**解决方案 A - 增大网格步长**:
在快速平移时临时增大网格间距

```typescript
const effectiveGridSize = isPanning ? gridSize * 2 : gridSize;
```

**解决方案 B - 禁用网格监听**:
```typescript
<Group listening={false}>
  <Shape perfectDrawEnabled={false} />
</Group>
```

**解决方案 C - 离屏 Canvas 缓存**:
将网格渲染到离屏 canvas，只在缩放时重绘

### 4. Layer 分离策略

将不同更新频率的元素放到不同 Layer：

```typescript
<Stage>
  {/* 静态层 - 很少更新 */}
  <Layer listening={false}>
    <GridBackground />
  </Layer>

  {/* 内容层 - 节点和边 */}
  <Layer>
    {culledNodes.map(...)}
    {renderEdges()}
  </Layer>

  {/* 交互层 - 选择框、连接线等 */}
  <Layer>
    {selectionRect && <Rect ... />}
  </Layer>
</Stage>
```

## 性能预期

| 优化项 | 预期提升 | 实现复杂度 |
|--------|----------|------------|
| Konva 原生变换 | +40-50 FPS | 低 |
| 降低节流阈值 | +10-20 FPS | 极低 |
| GridBackground 优化 | +5-10 FPS | 中 |
| Layer 分离 | +5-10 FPS | 中 |

## 风险与缓解

### 风险 1: 状态不同步
Konva 位置与 React 状态在平移期间不同步

**缓解**:
- 只影响平移期间
- mouseUp 时立即同步
- 添加 blur/visibility 事件监听确保同步

### 风险 2: viewport culling 失效
平移期间不更新 culledNodes 可能导致节点突然出现

**缓解**:
- 使用更大的 padding (从 300 增加到 500)
- 或在 RAF 中更新 culled 状态（但不触发 React 渲染）

### 风险 3: 其他组件依赖 viewport 状态
某些 UI 元素可能需要实时 viewport

**缓解**:
- 审计所有 viewport 使用处
- 对关键 UI 使用独立的 ref 更新

## 实现顺序

1. **Phase 1**: 降低 `WHEEL_THROTTLE_MS` 到 8ms（5 分钟）
2. **Phase 2**: 实现 Konva 原生变换（30 分钟）
3. **Phase 3**: 测量并调优（15 分钟）
4. **Phase 4**: 如需要，优化 GridBackground（30 分钟）

## 测试计划

1. **基准测试**: 使用 FPS Monitor 记录当前帧率
2. **每步验证**: 每个优化后测量 FPS
3. **边界测试**:
   - 快速平移
   - 边缘情况（画布边界）
   - 缩放 + 平移组合
4. **回归测试**:
   - 节点拖拽仍然正常
   - 框选功能正常
   - 连接线绘制正常
