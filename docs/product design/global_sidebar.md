# 产品需求文档 (PRD): Global Navigation Rail (全局导航轨)

## 1\. 组件概述

  * **组件名称**：Global Sidebar / Navigation Rail
  * **位置**：视口 (Viewport) 最左侧，`position: fixed`，全高。
  * **视觉规格**：
      * **宽度**：固定 **72px** (参考截图比例)。
      * **背景**：极简白/浅灰，右侧有一条 1px 的分割线 (`border-right`)。
      * **层级 (Z-Index)**：最高，始终位于所有层之上。
  * **核心交互**：点击图标切换**一级路由 (Primary Route)**，并决定**二级侧边栏 (Secondary Panel)** 的内容。

-----

## 2\. 功能模块拆解 (Functional Breakdown)

我们将侧边栏从上到下分为三个区域：**Command (指令区)**、**Context (模式区)**、**User (用户区)**。

### 2.1 顶部：Command Zone (指令区)

| UI 元素 | 图标描述 | 交互逻辑 (Interaction) | 对应需求/价值 |
| :--- | :--- | :--- | :--- |
| **Home / Command** | **黑色圆角矩形 + 白色 "K"** (Logo) | **单击**：回到 Dashboard 首页 (所有项目的概览)。<br>**双击/快捷键 (`Cmd+K`)**：呼出 **Global Command Palette**。允许用户输入指令（如 "Create new project", "Search global concept"）。 | **全局掌控**<br>提供一个类似于“开始菜单”的万能入口，确保用户不会迷路。 |

### 2.2 中部：Context Zone (模式切换区)

这是该组件的核心，对应用户认知的三个阶段：**收集 $\rightarrow$ 内化 $\rightarrow$ 链接**。

| 模式 (Mode) | 图标 | 选中态样式 (Active State) | 核心行为 (Behavior) | 关联的二级面板 (Secondary Panel) |
| :--- | :--- | :--- | :--- | :--- |
| **1. Inbox Mode**<br>(收集模式) | **Tray (收件箱)**<br>*(截图选中项)* | 蓝色圆角矩形边框 + 蓝色图标 | **功能**：进入“信息清洗站”。<br>**视图**：右侧主区域显示未分类的列表。<br>**角标**：若有未读条目，图标右上角显示红点 (Red Dot)。 | **Filter Panel**<br>(可选) 显示来源过滤器：<br>• Web Clips<br>• Uploads<br>• Mobile |
| **2. Studio Mode**<br>(工作台模式) | **Layout (看板)** | 黑色填充/深色背景 | **功能**：进入“深度学习/项目管理”。<br>**视图**：显示 Active Topics 卡片流。<br>**逻辑**：点击具体项目后，**二级侧边栏**滑出。 | **Project Navigator**<br>(即之前设计的“Path + Library”栏)<br>• Curriculum<br>• Files Tree |
| **3. Brain Mode**<br>(第二大脑) | **Brain (大脑)** | 黑色填充/深色背景 | **功能**：进入“全域知识图谱”。<br>**视图**：全屏无边框的 Canvas/Graph View。<br>**逻辑**：强调沉浸感，可能自动收起二级侧边栏。 | **Graph Controls**<br>(可选) 图谱控制器：<br>• Filter by Tag<br>• Time Range<br>• Clusters |

### 2.3 底部：User Zone (用户区)

| UI 元素 | 图标描述 | 交互逻辑 (Interaction) | 对应需求/价值 |
| :--- | :--- | :--- | :--- |
| **Profile** | **圆形用户头像** | **单击**：弹出 Popover 菜单。<br>• Settings<br>• Billing (Pro Plan)<br>• Dark Mode Toggle<br>• Sync Status (Last synced: 2m ago) | **个人设置与状态**<br>保持界面底部的稳重感。 |

-----

## 3\. 关键交互细节 (UX Micro-interactions)

为了让这个极简侧边栏好用，必须配合细腻的交互：

### 3.1 双层导航逻辑 (The Drawer Interaction)

这是解决“侧边栏太窄放不下目录”的关键逻辑。

  * **状态 A (首页)**：点击 `Dashboard` 图标 $\rightarrow$ 右侧显示卡片流 $\rightarrow$ **无二级侧边栏**。
  * **状态 B (进入项目)**：在卡片流中点击 "AI Agent" 项目 $\rightarrow$ **二级侧边栏 (Project Navigator) 从 Rail 右侧滑出** $\rightarrow$ 形成 `[Rail] | [Panel] | [Canvas]` 的三栏布局。
  * **状态 C (折叠)**：用户可以点击二级侧边栏边缘的 `<` 按钮将其收起，仅保留 Rail，最大化画布空间。

### 3.2 键盘快捷键 (Shortcuts)

为专业用户提供无鼠标操作体验：

  * `Cmd + 1` $\rightarrow$ Switch to **Inbox**
  * `Cmd + 2` $\rightarrow$ Switch to **Studio**
  * `Cmd + 3` $\rightarrow$ Switch to **Brain**
  * `Cmd + /` $\rightarrow$ Toggle Secondary Sidebar (展开/收起二级栏)

### 3.3 拖拽投喂 (Global Drag & Drop)

  * **场景**：用户从桌面拖拽一个 PDF 文件。
  * **反馈**：当文件经过 Navigation Rail 上方时：
      * **Inbox 图标**高亮并“张开”：表示“放入收集箱”。
      * **Dashboard 图标**高亮：表示“放入具体项目”（需悬停 1s 等待二级菜单展开）。
      * **Brain 图标**高亮：表示“直接进行语义分析并存入库”。

