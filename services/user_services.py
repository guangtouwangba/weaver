

# TODO: Implement a mock user service for testing purposes
# This mock service simulates user management operations such as creating, retrieving,
class MockUserService:
    def __init__(self):
        self.users = {"mock_user": {"name": "Mock User", "email": ""}}

    def create_user(self, user_id, user_data):
        if user_id in self.users:
            raise ValueError("User already exists")
        self.users[user_id] = user_data
        return self.users[user_id]

    def get_user(self, user_id):
        return self.users.get(user_id, None)

    def update_user(self, user_id, user_data):
        if user_id not in self.users:
            raise ValueError("User does not exist")
        self.users[user_id].update(user_data)
        return self.users[user_id]

    def delete_user(self, user_id):
        if user_id not in self.users:
            raise ValueError("User does not exist")
        del self.users[user_id]
        return True