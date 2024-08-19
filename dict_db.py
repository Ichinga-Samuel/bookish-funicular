"""
Mock DB for testing purposes
"""
import shelve

from models import Story, Comment, User


class DictDB:
    types = {'story': Story, 'comment': Comment, 'job': Story}
    
    def __init__(self, name='data'):
        # self.db = shelve.open(name, writeback=True)
        # self.data = self.db.setdefault('data', {'story': {}, 'comment': {}, 'job': {}, 'user': {}})
        self.data = {'story': {}, 'comment': {}, 'job': {}, 'user': {}}


    def clear(self):
        ...
        # self.db.clear()
        # self.db.sync()

    def __len__(self):
        return sum(len(v) for v in self.data.values())

    def __str__(self):
        return (f"Stories: {len(self.data['story'])}\n"
                f"Comments: {len(self.data['comment'])}\n"
                f"Jobs: {len(self.data['job'])}\n"
                f"Users: {len(self.data['user'])}\n")

    def get(self, key):
        return self.data.get(key)

    async def save(self, *, data):
        try:
            key = data['type']
            model = self.types[key]
            data = model(**data)
            self.data[key][data.id] = data
            # self.db.sync()
        except (Exception) as exe:
            print(f"Error saving item: {exe}")
    
    async def save_user(self, *, data):
        try:
            data = User(**data)
            self.data['user'][data.id] = data
            # self.db.sync()
        except Exception as exe:
            print(f"Error saving user: {exe}")

    def delete(self, key):
        del self.data[key]
        # self.db.sync()
