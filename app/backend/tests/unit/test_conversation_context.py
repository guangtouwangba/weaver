from research_agent.domain.services.conversation_context import ConversationContext


class TestConversationContext:
    def test_resolve_reference_video(self):
        entities = {
            "v1": {"id": "v1", "type": "video", "title": "Intro to AI"},
            "v2": {"id": "v2", "type": "video", "title": "Advanced AI"},
        }
        ctx = ConversationContext(entities=entities)

        # "this video" should resolve to v2 (last added)
        resolved = ctx.resolve_reference("summarize this video")
        assert resolved is not None
        assert resolved["id"] == "v2"

    def test_resolve_reference_pdf(self):
        entities = {
            "doc1": {"id": "doc1", "type": "document", "title": "Spec.pdf"},
            "v1": {"id": "v1", "type": "video", "title": "Video.mp4"},
        }
        ctx = ConversationContext(entities=entities)

        # "the pdf" should resolve to doc1, skipping v1
        resolved = ctx.resolve_reference("what is inside the pdf")
        assert resolved is not None
        assert resolved["id"] == "doc1"

    def test_resolve_generic_focus(self):
        entities = {"v1": {"id": "v1", "type": "video", "title": "V1"}}
        ctx = ConversationContext(entities=entities, focus=entities["v1"])

        resolved = ctx.resolve_reference("tell me about it")
        assert resolved is not None
        assert resolved["id"] == "v1"

    def test_resolve_no_match(self):
        ctx = ConversationContext()
        assert ctx.resolve_reference("hello") is None
