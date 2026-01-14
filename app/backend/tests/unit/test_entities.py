"""Unit tests for domain entities."""

from uuid import uuid4

from research_agent.domain.entities.canvas import Canvas, CanvasEdge, CanvasNode
from research_agent.domain.entities.chunk import DocumentChunk
from research_agent.domain.entities.document import Document, DocumentStatus
from research_agent.domain.entities.project import Project


class TestProject:
    """Tests for Project entity."""

    def test_create_project(self):
        """Test creating a project."""
        project = Project(name="Test Project", description="A test")

        assert project.name == "Test Project"
        assert project.description == "A test"
        assert project.id is not None

    def test_update_project(self):
        """Test updating a project."""
        project = Project(name="Original")

        project.update(name="Updated", description="New description")

        assert project.name == "Updated"
        assert project.description == "New description"


class TestDocument:
    """Tests for Document entity."""

    def test_create_document(self):
        """Test creating a document."""
        project_id = uuid4()
        document = Document(
            project_id=project_id,
            filename="test.pdf",
            file_path="/path/to/test.pdf",
        )

        assert document.filename == "test.pdf"
        assert document.status == DocumentStatus.PENDING

    def test_document_status_transitions(self):
        """Test document status transitions."""
        document = Document(filename="test.pdf")

        assert document.status == DocumentStatus.PENDING

        document.mark_processing()
        assert document.status == DocumentStatus.PROCESSING

        document.mark_ready(page_count=10)
        assert document.status == DocumentStatus.READY
        assert document.page_count == 10
        assert document.is_ready

    def test_document_error_status(self):
        """Test document error status."""
        document = Document(filename="test.pdf")
        document.mark_processing()
        document.mark_error()

        assert document.status == DocumentStatus.ERROR
        assert not document.is_ready


class TestDocumentChunk:
    """Tests for DocumentChunk entity."""

    def test_create_chunk(self):
        """Test creating a chunk."""
        chunk = DocumentChunk(
            content="Test content",
            chunk_index=0,
            page_number=1,
        )

        assert chunk.content == "Test content"
        assert not chunk.has_embedding

    def test_set_embedding(self):
        """Test setting embedding."""
        chunk = DocumentChunk(content="Test")
        chunk.set_embedding([0.1, 0.2, 0.3])

        assert chunk.has_embedding
        assert len(chunk.embedding) == 3


class TestCanvas:
    """Tests for Canvas entity."""

    def test_create_empty_canvas(self):
        """Test creating an empty canvas."""
        project_id = uuid4()
        canvas = Canvas(project_id=project_id)

        assert len(canvas.nodes) == 0
        assert len(canvas.edges) == 0

    def test_add_node(self):
        """Test adding a node."""
        canvas = Canvas()
        node = CanvasNode(id="node-1", title="Test Node")

        canvas.add_node(node)

        assert len(canvas.nodes) == 1
        assert canvas.nodes[0].title == "Test Node"

    def test_remove_node(self):
        """Test removing a node and its edges."""
        canvas = Canvas()
        canvas.add_node(CanvasNode(id="node-1"))
        canvas.add_node(CanvasNode(id="node-2"))
        canvas.add_edge(CanvasEdge(source="node-1", target="node-2"))

        canvas.remove_node("node-1")

        assert len(canvas.nodes) == 1
        assert len(canvas.edges) == 0

    def test_canvas_to_dict(self):
        """Test canvas serialization."""
        canvas = Canvas()
        canvas.add_node(CanvasNode(id="node-1", title="Test", x=100, y=200))

        data = canvas.to_dict()

        assert len(data["nodes"]) == 1
        assert data["nodes"][0]["id"] == "node-1"
        assert data["nodes"][0]["x"] == 100

    def test_canvas_from_dict(self):
        """Test canvas deserialization."""
        project_id = uuid4()
        data = {
            "nodes": [{"id": "node-1", "title": "Test", "x": 100, "y": 200}],
            "edges": [],
            "viewport": {"x": 0, "y": 0, "scale": 1},
        }

        canvas = Canvas.from_dict(data, project_id)

        assert len(canvas.nodes) == 1
        assert canvas.nodes[0].id == "node-1"
        assert canvas.project_id == project_id

