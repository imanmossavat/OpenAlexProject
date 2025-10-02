"""
The FeatureComputer class computes and adds metadata and citation-related features to a set of DataFrames that represent academic papers, authors, and venues.

Paper Features: It adds features like whether a paper has an abstract, whether it's a preprint, and if it fits certain paper categories (e.g., review, tutorial).

Author Features: It computes statistics about authors, such as the number of papers they've written, their citation counts (total, average, and maximum), and their co-authorships.

Venue Features: It calculates citation behaviors for academic venues, including self-citations, citations from others, and total papers published per venue.
"""

import pandas as pd
#import torch
import numpy as np

class AcademicFeatureComputer:
    def __init__(self, preprint_repositories):
        self.preprint_repositories = preprint_repositories
        self.venue_features=None
        self.cleaned_venues= None

    def compute_meta_paper_features(self, frames, indicators = ['review', 'survey', 'tutorial', 'benchmark', 'dataset']):
        # mostly useful for paper nodes in the graph
        frames.df_paper_metadata['has_abstract'] = frames.df_paper_metadata['paperId'].isin(frames.df_abstract['paperId'])
        frames.df_paper_metadata['is_preprint'] = frames.df_paper_metadata['venue'].apply(
            lambda x: 1 if str(x).lower() in self.preprint_repositories else 0
        )

        for indicator in indicators:
            frames.df_paper_metadata[f'tc_{indicator}'] = frames.df_paper_metadata['title'].str.contains(indicator, case=False, na=False)

        #frames.df_paper_metadata['has_abstract'] = frames.df_abstract['abstract'].notna().astype(int)
        if frames.df_abstract.empty:
            frames.df_paper_metadata['has_abstract'] = np.nan
        else:
            frames.df_paper_metadata['has_abstract'] = frames.df_paper_metadata['paperId'].isin(frames.df_abstract['paperId']).astype(int)
        return frames


            
    def compute_author_features(self, frames):

        # Verify Consistency Between Paper Metadata and Citation/Reference Data. 
        # For every legitimate paper entry we need to have a corresponding element in frames.df_paper_metadata
        # Directly work with the frames' dataframes

        with pd.option_context('future.no_silent_downcasting', True):
            # Number of papers
            num_papers = frames.df_paper_author.groupby('authorId').size().reindex(frames.df_author['authorId']).infer_objects().fillna(0)
            frames.df_author['num_papers'] = num_papers.values

            # Total number of references and citations for each paper
            paper_citations_count = frames.df_citations.groupby('paperId').size().reindex(frames.df_paper_metadata['paperId']).infer_objects().fillna(0)
            frames.df_paper_author = frames.df_paper_author.merge(paper_citations_count.rename('citation_count'), left_on='paperId', right_index=True, how='left')
            frames.df_paper_author['citation_count'] = frames.df_paper_author['citation_count'].fillna(0)
            
            author_citations = frames.df_paper_author.groupby('authorId')['citation_count'].sum().reindex(frames.df_author['authorId']).infer_objects().fillna(0)

            # Assign to frames.df_author
            avg_citations = (author_citations / (frames.df_author['num_papers'].values + 1E-8)).fillna(0)
            max_citations = frames.df_paper_author.groupby('authorId')['citation_count'].max().reindex(frames.df_author['authorId']).fillna(0)
        
            frames.df_author['avg_citations'] = avg_citations.values
            frames.df_author['max_citations'] = max_citations.values
            
            # Merge author_frames.df_citations with frames.df_author on 'authorId'
            frames.df_author['num_citations'] = author_citations.values

            # Number of co-authors
            co_authors = frames.df_paper_author.groupby('authorId')['paperId'].nunique().reindex(frames.df_author['authorId']).infer_objects().fillna(0)
            frames.df_author['num_coauthors'] = co_authors.values
            
            # Update the meta data
            num_authors = frames.df_paper_author.groupby('paperId')['authorId'].nunique().reindex(frames.df_paper_metadata['paperId'])
            frames.df_paper_metadata['num_authors'] = num_authors.values
            frames.df_paper_metadata['citation_count'] = paper_citations_count.values

            # Year of first and last publication
            publication_years = frames.df_paper_metadata.set_index('paperId').reindex(frames.df_paper_author['paperId'])['year'].infer_objects().fillna(0)
            frames.df_paper_author = frames.df_paper_author.merge(publication_years.rename('publication_years'), left_on='paperId', right_index=True, how='left')
            min_py = frames.df_paper_author.groupby('authorId')['publication_years'].min()
            max_py = frames.df_paper_author.groupby('authorId')['publication_years'].max()

            frames.df_author['year_first_publication'] = min_py.values
            frames.df_author['year_last_publication'] = max_py.values

        return frames


    def compute_venue_features(self, frames, predefined_list=['www', 'arxiv']):
        # Apply predefined list filter
        frames.df_paper_metadata['venue'] = frames.df_paper_metadata['venue'].apply(lambda x: None if str(x).lower() in predefined_list else x)

        # Clean and filter venues
        self.cleaned_venues = frames.df_paper_metadata['venue'].dropna().unique()
        
        # Compute citation statistics
        # Merge citation data with paper metadata
        # citations_with_venues = frames.df_citations.merge(
        #     frames.df_paper_metadata[['paperId', 'venue']],
        #     left_on='paperId',
        #     right_on='paperId',
        #     suffixes=('_cited', '_citing')
        # )
        
        # First merge: get venue of cited papers
        citations_with_cited_venues = frames.df_citations.merge(
            frames.df_paper_metadata[['paperId', 'venue']],
            left_on='paperId',
            right_on='paperId',
            how='left'
        ).rename(columns={'venue': 'venue_cited'})

        # Second merge: get venue of citing papers
        citations_with_venues = citations_with_cited_venues.merge(
            frames.df_paper_metadata[['paperId', 'venue']],
            left_on='citingPaperId',
            right_on='paperId',
            how='left'
        ).rename(columns={'venue': 'venue_citing'})

        # Calculate self-citations (citations from papers of the same venue)
        self_citations = citations_with_venues[citations_with_venues['venue_cited'] == citations_with_venues['venue_citing']]
        self_citation_counts = self_citations.groupby('venue_cited').size().rename('self_citations')

        # Calculate citations by others (citations from papers of different venues)
        citations_by_others = citations_with_venues[citations_with_venues['venue_cited'] != citations_with_venues['venue_citing']]
        citations_by_others_counts = citations_by_others.groupby('venue_cited').size().rename('citing_others')

        # Calculate how many times a venue is cited by others (being cited by others)
        citations_to_others = citations_with_venues[citations_with_venues['venue_cited'] != citations_with_venues['venue_citing']]
        citations_to_others_counts = citations_to_others.groupby('venue_citing').size().rename('being_cited_by_others')

        # Calculate the total number of papers per venue
        total_papers_per_venue = frames.df_paper_metadata['venue'].value_counts().rename('total_papers')

        # Combine all results into a single DataFrame
        frames.venue_summary = pd.concat([
            total_papers_per_venue,
            self_citation_counts,
            citations_by_others_counts,
            citations_to_others_counts
        ], axis=1).fillna(0)

        # Rename columns for clarity
        frames.venue_summary.columns = ['total_papers', 'self_citations', 'citing_others', 'being_cited_by_others']
        return frames 