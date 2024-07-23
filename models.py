from dataclasses import dataclass, field
from enum import StrEnum


class Types(StrEnum):
    JOB = 'job'
    STORY = 'story'
    COMMENT = 'comment'
    
    
@dataclass
class BaseClass:
    id: int
    type: Types
    deleted: bool = False
    by: str = 'anon'
    time: int = 0
    dead: bool = False
    kids: list[int] = field(default_factory=list)

    def __str__(self):
        return f'{self.id}'


@dataclass
class Story(BaseClass):
    descendants: int = 0
    title: str = ''
    url: str = 'https://news.ycombinator.com/'
    text: str = ''
    score: int = 0
        

@dataclass
class Comment(BaseClass):
    parent: int = 0
    text: str = ''


@dataclass
class User:
    id: str
    created: int
    karma: int = 0
    about: str = ''
    delay: int = 0
    submitted: list[int] = field(default_factory=list)
    
    def __str__(self):
        return f'{self.id}'
