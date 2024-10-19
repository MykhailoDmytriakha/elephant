from dataclasses import dataclass
from typing import Optional

@dataclass
class UserInteraction:
    query: str
    answer: str

    def to_dict(self):
        return {
            "query": self.query,
            "answer": self.answer
        }
