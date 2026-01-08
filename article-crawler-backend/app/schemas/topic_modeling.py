from pydantic import BaseModel, Field, field_validator
from typing import List, Optional


class StartTopicModelingRequest(BaseModel):
    model_type: str = Field(default="NMF", description="Topic modeling algorithm: NMF or LDA")
    num_topics: int = Field(default=20, ge=2, le=100, description="Number of topics")

    @field_validator('model_type')
    @classmethod
    def validate_model_type(cls, v: str) -> str:
        v_up = v.upper()
        if v_up not in {"NMF", "LDA"}:
            raise ValueError("model_type must be 'NMF' or 'LDA'")
        return v_up


class TopicSummary(BaseModel):
    topic_id: int = Field(..., description="Topic identifier")
    label: str = Field(..., description="Topic label")
    paper_count: int = Field(..., description="Number of papers assigned")


class StartTopicModelingResponse(BaseModel):
    session_id: str
    model_type: str
    num_topics: int
    total_topics_with_papers: int
    topics: List[TopicSummary] = Field(default_factory=list)
    overview_path: str = Field(..., description="Path to the topic overview markdown file")
    topics_folder: str = Field(..., description="Path to the topics folder in the library")
