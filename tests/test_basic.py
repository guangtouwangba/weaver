"""
Basic tests for the research agent RAG system
"""
import pytest
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Config
from retrieval.arxiv_client import ArxivClient
from database.vector_store import VectorStore


class TestBasicFunctionality:
    """Basic functionality tests"""

    def test_config_validation(self):
        """Test configuration validation"""
        # This should not raise an exception even without API keys in test
        try:
            Config.validate()
        except ValueError:
            # Expected when no API keys are set
            pass

    def test_arxiv_client_initialization(self):
        """Test ArxivClient can be initialized"""
        client = ArxivClient(max_results=5)
        assert client.max_results == 5
        assert client.client is not None

    def test_vector_store_initialization(self):
        """Test VectorStore can be initialized"""
        # Use a test database path
        test_db_path = "./test_data/vector_db"
        store = VectorStore(db_path=test_db_path)
        assert store.db_path.name == "vector_db"
        assert store.collection_name == "research_papers"

    @pytest.mark.integration
    def test_arxiv_search_basic(self):
        """Test basic arXiv search (requires internet)"""
        client = ArxivClient(max_results=2)
        papers = client.search_papers("machine learning", max_results=2)
        
        # Should return some papers (or empty list if API issues)
        assert isinstance(papers, list)
        assert len(papers) <= 2
        
        if papers:
            paper = papers[0]
            assert hasattr(paper, 'title')
            assert hasattr(paper, 'authors')
            assert hasattr(paper, 'abstract')

    def test_paper_data_structure(self):
        """Test Paper data structure"""
        from retrieval.arxiv_client import Paper
        from datetime import datetime
        
        paper = Paper(
            id="test_id",
            title="Test Paper",
            authors=["Author One", "Author Two"],
            abstract="This is a test abstract",
            categories=["cs.AI"],
            published=datetime.now(),
            updated=datetime.now(),
            pdf_url="https://example.com/paper.pdf",
            entry_id="https://arxiv.org/abs/test_id"
        )
        
        assert paper.id == "test_id"
        assert paper.title == "Test Paper"
        assert len(paper.authors) == 2
        assert "cs.AI" in paper.categories


class TestAgentInitialization:
    """Test agent initialization (without API calls)"""

    def test_base_agent_import(self):
        """Test base agent can be imported"""
        from agents.base_agent import BaseResearchAgent, AnalysisResult
        assert BaseResearchAgent is not None
        assert AnalysisResult is not None

    def test_agent_imports(self):
        """Test all agents can be imported"""
        from agents.google_engineer_agent import GoogleEngineerAgent
        from agents.mit_researcher_agent import MITResearcherAgent
        from agents.industry_expert_agent import IndustryExpertAgent
        from agents.paper_analyst_agent import PaperAnalystAgent
        
        # All agents should be importable
        assert GoogleEngineerAgent is not None
        assert MITResearcherAgent is not None
        assert IndustryExpertAgent is not None
        assert PaperAnalystAgent is not None


@pytest.mark.slow
class TestSystemIntegration:
    """Integration tests that may be slow"""

    @pytest.mark.integration
    def test_full_workflow_mock(self):
        """Test a mock version of the full workflow"""
        # This would test the complete workflow with mock data
        # Implementation depends on having mock/test data
        pass


if __name__ == "__main__":
    pytest.main([__file__])