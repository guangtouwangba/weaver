"""Knowledge extraction domain service."""

from typing import List, Dict, Any, Optional
from ..entities.document import Document
from ..entities.knowledge_base import Knowledge, KnowledgeType


class KnowledgeExtractionService:
    """Domain service for knowledge extraction from documents."""
    
    def __init__(self):
        """Initialize knowledge extraction service."""
        pass
    
    async def extract_knowledge(self, document: Document) -> List[Knowledge]:
        """
        Extract knowledge items from a document.
        
        Args:
            document: Document to extract knowledge from
            
        Returns:
            List[Knowledge]: Extracted knowledge items
        """
        if not document.is_processed:
            raise ValueError("Document must be processed before knowledge extraction")
        
        knowledge_items = []
        
        # Simple knowledge extraction (in real implementation, would use NLP/ML)
        if document.content:
            # Extract concepts (simplified approach)
            concepts = await self._extract_concepts(document)
            knowledge_items.extend(concepts)
            
            # Extract facts (simplified approach)
            facts = await self._extract_facts(document)
            knowledge_items.extend(facts)
        
        return knowledge_items
    
    async def _extract_concepts(self, document: Document) -> List[Knowledge]:
        """Extract concepts from document content."""
        concepts = []
        
        # Very simplified concept extraction
        # In real implementation, would use NLP libraries
        if document.content:
            words = document.content.lower().split()
            
            # Look for potential concepts (words that appear multiple times)
            word_counts = {}
            for word in words:
                if len(word) > 3:  # Only consider longer words
                    word_counts[word] = word_counts.get(word, 0) + 1
            
            # Create knowledge items for frequently mentioned concepts
            for word, count in word_counts.items():
                if count >= 3:  # Appears at least 3 times
                    knowledge = Knowledge(
                        content=f"The concept '{word}' is mentioned {count} times in this document.",
                        knowledge_type=KnowledgeType.CONCEPT,
                        source_document_id=document.id,
                        confidence_score=min(count / 10.0, 1.0),  # Simple confidence scoring
                        relevance_score=0.7,
                        tags=[word, "concept", "extracted"]
                    )
                    concepts.append(knowledge)
        
        return concepts
    
    async def _extract_facts(self, document: Document) -> List[Knowledge]:
        """Extract facts from document content."""
        facts = []
        
        # Very simplified fact extraction
        if document.content:
            sentences = document.content.split('.')
            
            for i, sentence in enumerate(sentences):
                sentence = sentence.strip()
                if len(sentence) > 20 and ('is' in sentence or 'are' in sentence):
                    # Simple heuristic for factual statements
                    knowledge = Knowledge(
                        content=sentence,
                        knowledge_type=KnowledgeType.FACT,
                        source_document_id=document.id,
                        source_location=f"sentence_{i}",
                        confidence_score=0.6,
                        relevance_score=0.5,
                        tags=["fact", "extracted"]
                    )
                    facts.append(knowledge)
                    
                    # Limit number of facts extracted
                    if len(facts) >= 10:
                        break
        
        return facts
    
    async def validate_knowledge_quality(self, knowledge: Knowledge) -> Dict[str, Any]:
        """
        Validate the quality of extracted knowledge.
        
        Args:
            knowledge: Knowledge item to validate
            
        Returns:
            Dict[str, Any]: Validation results
        """
        validation_result = {
            'is_valid': True,
            'score': 0.0,
            'issues': []
        }
        
        # Content length check
        if len(knowledge.content) < 10:
            validation_result['issues'].append("Content too short")
            validation_result['score'] -= 0.3
        
        # Confidence score check
        if knowledge.confidence_score < 0.5:
            validation_result['issues'].append("Low confidence score")
            validation_result['score'] -= 0.2
        
        # Source validation
        if not knowledge.source_document_id:
            validation_result['issues'].append("Missing source document")
            validation_result['score'] -= 0.5
        
        # Calculate final score
        base_score = 1.0
        validation_result['score'] = max(0.0, base_score + validation_result['score'])
        validation_result['is_valid'] = validation_result['score'] >= 0.6
        
        return validation_result
