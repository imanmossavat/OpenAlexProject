from fastapi import APIRouter, Depends, UploadFile, File, Form, Path
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
from app.schemas.seeds import MatchedSeed
from app.schemas.staging import StagingPaperCreate
from ArticleCrawler.api.api_factory import create_api_provider
from app.api.dependencies import get_pdf_seed_service, get_seed_session_service, get_staging_service

router = APIRouter()


@router.post("/{session_id}/pdfs/upload", response_model=PDFUploadResponse)
async def upload_pdfs(
    session_id: str = Path(..., description="Seed session ID"),
    files: List[UploadFile] = File(..., description="PDF files to upload (max 20 files, 10MB each)"),
    pdf_service = Depends(get_pdf_seed_service)
):
    """
    Upload PDF files for seed extraction.
    
    **Requirements:**
    - GROBID service must be running on port 8070
    - Maximum 20 PDF files per upload
    - Maximum 10MB per PDF file
    
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
    Extract metadata from uploaded PDFs using GROBID.
    
    This process may take a few seconds per PDF.
    
    **Returns:**
    - Extracted metadata for each PDF (title, authors, year, DOI, venue)
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
    pdf_service = Depends(get_pdf_seed_service),
    session_service = Depends(get_seed_session_service),
    staging_service=Depends(get_staging_service),
):
    """
    Stage reviewed PDF metadata into the unified staging table without matching.
    """
    session_service.get_session(session_id)
    reviewed = pdf_service.get_reviewed_metadata(upload_id)
    if not reviewed:
        raise ValueError("No reviewed metadata available. Review metadata before staging.")
    staging_rows = [
        StagingPaperCreate(
            source="PDF Uploads",
            source_type="pdf",
            title=md.title,
            authors=md.authors,
            year=md.year,
            venue=md.venue,
            doi=md.doi,
            url=None,
            abstract=None,
            source_id=md.doi or md.filename,
            is_selected=False,
        )
        for md in reviewed
    ]
    added_rows = staging_service.add_rows(session_id, staging_rows)
    stats = staging_service.list_rows(session_id, page=1, page_size=1)
    pdf_service.cleanup_session(upload_id)
    return PDFStageResponse(upload_id=upload_id, staged_count=len(added_rows), total_staged=stats.total_rows)


@router.post("/{session_id}/pdfs/{upload_id}/confirm", response_model=PDFConfirmResponse)
async def confirm_pdf_seeds(
    session_id: str = Path(..., description="Seed session ID"),
    upload_id: str = Path(..., description="Upload ID"),
    request: PDFConfirmRequest = None,
    pdf_service = Depends(get_pdf_seed_service),
    session_service = Depends(get_seed_session_service),
    staging_service = Depends(get_staging_service),
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
    session_service.get_session(session_id)

    seeds_data = pdf_service.get_matched_seeds(upload_id, request.action)
    
    matched_seeds = [
        MatchedSeed(
            paper_id=s["paper_id"],
            title=s["title"],
            authors=s["authors"],
            year=s["year"],
            venue=s["venue"],
            confidence=s["confidence"],
            match_method=s["match_method"],
            source="PDF Uploads",
            source_type="pdf",
            source_id=s.get("source_id") or s["paper_id"],
        )
        for s in seeds_data
    ]

    try:
        api = create_api_provider("openalex")
    except Exception:
        api = None

    def extract_enrichments(paper):
        extras = {
            "doi": None,
            "url": None,
            "abstract": None,
            "cited_by_count": None,
            "references_count": None,
            "institutions": None,
        }
        try:
            if isinstance(paper, dict):
                cited = paper.get('cited_by_count')
                if isinstance(cited, int):
                    extras["cited_by_count"] = cited
                refs = paper.get('referenced_works')
                extras["references_count"] = len(refs) if isinstance(refs, list) else None
                extras["doi"] = paper.get('doi') or None
                pl = paper.get('primary_location') or {}
                if isinstance(pl, dict):
                    extras["url"] = pl.get('landing_page_url') or None
                abstract = paper.get('abstract') or None
                if not abstract:
                    inv = paper.get('abstract_inverted_index')
                    if isinstance(inv, dict):
                        try:
                            max_pos = 0
                            for _, positions in inv.items():
                                if positions:
                                    max_pos = max(max_pos, max(positions))
                            tokens = [''] * (max_pos + 1)
                            for word, positions in inv.items():
                                for pos in positions:
                                    tokens[pos] = word
                            abstract = ' '.join([t for t in tokens if t]) or None
                        except Exception:
                            abstract = None
                extras["abstract"] = abstract
                inst_names = []
                for auth in (paper.get('authorships') or []):
                    for inst in (auth.get('institutions') or []):
                        name = inst.get('display_name') or inst.get('name')
                        if name:
                            inst_names.append(name)
                if inst_names:
                    seen = set()
                    dedup = []
                    for n in inst_names:
                        if n not in seen:
                            seen.add(n)
                            dedup.append(n)
                    extras["institutions"] = dedup
            else:
                cited = getattr(paper, 'cited_by_count', None)
                if isinstance(cited, int):
                    extras["cited_by_count"] = cited
                refs = getattr(paper, 'referenced_works', None)
                extras["references_count"] = len(refs) if isinstance(refs, list) else None
                extras["doi"] = getattr(paper, 'doi', None) if hasattr(paper, 'doi') else None
                url = None
                try:
                    pl = getattr(paper, 'primary_location', None)
                    if pl and hasattr(pl, 'landing_page_url'):
                        url = pl.landing_page_url or None
                except Exception:
                    url = None
                extras["url"] = url
                abstract = None
                if hasattr(paper, 'abstract'):
                    abstract = getattr(paper, 'abstract') or None
                elif hasattr(paper, 'abstract_inverted_index'):
                    inv = getattr(paper, 'abstract_inverted_index')
                    if isinstance(inv, dict):
                        try:
                            max_pos = 0
                            for _, positions in inv.items():
                                if positions:
                                    max_pos = max(max_pos, max(positions))
                            tokens = [''] * (max_pos + 1)
                            for word, positions in inv.items():
                                for pos in positions:
                                    tokens[pos] = word
                            abstract = ' '.join([t for t in tokens if t]) or None
                        except Exception:
                            abstract = None
                extras["abstract"] = abstract
                inst_names = []
                try:
                    auths = getattr(paper, 'authorships', None)
                    if auths:
                        for auth in auths:
                            if hasattr(auth, 'institutions') and auth.institutions:
                                for inst in auth.institutions:
                                    nm = getattr(inst, 'display_name', None) or getattr(inst, 'name', None)
                                    if nm:
                                        inst_names.append(nm)
                except Exception:
                    pass
                if inst_names:
                    seen = set()
                    dedup = []
                    for n in inst_names:
                        if n not in seen:
                            seen.add(n)
                            dedup.append(n)
                    extras["institutions"] = dedup
        except Exception:
            pass
        return extras

    if api:
        enriched = []
        for seed in matched_seeds:
            try:
                paper = api.get_paper_metadata_only(seed.paper_id) if hasattr(api, 'get_paper_metadata_only') else api.get_paper(seed.paper_id)
                ex = extract_enrichments(paper)
                enriched.append(
                    MatchedSeed(
                        paper_id=seed.paper_id,
                        title=seed.title,
                        authors=seed.authors,
                        year=seed.year,
                        venue=seed.venue,
                        confidence=seed.confidence,
                        match_method=seed.match_method,
                        doi=ex.get("doi"),
                        url=ex.get("url"),
                        abstract=ex.get("abstract"),
                        cited_by_count=ex.get("cited_by_count"),
                        references_count=ex.get("references_count"),
                        institutions=ex.get("institutions"),
                    )
                )
            except Exception:
                enriched.append(seed)
        matched_seeds = enriched
    
    staging_rows = [
        StagingPaperCreate(
            source=seed.source or "PDF Uploads",
            source_type=seed.source_type or "pdf",
            title=seed.title,
            authors=seed.authors,
            year=seed.year,
            venue=seed.venue,
            doi=seed.doi,
            url=seed.url,
            abstract=seed.abstract,
            source_id=seed.source_id or seed.paper_id,
            is_selected=False,
        )
        for seed in matched_seeds
    ]
    staged = staging_service.add_rows(session_id, staging_rows) if staging_rows else []
    
    pdf_service.cleanup_session(upload_id)
    
    stats = staging_service.list_rows(session_id, page=1, page_size=1)
    
    return PDFConfirmResponse(
        upload_id=upload_id,
        added_count=len(staged),
        total_seeds_in_session=stats.total_rows
    )


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
