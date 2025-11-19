from fastapi import APIRouter, Depends, Path, Body

from app.schemas.keywords import (
    AddKeywordRequest,
    RemoveKeywordRequest,
    KeywordsListResponse,
    AddKeywordResponse,
    FinalizeKeywordsResponse
)
from app.api.dependencies import get_keyword_service

router = APIRouter()


@router.post("/{session_id}/keywords", response_model=AddKeywordResponse)
async def add_keyword(
    session_id: str = Path(..., description="Seed session ID"),
    request: AddKeywordRequest = Body(...),
    service = Depends(get_keyword_service)
):
    """
    Add a keyword filter to the session.
    
    **Supports boolean operators:**
    - AND, OR, NOT
    - Parentheses for grouping: `(machine learning) AND (fake news OR misinformation)`
    
    **Validation:**
    - Expression must not be empty
    - Parentheses must be balanced
    
    **Examples:**
    - Simple keyword: `"fake news"`
    - Boolean AND: `"fake news AND social media"`
    - Boolean OR: `"misinformation OR disinformation"`
    - Complex: `"(fake news OR misinformation) AND NOT satire"`
    """
    total = service.add_keyword(session_id, request.expression)
    return AddKeywordResponse(
        session_id=session_id,
        added_expression=request.expression,
        total_keywords=total
    )


@router.get("/{session_id}/keywords", response_model=KeywordsListResponse)
async def get_keywords(
    session_id: str = Path(..., description="Seed session ID"),
    service = Depends(get_keyword_service)
):
    """
    Get all keyword filters for the session.
    
    Returns keywords in the order they were added.
    """
    keywords = service.get_keywords(session_id)
    return KeywordsListResponse(
        session_id=session_id,
        keywords=keywords,
        total_count=len(keywords)
    )


@router.delete("/{session_id}/keywords/item", response_model=KeywordsListResponse)
async def remove_keyword(
    session_id: str = Path(..., description="Seed session ID"),
    request: RemoveKeywordRequest = Body(...),
    service = Depends(get_keyword_service)
):
    """
    Remove a specific keyword filter.
    
    Send the exact keyword expression in the request body.
    """
    service.remove_keyword(session_id, request.expression)
    keywords = service.get_keywords(session_id)
    return KeywordsListResponse(
        session_id=session_id,
        keywords=keywords,
        total_count=len(keywords)
    )


@router.delete("/{session_id}/keywords/all", response_model=KeywordsListResponse)
async def clear_keywords(
    session_id: str = Path(..., description="Seed session ID"),
    service = Depends(get_keyword_service)
):
    """
    Clear all keyword filters for the session.
    """
    service.clear_keywords(session_id)
    keywords = service.get_keywords(session_id)
    return KeywordsListResponse(
        session_id=session_id,
        keywords=keywords,
        total_count=len(keywords)
    )


@router.post("/{session_id}/keywords/finalize", response_model=FinalizeKeywordsResponse)
async def finalize_keywords(
    session_id: str = Path(..., description="Seed session ID"),
    service = Depends(get_keyword_service)
):
    """
    Finalize keyword selection.
    
    Marks the keyword selection as complete and ready to proceed to configuration.
    
    **Note:** It's okay to have zero keywords. The crawler will process all papers.
    """
    keywords = service.finalize_keywords(session_id)
    
    if not keywords:
        message = "No keywords provided. Crawler will process all papers."
    else:
        message = f"Finalized {len(keywords)} keyword filter(s)"
    
    return FinalizeKeywordsResponse(
        session_id=session_id,
        keywords=keywords,
        total_count=len(keywords),
        message=message
    )