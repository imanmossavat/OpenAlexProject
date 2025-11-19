from pydantic import BaseModel, Field, field_validator
from typing import List


class KeywordFilter(BaseModel):
    """A single keyword filter/expression."""
    expression: str = Field(..., description="Keyword or boolean expression")
    
    @field_validator('expression')
    @classmethod
    def validate_expression(cls, v: str) -> str:
        """Validate that expression is not empty and has balanced parentheses."""
        v = v.strip()
        if not v:
            raise ValueError("Expression cannot be empty")
        
        stack = []
        for char in v:
            if char == '(':
                stack.append(char)
            elif char == ')':
                if not stack:
                    raise ValueError("Unbalanced parentheses: too many closing parentheses")
                stack.pop()
        
        if stack:
            raise ValueError("Unbalanced parentheses: unclosed opening parentheses")
        
        return v


class AddKeywordRequest(BaseModel):
    """Request to add a keyword filter."""
    expression: str = Field(..., description="Keyword or boolean expression (supports AND, OR, NOT, parentheses)")

class RemoveKeywordRequest(BaseModel):
    """Request to remove a keyword filter."""
    expression: str = Field(..., description="Exact keyword expression to remove")


class KeywordsListResponse(BaseModel):
    """Response showing current keywords."""
    session_id: str
    keywords: List[str]
    total_count: int


class AddKeywordResponse(BaseModel):
    """Response after adding a keyword."""
    session_id: str
    added_expression: str
    total_keywords: int


class FinalizeKeywordsResponse(BaseModel):
    """Response after finalizing keywords."""
    session_id: str
    keywords: List[str]
    total_count: int
    message: str