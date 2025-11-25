from fastapi import APIRouter, Depends, UploadFile, File, Form, Path, HTTPException
from typing import List

from app.schemas.pdf_seeds import (
    PDFUploadResponse,
    PDFExtractionResponse,
    PDFMatchResponse,
    PDFConfirmRequest,
    PDFConfirmResponse,
    PDFReviewRequest,
    PDFStageResponse,
)
from app.api.dependencies import (
    get_pdf_seed_service,
    get_seed_session_service,
    get_pdf_seed_workflow_service,
)

router = APIRouter()


@router.post("/{session_id}/pdfs/upload", response_model=PDFUploadResponse)
async def upload_pdfs(
    session_id: str = Path(..., description="Seed session ID"),
    files: List[UploadFile] = File(..., description="Document files to upload (PDF, DOCX, HTML, XML, LaTeX; max 20 files, 10MB each)"),
    pdf_service = Depends(get_pdf_seed_service)
):
    """
    Upload document files for seed extraction.
    
    **Requirements:**
    - GROBID service must be running on port 8070 when uploading PDFs
    - Maximum 20 files per upload
    - Maximum 10MB per file
    
    **Returns:**
    - upload_id to use for subsequent operations
    - List of uploaded filenames
    """
    return pdf_service.upload_pdfs(files)


@router.get("/{session_id}/pdfs/grobid/status")
async def grobid_status(
    session_id: str = Path(..., description="Seed session ID"),
    pdf_service = Depends(get_pdf_seed_service),
    session_service = Depends(get_seed_session_service),
):
    """
    Check whether the GROBID service is currently reachable.
    """
    session_service.get_session(session_id)
    available, message = pdf_service.check_grobid_availability()
    return {"available": available, "message": message}


@router.post("/{session_id}/pdfs/{upload_id}/extract", response_model=PDFExtractionResponse)
async def extract_pdf_metadata(
    session_id: str = Path(..., description="Seed session ID"),
    upload_id: str = Path(..., description="Upload ID from upload step"),
    pdf_service = Depends(get_pdf_seed_service)
):
    """
    Extract metadata from uploaded documents (PDF, DOCX, HTML, XML, LaTeX).
    
    PDF files still rely on GROBID; other formats are processed directly.
    
    **Returns:**
    - Extracted metadata for each file (title, authors, year, DOI, venue, abstract)
    - Success/failure status for each file
    """
    return pdf_service.extract_metadata(upload_id)


@router.post("/{session_id}/pdfs/{upload_id}/review")
async def review_pdf_metadata(
    session_id: str = Path(..., description="Seed session ID"),
    upload_id: str = Path(..., description="Upload ID"),
    request: PDFReviewRequest = None,
    pdf_service = Depends(get_pdf_seed_service)
):
    """
    Submit reviewed PDF metadata.
    
    For each PDF, user can:
    - **accept**: Use extracted metadata as-is
    - **edit**: Modify metadata before matching
    - **skip**: Don't use this PDF as a seed
    
    **Returns:**
    - Confirmation of reviews processed
    """
    return pdf_service.review_metadata(upload_id, request.reviews)


@router.post("/{session_id}/pdfs/{upload_id}/match", response_model=PDFMatchResponse)
async def match_pdf_metadata(
    session_id: str = Path(..., description="Seed session ID"),
    upload_id: str = Path(..., description="Upload ID"),
    api_provider: str = Form(default="openalex", description="API provider (openalex or semantic_scholar)"),
    pdf_service = Depends(get_pdf_seed_service)
):
    """
    Match reviewed PDF metadata against API.
    
    Tries to find papers in the API using:
    1. DOI lookup (if available)
    2. Title search
    
    **Returns:**
    - Match results with confidence scores
    - Paper metadata for matched papers
    """
    return pdf_service.match_against_api(upload_id, api_provider)


@router.post("/{session_id}/pdfs/{upload_id}/stage", response_model=PDFStageResponse)
async def stage_reviewed_pdfs(
    session_id: str = Path(..., description="Seed session ID"),
    upload_id: str = Path(..., description="Upload ID"),
    workflow_service=Depends(get_pdf_seed_workflow_service),
):
    """
    Stage reviewed PDF metadata into the unified staging table without matching.
    """
    try:
        return workflow_service.stage_reviewed(session_id, upload_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/{session_id}/pdfs/{upload_id}/confirm", response_model=PDFConfirmResponse)
async def confirm_pdf_seeds(
    session_id: str = Path(..., description="Seed session ID"),
    upload_id: str = Path(..., description="Upload ID"),
    request: PDFConfirmRequest = None,
    workflow_service=Depends(get_pdf_seed_workflow_service),
):
    """
    Confirm which PDF matches to add as seeds.
    
    **Actions:**
    - **use_all**: Add all successfully matched papers as seeds
    - **skip_all**: Don't add any papers as seeds
    
    **Returns:**
    - Number of seeds added
    - Total seeds in session
    
    Note: Temp files are cleaned up after confirmation.
    """
    if not request:
        raise HTTPException(status_code=400, detail="Confirmation request payload is required.")
    try:
        return workflow_service.confirm_matches(session_id, upload_id, request.action)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.delete("/{session_id}/pdfs/{upload_id}")
async def cancel_pdf_upload(
    session_id: str = Path(..., description="Seed session ID"),
    upload_id: str = Path(..., description="Upload ID"),
    pdf_service = Depends(get_pdf_seed_service)
):
    """
    Cancel PDF upload and cleanup temporary files.
    """
    pdf_service.cleanup_session(upload_id)
    return {"message": f"PDF upload {upload_id} cancelled and cleaned up"}
