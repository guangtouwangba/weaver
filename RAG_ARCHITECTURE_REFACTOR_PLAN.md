---
name: RAG系统架构改造
overview: 将当前RAG系统改造为符合目标设计的架构：1) 完善异步文档处理流程（添加摘要生成、WebSocket通知）；2) 优化RAG查询流程（明确并发检索、支持文档全文模式）；3) 统一文档上传接口
todos:
  - id: add_summary_field
    content: 添加文档摘要字段到数据库Schema和实体模型
    status: completed
  - id: enhance_pdf_parsing
    content: 增强PDF解析逻辑，提取并保存"页码-字符索引映射表"(page_map)到parsing_metadata，用于后续精确页码计算
    status: pending
  - id: implement_summary_generation
    content: 在DocumentProcessorTask中实现文档摘要生成功能
    status: completed
  - id: create_websocket_service
    content: 创建后端WebSocket通知服务，支持文档处理状态推送
    status: pending
  - id: add_websocket_endpoint
    content: 添加后端WebSocket API端点，供前端连接接收通知
    status: pending
  - id: integrate_websocket_notification
    content: 在DocumentProcessorTask中集成WebSocket通知
    status: pending
  - id: create_document_retrieval_service
    content: 创建文档全文检索服务，支持chunks和full_document两种模式，实现Adaptive Context Strategy（动态降级）以防Token爆炸
    status: pending
  - id: implement_mega_prompt
    content: 实现Mega-Prompt构建函数，使用XML标签结构（system_instruction、documents、output_rules、thinking_process、user_query），支持文档全文模式和引用标记机制。在output_rules中添加Few-Shot示例强化Prompt，创建容错解析服务支持多种引用格式变体
    status: pending
  - id: create_citation_parser
    content: 创建XML引用标签解析服务，解析<cite doc_id="doc_01" quote="...">格式，提取doc_id和quote
    status: pending
  - id: create_text_locator
    content: 创建原文定位服务（Quote-to-Coordinate），使用rapidfuzz在全文中模糊匹配定位quote的位置，结合page_map计算精确页码，返回char_start/char_end/page_number
    status: pending
  - id: implement_streaming_citation_parsing
    content: 在RAG Graph流式生成中实时解析XML cite标签，调用定位服务计算位置，发送citation事件给前端
    status: pending
  - id: update_rag_graph
    content: 更新RAG Graph流程，支持文档全文检索和Mega-Prompt模式
    status: pending
  - id: unify_upload_api
    content: 统一文档上传接口，废弃同步方式，统一使用异步接口
    status: pending
  - id: add_config_options
    content: 添加RAG检索模式配置选项（chunks/full_document/auto）
    status: pending
  - id: update_api_responses
    content: 更新后端API响应模型，添加task_id和summary字段
    status: pending
  - id: update_frontend_types
    content: 更新前端TypeScript类型定义（ProjectDocument添加summary、task_id字段，ChatMessage添加citations字段）
    status: pending
  - id: create_websocket_client
    content: 创建前端WebSocket客户端工具类，支持文档状态更新连接和自动重连
    status: pending
  - id: integrate_websocket_upload
    content: 在文档上传流程中集成WebSocket，实时接收处理状态更新，替换轮询机制
    status: pending
  - id: display_document_summary
    content: 在文档列表和详情中显示文档摘要（支持折叠/展开）
    status: pending
  - id: render_citation_marks
    content: 在聊天界面中渲染XML格式的cite标签为可点击元素，处理citation事件，实现点击跳转并高亮PDF段落（使用搜索功能）
    status: pending
  - id: support_citations_event
    content: 支持SSE流中的citations事件类型，显示结构化引用信息（如果后端添加）
    status: pending
---

# RAG系统架构改造计划

## 目标设计对比分析

### 当前系统状态

- ✅ 已有异步Worker系统（数据库队列）
- ✅ 已有混合搜索（hybrid search）
- ✅ 已有查询重写、Rerank、流式返回
- ❌ 缺少文档摘要生成
- ❌ 缺少WebSocket通知
- ❌ RAG流程使用chunks而非文档全文
- ❌ 存在同步和异步两套上传接口

### 目标设计要求

1. **阶段一（数据入库）**：异步处理 + 摘要生成 + WebSocket通知 + 页码映射构建
2. **阶段二（RAG查询）**：并发检索 + 拉取文档全文 + Mega-Prompt + 精确引用定位

---

## 改造任务

### 1. 文档处理流程增强（后端）

#### 1.0 增强PDF解析（页码映射）

**文件**: `app/backend/src/research_agent/worker/tasks/document_processor.py`

**关键问题**: 为了支持Quote-to-Coordinate（从引用文本反推页码），必须在解析阶段建立字符索引与页码的映射关系。纯文本不包含分页信息，如果不保存此映射，后续无法计算引用位于第几页。

**实现要点**:
1. 在PDF解析循环中，记录每一页的起始字符索引和结束字符索引。
2. 将此映射表存储在`DocumentModel.parsing_metadata`中。

```python
# parsing_metadata 结构示例
metadata = {
    "page_map": [
        {"page": 1, "start": 0, "end": 1500},
        {"page": 2, "start": 1501, "end": 3200},
        # ...
    ],
    # ... 其他元数据
}
doc.parsing_metadata = metadata
```

#### 1.1 添加文档摘要生成功能

**文件**: `app/backend/src/research_agent/worker/tasks/document_processor.py`

- 在`DocumentProcessorTask.execute()`中添加摘要生成步骤
- 位置：在PDF解析后、chunking之前
- 调用LLM生成文档摘要（使用OpenRouter）
- 保存摘要到`DocumentModel.summary`字段（需要migration）

**实现要点**:

```python
# Step 2.5: Generate document summary
logger.info(f"📝 Step 2.5: Generating document summary")
summary = await self._generate_summary(full_content, llm)
doc.summary = summary
```

#### 1.2 添加WebSocket通知机制

**新文件**: `app/backend/src/research_agent/infrastructure/websocket/notification_service.py`

- 创建WebSocket通知服务
- 支持文档处理状态更新（processing → ready → error）
- 使用FastAPI WebSocket

**集成点**:

- `DocumentProcessorTask`完成后发送通知
- API层提供WebSocket端点：`/ws/projects/{project_id}/documents/{document_id}`

#### 1.3 统一文档上传接口

**文件**: `app/backend/src/research_agent/api/v1/documents.py`

- 废弃同步的`upload_document`端点（或标记为deprecated）
- 统一使用`confirm_upload`异步接口
- 确保所有上传都返回202 Accepted + Task ID

---

### 2. RAG查询流程优化（后端）

#### 2.1 明确并发检索流程

**文件**: `app/backend/src/research_agent/application/graphs/rag_graph.py`

当前`hybrid_search`内部已并发，但需要：

- 在`retrieve()`节点中明确显示并发检索步骤
- 添加日志标识并发检索开始/结束
- 确保向量检索和关键词检索真正并行执行

**修改位置**: `retrieve()`函数（约642行）

#### 2.2 添加文档全文检索模式与动态降级

**新文件**: `app/backend/src/research_agent/domain/services/document_retrieval_service.py`

- 创建文档全文检索服务
- 支持两种模式：
  - **Chunks模式**（当前）：返回chunks，适合精确检索
  - **Full Document模式**（新增）：返回Top-K文档全文，适合Mega-Prompt

**关键风险控制**: 上下文爆炸风险。如果多个大文档全文叠加超过LLM上下文限制（或导致费用过高），必须有降级策略。

**实现逻辑**:

```python
async def retrieve_documents_for_rag(
    query: str,
    project_id: UUID,
    mode: str = "chunks",  # "chunks" | "full_document" | "auto"
    top_k: int = 5,
) -> List[Document]:
    if mode == "full_document" or mode == "auto":
        # 1. 先检索chunks获取Top-K文档ID
        chunks = await vector_store.search(...)
        doc_ids = get_top_documents(chunks, top_k)
        
        # 2. 并发拉取文档全文
        documents = await asyncio.gather(*[
            get_document_full_content(doc_id) for doc_id in doc_ids
        ])
        
        # 3. 动态上下文降级（Adaptive Context Strategy）
        # 防止Token爆炸：如果总Token超过阈值，自动降级处理
        total_tokens = sum(doc.content_token_count or 0 for doc in documents)
        TOKEN_LIMIT = 30000  # 设定安全阈值（根据模型调整，例如GPT-4o mini可设更高）
        
        if total_tokens > TOKEN_LIMIT:
            logger.warning(f"Context size {total_tokens} exceeds limit. Switching to Adaptive Mode.")
            # 策略A：仅保留Top-1最相关文档的全文，其他文档降级为Top-Chunks拼接
            # 策略B（简单）：仅返回Top-1文档全文
            documents = documents[:1] 
            
        return documents
    else:
        # 当前chunks模式
        return await vector_store.search(...)
```

#### 2.3 构建Mega-Prompt支持（XML结构化）

**文件**: `app/backend/src/research_agent/infrastructure/llm/prompts/rag_prompt.py`

根据Mega-Prompt标准定义，需要实现XML标签结构化的提示词。这是让大模型理解长文本的最佳实践。

**Mega-Prompt完整结构**（参考NotebookLM模式）：

```xml
<system_instruction>
You are an expert {role}. Your task is to answer the user's question based on the provided documents.

You must cite specific data from the documents. If the information is not present in the documents, state that you do not know.
At the end of each sentence in your answer, append a citation using the [doc_id] format, e.g., [doc_01].
</system_instruction>

<documents>
  <document id="doc_01" title="2023_Q4_Financial_Report.pdf" page_count="45">
    ...Full text parsed from PDF (possibly tens of thousands of words)...
  </document>
  
  <document id="doc_02" title="2024_Q1_Financial_Report.pdf" page_count="48">
    ...Full text parsed from PDF (possibly tens of thousands of words)...
  </document>
</documents>

<output_rules>
Please output in Markdown format.
At the end of each sentence, append a citation using the [doc_id] format, e.g., [doc_01].
First list core points, then provide a detailed comparison.
If data is involved, cite specific numbers.
</output_rules>

<thinking_process>
Before answering, please think:
1. Identify key metrics/concepts in the user's question.
2. Locate these metrics/concepts in the documents.
3. Extract relevant data and context.
4. Organize your language and ensure accurate citations.
</thinking_process>

<user_query>
How has the gross margin changed over these two quarters? What are the main reasons?
</user_query>
```

**实现要点**：

1. **创建`build_mega_prompt()`函数**：

   - 替代或增强现有的`build_long_context_prompt()`
   - 接收参数：`query`, `documents` (List[DocumentModel]), `intent_type` (可选)
   - 返回完整的XML格式Mega-Prompt字符串

2. **XML标签结构化组织**：

   - `<system_instruction>`: 系统角色、任务说明、引用要求
   - `<documents>`: 包含所有文档全文，每个文档用`<document id="doc_XX" title="..." page_count="...">`包裹
   - `<output_rules>`: 输出格式（Markdown）、引用标记方式（`[doc_id]`）
   - `<thinking_process>`: 根据意图类型提供思维链引导（可选，提升推理质量）
   - `<user_query>`: 用户问题

3. **引用标记机制（鲁棒性设计）**：

   **问题**: LLM可能不严格按照`[doc_01]`格式输出，常见变体包括：
   - `(doc 1)`、`[Document 1]`、`(doc_01)`等
   - 引用标记位置不固定（句首而非句尾）
   - 完全忽略引用标记要求

   **解决方案（多层级）**：

   **方案A: XML摘录格式（推荐，支持精确定位）**
   - 要求LLM输出XML格式的`<cite>`标签，包含原文摘录
   - 支持后端定位到具体字符位置，实现精确跳转和高亮
   - 格式：
     ```xml
     <output_rules>
     Citation Format Requirements (Must be strictly followed):
     
     1. Please output the answer in Markdown format.
     2. You must cite verbatim text from the documents to support your points.
     3. Citation Format: Use the XML tag <cite doc_id="doc_01" quote="exact sentence from the document...">your conclusion</cite>.
        - doc_id: The ID of the document (format: doc_01, doc_02, etc.)
        - quote: Must be a continuous text fragment copied exactly from the document without modification (at least 5-10 words).
     4. Examples:
        Correct Examples:
        - <cite doc_id="doc_01" quote="Q4 2023 gross margin was 45.2%, an increase of 2.3 percentage points from the previous quarter">According to the financial report, gross margin improved significantly</cite>
        - <cite doc_id="doc_02" quote="Revenue increased by 15%, mainly driven by new product contributions">Revenue growth was primarily due to new product lines</cite>
        
        Incorrect Examples (Do NOT use):
        - "Gross margin was 45.2% [doc_01]"  ❌ Missing quote attribute
        - <cite doc_id="doc_01">Gross margin improved</cite>  ❌ Missing quote attribute
        - <cite doc_id="doc_01" quote="Gross margin">Conclusion</cite>  ❌ quote too short (less than 5 words)
     
     Rules:
     1. Every factual statement must be wrapped in a <cite> tag.
     2. The 'quote' must be verbatim text from the document, no modifications or summarization.
     3. The 'quote' length must be at least 5-10 words to ensure unique localization.
     4. The 'doc_id' format must be strict: doc_XX (XX is two digits).
     </output_rules>
     ```
   
   **方案B: 简单文本标记（备选，仅支持文档级跳转）**
   - 如果不需要精确定位，可以使用简单的`[doc_01]`格式
   - 只能跳转到文档，无法高亮具体段落
   - 提供Few-Shot示例强化格式要求

   **方案C: 原文定位服务（核心功能）**
   
   **新文件**: `app/backend/src/research_agent/utils/text_locator.py`
   
   - 实现"原文摘录 + 后端定位"策略（Quote-to-Coordinate）
   - **核心依赖**: 必须结合 `DocumentModel.parsing_metadata['page_map']` 才能计算出页码
   - 使用模糊匹配在全文中定位quote的位置
   - 支持精确匹配和模糊匹配两种模式
   - 返回字符位置索引（char_start, char_end），可用于计算page_number
   
   **实现逻辑**:
   ```python
   from rapidfuzz import fuzz, process
   
   def locate_citation_in_document(
       full_text: str, 
       quote: str, 
       threshold: int = 85
   ) -> Tuple[int, int, float]:
       """
       在全文中定位摘录的位置（Quote-to-Coordinate策略）。
       
       Args:
           full_text: 文档全文
           quote: LLM摘录的原文片段
           threshold: 模糊匹配阈值（0-100）
       
       Returns:
           (start_index, end_index, match_score)
           如果未找到，返回 (None, None, 0)
       """
       # 1. 精确匹配（最快）
       start = full_text.find(quote)
       if start != -1:
           return start, start + len(quote), 100.0
       
       # 2. 模糊匹配（处理LLM可能的细微修改）
       # 注意：可能存在重复文本问题，默认匹配第一个最佳结果
       # 如果需要更高精度，可结合上下文（如前一句话）进行定位
       sentences = split_into_sentences(full_text)
       best_match = process.extractOne(quote, sentences, scorer=fuzz.ratio)
       
       if best_match and best_match[1] >= threshold:
           matched_sentence = best_match[0]
           start = full_text.find(matched_sentence)
           if start != -1:
               return start, start + len(matched_sentence), best_match[1]
       
       return None, None, 0.0
   ```
   
   **方案D: XML标签解析服务**
   
   **文件**: `app/backend/src/research_agent/domain/services/citation_parser.py`
   
   - 解析LLM输出的XML格式`<cite>`标签
   - 提取doc_id和quote
   - 调用text_locator定位原文位置
   - 支持流式解析（边生成边解析）
   
   **实现逻辑**:
   ```python
   import re
   from typing import Optional, Dict
   
   def parse_cite_tags(text: str) -> List[Dict]:
       """解析XML格式的cite标签"""
       pattern = r'<cite\s+doc_id="(doc_\d+)"\s+quote="([^"]+)">([^<]+)</cite>'
       matches = re.finditer(pattern, text)
       return [
           {
               'doc_id': m.group(1),
               'quote': m.group(2),
               'conclusion': m.group(3),
               'start': m.start(),
               'end': m.end()
           }
           for m in matches
       ]
   ```
   
   **方案E: 容错解析（兼容旧格式）**
   - 作为备选，支持简单的`[doc_01]`格式（如果用户选择简单模式）
   - 正则表达式兼容多种变体

   **方案C: 结构化输出（JSON Mode，备选）**
   - 如果模型支持JSON Mode，强制输出结构化格式
   - 格式：`{"answer": "...", "citations": [{"text": "...", "doc_id": "doc_01", "position": "sentence_end"}]}`
   - 优点：解析稳定，无需正则匹配
   - 缺点：牺牲流式输出体验（需要流式JSON解析，复杂度高）
   - 建议：作为配置选项，默认使用方案A+B，高级用户可选择JSON Mode

   **推荐实现策略（Quote-to-Coordinate）**：
   1. **默认方案**：方案A（XML摘录格式）+ 方案C（原文定位服务）+ 方案D（XML解析服务）
   2. **工作流程**：
      - LLM输出：`<cite doc_id="doc_01" quote="原文片段">结论</cite>`
      - 后端解析：提取doc_id和quote
      - 后端定位：调用`locate_citation_in_document()`在全文中定位quote位置
      - **页码计算**：根据 char_start 在 page_map 中查找对应页码
      - 流式发送：发送citation事件给前端，包含char_start、char_end、page_number
      - 前端跳转：点击引用时，使用quote文本在PDF中搜索并高亮
   3. **配置选项**：在`config.py`中添加`mega_prompt_citation_mode`：
      - `"xml_quote"`（默认）：XML摘录格式 + 原文定位（支持精确跳转）
      - `"text_markers"`：简单文本标记（仅文档级跳转）
      - `"json_mode"`：结构化JSON输出（如果模型支持）
   4. **依赖库**：需要安装`rapidfuzz`用于模糊匹配

4. **意图驱动的思维链**：

   - 根据`intent_type`（factual/conceptual/comparison等）提供不同的思考步骤
   - 例如：comparison类型提供"对比分析"的思维链

5. **引用标记容错解析服务**：

   **新文件**: `app/backend/src/research_agent/domain/services/citation_parser.py`
   
   - 创建统一的引用标记解析服务
   - 支持多种格式变体：`[doc_01]`、`(doc_01)`、`[Document 1]`、`(doc 1)`等
   - 位置容错：支持句首、句中、句尾的引用标记
   - 返回结构化结果：`List[CitationMatch]`，包含doc_index、位置、原始文本等
   - 用于后端验证和前端渲染

6. **与现有Citation服务的集成**：

   - 检查`research_agent/domain/services/citation_service.py`
   - 确保Mega-Prompt生成的引用标记可以被解析和验证
   - 容错解析服务可以作为CitationService的补充

**集成点**: `rag_graph.py`的`generate_long_context()`函数（约847行）

- 长上下文模式时调用`build_mega_prompt()`而非`build_long_context_prompt()`
- 确保传递完整的文档元数据（id、filename、page_count等）
- 传递`intent_type`用于生成对应的思维链引导
- 根据配置选择引用标记模式（text_markers或json_mode）
- 如果使用text_markers模式，在生成后使用容错解析服务验证和提取引用

**后续优化（Phase 2）**：

- Context Caching（上下文缓存）：将Mega-Prompt的计算状态缓存，复用时可降低90%+成本
- 流式输出优化：处理长文本时的延迟优化

#### 2.4 更新RAG Graph流程（流式解析XML引用）

**文件**: `app/backend/src/research_agent/application/graphs/rag_graph.py`

修改`stream_rag_response()`函数（约1097行）：

- 在检索后添加文档全文拉取步骤（如果使用全文模式）
- 确保Top-K文档全文并发拉取
- 传递完整文档给生成节点
- **新增**：在流式生成过程中实时解析XML格式的`<cite>`标签
- **新增**：检测到完整的`<cite>`标签后，立即调用定位服务计算位置
- **新增**：发送citation事件给前端，包含定位信息

**流式解析实现要点**:

```python
# 在generate_long_context()或流式生成循环中
buffer = ""  # 累积未完成的标签
doc_contents = {}  # 存储文档全文，用于定位

async for token in llm_stream:
    buffer += token
    
    # 检测完整的 <cite> 标签
    cite_pattern = r'<cite\s+doc_id="(doc_\d+)"\s+quote="([^"]+)">([^<]+)</cite>'
    matches = re.finditer(cite_pattern, buffer)
    
    for match in matches:
        doc_id = match.group(1)  # doc_01
        quote = match.group(2)   # 原文片段
        conclusion = match.group(3)  # LLM的结论
        
        # 获取文档全文
        doc_model = get_document_by_id(doc_id)
        full_text = doc_model.full_content
        
        # 定位quote在原文中的位置
        char_start, char_end, score = locate_citation_in_document(
            full_text, quote, threshold=85
        )
        
        if char_start is not None:
            # 计算page_number（如果有分页信息）
            # 关键：使用 parsing_metadata 中的 page_map
            page_map = doc_model.parsing_metadata.get("page_map", [])
            page_number = calculate_page_number(page_map, char_start)
            
            # 发送citation事件
            yield {
                "type": "citation",
                "data": {
                    "doc_id": doc_id,
                    "document_id": doc_model.id,  # 实际UUID
                    "quote": quote,
                    "conclusion": conclusion,
                    "char_start": char_start,
                    "char_end": char_end,
                    "page_number": page_number,
                    "match_score": score
                }
            }
        
        # 从buffer中移除已处理的标签
        buffer = buffer[:match.start()] + conclusion + buffer[match.end():]
```

---

### 3. 数据库Schema更新（后端）

#### 3.1 添加文档摘要字段

**新migration文件**: `app/backend/alembic/versions/YYYYMMDD_HHMMSS_add_document_summary.py`

```python
def upgrade():
    op.add_column('documents', sa.Column('summary', sa.Text(), nullable=True))

def downgrade():
    op.drop_column('documents', 'summary')
```

#### 3.2 更新Document实体

**文件**: `app/backend/src/research_agent/domain/entities/document.py`

- 添加`summary: Optional[str]`字段

**文件**: `app/backend/src/research_agent/infrastructure/database/models.py`

- 更新`DocumentModel`添加`summary`字段

---

### 4. 配置和API更新（后端）

#### 4.1 添加RAG模式配置

**文件**: `app/backend/src/research_agent/config.py`

```python
rag_retrieval_mode: str = "chunks"  # "chunks" | "full_document" | "auto"
mega_prompt_citation_mode: str = "xml_quote"  # "xml_quote" | "text_markers" | "json_mode"
# xml_quote: XML摘录格式 + 原文定位（默认，支持精确跳转和高亮）
# text_markers: 简单文本标记（仅文档级跳转）
# json_mode: 结构化JSON输出（更稳定，但流式体验差）

# 原文定位配置
citation_match_threshold: int = 85  # 模糊匹配阈值（0-100）
```

#### 4.2 更新API响应

**文件**: `app/backend/src/research_agent/api/v1/documents.py`

- `DocumentUploadResponse`添加`task_id`字段
- `DocumentResponse`添加`summary`字段

#### 4.3 添加WebSocket端点

**新文件**: `app/backend/src/research_agent/api/v1/websocket.py`

```python
@router.websocket("/ws/projects/{project_id}/documents/{document_id}")
async def document_status_websocket(...):
    # WebSocket连接，推送文档处理状态更新
```

---

## 前端改造任务

### 5. 前端API类型更新

#### 5.1 更新ProjectDocument接口

**文件**: `app/frontend/src/lib/api.ts`

- 添加`summary?: string`字段
- 添加`task_id?: string`字段（用于跟踪异步任务）

```typescript
export interface ProjectDocument {
  id: string;
  project_id: string;
  filename: string;
  file_size: number;
  page_count: number;
  status: 'pending' | 'processing' | 'ready' | 'error';
  graph_status?: 'pending' | 'processing' | 'ready' | 'error';
  summary?: string;  // 新增：文档摘要
  task_id?: string;  // 新增：异步任务ID
  created_at: string;
}
```

#### 5.2 更新ChatMessage类型

**文件**: `app/frontend/src/lib/api.ts`

- 添加`citations`字段支持（如果后端添加）

```typescript
export interface ChatMessage {
  message: string;
  document_id?: string;
  citations?: Array<{  // 新增：Mega-Prompt模式的引用
    document_id: string;
    page_number: number;
    char_start: number;
    char_end: number;
    snippet: string;
  }>;
}
```

---

### 6. WebSocket客户端实现

#### 6.1 创建WebSocket工具

**新文件**: `app/frontend/src/lib/websocket.ts`

- 创建WebSocket客户端封装
- 支持自动重连机制
- 处理连接状态管理
- 提供事件订阅/取消订阅API

**实现要点**:

```typescript
export class DocumentWebSocket {
  private ws: WebSocket | null = null;
  private reconnectAttempts = 0;
  private listeners: Map<string, Set<Function>> = new Map();
  
  connect(projectId: string, documentId: string): void;
  disconnect(): void;
  on(event: 'status_update', callback: (data: DocumentStatusUpdate) => void): void;
  off(event: string, callback: Function): void;
}
```

#### 6.2 集成WebSocket到上传流程

**文件**: `app/frontend/src/components/studio/SourcePanel.tsx`

- 在`handleUpload()`中，上传成功后建立WebSocket连接
- 监听文档处理状态更新
- 实时更新文档状态显示

**实现逻辑**:

```typescript
const newDoc = await documentsApi.uploadWithPresignedUrl(...);
setDocuments([...documents, newDoc]);

// 如果返回task_id，建立WebSocket连接
if (newDoc.task_id || newDoc.status === 'pending' || newDoc.status === 'processing') {
  const ws = new DocumentWebSocket();
  ws.connect(projectId, newDoc.id);
  ws.on('status_update', (data) => {
    // 更新文档状态
    setDocuments(prev => prev.map(d => 
      d.id === newDoc.id ? { ...d, status: data.status, summary: data.summary } : d
    ));
  });
}
```

---

### 7. 替换轮询为WebSocket

#### 7.1 移除轮询逻辑

**文件**: `app/frontend/src/components/studio/SourcePanel.tsx`

- 删除现有的轮询逻辑（如果有）
- 改为使用WebSocket实时更新

#### 7.2 在StudioContext中管理WebSocket

**文件**: `app/frontend/src/contexts/StudioContext.tsx`

- 在`StudioProvider`中管理WebSocket连接
- 监听文档状态更新事件
- 自动更新文档列表状态
- 清理：组件卸载时断开连接

---

### 8. 文档摘要显示

#### 8.1 在文档列表中显示摘要

**文件**: `app/frontend/src/components/studio/SourcePanel.tsx`

- 在文档卡片/列表中显示摘要（如果有）
- 可以折叠/展开摘要
- 摘要样式：灰色文字，较小字号

#### 8.2 文档详情中显示摘要

**文件**: `app/frontend/src/components/studio/SourcePanel.tsx`

- 在PDF阅读器上方或侧边显示文档摘要
- 提供"查看摘要"按钮或自动展开

---

### 9. 聊天响应增强

#### 9.1 处理Mega-Prompt引用标记（XML格式 + 精确定位）

**文件**: `app/frontend/src/components/studio/AssistantPanel.tsx`

- 处理流式接收的citation事件（包含定位信息）
- 渲染XML格式的`<cite>`标签为可点击元素
- 点击引用时跳转到PDF并高亮对应段落

**实现要点（流式处理citation事件）**:

```typescript
// 在handleSend()的流处理循环中
} else if (chunk.type === 'citation') {
    // 处理Mega-Prompt模式的引用（包含精确定位信息）
    const citation = chunk.data;
    flushSync(() => {
      setChatMessages(prev => prev.map(m => 
        m.id === aiMsgId ? { 
          ...m, 
          citations: [...(m.citations || []), citation] 
        } : m
      ));
    });
}
```

**渲染引用标记（支持XML格式）**:

```typescript
// 解析并渲染XML格式的cite标签
const renderWithCitations = (
  text: string, 
  citations: Citation[] = []
): React.ReactNode[] => {
  // 如果有后端发送的citation事件，优先使用（包含精确定位）
  if (citations.length > 0) {
    // 将citations映射到文本中的位置
    // 渲染为可点击的引用标签
    return renderCitationsWithPosition(text, citations);
  }
  
  // 否则解析文本中的XML标签（流式生成过程中）
  const citeRegex = /<cite\s+doc_id="(doc_\d+)"\s+quote="([^"]+)">([^<]+)<\/cite>/g;
  const parts: React.ReactNode[] = [];
  let lastIndex = 0;
  let match;
  
  while ((match = citeRegex.exec(text)) !== null) {
    // 添加普通文本
    if (match.index > lastIndex) {
      parts.push(
        <span key={`text-${lastIndex}`}>
          {text.slice(lastIndex, match.index)}
        </span>
      );
    }
    
    // 添加引用标签
    const docId = match[1];  // doc_01
    const quote = match[2];  // 原文片段
    const conclusion = match[3];  // LLM结论
    
    parts.push(
      <CitationTag
        key={`cite-${match.index}`}
        docId={docId}
        quote={quote}
        conclusion={conclusion}
        onClick={() => handleCitationClick({ docId, quote })}
      />
    );
    
    lastIndex = match.index + match[0].length;
  }
  
  // 添加剩余文本
  if (lastIndex < text.length) {
    parts.push(
      <span key={`text-${lastIndex}`}>
        {text.slice(lastIndex)}
      </span>
    );
  }
  
  return parts;
};
```

**点击引用跳转并高亮（PDF搜索方案）**:

```typescript
const handleCitationClick = (citation: Citation) => {
  // 1. 打开对应文档
  const doc = documents.find(d => {
    // 根据doc_id（doc_01）找到实际文档
    // 需要维护doc_id到document的映射
    return getDocumentByDocId(citation.doc_id)?.id === d.id;
  });
  
  if (!doc) return;
  
  // 2. 切换到文档视图
  setActiveDocumentId(doc.id);
  navigateToSource(doc.id, citation.page_number || 0);
  
  // 3. 等待PDF加载后，触发搜索高亮
  // 方案A：使用PDF阅读器的搜索功能（推荐，实现简单）
  setTimeout(() => {
    const pdfViewer = pdfViewerRef.current;
    if (pdfViewer && pdfViewer.searchText) {
      // 使用quote文本在PDF中搜索，自动跳转并高亮
      pdfViewer.searchText(citation.quote);
    }
  }, 500);
  
  // 方案B：如果后端提供了精确坐标（char_start/char_end）
  // 可以使用react-pdf-highlighter等库进行精确高亮
  // 但这需要后端维护字符索引到PDF坐标的映射表
};
```

// 渲染时替换为可点击元素
const renderWithCitations = (text: string, documents: ProjectDocument[]) => {
  const parts = [];
  let lastIndex = 0;
  let match;
  
  while ((match = citationRegex.exec(text)) !== null) {
    // 添加普通文本
    if (match.index > lastIndex) {
      parts.push(<span key={`text-${lastIndex}`}>{text.slice(lastIndex, match.index)}</span>);
    }
    
    // 添加引用标记
    const docIndex = parseInt(match[1]) - 1;
    const doc = documents[docIndex];
    parts.push(
      <CitationTag 
        key={`cite-${match.index}`} 
        docId={doc?.id}
        docTitle={doc?.filename}
        onClick={() => navigateToSource(doc?.id)}
      />
    );
    
    lastIndex = match.index + match[0].length;
  }
  
  // 添加剩余文本
  if (lastIndex < text.length) {
    parts.push(<span key={`text-${lastIndex}`}>{text.slice(lastIndex)}</span>);
  }
  
  return parts;
};
```

#### 9.2 支持Citation事件（精确定位）

**文件**: `app/frontend/src/components/studio/AssistantPanel.tsx`

- 在SSE流处理中添加对`citation`事件类型的处理（单个引用）
- 接收后端发送的定位信息（char_start, char_end, page_number）
- 存储引用信息，用于渲染和跳转

**修改位置**: `handleSend()`函数中的流处理逻辑（约92行）

```typescript
} else if (chunk.type === 'citation') {
    // 处理Mega-Prompt模式的引用（包含精确定位信息）
    const citation = chunk.data;
    flushSync(() => {
      setChatMessages(prev => prev.map(m => 
        m.id === aiMsgId ? { 
          ...m, 
          citations: [...(m.citations || []), citation] 
        } : m
      ));
    });
}
```

**Citation数据结构**:

```typescript
interface Citation {
  doc_id: string;        // doc_01
  document_id: string;   // 实际文档UUID
  quote: string;         // 原文片段
  conclusion: string;    // LLM的结论
  char_start: number;    // 在原文中的起始位置
  char_end: number;      // 在原文中的结束位置
  page_number?: number;  // PDF页码（如果可计算）
  match_score: number;   // 匹配分数（0-100）
}
```

---

## 实施顺序

1. **Phase 1**: 数据库Schema + 文档摘要生成（后端） + **PDF解析增强（页码映射）**
2. **Phase 2**: WebSocket通知机制（后端 + 前端）
3. **Phase 3**: 前端类型更新 + WebSocket集成
4. **Phase 4**: 替换轮询为WebSocket + 显示摘要
5. **Phase 5**: RAG全文检索模式（后端）+ **动态上下文降级策略**
6. **Phase 6**: Mega-Prompt支持（后端）+ **基于页码映射的引用定位**
7. **Phase 7**: 统一上传接口 + 测试验证

---

## 关键文件清单

### 后端新增文件

- `app/backend/src/research_agent/infrastructure/websocket/notification_service.py`
- `app/backend/src/research_agent/domain/services/document_retrieval_service.py`
- `app/backend/src/research_agent/domain/services/citation_parser.py` - XML引用标签解析服务
- `app/backend/src/research_agent/utils/text_locator.py` - 原文定位服务（Quote-to-Coordinate，模糊匹配）
- `app/backend/src/research_agent/api/v1/websocket.py`
- `app/backend/alembic/versions/YYYYMMDD_HHMMSS_add_document_summary.py`

### 后端修改文件

- `app/backend/src/research_agent/worker/tasks/document_processor.py` - 添加摘要生成、页码映射构建
- `app/backend/src/research_agent/application/graphs/rag_graph.py` - 支持全文模式、流式解析XML引用、发送citation事件
- `app/backend/src/research_agent/infrastructure/llm/prompts/rag_prompt.py` - Mega-Prompt
- `app/backend/src/research_agent/api/v1/documents.py` - 统一接口
- `app/backend/src/research_agent/domain/entities/document.py` - 添加summary字段
- `app/backend/src/research_agent/infrastructure/database/models.py` - 更新模型
- `app/backend/src/research_agent/config.py` - 添加配置

### 前端新增文件

- `app/frontend/src/lib/websocket.ts` - WebSocket客户端工具

### 前端修改文件

- `app/frontend/src/lib/api.ts` - 更新类型定义（添加summary、task_id、citations字段）
- `app/frontend/src/components/studio/SourcePanel.tsx` - 添加WebSocket连接、显示摘要
- `app/frontend/src/components/studio/AssistantPanel.tsx` - 解析引用标记、支持citations事件
- `app/frontend/src/contexts/StudioContext.tsx` - WebSocket管理

---

## 注意事项

1. **向后兼容**: 保持chunks模式作为默认，全文模式作为可选
2. **性能考虑**: 
   - 全文模式会增加token消耗（可能几万到几十万token），需要合理控制Top-K数量
   - **风险控制**: 必须实现`Adaptive Context Strategy`，在Token超出阈值时自动降级或截断，避免请求失败或费用失控。
   - 考虑Context Caching（上下文缓存）优化，避免每次查询都重新传输完整文档
   - 流式输出减少延迟感知

3. **XML结构优势**: 
   - XML标签帮助大模型理解长文本结构，提升准确性
   - 区分System Instruction、Documents、Output Rules等部分
   - 支持Thinking Process引导，提升推理质量

4. **引用标记鲁棒性与精确定位**:
   - **XML摘录格式**: 要求LLM输出`<cite doc_id="doc_01" quote="原文片段">结论</cite>`格式，包含原文摘录
   - **原文定位服务**: 使用rapidfuzz在全文中模糊匹配定位quote位置，返回char_start/char_end
   - **关键依赖**: 必须在PDF解析阶段生成`page_map`并存储，否则无法计算页码。
   - **流式解析**: 在生成过程中实时解析XML标签，立即计算位置并发送citation事件
   - **前端跳转**: 点击引用时，使用quote文本在PDF中搜索并高亮（方案A，推荐）或使用精确坐标高亮（方案B，需坐标映射）
   - **容错性**: 模糊匹配阈值85%，处理LLM可能的细微修改
   - **备选方案**: 简单文本标记`[doc_01]`（仅文档级跳转）或JSON Mode（结构化输出）
   - **推荐策略**: 默认使用XML摘录格式 + 原文定位 + PDF搜索高亮，平衡开发成本和用户体验

5. **错误处理**: WebSocket连接断开时的重连机制
6. **测试**: 确保chunks模式和Mega-Prompt模式都能正常工作，特别测试引用标记解析的容错性
7. **成本控制**: Mega-Prompt模式成本较高，建议：
   - 提供配置开关
   - 根据文档数量和大小智能选择模式
   - 考虑实现Context Caching（后续优化）
