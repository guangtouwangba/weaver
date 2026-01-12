# Implementation Plan: Fix Mindmap Generation

## Overview

本实现计划分为三个主要部分：布局算法改进、解析器改进、状态同步修复。使用 TypeScript 实现，使用 fast-check 进行属性测试。

## Tasks

- [ ] 1. 改进布局算法防止节点重叠
  - [ ] 1.1 实现重叠检测函数 `detectOverlaps`
    - 在 `layoutAlgorithms.ts` 中添加 AABB 碰撞检测
    - 支持自定义 padding 参数
    - 返回重叠节点对列表
    - _Requirements: 1.1, 1.4_

  - [ ] 1.2 实现重叠解决函数 `resolveAllOverlaps`
    - 迭代调整重叠节点位置
    - 移动整个子树而非单个节点
    - 设置最大迭代次数防止无限循环
    - _Requirements: 1.3, 1.4_

  - [ ] 1.3 实现动态节点高度计算 `calculateDynamicNodeHeight`
    - 基于内容长度估算行数
    - 考虑最大宽度和字体大小
    - 返回计算后的高度值
    - _Requirements: 1.2_

  - [ ] 1.4 改进 `balancedLayout` 函数
    - 集成动态高度计算
    - 在布局后调用重叠解决
    - 确保最小间距 40px 垂直、80px 水平
    - _Requirements: 1.1, 1.2, 1.3, 4.1, 4.3_

  - [ ] 1.5 编写布局算法属性测试
    - **Property 1: No Node Overlap After Layout**
    - **Validates: Requirements 1.1, 1.2, 1.3, 1.4**

- [ ] 2. Checkpoint - 验证布局改进
  - 确保所有布局测试通过，如有问题请询问用户

- [ ] 3. 改进 Mindmap Parser 确保单一根节点
  - [ ] 3.1 实现解析结果验证函数 `validateParseResult`
    - 统计根节点数量（depth=0 且无 parentId）
    - 返回验证结果和错误信息
    - _Requirements: 2.3_

  - [ ] 3.2 实现单一根节点保证函数 `ensureSingleRoot`
    - 当存在多个根节点时，将后续根节点连接为第一个根节点的子节点
    - 更新 depth 和 parentId
    - 创建相应的 edges
    - _Requirements: 2.2, 2.4_

  - [ ] 3.3 实现默认根节点创建 `createDefaultRoot`
    - 当 markdown 无 heading 时创建 "Overview" 根节点
    - 将所有现有节点连接为其子节点
    - _Requirements: 5.3_

  - [ ] 3.4 改进 `parseMarkdownToMindmap` 函数
    - 在解析完成后调用验证
    - 根据验证结果调用修复函数
    - 确保返回结果只有一个根节点
    - _Requirements: 2.1, 2.2, 2.3, 2.4_

  - [ ] 3.5 编写解析器属性测试
    - **Property 2: Single Root Node Guarantee**
    - **Validates: Requirements 2.1, 2.2, 2.3, 2.4**

- [ ] 4. Checkpoint - 验证解析器改进
  - 确保所有解析器测试通过，如有问题请询问用户

- [ ] 5. 修复生成完成状态同步问题
  - [ ] 5.1 检查并修复 `handleMindmapStreamingConcurrent` 中的状态更新
    - 确保 `completeGeneration` 被正确调用
    - 验证 WebSocket 消息处理逻辑
    - 添加详细日志便于调试
    - _Requirements: 3.1, 3.2_
    - **调查进展**: 已验证数据流正确，添加了调试日志到 `parseSourceMarkers` 和 `KonvaCanvas.onOpenSourceRef`

  - [ ] 5.2 检查并修复 `completeGeneration` 函数
    - 确保 `setCanvasNodes` 创建新数组引用
    - 确保 `setGenerationTasks` 正确移除任务
    - 验证状态更新顺序
    - _Requirements: 3.4_

  - [ ] 5.3 确保布局计算同步执行
    - 验证 `applyLayout` 不包含异步操作
    - 确保布局结果立即可用
    - _Requirements: 3.3_

  - [ ] 5.4 添加 WebSocket 连接失败回退逻辑
    - 确保回退到轮询时状态正确更新
    - 测试各种断连场景
    - _Requirements: 3.5_

  - [ ] 5.5 编写状态同步集成测试
    - 测试 WebSocket 完成事件处理
    - 测试状态更新时机
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_

  - [x] 5.6 修复时间戳跳转功能
    - **根本原因**: LLM refine 步骤删除了 `[TIME:XX:XX]` 标记
    - **修复方案**: 
      1. 更新 `refine.j2` 模板，添加更强的来源标记保留指令
         - 添加 "⚠️ CRITICAL: Source Marker Preservation" 专门章节
         - 添加正确/错误示例对比
         - 将保留标记从规则列表中的一项提升为独立的强制要求
      2. 添加后端校验逻辑 `_validate_marker_preservation`
         - 在 refine 后检查标记保留率
         - 如果超过 50% 的标记丢失，回退到原始内容
         - 添加详细日志记录标记数量变化
    - **已添加调试日志**:
      - `mindmap-parser.ts`: `parseSourceMarkers` 函数记录 TIME 标记和 documentId
      - `KonvaCanvas.tsx`: `onOpenSourceRef` 记录 sourceId 和可用的 urlContents
    - **修改文件**: 
      - `app/backend/src/research_agent/infrastructure/llm/prompts/templates/agents/mindmap/refine.j2`
      - `app/backend/src/research_agent/application/graphs/mindmap_graph.py`
    - _Requirements: 5.4_

- [ ] 6. Checkpoint - 验证状态同步修复
  - 确保所有状态同步测试通过，如有问题请询问用户

- [ ] 7. 额外改进和优化
  - [ ] 7.1 改进 heading 层级解析
    - 正确处理 ##, ###, #### 等多级 heading
    - 确保 bullet points 正确附加到最近的 heading
    - _Requirements: 5.1, 5.2_

  - [ ] 7.2 改进 source marker 提取
    - 支持 [PAGE:X], [Page X], [TIME:MM:SS] 等格式
    - 确保 sourceRefs 正确填充
    - _Requirements: 5.4_

  - [ ] 7.3 编写额外属性测试
    - **Property 3: Balanced Layout Distribution**
    - **Property 4: Parent-Child Hierarchy Preservation**
    - **Property 5: Layout Performance**
    - **Property 6: Source Marker Extraction**
    - **Property 7: Heading Hierarchy Correctness**
    - **Validates: Requirements 4.1, 4.3, 4.4, 5.1, 5.2, 5.4**

- [ ] 8. Final Checkpoint - 完整验证
  - 运行所有测试确保通过
  - 手动测试完整生成流程
  - 如有问题请询问用户

## Notes

- All tasks are required for complete implementation
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties
- Unit tests validate specific examples and edge cases
- 使用 fast-check 库进行属性测试
- 测试配置：每个属性测试运行 100 次迭代
