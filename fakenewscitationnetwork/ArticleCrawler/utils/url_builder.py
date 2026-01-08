class PaperURLBuilder:
    
    @staticmethod
    def build_url(paper_id: str, api_provider: str) -> str:
        api_provider = api_provider.lower()
        
        if api_provider in ['openalex', 'open_alex']:
            if paper_id.startswith('W'):
                return f"https://openalex.org/works/{paper_id}"
            else:
                return f"https://openalex.org/works/W{paper_id}"
        else:
            return f"https://www.semanticscholar.org/paper/{paper_id}"