"""
Test utilities and factories for generating test data.

Provides reusable test data generation and helper functions.
"""

import random
import string
import io
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from faker import Faker

fake = Faker(['zh_CN', 'en_US'])


class TestDataFactory:
    """Factory for generating test data."""
    
    @staticmethod
    def create_topic_data(
        title: Optional[str] = None,
        description: Optional[str] = None,
        tags: Optional[List[str]] = None,
        is_public: bool = True,
        **kwargs
    ) -> Dict[str, Any]:
        """Create topic test data."""
        return {
            "title": title or fake.sentence(nb_words=3),
            "description": description or fake.paragraph(nb_sentences=2),
            "tags": tags or [fake.word() for _ in range(random.randint(1, 4))],
            "is_public": is_public,
            **kwargs
        }
    
    @staticmethod
    def create_file_data(
        filename: Optional[str] = None,
        content: Optional[bytes] = None,
        content_type: str = "text/plain",
        topic_id: Optional[int] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Create file test data."""
        if filename is None:
            extension = "txt" if content_type == "text/plain" else "bin"
            filename = f"{fake.word()}.{extension}"
        
        if content is None:
            content = fake.text(max_nb_chars=1000).encode()
        
        return {
            "filename": filename,
            "content": content,
            "content_type": content_type,
            "topic_id": topic_id,
            "file_size": len(content),
            **kwargs
        }
    
    @staticmethod
    def create_document_content(
        title: Optional[str] = None,
        content_type: str = "article",
        word_count: int = 500,
        include_keywords: Optional[List[str]] = None
    ) -> str:
        """Create realistic document content."""
        if content_type == "article":
            content = fake.text(max_nb_chars=word_count * 6)
        elif content_type == "technical":
            content = TestDataFactory._create_technical_content(word_count)
        elif content_type == "academic":
            content = TestDataFactory._create_academic_content(word_count)
        else:
            content = fake.text(max_nb_chars=word_count * 6)
        
        # Insert keywords if provided
        if include_keywords:
            for keyword in include_keywords:
                # Insert keyword at random positions
                insert_pos = random.randint(0, len(content) // 2)
                content = content[:insert_pos] + f" {keyword} " + content[insert_pos:]
        
        return content
    
    @staticmethod
    def _create_technical_content(word_count: int) -> str:
        """Create technical document content."""
        technical_terms = [
            "API", "数据库", "算法", "架构", "微服务", "容器化", "云计算",
            "人工智能", "机器学习", "深度学习", "神经网络", "自然语言处理"
        ]
        
        content_parts = []
        remaining_words = word_count
        
        while remaining_words > 0:
            # Add a paragraph with technical terms
            paragraph_words = min(remaining_words, random.randint(50, 100))
            paragraph = fake.text(max_nb_chars=paragraph_words * 6)
            
            # Insert some technical terms
            for _ in range(random.randint(1, 3)):
                term = random.choice(technical_terms)
                insert_pos = random.randint(0, len(paragraph) // 2)
                paragraph = paragraph[:insert_pos] + f" {term} " + paragraph[insert_pos:]
            
            content_parts.append(paragraph)
            remaining_words -= paragraph_words
        
        return "\n\n".join(content_parts)
    
    @staticmethod
    def _create_academic_content(word_count: int) -> str:
        """Create academic paper-style content."""
        sections = ["摘要", "引言", "方法", "实验结果", "讨论", "结论"]
        content_parts = []
        words_per_section = word_count // len(sections)
        
        for section in sections:
            section_content = f"## {section}\n\n"
            section_content += fake.text(max_nb_chars=words_per_section * 6)
            content_parts.append(section_content)
        
        return "\n\n".join(content_parts)
    
    @staticmethod
    def create_bulk_test_data(
        topic_count: int = 5,
        files_per_topic: int = 3,
        content_type: str = "mixed"
    ) -> Dict[str, Any]:
        """Create bulk test data for performance testing."""
        topics = []
        
        for i in range(topic_count):
            topic_data = TestDataFactory.create_topic_data(
                title=f"批量测试主题 {i+1}",
                description=f"用于批量测试的主题 {i+1}"
            )
            
            files = []
            for j in range(files_per_topic):
                if content_type == "mixed":
                    selected_type = random.choice(["article", "technical", "academic"])
                else:
                    selected_type = content_type
                
                content = TestDataFactory.create_document_content(
                    content_type=selected_type,
                    word_count=random.randint(200, 800)
                )
                
                file_data = TestDataFactory.create_file_data(
                    filename=f"文档_{i+1}_{j+1}.txt",
                    content=content.encode(),
                    content_type="text/plain"
                )
                files.append(file_data)
            
            topics.append({
                "topic": topic_data,
                "files": files
            })
        
        return {
            "topics": topics,
            "total_topics": topic_count,
            "total_files": topic_count * files_per_topic,
            "estimated_size": sum(
                sum(len(f["content"]) for f in topic["files"])
                for topic in topics
            )
        }


class TestAssertions:
    """Custom assertions for testing RAG system."""
    
    @staticmethod
    def assert_valid_api_response(response, expected_status: int = 200):
        """Assert API response is valid."""
        assert response.status_code == expected_status, \
            f"Expected status {expected_status}, got {response.status_code}: {response.text}"
        
        if expected_status == 200 and response.headers.get("content-type", "").startswith("application/json"):
            data = response.json()
            assert isinstance(data, (dict, list)), "Response should be valid JSON"
    
    @staticmethod
    def assert_topic_structure(topic_data: Dict[str, Any]):
        """Assert topic data has correct structure."""
        required_fields = ["id", "name", "description", "status", "created_at", "updated_at"]
        
        for field in required_fields:
            assert field in topic_data, f"Topic missing required field: {field}"
        
        assert isinstance(topic_data["id"], (int, str))
        assert isinstance(topic_data["name"], str)
        assert len(topic_data["name"]) > 0
    
    @staticmethod
    def assert_file_structure(file_data: Dict[str, Any]):
        """Assert file data has correct structure."""
        required_fields = ["id", "original_name", "content_type", "file_size", "status", "created_at"]
        
        for field in required_fields:
            assert field in file_data, f"File missing required field: {field}"
        
        assert isinstance(file_data["file_size"], int)
        assert file_data["file_size"] >= 0
    
    @staticmethod
    def assert_search_results_relevance(results: List[Dict], query: str, min_relevance: float = 0.1):
        """Assert search results are relevant to query."""
        if not results:
            return  # Empty results are valid
        
        relevant_count = 0
        query_lower = query.lower()
        
        for result in results:
            # Check if query terms appear in result
            text_fields = ["title", "content", "name", "description"]
            
            for field in text_fields:
                if field in result and query_lower in str(result[field]).lower():
                    relevant_count += 1
                    break
        
        relevance_ratio = relevant_count / len(results)
        assert relevance_ratio >= min_relevance, \
            f"Search relevance {relevance_ratio:.2f} below threshold {min_relevance}"
    
    @staticmethod
    def assert_performance_acceptable(
        operation_time: float,
        max_time: float,
        operation_name: str = "operation"
    ):
        """Assert operation performance is acceptable."""
        assert operation_time <= max_time, \
            f"{operation_name} took {operation_time:.2f}s, exceeds limit {max_time}s"
    
    @staticmethod
    def assert_pagination_structure(data: Dict[str, Any]):
        """Assert pagination response has correct structure."""
        required_fields = ["items", "total", "limit", "offset"]
        
        for field in required_fields:
            assert field in data, f"Pagination response missing field: {field}"
        
        assert isinstance(data["items"], list)
        assert isinstance(data["total"], int)
        assert isinstance(data["limit"], int)
        assert isinstance(data["offset"], int)
        assert data["total"] >= 0
        assert data["limit"] > 0
        assert data["offset"] >= 0


class TestHelpers:
    """Helper functions for tests."""
    
    @staticmethod
    def create_test_file(content: str, filename: str = "test.txt", content_type: str = "text/plain"):
        """Create a test file object for upload."""
        return {
            "file": (filename, io.BytesIO(content.encode()), content_type)
        }
    
    @staticmethod
    def wait_for_condition(condition_func, timeout: float = 10.0, interval: float = 0.5):
        """Wait for a condition to be met."""
        import time
        
        start_time = time.time()
        while time.time() - start_time < timeout:
            if condition_func():
                return True
            time.sleep(interval)
        return False
    
    @staticmethod
    def generate_random_string(length: int = 10) -> str:
        """Generate random string for testing."""
        return ''.join(random.choices(string.ascii_letters + string.digits, k=length))
    
    @staticmethod
    def create_large_text(size_mb: float) -> str:
        """Create large text for testing."""
        target_size = int(size_mb * 1024 * 1024)  # Convert MB to bytes
        chunk = "This is a test content chunk for large file testing. " * 100
        
        content = ""
        while len(content.encode()) < target_size:
            content += chunk
        
        # Trim to exact size
        while len(content.encode()) > target_size:
            content = content[:-100]
        
        return content
    
    @staticmethod
    def extract_ids_from_responses(responses: List[Dict[str, Any]], id_field: str = "id") -> List:
        """Extract IDs from API responses."""
        return [response.get(id_field) for response in responses if id_field in response]
    
    @staticmethod
    def calculate_similarity(text1: str, text2: str) -> float:
        """Calculate basic text similarity for testing."""
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 and not words2:
            return 1.0
        if not words1 or not words2:
            return 0.0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union)


# Pytest fixtures using the factories
def pytest_configure(config):
    """Configure additional pytest markers."""
    config.addinivalue_line("markers", "data_factory: tests using test data factories")
    config.addinivalue_line("markers", "performance_baseline: performance baseline tests")
    config.addinivalue_line("markers", "load_test: load and stress tests")


# Example usage functions
def create_realistic_ml_dataset():
    """Create a realistic machine learning dataset for testing."""
    return TestDataFactory.create_bulk_test_data(
        topic_count=3,
        files_per_topic=5,
        content_type="technical"
    )


def create_academic_research_dataset():
    """Create academic research dataset for testing."""
    return TestDataFactory.create_bulk_test_data(
        topic_count=2,
        files_per_topic=8,
        content_type="academic"
    )