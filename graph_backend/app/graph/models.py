from pydantic import BaseModel, Field


class Node(BaseModel):
    id: str
    type: str
    properties: dict = Field(default_factory=dict)


class Edge(BaseModel):
    src: str
    dst: str
    type: str
