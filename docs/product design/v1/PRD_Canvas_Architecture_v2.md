# PRD: Canvas统一架构设计 v2.0

| Document Info | Details |
| --- | --- |
| **Version** | v2.0 |
| **Status** | Design Phase |
| **Scope** | Canvas Unified Architecture (Views + Sections) |
| **Feature Type** | Core Architecture Update |
| **MVP Scope** | Free Canvas + Thinking Paths Views |

---

## 1. 核心设计理念：视图为体，Section为用

为了解决Canvas节点混乱、布局逻辑冲突以及组织困难的问题，我们采用**"Sidebar + Section"**的分层治理策略：

1. **Sidebar（宏观视图）**：负责切换**世界观**（交互规则）。解决"自由布局"与"自动布局"的冲突。
2. **Section（微观组织）**：负责管理**领地**（内容分组）。解决"节点数量多"和"结构化"问题。
3. **流转机制（Flow）**：定义内容如何在不同视图间移动，保证知识的连续性。

### 1.1 MVP范围

**Phase 1 MVP聚焦**：
- ✅ **自由画布 (Free Canvas)**：绝对定位，手动整理笔记
- ✅ **思考路径 (Thinking Paths)**：流式布局，对话沉淀
- ⏸️ **知识图谱 (Knowledge Graph)**：延后到Phase 3
- ⏸️ **混合视图 (Mixed View)**：延后到Phase 3

---

## 2. 视图架构（Sidebar控制）

侧边栏提供两个MVP视图，对应不同的物理规则和认知模式。

### 2.1 视图定义

| 视图模式 | 对应认知模式 | 物理规则 (Physics) | 典型用途 | MVP状态 |
| :--- | :--- | :--- | :--- | :--- |
| **1. 自由画布 (Free Canvas)** | **整理/笔记** | **绝对定位**<br>用户拖哪放哪，无引力，网格吸附 | 手动整理笔记、拼贴想法、空间记忆 | ✅ MVP |
| **2. 思考路径 (Thinking Paths)** | **回顾/反思** | **流式布局**<br>从左到右/从上到下，半自动排列 | 回顾对话过程、理解推导逻辑 | ✅ MVP |
| **3. 知识图谱 (Knowledge Graph)** | **发现/关联** | **力导向布局**<br>节点自动飘动，聚类，引力排斥 | 查看全局关系、发现隐藏关联 | ⏸️ Phase 3 |

### 2.2 侧边栏交互

**位置**：Canvas右侧，默认宽度280px，可折叠。

**MVP侧边栏结构**：
```
┌─────────────────────────┐
│ 视图模式                │
├─────────────────────────┤
│ ┌─────────────────────┐ │
│ │ 📝 自由画布         │ │ ← 当前视图
│ │    (12个节点)       │ │
│ └─────────────────────┘ │
│ ┌─────────────────────┐ │
│ │ 🌱 思考路径         │ │
│ │    (3个路径)        │ │
│ └─────────────────────┘ │
├─────────────────────────┤
│ [设置] [折叠]            │
└─────────────────────────┘
```

**交互特性**：
- **切换**：点击视图卡片快速切换视图
- **状态保持**：每个视图保持独立的状态（缩放级别、视口位置、过滤器设置）
- **快捷键**：`Cmd+1` 切换到自由画布，`Cmd+2` 切换到思考路径
- **折叠**：点击"折叠"按钮，侧边栏折叠为图标条

### 2.3 视图切换机制

#### 2.3.1 切换流程

1. **用户点击视图卡片**
2. **保存当前视图状态**（节点位置、缩放、选择等）
3. **加载目标视图**（节点、连接、状态）
4. **更新Canvas显示**
5. **更新侧边栏高亮**

#### 2.3.2 视图状态管理

**每个视图独立的状态**：
- 节点位置和布局
- 视图缩放级别（viewport: { x, y, scale }）
- 选中的节点
- Section折叠状态

**状态持久化**：
- 每个视图的状态独立保存到后端
- 切换视图时自动保存和恢复
- 支持撤销/重做（每个视图独立）

#### 2.3.3 切换动画

**过渡效果**：
- 淡入淡出（0.2秒）
- 平滑过渡，不突兀
- 保持Canvas的连续性

---

## 3. Section：通用的组织容器

Section是所有视图通用的容器组件，但在不同视图中承担不同的角色。

### 3.1 Section在各视图中的角色

#### 3.1.1 在自由画布中

**角色**：手动整理箱。

**行为**：
- 用户框选节点 → 创建Section
- 可以手动拖拽Section标题栏，整体移动

**价值**：
- 将相关笔记归拢，整体拖拽
- 保持Canvas组织清晰

#### 3.1.2 在思考路径中

**角色**：对话容器。

**行为**：
- 每次深度探索对话自动生成一个Section
- Section标题：对话的问题（前30个字符）
- Section位置：Canvas右侧区域（不干扰左侧知识节点）

**价值**：
- 区分不同话题的思考过程
- 每个对话的思考路径独立管理

### 3.2 Section通用交互

**折叠/展开**：
- 点击标题栏折叠，仅显示标题和节点数
- **性能优化关键**：折叠时内部节点完全不渲染

**整体拖拽**：
- 拖拽标题栏，移动整个Section及其内部所有节点
- 利用 `Konva.Group` 实现，拖拽计算成本为 O(1)

**右键菜单**：
```
┌─────────────────────────────────────────┐
│ 🌱 思考路径: "什么是RAG？"              │
├─────────────────────────────────────────┤
│ 📋 复制Section                           │
│ ⬆️  提升所有节点到自由画布                │
│ 📦 归档Section                            │
│ 🗑️  删除Section                          │
└─────────────────────────────────────────┘
```

**操作说明**：
- **复制**：复制整个Section到新位置
- **提升**：将所有节点提升到自由画布视图
- **归档**：移到Canvas边缘，标记为"已归档"
- **删除**：删除整个Section（确认对话框）

### 3.3 Section视觉设计

**展开状态**：
```
┌─────────────────────────────────────────────┐
│ 🌱 思考路径: "什么是RAG？"  [折叠 ▼]      │
│ 包含 5 个节点 | 创建于 2分钟前              │
├─────────────────────────────────────────────┤
│ ┌─────┐ → ┌─────┐ → ┌─────┐ → ┌─────┐   │
│ │提问1│   │回答1│   │提问2│   │结论 │   │
│ └─────┘   └─────┘   └─────┘   └─────┘   │
└─────────────────────────────────────────────┘
```

**折叠状态**：
```
┌─────────────────────────────────────────────┐
│ 🌱 思考路径: "什么是RAG？"  [展开 ▶]      │
│ 包含 5 个节点                                │
└─────────────────────────────────────────────┘
```

**设计要点**：
- Section有明确的边框和背景色（浅灰色 #F3F4F6）
- 标题栏有图标和操作按钮
- 节点在Section内，有视觉边界
- 使用 `Konva.Group` 实现，支持整体变换

---

## 4. 节点类型与视觉区分

### 4.1 节点类型定义

| 节点类型 | 所属视图 | 来源 | 说明 |
|---------|---------|------|------|
| **知识卡片** | 自由画布 | 从PDF拖拽/右键创建 | 有sourceId，是"内容" |
| **对话节点** | 自由画布 | 从Assistant对话"Add to Canvas" | 是"洞察" |
| **手动节点** | 自由画布 | 用户手动创建 | 是"笔记" |
| **提问节点** | 思考路径 | AI的提问 | 是"过程" |
| **回答节点** | 思考路径 | 用户的回答 | 是"过程" |
| **结论节点** | 思考路径 | 最终结论 | 是"过程+结果" |

### 4.2 节点视觉区分

| 节点类型 | 边框样式 | 图标 | 背景色 | 说明 |
|---------|---------|------|--------|------|
| **知识卡片** | 实线，默认/白色 | 📄 | 白色 | 从PDF/文档创建 |
| **对话节点** | 实线，蓝色 | 💡 | 浅蓝 #EFF6FF | 从Assistant对话添加 |
| **手动节点** | 实线，灰色 | ✏️ | 白色 | 用户手动创建 |
| **提问节点** | 虚线，蓝色 | 🤔 | 浅蓝 #EFF6FF | AI的提问 |
| **回答节点** | 虚线，绿色 | 💭 | 浅绿 #F0FDF4 | 用户的回答 |
| **结论节点** | 虚线，金色 | ✨ | 浅金 #FFFBEB | 最终结论 |

**节点标识**：
- 节点左上角显示类型图标
- 节点边框颜色和样式区分类型
- 思考路径节点有虚线边框，知识节点有实线边框

---

## 5. 跨视图流转机制：提升 (Promote)

为了避免视图隔离导致内容割裂，引入**"提升"**机制。

### 5.1 提升场景

**场景**：用户在"思考路径视图"中通过对话得出了一个重要结论，希望将其沉淀到自由画布。

### 5.2 提升操作流程

1. 用户选中目标节点（或框选多个节点）
2. 右键 → 选择"提升到自由画布"
3. **系统行为**：
   - 将该节点**复制**到自由画布视图的中心（或指定位置）
   - 在原节点和新节点之间建立**弱引用**（Backlink）
   - 原节点保留在思考路径视图中（作为历史/背景）

### 5.3 提升方式

**方式1：单个节点提升**
- 右键点击思考节点 → "提升到自由画布"
- 节点复制到自由画布，成为独立的知识节点
- 保留节点内容，但移除思考路径的连接

**方式2：批量提升**
- 框选多个节点 → 右键 → "提升到自由画布"
- 所有选中的节点提升到自由画布

**方式3：Section整体提升**
- 右键Section标题 → "提升所有节点到自由画布"
- Section内所有节点提升
- Section自动删除（如果所有节点都提升）

### 5.4 提升后的节点

- 保留原内容
- 移除思考路径的连接
- 可以重新连接到其他知识节点
- 可以编辑、删除、移动
- 保留弱引用链接回原节点（可选，用于追溯）

**价值**：让"过程"留在思考路径，让"结论"沉淀到自由画布。

---

## 6. 数据模型定义

### 6.1 CanvasNode 接口

```typescript
interface CanvasNode {
  id: string;
  type: 'knowledge' | 'insight' | 'manual' | 'question' | 'answer' | 'conclusion';
  title: string;
  content: string;
  x: number;
  y: number;
  width?: number;
  height?: number;
  color?: string;
  tags?: string[];
  sourceId?: string;        // 来源文档ID（知识卡片）
  sourcePage?: number;       // 来源页码
  sectionId?: string;       // 所属Section ID
  viewType: 'free' | 'thinking';  // 所属视图
  promotedFrom?: string;    // 提升来源节点ID（弱引用）
  createdAt: Date;
  updatedAt: Date;
}
```

### 6.2 CanvasSection 接口

```typescript
interface CanvasSection {
  id: string;
  title: string;
  viewType: 'free' | 'thinking';
  isCollapsed: boolean;
  nodeIds: string[];         // 包含的节点ID列表
  x: number;                // Section位置
  y: number;
  width?: number;           // Section边界宽度（自动计算）
  height?: number;          // Section边界高度（自动计算）
  createdAt: Date;
  updatedAt: Date;
  // 思考路径特有字段
  conversationId?: string;   // 关联的对话ID
  question?: string;        // 对话的问题
}
```

### 6.3 CanvasViewState 接口

```typescript
interface CanvasViewState {
  viewType: 'free' | 'thinking';
  viewport: {
    x: number;
    y: number;
    scale: number;
  };
  selectedNodeIds: string[];  // 当前选中的节点
  collapsedSectionIds: string[];  // 折叠的Section ID列表
}
```

### 6.4 Canvas 完整数据结构

```typescript
interface CanvasData {
  projectId: string;
  nodes: CanvasNode[];
  sections: CanvasSection[];
  edges: CanvasEdge[];       // 节点之间的连接
  viewStates: {
    free: CanvasViewState;
    thinking: CanvasViewState;
  };
  updatedAt: Date;
}
```

---

## 7. 详细交互设计

### 7.1 思考路径Section创建流程

#### 场景1：实时自动沉淀

1. 用户开始深度探索对话（Level 3）
2. 系统检测到深度探索模式
3. 自动创建"思考路径"Section（在思考路径视图的右侧区域）
4. AI提问 → 在Section内创建提问节点
5. 用户回答 → 在Section内创建回答节点
6. 建立连接：提问 → 回答 → 下一个提问
7. 用户得出结论 → 创建结论节点

#### 场景2：对话结束后沉淀

1. 深度探索对话完成
2. Assistant Panel显示"将思考过程添加到Canvas"
3. 用户点击
4. 系统分析对话，生成思考路径图
5. 创建新的"思考路径"Section
6. 用户确认后，节点添加到Section

### 7.2 Section折叠/展开交互

**折叠**：
- 点击Section标题栏 → Section折叠
- 折叠后只显示标题和节点数量
- 节点和连接隐藏（性能优化）

**展开**：
- 点击折叠的Section → Section展开
- 显示所有节点和连接
- 可以编辑、拖拽节点

**自动折叠**：
- 在宏观视图下（scale < 0.5），思考路径Section自动折叠
- 切换到微观视图时，保持用户的手动折叠状态

### 7.3 节点提升交互

**单个节点提升**：
1. 右键点击思考节点
2. 选择"提升到自由画布"
3. 节点复制到自由画布视图的中心
4. 移除思考路径的连接
5. 节点可以重新连接到其他知识节点

**批量提升**：
1. 框选多个思考节点
2. 右键 → "提升到自由画布"
3. 所有选中的节点提升
4. 如果Section内所有节点都提升，Section自动删除

**Section整体提升**：
1. 右键Section标题
2. 选择"提升所有节点到自由画布"
3. 所有节点提升
4. Section自动删除

### 7.4 自由画布Section创建

**手动创建Section**：
1. 用户框选多个节点（拖拽选择框）
2. 右键 → "创建Section"
3. 输入Section标题
4. 创建Section，包含选中的节点
5. 节点自动调整到Section边界内

**Section管理**：
- 拖拽Section标题栏 → 整体移动Section
- 右键Section标题 → 显示操作菜单（删除、重命名等）

---

## 8. 技术实现方案

### 8.1 技术栈

基于项目当前使用的 **Konva (HTML5 Canvas)** 技术栈：

- **渲染引擎**：Konva.js (react-konva)
- **Section实现**：`Konva.Group`
- **性能优化**：视口剔除、折叠时停止渲染

### 8.2 Section技术实现

**Konva.Group 实现**：
```typescript
// Section作为Konva.Group
<Group
  x={section.x}
  y={section.y}
  draggable={true}
  onDragEnd={handleSectionDrag}
>
  {/* Section标题栏 */}
  <Rect ... />
  <Text ... />
  
  {/* Section内容（折叠时不渲染） */}
  {!section.isCollapsed && (
    <>
      {section.nodeIds.map(nodeId => (
        <KnowledgeNode key={nodeId} node={nodes[nodeId]} />
      ))}
    </>
  )}
</Group>
```

**性能优化**：
- **Group变换**：拖拽时只需更新Group的变换矩阵，内部节点无需独立计算（O(1)）
- **渲染剔除**：
  - 折叠状态：Section折叠时，内部节点完全不渲染
  - 视口剔除：Konva自动检测并剔除视口外的Group
- **布局引擎隔离**：
  - 自由画布：绝对定位，无布局计算
  - 思考路径：流式布局（简单的从左到右排列），计算成本低

### 8.3 视图切换实现

**状态管理**：
```typescript
// 在StudioContext中管理视图状态
const [currentView, setCurrentView] = useState<'free' | 'thinking'>('free');
const [viewStates, setViewStates] = useState<{
  free: CanvasViewState;
  thinking: CanvasViewState;
}>({
  free: { viewType: 'free', viewport: { x: 0, y: 0, scale: 1 }, ... },
  thinking: { viewType: 'thinking', viewport: { x: 0, y: 0, scale: 1 }, ... },
});

// 切换视图时保存和恢复状态
const switchView = (newView: 'free' | 'thinking') => {
  // 保存当前视图状态
  saveViewState(currentView, viewStates[currentView]);
  // 切换到新视图
  setCurrentView(newView);
  // 恢复新视图状态
  loadViewState(newView);
};
```

**数据过滤**：
```typescript
// 根据当前视图过滤节点和Section
const visibleNodes = nodes.filter(node => node.viewType === currentView);
const visibleSections = sections.filter(section => section.viewType === currentView);
```

---

## 9. 实施路线图

### Phase 1: 基础架构 (MVP)

**目标**：实现侧边栏和视图切换基础架构

**任务**：
- [ ] 实现侧边栏UI组件（Canvas右侧，可折叠）
- [ ] 实现视图切换机制（数据层面过滤）
- [ ] 扩展数据模型（添加 `viewType`、`sectionId` 字段）
- [ ] 实现视图状态管理（每个视图独立的viewport）
- [ ] 更新后端API支持视图状态保存

**验收标准**：
- 用户可以通过侧边栏切换自由画布和思考路径视图
- 每个视图的状态独立保存和恢复
- 切换视图时Canvas正确显示对应视图的节点

### Phase 2: Section组件 + 思考路径自动沉淀

**目标**：实现Section组件和思考路径自动生成

**任务**：
- [ ] 实现基础Section组件（基于Konva.Group）
- [ ] 实现Section折叠/展开功能
- [ ] 实现Section整体拖拽
- [ ] 实现思考路径视图：对话自动生成节点并放入Section
- [ ] 实现思考路径Section自动创建（深度探索对话时）
- [ ] 实现节点类型视觉区分（实线/虚线边框，图标）

**验收标准**：
- 深度探索对话时，自动在思考路径视图创建Section
- Section可以折叠/展开，折叠时内部节点不渲染
- Section可以整体拖拽移动
- 思考路径节点有清晰的视觉区分

### Phase 3: 提升机制 + 自由画布Section

**目标**：实现跨视图提升和自由画布组织功能

**任务**：
- [ ] 实现"提升"机制：思考路径节点提升到自由画布
- [ ] 实现弱引用链接（Backlink）
- [ ] 实现自由画布Section创建（手动框选）
- [ ] 实现Section右键菜单（复制、提升、归档、删除）
- [ ] 优化Section性能（视口剔除、位图缓存）

**验收标准**：
- 用户可以将思考路径中的节点提升到自由画布
- 用户可以在自由画布中手动创建Section组织节点
- Section管理功能完整（复制、提升、归档、删除）

### Phase 4: 知识图谱视图（延后）

**目标**：实现知识图谱视图和力导向布局

**任务**：
- [ ] 实现知识图谱视图
- [ ] 接入力导向布局算法（d3-force）
- [ ] 实现实体类型过滤
- [ ] 实现自动聚类Section

**验收标准**：
- 用户可以在知识图谱视图中查看实体关系
- 节点自动布局，支持力导向算法
- 可以按实体类型过滤和聚类

---

## 10. 用户场景示例

### 场景一：使用思考路径回顾对话

**用户**：学生，学习"机器学习中的过拟合"

**体验**：
1. 开始深度探索对话，问题："如何理解过拟合？"
2. 系统自动在思考路径视图创建Section
3. AI提问，在Section内创建提问节点
4. 用户回答，在Section内创建回答节点
5. 完成对话，查看思考路径图
6. 将重要的结论节点提升到自由画布
7. 折叠Section，保持视图清晰

### 场景二：在自由画布中整理知识

**用户**：研究员，整理多个主题的知识

**体验**：
1. 在自由画布视图中，从PDF拖拽多个知识卡片
2. 框选相关节点，创建Section分组
3. 拖拽Section标题栏，整体移动相关节点
4. 切换到思考路径视图，回顾深度探索的思考过程
5. 将重要的思考节点提升到自由画布
6. 在自由画布中整合所有知识，形成知识体系

### 场景三：管理多个思考路径

**用户**：产品经理，研究多个问题

**体验**：
1. 完成多个深度探索对话，产生多个思考路径Section
2. 在思考路径视图中，展开需要的Section查看
3. 折叠不需要的Section，保持视图清晰
4. 将重要的结论节点提升到自由画布
5. 归档旧的思考路径Section，不干扰当前工作
6. 在自由画布中整合所有重要结论

---

## 11. 设计原则总结

### 11.1 分离关注点

- 思考路径（过程）与知识节点（内容）通过视图分离
- 通过Section和视觉区分实现清晰的组织

### 11.2 可折叠

- Section可以折叠，不占用Canvas空间
- 折叠时内部节点完全不渲染（性能优化）
- 需要时可以展开

### 11.3 可提升

- 重要的思考节点可以提升到自由画布
- 从"过程"变为"内容"
- 保留价值，去除临时性

### 11.4 状态独立

- 每个视图保持独立的状态
- 切换视图时自动保存和恢复
- 支持渐进式组织

### 11.5 性能优先

- 利用Konva.Group实现Section，拖拽成本O(1)
- 折叠时停止渲染内部节点
- 视口剔除优化

---

## 附录：与现有实现的集成

### A.1 当前Canvas实现

当前 `KonvaCanvas.tsx` 实现：
- 基础节点渲染（KnowledgeNode）
- 节点拖拽
- 视口平移和缩放
- 连接线渲染

### A.2 需要扩展的部分

1. **数据模型扩展**：
   - 在 `CanvasNode` 中添加 `viewType`、`sectionId` 字段
   - 添加 `CanvasSection` 接口
   - 添加 `CanvasViewState` 接口

2. **组件扩展**：
   - 创建 `CanvasSidebar` 组件
   - 创建 `CanvasSection` 组件（基于Konva.Group）
   - 扩展 `KnowledgeNode` 支持不同类型和视觉样式

3. **状态管理扩展**：
   - 在 `StudioContext` 中添加视图状态管理
   - 添加视图切换逻辑
   - 添加Section管理逻辑

4. **后端API扩展**：
   - 扩展Canvas保存API支持Section和视图状态
   - 添加视图状态查询API

---

## 版本历史

| 版本 | 日期 | 变更说明 |
|------|------|---------|
| v2.0 | 2025-12-07 | 整合三个PRD文档，聚焦MVP（自由画布+思考路径） |
| v1.1 | - | PRD_Canvas_Unified_Architecture.md |
| v1.0 | - | PRD_Canvas_Node_Organization.md, PRD_Canvas_View_Sidebar.md |
