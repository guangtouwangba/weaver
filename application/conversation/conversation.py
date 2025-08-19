



class Conversation:
    def __init__(self, conversation_service):
        self.conversation_service = conversation_service


    async def get_conversation_history(self, conversation_id: str, user_id: str):
        """
        Retrieve the conversation history for a given conversation ID and user ID.
        """
        conversation = await self.conversation_service.get_conversation_by_id(conversation_id, user_id)
        if not conversation:
            return {"error": "Conversation not found"}, 404

        return {"conversation": conversation}, 200


    async def create_conversation(self, user_id: str, conversation_data: dict):
        """
        Create a new conversation for a given user ID.
        """
        conversation = await self.conversation_service.create_conversation(user_id, conversation_data)
        if not conversation:
            return {"error": "Failed to create conversation"}, 500

        return {"conversation": conversation}, 201