import os
import requests
import pandas as pd

import logging


class RetractionWatchManager:

    def __init__(self, retraction_options,storage_and_logging_options= None, logger=None):
        
        self.retraction_options= retraction_options 
        # Set up logger
        if logger is not None:
            self.logger = logger
        else:
            self.logger = logging.getLogger("RetractedPapersIdentifier")
            logging.basicConfig(level=logging.INFO)  # Default logging level

        if self.retraction_options.enable_retraction_watch:
            self.fetcher= RetractionWatchFetcher(storage_and_logging_options=storage_and_logging_options, retraction_options=self.retraction_options)    
            self.logger.info("Fetching retraction data...")
            self.retraction_data = self.fetcher.get_retraction_watch_data()
            self.retracted_paper_processing= RetractedPapersProcessing(fetcher=self.fetcher, retraction_options=retraction_options, logger=logger)
        else:
            self.logger.info("Retraction pipeline if disabled.")
    
    def get_retracted_papers(self, doi_list=None):
        if self.retraction_options.enable_retraction_watch:
            return self.retracted_paper_processing.get_retracted_papers(retraction_data= self.retraction_data, doi_list= doi_list)
        else:
            return None

    def process_retracted_papers(self, doi_list):
        """
        Calls the RetractedPapersProcessing method to process retracted papers.
        
        Parameters:
        - doi_list: List of DOIs to check for retractions
        
        Returns:
        - DataFrames for retracted papers and forbidden entries
        """
        if self.retraction_options.enable_retraction_watch:
            return self.retracted_paper_processing.process_retracted_papers(
                retraction_data =self.retraction_data, doi_list =doi_list)
        else:
            return pd.DataFrame(), pd.DataFrame()  # Empty DataFrames if retraction watch is disabled


class RetractionWatchFetcher:
    """
    Fetches and manages Retraction Watch data from GitLab.
    """
    def __init__(self, storage_and_logging_options, retraction_options, logger=None):

        self.storage_and_logging_options = storage_and_logging_options
        self.retraction_options= retraction_options

        # Retrieve paths and URLs from the storage config
        self.local_csv_path = storage_and_logging_options.retraction_watch_csv_path
        self.version_file_path = storage_and_logging_options.retraction_watch_version_file_path
        self.raw_url = retraction_options.retraction_watch_raw_url
        self.commits_api_url = retraction_options.retraction_watch_commits_api_url

        # Set up logger
        if logger is not None:
            self.logger = logger
        else:
            self.logger = logging.getLogger("RetractionWatchFetcher")
            logging.basicConfig(level=logging.INFO)  # Default logging level

    def get_file_from_git(self):
        """
        Fetches the latest version of a file from GitLab and its commit SHA.
        
        Returns:
            tuple: (file_content as bytes, latest_commit_sha as str)
        """
        try:
            self.logger.info("Fetching latest commit SHA from GitLab...")
            commit_response = requests.get(self.commits_api_url)
            commit_response.raise_for_status()
            latest_commit_sha = commit_response.json()[0]["id"]
            self.logger.info(f"Latest commit SHA: {latest_commit_sha}")

            self.logger.info(f"Downloading latest retraction data CSV from GitLab from {self.raw_url}...")
            file_response = requests.get(self.raw_url)
            file_response.raise_for_status()
            
            self.logger.info("File fetched successfully from GitLab.")
            return file_response.content, latest_commit_sha

        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error fetching file from GitLab: {e}")
            return None, None

    def _save_file(self, content, version):
        """
        Saves the file content as a CSV and stores the version (commit SHA).
        """
        try:
            # Ensure the storage directory exists
            os.makedirs(self.local_csv_path.parent, exist_ok=True)

            # Save the CSV file
            with open(self.local_csv_path, "wb") as f:
                f.write(content)
            
            # Save the version file
            with open(self.version_file_path, "w") as f:
                f.write(version)

            self.logger.info(f"File saved: {self.local_csv_path}")
            self.logger.info(f"Version saved: {self.version_file_path}")

        except Exception as e:
            self.logger.error(f"Error saving file: {e}")

    def _check_and_update_file(self):
        """
        Checks if the CSV file and version file exist. If either is missing, downloads the file.
        If both exist, compares the version and updates the file if needed.
        """
        if not self.local_csv_path.exists() or not self.version_file_path.exists():
            self.logger.warning("Either the file or version file is missing. Downloading latest version...")
            file_content, latest_sha = self.get_file_from_git()
            if file_content:
                self._save_file(file_content, latest_sha)
        else:
            # Both files exist, so check the versions
            with open(self.version_file_path, "r") as version_file:
                stored_sha = version_file.read().strip()
            
            file_content, latest_sha = self.get_file_from_git()

            if file_content and stored_sha != latest_sha:
                self.logger.info("File is outdated. Downloading the latest version...")
                self._save_file(file_content, latest_sha)
            else:
                self.logger.info("File is up-to-date. No update needed.")

    def _load_data(self):
        """
        Reads the retraction watch CSV file into a Pandas DataFrame.
        
        Returns:
            pd.DataFrame: The loaded dataset, or None if the file is missing.
        """
        if not self.local_csv_path.exists():
            self.logger.error(f"Error: File not found at {self.local_csv_path}")
            return None

        try:
            self.logger.info(f"Loading data from {self.local_csv_path}...")
            retraction_data= pd.read_csv(self.local_csv_path)


            # Get retracted papers from the retraction data by matching the DOI
            doi_columns = ['RetractionDOI', 'OriginalPaperDOI']  #  
            retraction_data = retraction_data[retraction_data[doi_columns].notnull().any(axis=1)]
            return retraction_data

        except Exception as e:
            self.logger.error(f"Error reading CSV file: {e}")
            return None
        
    def get_retraction_watch_data(self):
        """
        Ensures the latest data is available and loads it into a Pandas DataFrame.
        
        Returns:
            pd.DataFrame: The latest retraction watch data.
        """
        self._check_and_update_file()
        return self._load_data()



class RetractedPapersProcessing:
    """
    Identifies which papers in a dataset have been retracted.
    """
    def __init__(self, retraction_options, fetcher=None,  logger=None): 
        self.fetcher = fetcher
        self.retraction_options= retraction_options # see RetractionOptions in initilization
        self.retraction_watch_df = None
        self.papers_retracted_df = None
        self.author_retractions_df = None



    def get_retracted_papers(self, retraction_data, doi_list):
        """
        Given a list of DOIs, return a set of DOIs that are retracted.
        """
        if retraction_data is None or retraction_data.empty:
            return None

        # Columns to search for retractions
        doi_columns = ['RetractionDOI', 'OriginalPaperDOI']

        # Find all rows where any of the doi_columns match the input DOIs
        retracted_mask = retraction_data[doi_columns].apply(lambda col: col.isin(doi_list)).any(axis=1)

        # Extract the retracted DOIs
        retracted_dois = list(set(retraction_data.loc[retracted_mask, doi_columns].values.flatten()))

        return retracted_dois

    def process_retracted_papers(self, retraction_data, doi_list):
        """Returns DataFrames with retraction info without modifying external data."""
        if not doi_list:
            return pd.DataFrame(), pd.DataFrame()  # Return empty DataFrames if no input

        if not self.retraction_options.enable_retraction_watch:
            return pd.DataFrame(), pd.DataFrame()  # Return empty DataFrames if retraction watch is disabled

        # Fetch retracted DOIs
        retracted_papers = self.get_retracted_papers(retraction_data=retraction_data, doi_list=doi_list)

        if retracted_papers is None or not isinstance(retracted_papers, (list, pd.Series)):
            return pd.DataFrame(), pd.DataFrame()  # Return empty DataFrames if invalid

        # Create DataFrame with retracted status
        retracted_papers_df = pd.DataFrame({
            "doi": retracted_papers,
            "retracted": True
        })

        # Create DataFrame with forbidden entries (if applicable)
        avoid_retraction_in_sampler = self.retraction_options.avoid_retraction_in_sampler
        avoid_retraction_in_reporting = self.retraction_options.avoid_retraction_in_reporting
        avoid_retractions = avoid_retraction_in_sampler or avoid_retraction_in_reporting

        forbidden_entries_df = pd.DataFrame()
        if avoid_retractions:
            forbidden_entries_df = pd.DataFrame({
                'doi': retracted_papers,
                'reason': ['retraction watch'] * len(retracted_papers),
                'sampler': [avoid_retraction_in_sampler] * len(retracted_papers),
                'textProcessing': [avoid_retraction_in_reporting] * len(retracted_papers)
            })

        return retracted_papers_df, forbidden_entries_df


# unused code, maybe used for future

    # def process_retracted_papers(self, frames):
    #     """
    #     Runs the full pipeline: finding retracted papers, counting them per author, 
    #     and merging retraction reasons.
    #     """
    #     if self.retraction_data is None:
    #         self.logger.error("Retracted papers data is missing. Ensure fetcher is set or retraction data is manually provided.")
    #         return

    #     self.logger.info("Starting retracted papers identification pipeline...")
    #     self.find_retracted_papers(frames)
    #     self.count_retracted_papers(frames)
    #     self.merge_retraction_reasons(frames)
    #     self.logger.info("Retraction pipeline completed successfully.")

    
    # def find_and_merge_retracted_papers(self, frames):
    #     """
    #     Identifies which papers are retracted.

    #     Returns:
    #         pd.DataFrame: A DataFrame containing only retracted papers.
    #     """
    #     if self.retraction_data is None or self.retraction_data.empty:
    #         self.logger.error("No retraction data available.")
    #         return pd.DataFrame()  # Return an empty DataFrame in case of no data.

    #     self.logger.info("Finding retracted papers...")

    #     # Merge metadata with retraction data on all possible DOI columns
    #     doi_columns = ['RetractionDOI', 'OriginalPaperDOI']  # Add any other relevant DOI columns if needed
        
    #     # Perform multiple merges on different DOI columns and combine results
    #     merged_dfs = [
    #         frames.df_paper_metadata.merge(
    #             self.retraction_data,
    #             left_on='DOI', right_on=doi_col,
    #             how='left'
    #         )
    #         for doi_col in doi_columns
    #     ]

    #     # Concatenate results and drop duplicates
    #     merged_df = pd.concat(merged_dfs).drop_duplicates(subset=['DOI'])


    #     # Add binary 'retracted' column (1 for retracted, 0 for not)
    #     merged_df['retracted'] = merged_df['RetractionDOI'].notnull().astype(int)

    #     # Store the result in the class
    #     self.papers_retracted_df = merged_df

    #     self.logger.info(f"Identified {merged_df['retracted'].sum()} retracted papers.")

    #     return merged_df  # Return the merged DataFrame with retracted papers

    # def count_retracted_papers(self, frames):
    #     """
    #     Counts how many papers each author has that are retracted.

    #     Updates:
    #         frames.df_author: Adds the 'retracted_count' column to the df_author dataframe.
    #     """
    #     if self.papers_retracted_df is None or self.papers_retracted_df.empty:
    #         self.logger.warning("No retracted papers found. Skipping count_retracted_papers step.")
    #         return

    #     self.logger.info("Counting retracted papers per author...")

    #     # Join df_paper_author to count how many retracted papers each author has
    #     retracted_papers_with_authors = self.papers_retracted_df.merge(
    #         frames.df_paper_author, left_on='paperId', right_on='paperId', how='left'
    #     )

    #     # Create the binary 'is_retracted' column (1 for retracted, 0 for not)
    #     retracted_papers_with_authors['is_retracted'] = retracted_papers_with_authors['retracted'] == 1

    #     # Count the retracted papers for each author
    #     author_retraction_count = retracted_papers_with_authors.groupby('authorId')['is_retracted'].sum().reset_index()

    #     # Merge this count with author_retractions_df
    #     self.author_retractions_df = frames.df_author.merge(
    #         author_retraction_count, on='authorId', how='left'
    #     )

    #     # Rename the column to 'retracted_count'
    #     self.author_retractions_df.rename(columns={'is_retracted': 'retracted_count'}, inplace=True)

    #     self.logger.info("Retraction counts added to authors dataframe.")

    # def merge_retraction_reasons(self, frames):
    #     """
    #     Merges all retraction reasons for each author and adds the information to df_author.

    #     Updates:
    #         frames.df_author: Adds the 'retracted_reasons' column to the df_author dataframe.
    #     """
    #     if self.papers_retracted_df is None or self.papers_retracted_df.empty:
    #         self.logger.warning("No retracted papers found. Skipping merge_retraction_reasons step.")
    #         return

    #     self.logger.info("Merging retraction reasons per author...")

    #     # Create a dictionary to store merged reasons for each author
    #     author_reasons = {}

    #     # For each paper in papers_retracted_df, gather the reason and associate it with the author
    #     for _, row in self.papers_retracted_df.iterrows():
    #         paper_id = row['paperId']
    #         reason = row['Reason']
    #         authors = frames.df_paper_author[frames.df_paper_author['paperId'] == paper_id]['authorId']

    #         # Add the reason for each author of the retracted paper
    #         for author_id in authors:
    #             if author_id not in author_reasons:
    #                 author_reasons[author_id] = []
    #             author_reasons[author_id].append(reason)

    #     # Convert the list of reasons into a single string for each author
    #     self.author_retractions_df['retracted_reasons'] = self.author_retractions_df['authorId'].map(
    #         lambda author_id: ', '.join(author_reasons.get(author_id, []))
    #     )

    #     self.logger.info("Retraction reasons merged successfully.")

