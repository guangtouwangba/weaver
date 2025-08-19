


async def get_conversation_history(
    conversation_id: str,
    user_id: str,
):
    """
    Retrieve the conversation history for a given conversation ID and user ID.
    """
    conversation = await db.get_conversation_by_id(conversation_id, user_id)
    if not conversation:
        return {"error": "Conversation not found"}, 404

    return {"conversation": conversation}, 200


