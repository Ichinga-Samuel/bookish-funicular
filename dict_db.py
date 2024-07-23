"""
Mock DB for testing purposes
"""
from models import Story, Comment, User


class DictDB:
    types = {'story': Story, 'comment': Comment, 'job': Story, 'user': User}
    
    def __init__(self):
        self.data = {}

    def __len__(self):
        return len(self.data)

    def get(self, key):
        return self.data.get(key)

    def save(self, *, data):
        try:
            model = self.types[data['type']]
            data = model(**data)
            self.data[data.id] = data
        except (KeyError, TypeError) as exe:
            print('Unable to save data', exe)

    def delete(self, key):
        del self.data[key]
