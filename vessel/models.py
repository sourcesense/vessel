from kopf._core.intents import registries
from peewee import *
import datetime
import json

class Context():
    registries: dict

    def __init__(self, registries_file) -> None:
        if registries_file is not None:
            self.registries = json.load(registries_file)
        else:
            self.registries = {}
            
        

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
    issue_metadata = CharField(null=True)
    tool = CharField(index=True)
    current = BooleanField(index=True, default=True)
    created_at = DateTimeField(default=lambda: datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),index=True)

    def __str__(self):
        return f"{self.namespace}:{self.kind}:{self.name} {self.issue} {self.tool} {self.current}"
    
    def to_dict(self):
        return {
            'name': self.name,
            'namespace': self.namespace,
            'kind': self.kind,
            'issue': self.issue,
            'issue_metadata': self.issue_metadata,
            'tool': self.tool,
            'created_at': self.created_at
        }


