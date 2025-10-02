# usecases/author_investigation.py

class AuthorInvestigation:
    def __init__(self, data_manager, api=None, logger=None):
        self.data_manager = data_manager
        self.api = api if api else data_manager.api
        self.logger = logger if logger else data_manager.logger 

    def retrieve_and_process_author_papers(self, author_ids, check_for_keywords=True):
        """
        Retrieves and processes papers associated with the given author IDs.

        :param author_ids: List of author IDs.
        :param check_for_keywords: Boolean flag to filter papers by keywords.
        """
        if not author_ids:
            self.logger.info("No author IDs provided for retrieval.")
            return

        paper_ids, papers_list = self.retrieve_author_papers(author_ids)

        if check_for_keywords:
            accepted_paper_ids = self.data_manager.filter_papers_by_keywords(papers_list)
        else:
            accepted_paper_ids = paper_ids

        self.data_manager.retrieve_and_process_papers(accepted_paper_ids)
        self.data_manager.frames.set_key_author_flag(accepted_paper_ids)

        return paper_ids, papers_list

    def retrieve_author_papers(self, author_ids):
        """
        Retrieves papers associated with the given author IDs.

        :param author_ids: List of author IDs.
        :return: Tuple (list of paper IDs, list of paper data).
        """
        papers, paper_ids = [], []
        for author_id in author_ids:
            try:
                papers_, paper_ids_ = self.api.get_author_papers(author_id=author_id)
                papers.extend(papers_)
                paper_ids.extend(paper_ids_)
            except Exception as e:
                self.logger.error(f"Failed to retrieve papers for author {author_id}: {e}")
        
        return paper_ids, papers
