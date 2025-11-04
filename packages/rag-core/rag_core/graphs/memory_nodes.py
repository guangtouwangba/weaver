"""Memory nodes for conversational QA with vector similarity search."""

import asyncio
from typing import Optional
from uuid import UUID

from langchain_core.prompts import ChatPromptTemplate
from sqlalchemy.orm import Session

from rag_core.chains.llm import build_llm
from rag_core.chains.embeddings import build_embedding_function
from rag_core.graphs.state import QueryState
from rag_core.services.conversation_service import ConversationService
from rag_core.services.message_service import MessageService
from rag_core.storage.database import SessionLocal
from shared_config.settings import AppSettings


# Prompt for contextualizing questions
CONTEXTUALIZE_Q_SYSTEM_PROMPT = """
给定对话历史和最新的用户问题（可能引用了对话历史中的上下文），
请将该问题重新表述为一个独立的问题，使其不依赖对话历史也能理解。

规则：
1. 将代词（它、这个、那个、刚才的）替换为实际的实体
2. 补充省略的主语、宾语或背景信息
3. 保持问题的原意和语气
4. 如果问题已经完整独立，直接返回原问题（不要添加额外内容）

请只返回重写后的问题，不要添加任何解释。
"""

CONTEXTUALIZE_Q_USER_PROMPT = """
对话历史：
{chat_history}

最新问题：{question}

独立问题：
"""


def load_memory_node(state: QueryState) -> dict:
    """
    Load recent chat history from database (short-term memory).
    
    Args:
        state: Graph state containing conversation_id
        
    Returns:
        Updated state with chat_history
    """
    conversation_id = state.conversation_id
    
    if not conversation_id:
        print("📚 [Memory] 无对话ID，跳过历史加载")
        return {"chat_history": []}
    
    # Get database session
    db = SessionLocal()
    try:
        # Load recent messages (last 10) - SHORT-TERM MEMORY
        messages = MessageService.get_recent_messages(db, conversation_id, limit=10)
        
        # Format as chat history
        chat_history = []
        for msg in messages:
            chat_history.append({
                "role": msg.role,
                "content": msg.content
            })
        
        print(f"📚 [Short-term Memory] 加载了 {len(chat_history)} 条最近消息")
        return {"chat_history": chat_history}
        
    finally:
        db.close()


def retrieve_long_term_memory_node(state: QueryState) -> dict:
    """
    Retrieve relevant messages from long-term memory using vector similarity.
    This supplements short-term memory for long conversations.
    
    Args:
        state: Graph state containing conversation_id and question
        
    Returns:
        Updated state with long_term_memory
    """
    conversation_id = state.conversation_id
    question = state.question
    
    if not conversation_id:
        print("🔍 [Long-term Memory] 无对话ID，跳过")
        return {"long_term_memory": []}
    
    # Get database session
    db = SessionLocal()
    try:
        # Generate embedding for current question
        settings = AppSettings()  # type: ignore[arg-type]
        embedding_fn = build_embedding_function(settings)
        
        print("🔍 [Long-term Memory] 生成查询embedding...")
        try:
            query_embedding = asyncio.run(embedding_fn.aembed_query(question))
        except Exception as e:
            print(f"⚠️ [Long-term Memory] Embedding生成失败: {e}")
            return {"long_term_memory": []}
        
        # Find similar messages (top 3, similarity > 0.7)
        print("🔍 [Long-term Memory] 搜索相似历史...")
        similar_messages = MessageService.find_similar_messages(
            db,
            conversation_id=conversation_id,
            query_embedding=query_embedding,
            limit=3,
            similarity_threshold=0.7
        )
        
        # Format as memory entries
        long_term_memory = []
        for msg in similar_messages:
            long_term_memory.append({
                "role": msg.role,
                "content": msg.content
            })
        
        print(f"🔍 [Long-term Memory] 检索到 {len(long_term_memory)} 条相关历史")
        return {"long_term_memory": long_term_memory}
        
    finally:
        db.close()


def contextualize_query_node(state: QueryState) -> dict:
    """
    Rewrite the question based on chat history (short-term + long-term) to make it standalone.
    
    Args:
        state: Graph state containing question, chat_history, and long_term_memory
        
    Returns:
        Updated state with contextualized_question
    """
    question = state.question
    chat_history = state.chat_history or []
    long_term_memory = state.long_term_memory or []
    
    # If no history, use original question
    if not chat_history and not long_term_memory:
        print("🔄 [Contextualize] 无历史记录，使用原始问题")
        return {"contextualized_question": question}
    
    # Merge memories: long-term first (context), then short-term (recent)
    all_memory = []
    
    if long_term_memory:
        print(f"🔄 [Contextualize] 包含 {len(long_term_memory)} 条长期记忆（相似历史）")
        all_memory.append("【相关历史】")
        for msg in long_term_memory:
            all_memory.append(f"[{msg['role']}]: {msg['content']}")
    
    if chat_history:
        print(f"🔄 [Contextualize] 包含 {len(chat_history)} 条短期记忆（最近对话）")
        if long_term_memory:
            all_memory.append("\n【最近对话】")
        for msg in chat_history:
            all_memory.append(f"[{msg['role']}]: {msg['content']}")
    
    # Format memory for prompt
    history_str = "\n".join(all_memory)
    
    # Create prompt
    prompt = ChatPromptTemplate.from_messages([
        ("system", CONTEXTUALIZE_Q_SYSTEM_PROMPT),
        ("human", CONTEXTUALIZE_Q_USER_PROMPT),
    ])
    
    # Get LLM
    settings = AppSettings()  # type: ignore[arg-type]
    llm = build_llm(settings)
    
    # Chain: prompt | llm
    chain = prompt | llm
    
    # Invoke
    print(f"🔄 [Contextualize] 正在基于历史重写问题...")
    print(f"  原始问题: {question}")
    
    response = chain.invoke({
        "chat_history": history_str,
        "question": question
    })
    
    # Extract content
    contextualized = response.content.strip() if hasattr(response, 'content') else str(response).strip()
    
    print(f"  重写问题: {contextualized}")
    
    return {"contextualized_question": contextualized}


def save_memory_node(state: QueryState) -> dict:
    """
    Save the QA interaction to conversation history with embeddings.
    
    Args:
        state: Graph state containing conversation_id, question, answer, documents
        
    Returns:
        Updated state with conversation_id (creates new conversation if needed)
    """
    conversation_id = state.conversation_id
    question = state.question
    answer = state.answer or ""
    documents = state.documents or []
    topic_id = state.topic_id  # Optional: for creating new conversation
    
    # Get database session
    db = SessionLocal()
    try:
        # Check if conversation exists, or create a new one
        needs_new_conversation = False
        
        if conversation_id:
            # Verify the conversation exists in the database
            existing = ConversationService.get_conversation(db, conversation_id)
            if not existing:
                print(f"⚠️ [Memory] Conversation {conversation_id} 不存在，将创建新的")
                needs_new_conversation = True
        else:
            needs_new_conversation = True
        
        # Create new conversation if needed
        if needs_new_conversation:
            if not topic_id:
                print("⚠️ [Memory] 无对话ID且无topic_id，跳过保存")
                return {}
            
            # Verify topic exists before creating conversation
            from rag_core.services.topic_service import TopicService
            topic = TopicService.get_topic(db, topic_id)
            if not topic:
                print(f"❌ [Memory] Topic {topic_id} 不存在，无法创建对话，跳过保存")
                print(f"   提示：请确保前端传递了正确的topic_id，或先创建topic")
                return {}
            
            from domain_models import ConversationCreate
            
            # Generate title from question (first 50 chars)
            title = question[:50] + "..." if len(question) > 50 else question
            
            conversation_data = ConversationCreate(
                topic_id=UUID(topic_id),
                title=title
            )
            conversation = ConversationService.create_conversation(db, conversation_data)
            conversation_id = str(conversation.id)
            print(f"💾 [Memory] 创建新对话: {conversation_id}")
        
        # Generate embeddings for question and answer
        settings = AppSettings()  # type: ignore[arg-type]
        embedding_fn = build_embedding_function(settings)
        
        print("🔮 [Memory] 生成消息embedding...")
        
        # Generate embeddings (synchronously - LangGraph nodes are sync)
        # We'll use asyncio.run to call async embed functions
        try:
            question_embedding = asyncio.run(embedding_fn.aembed_query(question))
            answer_embedding = asyncio.run(embedding_fn.aembed_query(answer))
        except Exception as e:
            print(f"⚠️ [Memory] Embedding生成失败: {e}，将不保存embedding")
            question_embedding = None
            answer_embedding = None
        
        # Save user message with embedding
        MessageService.create_message(
            db,
            conversation_id=conversation_id,
            role="user",
            content=question,
            embedding=question_embedding
        )
        
        # Prepare sources
        sources = []
        for doc in documents:
            sources.append({
                "content": doc.get("page_content", ""),
                "metadata": doc.get("metadata", {})
            })
        
        # Save assistant message with embedding
        MessageService.create_message(
            db,
            conversation_id=conversation_id,
            role="assistant",
            content=answer,
            sources=sources if sources else None,
            embedding=answer_embedding
        )
        
        print(f"💾 [Memory] 保存了用户和助手消息（含embedding）到对话: {conversation_id}")
        
        return {"conversation_id": conversation_id}
        
    finally:
        db.close()

