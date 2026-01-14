from typing import Annotated, Any, Literal, TypedDict
from uuid import UUID

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AnyMessage, SystemMessage
from langgraph.graph import END, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode

from research_agent.application.agents.rag_memory import RAGAgentMemory
from research_agent.application.agents.rag_tools import RAGTools
from research_agent.domain.services.conversation_context import ConversationContext
from research_agent.shared.utils.logger import logger


class RAGAgentState(TypedDict):
    """
    State for the RAG Agent.
    Extends standard agent state with RAG-specific fields.
    """

    messages: Annotated[list[AnyMessage], add_messages]

    # RAG Context
    question: str
    project_id: UUID
    user_id: str | None

    # Memory Context
    session_summary: str
    retrieved_memories: list[dict]

    # RAG specific state
    documents: list[Any]
    active_document_id: str | None

    # Context Awareness
    active_entities: dict[str, Any]
    current_focus: dict[str, Any] | None


class RAGAgent:
    """
    RAG Agent using LangGraph and Tools.
    Orchestrates retrieval, reasoning, and generation.
    """

    def __init__(self, tools: RAGTools, memory: RAGAgentMemory, llm: BaseChatModel):
        self.tools_svc = tools
        self.memory_svc = memory
        self.llm = llm

        # Get bound tools
        self.bound_tools = tools.get_tools()

        self.graph = self._build_graph()

    def _build_graph(self) -> Any:
        workflow = StateGraph(RAGAgentState)

        # Define nodes
        workflow.add_node("load_context", self._load_context)
        workflow.add_node("prepare_query", self._prepare_query)
        workflow.add_node("agent", self._agent_node)
        workflow.add_node("tools", ToolNode(self.bound_tools))

        # Define edges
        workflow.set_entry_point("load_context")
        workflow.add_edge("load_context", "prepare_query")
        workflow.add_edge("prepare_query", "agent")

        workflow.add_conditional_edges(
            "agent", self._should_continue, {"continue": "tools", "end": END}
        )
        workflow.add_edge("tools", "agent")

        return workflow.compile()

    async def _load_context(self, state: RAGAgentState) -> dict:
        """Load memory/session context before agent loop."""
        project_id = state["project_id"]
        user_id = state.get("user_id")

        updates = {}

        # Load session summary
        try:
            summary = await self.memory_svc.get_session_summary(project_id, user_id)
            if summary:
                updates["session_summary"] = summary
        except Exception as e:
            logger.warning(f"Failed to load context: {e}")

        return updates

    async def _prepare_query(self, state: RAGAgentState) -> dict:
        """Resolve entity references and prepare query context."""
        question = state["question"]
        updates = {}

        try:
            # Resolve entity references
            auth_ctx = ConversationContext(
                entities=state.get("active_entities"),
                focus=state.get("current_focus"),
            )
            resolved_entity = auth_ctx.resolve_reference(question)

            if resolved_entity:
                logger.info(f"[Context] Resolved reference: {resolved_entity.get('title')}")
                updates["current_focus"] = resolved_entity
                if resolved_entity.get("type") in ["document", "video"]:
                    updates["active_document_id"] = resolved_entity.get("id")

        except Exception as e:
            logger.warning(f"Failed to resolve entities: {e}")

        return updates

    async def _agent_node(self, state: RAGAgentState) -> dict:
        """Main agent decision node."""
        messages = state["messages"]

        # Construct system prompt if not present
        if not any(isinstance(m, SystemMessage) for m in messages):
            system_msg = self._build_system_prompt(state)
            messages = [system_msg] + messages

        llm_with_tools = self.llm.bind_tools(self.bound_tools)

        response = await llm_with_tools.ainvoke(messages)

        return {"messages": [response]}

    def _should_continue(self, state: RAGAgentState) -> Literal["continue", "end"]:
        """Determine next step based on last message."""
        messages = state["messages"]
        last_message = messages[-1]

        if last_message.tool_calls:
            return "continue"
        return "end"

    def _build_system_prompt(self, state: RAGAgentState) -> SystemMessage:
        """Build the agent system prompt."""
        summary = state.get("session_summary", "")
        focus = state.get("current_focus")
        focus_str = f"Current Focus: {focus.get('title')}" if focus else ""

        prompt = """You are a Research Agent. Your goal is to answer the user's question by researching relevant documents.

Process:
1. Retrieval: Use 'vector_retrieve' to find documents.
2. Refinement: Use 'rerank' or 'grade_documents' to filter relevant information.
3. Analysis: Read relevant documents.
4. Answer: Use 'generate_answer' to produce the final response with citations.

Context Summary:
{summary}

{focus_str}

Guidelines:
- Always checking finding documents before answering.
- If a 'Current Focus' document is active (ID shown in context), you MUST use its ID as 'doc_id_filter' in 'vector_retrieve'.
- Use 'generate_answer' for the final output to ensure correct citation format.
- If you cannot find info, state so.
"""
        return SystemMessage(content=prompt.format(summary=summary, focus_str=focus_str))
