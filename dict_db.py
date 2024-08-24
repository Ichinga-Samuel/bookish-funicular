"""
Mock DB for testing purposes
"""
from models import Story, Comment, User


class DictDB:
    types = {'story': Story, 'comment': Comment, 'job': Story}
    
    def __init__(self):
        self.data = {'story': {}, 'comment': {}, 'job': {}, 'user': {}}
        self.index = dict()

    def __len__(self):
        return sum(len(v) for v in self.data.values())

    def __str__(self):
        return (f"Stories: {len(self.data['story'])}\n"
                f"Comments: {len(self.data['comment'])}\n"
                f"Jobs: {len(self.data['job'])}\n"
                f"Users: {len(self.data['user'])}\n")

    async def save(self, *, data):
        try:
            key = data['type']
            model = self.types[key]
            data = model(**data)
            self.data[key][data.id] = data
        except Exception as exe:
            print(f"Error saving item: {exe}")
    
    async def save_user(self, *, data):
        try:
            data = User(**data)
            self.data['user'][data.id] = data
        except Exception as exe:
            print(f"Error saving user: {exe}")
