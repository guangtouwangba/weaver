from infrastructure.db.topic_repostory import TopicRepository


class TopicService:
    def __init__(self, repository: TopicRepository):
        self.repository = repository

    def create_topic(self, topic_data: dict):
        topic = self.repository.create_topic(topic_data)
        return topic

    def get_topic(self, topic_id: int):
        topic = self.repository.get_topic(topic_id)
        return topic

    def update_topic(self, topic_id: int, topic_data: dict):
        topic = self.repository.update_topic(topic_id, topic_data)
        return topic

    def delete_topic(self, topic_id: int):
        topic = self.repository.delete_topic(topic_id)
        return topic