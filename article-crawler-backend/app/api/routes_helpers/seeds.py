from app.schemas.seeds import PaperIDsRequest, PaperIDsResponse


class SeedRouteHelper:
    """Wrapper that delegates seed-related commands to the selection service."""

    def __init__(self, seed_selection_service):
        self.seed_selection_service = seed_selection_service

    def match_paper_ids(self, request: PaperIDsRequest) -> PaperIDsResponse:
        result = self.seed_selection_service.match_paper_ids(
            paper_ids=request.paper_ids,
            api_provider=request.api_provider,
        )
        return PaperIDsResponse(result=result)
