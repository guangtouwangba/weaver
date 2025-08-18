"""RAG domain service containing core RAG business logic."""

from typing import List, Optional, Dict, Any
from ..entities.document import Document
from ..entities.knowledge_base import Knowledge, KnowledgeBase
from ..value_objects.search_criteria import SearchCriteria
from ..repositories.document_repository import DocumentRepository
from .knowledge_extraction_service import KnowledgeExtractionService


class RAGDomainService:
    """RAG core domain service containing RAG-specific business logic."""
    
    def __init__(
        self,
        document_repository: DocumentRepository,
        knowledge_extractor: KnowledgeExtractionService
    ):
        self.document_repository = document_repository
        self.knowledge_extractor = knowledge_extractor
    
    async def process_document_for_knowledge_base(
        self, 
        document: Document, 
        knowledge_base: KnowledgeBase
    ) -> List[Knowledge]:
        """
        Process document and extract knowledge for knowledge base.
        
        This is core domain logic that orchestrates document processing
        and knowledge extraction according to business rules.
        
        Args:
            document: Document to process
            knowledge_base: Target knowledge base
            
        Returns:
            List[Knowledge]: Extracted knowledge items
        """
        # Validate business rules
        if not document.is_processed:
            raise ValueError("Document must be processed before knowledge extraction")
        
        if not knowledge_base:
            raise ValueError("Knowledge base is required")
        
        # Extract knowledge using domain service
        knowledge_items = await self.knowledge_extractor.extract_knowledge(document)
        
        # Apply business rules for knowledge validation
        validated_knowledge = []
        for knowledge in knowledge_items:
            if self._validate_knowledge_quality(knowledge):
                # Associate with knowledge base topics
                for topic_id in knowledge_base.topics:
                    knowledge.add_to_topic(topic_id)
                
                validated_knowledge.append(knowledge)
                knowledge_base.add_knowledge(knowledge)
        
        return validated_knowledge
    
    async def retrieve_relevant_knowledge(
        self, 
        criteria: SearchCriteria,
        knowledge_base: KnowledgeBase
    ) -> List[Knowledge]:
        """
        Retrieve relevant knowledge based on search criteria.
        
        This implements domain-specific knowledge retrieval logic.
        
        Args:
            criteria: Search criteria
            knowledge_base: Knowledge base to search
            
        Returns:
            List[Knowledge]: Relevant knowledge items
        """
        if not criteria.has_text_query:
            raise ValueError("Text query is required for knowledge retrieval")
        
        # Get initial knowledge candidates
        candidates = knowledge_base.search_knowledge(criteria.query)
        
        # Apply domain-specific filtering rules
        filtered_knowledge = self._apply_knowledge_filters(candidates, criteria)
        
        # Apply domain-specific ranking rules
        ranked_knowledge = self._rank_knowledge_by_relevance(filtered_knowledge, criteria)
        
        # Apply pagination
        start = criteria.offset
        end = start + criteria.limit
        
        return ranked_knowledge[start:end]
    
    async def find_related_documents(
        self, 
        document: Document, 
        similarity_threshold: float = 0.7
    ) -> List[Document]:
        """
        Find documents related to the given document.
        
        Args:
            document: Source document
            similarity_threshold: Minimum similarity threshold
            
        Returns:
            List[Document]: Related documents
        """
        if not document.topic_id:
            return []
        
        # Find documents in the same topic
        topic_documents = await self.document_repository.find_by_topic_id(document.topic_id)
        
        # Filter out the source document
        related_documents = [doc for doc in topic_documents if doc.id != document.id]
        
        # Apply additional domain rules for relationship scoring
        scored_documents = []
        for doc in related_documents:
            score = self._calculate_document_similarity(document, doc)
            if score >= similarity_threshold:
                scored_documents.append((doc, score))
        
        # Sort by similarity score
        scored_documents.sort(key=lambda x: x[1], reverse=True)
        
        return [doc for doc, _ in scored_documents]
    
    async def suggest_knowledge_connections(
        self, 
        knowledge: Knowledge, 
        knowledge_base: KnowledgeBase
    ) -> List[Knowledge]:
        """
        Suggest connections between knowledge items.
        
        Args:
            knowledge: Source knowledge
            knowledge_base: Knowledge base to search
            
        Returns:
            List[Knowledge]: Suggested related knowledge
        """
        # Find knowledge items with similar content
        candidates = knowledge_base.search_knowledge(knowledge.content)
        
        # Filter out the source knowledge
        candidates = [k for k in candidates if k.id != knowledge.id]
        
        # Apply domain rules for connection scoring
        connection_scores = []
        for candidate in candidates:
            score = self._calculate_knowledge_connection_score(knowledge, candidate)
            if score > 0.5:  # Domain-defined threshold
                connection_scores.append((candidate, score))
        
        # Sort by connection score
        connection_scores.sort(key=lambda x: x[1], reverse=True)
        
        # Return top connections
        return [k for k, _ in connection_scores[:10]]
    
    def _validate_knowledge_quality(self, knowledge: Knowledge) -> bool:
        """
        Validate knowledge quality according to domain rules.
        
        Args:
            knowledge: Knowledge to validate
            
        Returns:
            bool: True if knowledge meets quality standards
        """
        # Domain rules for knowledge quality
        if len(knowledge.content.strip()) < 10:
            return False
        
        if knowledge.confidence_score < 0.6:
            return False
        
        # Additional quality checks can be added here
        return True
    
    def _apply_knowledge_filters(
        self, 
        knowledge_items: List[Knowledge], 
        criteria: SearchCriteria
    ) -> List[Knowledge]:
        """
        Apply domain-specific filters to knowledge items.
        
        Args:
            knowledge_items: Knowledge items to filter
            criteria: Search criteria
            
        Returns:
            List[Knowledge]: Filtered knowledge items
        """
        filtered = knowledge_items
        
        # Filter by topic IDs if specified
        if criteria.topic_ids:
            filtered = [
                k for k in filtered 
                if any(topic_id in k.topic_ids for topic_id in criteria.topic_ids)
            ]
        
        # Filter by tags if specified
        if criteria.tags:
            filtered = [
                k for k in filtered
                if any(tag in k.tags for tag in criteria.tags)
            ]
        
        return filtered
    
    def _rank_knowledge_by_relevance(
        self, 
        knowledge_items: List[Knowledge], 
        criteria: SearchCriteria
    ) -> List[Knowledge]:
        """
        Rank knowledge items by domain-specific relevance rules.
        
        Args:
            knowledge_items: Knowledge items to rank
            criteria: Search criteria
            
        Returns:
            List[Knowledge]: Ranked knowledge items
        """
        # Calculate relevance scores
        scored_items = []
        for knowledge in knowledge_items:
            score = self._calculate_knowledge_relevance_score(knowledge, criteria)
            scored_items.append((knowledge, score))
        
        # Sort by relevance score
        scored_items.sort(key=lambda x: x[1], reverse=True)
        
        return [knowledge for knowledge, _ in scored_items]
    
    def _calculate_knowledge_relevance_score(
        self, 
        knowledge: Knowledge, 
        criteria: SearchCriteria
    ) -> float:
        """
        Calculate relevance score for knowledge item.
        
        Args:
            knowledge: Knowledge item
            criteria: Search criteria
            
        Returns:
            float: Relevance score
        """
        score = 0.0
        
        # Base confidence score
        score += knowledge.confidence_score * 0.4
        
        # Relevance score
        score += knowledge.relevance_score * 0.4
        
        # Validation bonus
        if knowledge.is_validated:
            score += 0.2
        
        return min(score, 1.0)
    
    def _calculate_document_similarity(self, doc1: Document, doc2: Document) -> float:
        """
        Calculate similarity between two documents using domain rules.
        
        Args:
            doc1: First document
            doc2: Second document
            
        Returns:
            float: Similarity score between 0 and 1
        """
        score = 0.0
        
        # Tag similarity
        if doc1.tags and doc2.tags:
            common_tags = set(doc1.tags) & set(doc2.tags)
            tag_similarity = len(common_tags) / len(set(doc1.tags) | set(doc2.tags))
            score += tag_similarity * 0.3
        
        # Content type similarity
        if doc1.content_type == doc2.content_type:
            score += 0.2
        
        # Simple content similarity (in real implementation, use embeddings)
        if doc1.content and doc2.content:
            content1_words = set(doc1.content.lower().split())
            content2_words = set(doc2.content.lower().split())
            if content1_words and content2_words:
                content_similarity = len(content1_words & content2_words) / len(content1_words | content2_words)
                score += content_similarity * 0.5
        
        return min(score, 1.0)
    
    def _calculate_knowledge_connection_score(
        self, 
        knowledge1: Knowledge, 
        knowledge2: Knowledge
    ) -> float:
        """
        Calculate connection score between knowledge items.
        
        Args:
            knowledge1: First knowledge item
            knowledge2: Second knowledge item
            
        Returns:
            float: Connection score between 0 and 1
        """
        score = 0.0
        
        # Same knowledge type bonus
        if knowledge1.knowledge_type == knowledge2.knowledge_type:
            score += 0.2
        
        # Common topics
        common_topics = set(knowledge1.topic_ids) & set(knowledge2.topic_ids)
        if common_topics:
            score += len(common_topics) / len(set(knowledge1.topic_ids) | set(knowledge2.topic_ids)) * 0.3
        
        # Common tags
        common_tags = set(knowledge1.tags) & set(knowledge2.tags)
        if common_tags:
            score += len(common_tags) / len(set(knowledge1.tags) | set(knowledge2.tags)) * 0.2
        
        # Content similarity (simplified)
        content1_words = set(knowledge1.content.lower().split())
        content2_words = set(knowledge2.content.lower().split())
        if content1_words and content2_words:
            content_similarity = len(content1_words & content2_words) / len(content1_words | content2_words)
            score += content_similarity * 0.3
        
        return min(score, 1.0)
