# Border Radius 统一规范指南

根据 `design.json` 规范，统一了整个设计系统的圆角设置。

## 🎯 圆角比例表

| Token | Size | Usage | Tailwind Class |
|-------|------|-------|----------------|
| `xs` | 4px | 细微圆角 | `rounded-xs` |
| `sm` | 8px | 小型容器 | `rounded-sm` |
| `md` | 12px | 中等容器 | `rounded-md` |
| `lg` | 16px | 卡片和主要面板 | `rounded-lg` |
| `pill` | 999px | 完全圆角（按钮、标签） | `rounded-pill` |

---

## 📦 组件圆角规范

### 1. 输入类组件 (Inputs & Fields)

#### Input / TextField
- **外部容器**: `rounded-lg` (16px)
- **原因**: 根据 design.json - "Inputs and chips use 999 px radius when pill-shaped or 8–12 px when rectangular"
- **实际实现**: 使用 16px 提供更柔和的外观

```jsx
<input className="rounded-lg border ..." />
```

#### TokenizedInput
- **外部容器**: `rounded-xl` (16px)
- **内部 Token**: `rounded-pill` (999px)
- **原因**: 容器使用 12px per design.json specs，tokens 使用完全圆角

```jsx
<div className="rounded-xl border-2 ...">
  <div className="rounded-pill ...">Token</div>
</div>
```

#### Select / Dropdown
- **按钮容器**: `rounded-lg` (16px)
- **下拉面板**: `rounded-lg` (16px)
- **原因**: 与其他输入组件保持一致

```jsx
<button className="rounded-lg border ..." />
<div className="rounded-lg shadow-medium ...">Options</div>
```

---

### 2. 按钮类组件 (Buttons)

#### Button (所有变体)
- **Primary/Secondary/Ghost/Tiny**: `rounded-pill` (999px)
- **原因**: "Buttons and pills use fully rounded geometry"

```jsx
<button className="rounded-pill h-10 px-5">Primary</button>
```

---

### 3. 标签类组件 (Tags & Chips)

#### Chip / Tag
- **形状**: `rounded-pill` (999px)
- **高度**: 24px
- **原因**: "Inputs and chips use 999 px radius when pill-shaped"

```jsx
<span className="rounded-pill h-6 px-[10px]">Chip</span>
```

---

### 4. 卡片类组件 (Cards & Containers)

#### Card
- **圆角**: `rounded-lg` (16px)
- **原因**: "Cards and primary panels use 16 px rounded corners"

```jsx
<div className="bg-surface-card rounded-lg shadow-soft p-5">
  Card Content
</div>
```

#### Modal
- **圆角**: `rounded-lg` (16px)
- **原因**: 与卡片保持一致

```jsx
<div className="rounded-lg shadow-medium ...">
  Modal Content
</div>
```

---

### 5. 聊天类组件 (Chat Components)

#### ChatBox - Input Area
- **外部容器**: `rounded-xl` (16px)
- **消息气泡**: `rounded-lg` (16px)，对话方向的角使用 `rounded-tr-sm` / `rounded-tl-sm`

```jsx
// Input container
<div className="rounded-xl border ...">
  <textarea />
</div>

// Message bubble (own)
<div className="rounded-lg rounded-tr-sm bg-primary-strong">
  Message
</div>

// Message bubble (received)
<div className="rounded-lg rounded-tl-sm bg-surface-subtle">
  Message
</div>
```

---

### 6. 其他组件

#### ProgressBar
- **轨道**: `rounded-pill` (999px)
- **填充**: `rounded-pill` (999px)

#### Avatar
- **形状**: `rounded-full` (circle)

#### Toggle Switch
- **轨道**: `rounded-pill` (999px)
- **旋钮**: `rounded-full` (circle)

#### Banner / Notification
- **容器**: `rounded-lg` (16px)

---

## 📐 设计原则

### 1. 层次感原则
- **大容器**: 使用较大圆角 (16px) 提供柔和外观
- **小元素**: 使用完全圆角 (pill) 显示精致感
- **按钮**: 始终使用完全圆角保持一致性

### 2. 功能性原则
- **输入框**: 16px 圆角提供足够识别度
- **Token/Chip**: 完全圆角便于视觉识别和删除
- **卡片**: 16px 圆角与页面背景形成对比

### 3. 统一性原则
- 同类组件使用相同圆角规格
- 容器内的元素可以使用不同圆角形成层次
- 避免使用过多不同的圆角尺寸

---

## ✅ 更新清单

已统一的组件：
- [x] Input - `rounded-lg`
- [x] TokenizedInput - 容器 `rounded-xl`，token `rounded-pill`
- [x] Select - `rounded-lg`
- [x] Button - 所有变体 `rounded-pill`
- [x] Chip - `rounded-pill`
- [x] Card - `rounded-lg`
- [x] Modal - `rounded-lg`
- [x] ChatBox Input - `rounded-xl`
- [x] Toggle - `rounded-pill`
- [x] ProgressBar - `rounded-pill`

---

## 🎨 视觉效果

### 对比示例

**Input 圆角对比：**
- ❌ `rounded-md` (12px) - 略显生硬
- ✅ `rounded-lg` (16px) - 柔和自然

**TokenizedInput 圆角对比：**
- ❌ 容器 `rounded-md` + token `rounded-pill` - 视觉不协调
- ✅ 容器 `rounded-xl` + token `rounded-pill` - 层次分明

**Button 圆角对比：**
- ❌ `rounded-lg` - 显得不够亲和
- ✅ `rounded-pill` - 友好且现代

---

## 💡 使用建议

1. **新增组件时**：
   - 参考本文档选择合适的圆角大小
   - 保持与现有组件的一致性
   - 考虑组件的层级关系

2. **修改现有组件时**：
   - 检查是否符合本规范
   - 确保不会破坏整体视觉协调性
   - 更新相关文档

3. **特殊情况**：
   - 如需使用非标准圆角，需要在代码中注释说明原因
   - 确保有充分的设计理由
   - 团队评审通过后方可实施

---

## 📚 相关文档

- `design.json` - 设计系统源规范
- `DESIGN_SYSTEM.md` - 完整设计系统文档
- `tailwind.config.js` - Tailwind 配置文件

**版本**: 1.1.0  
**更新日期**: 2025-11-18  
**状态**: ✅ 已统一完成

