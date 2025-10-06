
from pathlib import Path
import os
import pandas as pd
from ArticleCrawler.utils.url_builder import PaperURLBuilder
class MarkdownFileGenerator:
    """
    Class responsible for generating markdown files based on provided dataframes.
    
    Attributes:
    - vault_path (str or Path): The base path of the vault.
    - experiment_file_name (str): The name of the experiment or project.
    - abstracts_folder (Path): The path to the folder where abstracts will be stored.
    """
    
    def __init__(self, 
                 storage_and_logging_options,
                 api_provider_type: str = 'semantic_scholar'):
        self.experiment_file_name = storage_and_logging_options.experiment_file_name
        self.vault_folder = storage_and_logging_options.vault_folder
        self.figure_folder = storage_and_logging_options.figure_folder
        self.abstracts_folder = storage_and_logging_options.abstracts_folder
        self.metadata_folder = storage_and_logging_options.metadata_folder
        self.summary_folder = storage_and_logging_options.summary_folder
        self.open_vault_folder = storage_and_logging_options.open_vault_folder
        self.api_provider_type = api_provider_type.lower()
        self.url_builder = PaperURLBuilder()



    def create_folders(self):
        """
        Creates necessary directory structure for abstracts storage.
        """
        self.abstracts_folder.mkdir(parents=True, exist_ok=True)
        self.figure_folder.mkdir(parents=True, exist_ok=True)
        self.metadata_folder.mkdir(parents=True, exist_ok=True)
        self.summary_folder.mkdir(parents=True, exist_ok=True)
        

    def _get_references(self, paper_id, df_paper_references):
        """
        Retrieves references for a specific paper ID from the paper references dataframe.

        Args:
        - paper_id (str): The ID of the paper.
        - df_paper_references (DataFrame): DataFrame containing paper references.

        Returns:
        - list: List of reference paper IDs.
        """
        return df_paper_references[df_paper_references['paperId'] == paper_id]['referencePaperId'].tolist()


    def _get_metadata(self, paper_id, df_meta, df_paper_author, df_author):
        """
        Retrieves metadata including Semantic Scholar link and author name for a specific paper ID from the metadata dataframe.

        Args:
        - paper_id (str): The ID of the paper.
        - df_meta (DataFrame): DataFrame containing paper metadata.
        - df_paper_author (DataFrame): DataFrame linking paper ID to author ID.
        - df_author (DataFrame): DataFrame linking author ID to author name.

        Returns:
        - DataFrame: Metadata for the paper including Semantic Scholar link and author name.
        """
        paper_metadata = df_meta[df_meta['paperId'] == paper_id][['paperId', 'venue', 'year', 'title']]
        
        # Adding Semantic Scholar link
        paper_metadata['semantic_scholar_link'] = 'https://www.semanticscholar.org/paper/' + paper_metadata['paperId']
        
        # Fetching and adding author names
        author_ids = df_paper_author[df_paper_author['paperId'] == paper_id]['authorId'].tolist()
        author_names = df_author[df_author['authorId'].isin(author_ids)]['authorName'].tolist()
        paper_metadata['authors'] = ', '.join(author_names) if author_names else "Unknown Author(s)"
        
        return paper_metadata
    
    def _get_paper_url(self, paper_id: str) -> str:
        return self.url_builder.build_url(paper_id, self.api_provider_type)

    def _get_author_names(self, paper_id, df_paper_author, df_author):
        """
        Retrieves author names for a specific paper ID.

        Args:
        - paper_id (str): The ID of the paper.
        - df_paper_author (DataFrame): DataFrame linking paper ID to author ID.
        - df_author (DataFrame): DataFrame linking author ID to author name.

        Returns:
        - str: Author names for the paper.
        """
        author_ids = df_paper_author[df_paper_author['paperId'] == paper_id]['authorId'].tolist()
        author_names = df_author[df_author['authorId'].isin(author_ids)]['authorName'].tolist()
        return ', '.join(author_names) if author_names else "Unknown Author(s)"

    def _get_top_authors(self, df_author, df_paper_author):
        """
        Retrieves the top authors based on max_citations, avg_citations, and num_citations.
        """
        # Sort authors by max_citations, avg_citations, num_citations
        top_authors_max_citations = df_author.nlargest(5, 'max_citations')
        top_authors_avg_citations = df_author.nlargest(5, 'avg_citations')
        top_authors_num_citations = df_author.nlargest(5, 'num_citations')
        
        # Combine and remove duplicates
        top_authors = pd.concat([top_authors_max_citations, top_authors_avg_citations, top_authors_num_citations]).drop_duplicates()

        return top_authors

    def _get_top_venues(self, df_venue_features):
        """
        Retrieves the top venues based on total_papers, self_citations, citing_others, and being_cited_by_others.
        """
        # Sort venues by the relevant features
        top_venues_total_papers = df_venue_features.nlargest(5, 'total_papers')
        top_venues_self_citations = df_venue_features.nlargest(5, 'self_citations')
        top_venues_citing_others = df_venue_features.nlargest(5, 'citing_others')
        top_venues_being_cited_by_others = df_venue_features.nlargest(5, 'being_cited_by_others')

        # Combine and remove duplicates
        top_venues = pd.concat([top_venues_total_papers, top_venues_self_citations, top_venues_citing_others, top_venues_being_cited_by_others]).drop_duplicates()

        return top_venues

    def _create_markdown_content(self, paper_id, abstract, paper_metadata, references, df_abstract):
        """
        Constructs markdown content for a specific paper.

        Args:
        - paper_id (str): The ID of the paper.
        - abstract (str): The abstract of the paper.
        - paper_metadata (DataFrame): Metadata for the paper.
        - references (list): List of reference paper IDs.
        - df_abstract (DataFrame): DataFrame containing abstracts data.

        Returns:
        - str: Constructed markdown content for the paper.
        """
        markdown_content = f"# Title: {paper_metadata['title'].values[0]}\n"
        markdown_content += f"## Abstract\n\n{abstract}\n\n"
        
        # Including Semantic Scholar link in the metadata section
        markdown_content += "## Metadata\n\n"
        markdown_content += paper_metadata.drop(columns=['authors']).to_markdown(index=False) + '\n\n'

        if references:
            markdown_content += "## References\n\n"
            for ref_id in references:
                if ref_id in df_abstract['paperId'].values:
                    markdown_content += f"[[{ref_id}]]\n"
                else:
                    markdown_content += f"{ref_id}\n"
        
        return markdown_content


    def _create_markdown_content_abstractOnly(self, abstract, paper_metadata):
        """
        Constructs markdown content for a specific paper.

        Args:
        - paper_id (str): The ID of the paper.
        - abstract (str): The abstract of the paper.
        - paper_metadata (DataFrame): Metadata for the paper.
        - references (list): List of reference paper IDs.
        - df_abstract (DataFrame): DataFrame containing abstracts data.

        Returns:
        - str: Constructed markdown content for the paper.
        """
        paper_url = self._get_paper_url(paper_metadata['paperId'].values[0])
        title = paper_metadata['title'].values[0]
        
        markdown_content = f"# [{title}]({paper_url})\n\n"
        markdown_content += f"## Abstract\n\n{abstract}\n\n"
                
        return markdown_content


    def _create_top_authors_markdown(self, top_authors):
        """
        Generates markdown content for top authors.
        """
        markdown_content = "# Top Authors\n\n"
        
        for idx, row in top_authors.iterrows():
            markdown_content += f"## {row['authorName']}\n"
            markdown_content += f"- Max Citations: {row['max_citations']}\n"
            markdown_content += f"- Avg Citations: {row['avg_citations']}\n"
            markdown_content += f"- Num Citations: {row['num_citations']}\n\n"

        return markdown_content
    
    def _create_top_venues_markdown(self, top_venues):
        """
        Generates markdown content for top venues.
        """
        markdown_content = "# Top Venues\n\n"
        
        for idx, row in top_venues.iterrows():
            markdown_content += f"## {row['venue']}\n"
            markdown_content += f"- Total Papers: {row['total_papers']}\n"
            markdown_content += f"- Self Citations: {row['self_citations']}\n"
            markdown_content += f"- Citing Others: {row['citing_others']}\n"
            markdown_content += f"- Being Cited by Others: {row['being_cited_by_others']}\n\n"

        return markdown_content
    
    def generate_markdown_files(self, df_abstract, df_meta, df_paper_references, 
                                df_paper_author, df_author, df_additional_abstract, df_venue_features):
        """
        Generates markdown files based on provided dataframes.

        Args:
        - df_abstract (DataFrame): DataFrame containing abstracts data.
        - df_meta (DataFrame): DataFrame containing paper metadata.
        - df_paper_references (DataFrame): DataFrame containing paper references.
        - df_paper_author (DataFrame): DataFrame linking paper ID to author ID.
        - df_author (DataFrame): DataFrame linking author ID to author name.
        - df_additional_abstract (DataFrame): Additional DataFrame containing abstracts data.
        - df_venue_features (DataFrame): DataFrame containing venue features.
        """
        
        # 1. Get Top Authors and Top Venues
        top_authors = self._get_top_authors(df_author, df_paper_author)
        top_venues = self._get_top_venues(df_venue_features)
        
        # 2. Create markdown content for Top Authors and Top Venues
        top_authors_markdown = self._create_top_authors_markdown(top_authors)
        top_venues_markdown = self._create_top_venues_markdown(top_venues)
        
        # 3. Save Top Authors and Top Venues markdown files
        top_authors_file = self.summary_folder / 'top_authors.md'
        top_venues_file = self.summary_folder / 'top_venues.md'
        
        with open(top_authors_file, 'w', encoding='utf-8') as file:
            file.write(top_authors_markdown)
        
        with open(top_venues_file, 'w', encoding='utf-8') as file:
            file.write(top_venues_markdown)

        # 4. Process the individual papers (as before)
        for index, row in df_abstract.iterrows():
            paper_id = row['paperId']
            abstract = row['abstract']

            if abstract is None:
                print("Skipping row with 'None' abstract.")
                continue
            elif len(abstract) < 10:
                print("Skipping short abstract.")
                print(abstract)
                continue

            references = self._get_references(paper_id, df_paper_references)
            paper_metadata = self._get_metadata(paper_id, df_meta, df_paper_author, df_author)

            try:
                markdown_content = self._create_markdown_content_abstractOnly(abstract, paper_metadata)
            except UnicodeEncodeError as e:
                print(f"Error writing file {paper_id}. Skipping... {e}")
                continue
            
            file_path = self.abstracts_folder / f'{paper_id}.md'

            with open(file_path, 'w', encoding='utf-8') as file:
                file.write(markdown_content)


    def generate_markdown_files_from_crawler(self, data_manager):
        """
        Generates markdown files based on dataframes extracted from a given myCrawler instance.

        Args:
        - myCrawler: An instance of the myCrawler class.
        """
        print('doing stuff generate markdown files ...')
        # Extract dataframes from myCrawler.data_manager.frames
        df_abstract = data_manager.frames.df_abstract
        df_abstract = df_abstract[df_abstract['abstract'] != 'None']

        df_meta = data_manager.frames.df_paper_metadata
        df_paper_references = data_manager.frames.df_paper_references
        df_paper_author = data_manager.frames.df_paper_author
        df_author = data_manager.frames.df_author
        df_venue_features = data_manager.frames.df_venue_features  # Get df_venue_features


        # Create folders if they don't exist
        self.create_folders()


        self.generate_markdown_files(df_abstract, df_meta, df_paper_references, df_paper_author, df_author, df_abstract, df_venue_features)

        
        if self.open_vault_folder:
            os.startfile(self.vault_folder)

        print(f'Vault stored at {self.vault_folder}')


