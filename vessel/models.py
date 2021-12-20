from collections import namedtuple
from peewee import *
import datetime

class Issue():
    name:str
    metadata: dict

    def __init__(self, name:str, metadata:dict = None ) -> None:
        self.name = name
        self.metadata = metadata

class Problem(Model):
    id = BigAutoField(primary_key=True)
    name = CharField()
    namespace = CharField(index=True)
    kind = CharField(index=True)
    issue = CharField(index=True)
    issue_metadata = CharField()
    task = CharField(index=True)
    created_at = DateTimeField(default=lambda: datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),index=True)

    def __str__(self):
        return f"{self.name} {self.issue}"
    
    def to_dict(self):
        return {
            'name': self.name,
            'namespace': self.namespace,
            'kind': self.kind,
            'issue': self.issue,
            'issue_metadata': self.issue_metadata,
            'task': self.task,
            'created_at': self.created_at
        }


