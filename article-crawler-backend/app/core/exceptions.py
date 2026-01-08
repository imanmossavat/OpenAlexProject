from fastapi import HTTPException, status


class ArticleCrawlerException(Exception):
    """Base exception for all ArticleCrawler errors."""
    pass


class LibraryNotFoundException(ArticleCrawlerException):
    """Raised when a library is not found."""
    pass


class InvalidInputException(ArticleCrawlerException):
    """Raised when input validation fails."""
    pass


class CrawlerException(ArticleCrawlerException):
    """Raised when crawler encounters an error."""
    pass


def to_http_exception(exc: Exception) -> HTTPException:
    """Convert domain exceptions to HTTP exceptions."""
    
    if isinstance(exc, LibraryNotFoundException):
        return HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc)
        )
    
    if isinstance(exc, InvalidInputException):
        return HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc)
        )
    
    if isinstance(exc, CrawlerException):
        return HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Crawler error: {str(exc)}"
        )
    
    return HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=f"Internal server error: {str(exc)}"
    )