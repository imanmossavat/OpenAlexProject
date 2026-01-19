import os
import logging
import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import yaml

from .preprocessing import TextPreProcessing
from .vectorization import TextTransformation
from .topic_modeling import TopicModeling
from .topic_companion_writer import TopicCompanionWriter
from ArticleCrawler.utils.url_builder import PaperURLBuilder


class TextAnalysisManager:
    """
    Enhanced text analysis manager using the new strategy-based architecture.
    
    This class orchestrates the end-to-end text analysis workflow with improved
    separation of concerns and strategy-based topic modeling.
    """
    
    def __init__(self, config=None, retraction_watch_manager=None, api_provider_type='semantic_scholar'):
        """
        Initialize the text analysis manager.
        
        Args:
            config: Text processing configuration
            retraction_watch_manager: Manager for retraction validation
        """
        self.config = config
        self.retraction_watch_manager = retraction_watch_manager
        self.api_provider_type = api_provider_type
        self.url_builder = PaperURLBuilder()


        # Initialize components with new architecture
        self.preprocessing = TextPreProcessing(config=config)
        self.transformations = TextTransformation(config=config)
        self.topicmodeling = TopicModeling(config=config)

    def analyze_and_report(self, 
                          data_manager,
                          model_types=['NMF', 'LDA'],
                          config=None,
                          logger=None,
                          figure_folder=None,
                          timestamp_final_pkl=None,
                          experiment_file_name=None, 
                          xlsx_folder=None,
                          vault_folder=None):
        """
        Enhanced analysis and reporting using strategy-based topic modeling.
        """
        if config is not None:
            self.config = config

        logger.info("Starting analysis and report generation with strategy-based architecture.")
        
        try:
            # Extract the relevant data
            companion_writer = None
            if vault_folder and experiment_file_name:
                topics_dir = Path(vault_folder) / "topics"
                companion_writer = TopicCompanionWriter(
                    topics_folder=topics_dir,
                    job_id=experiment_file_name,
                    run_file="../run.md",
                )
                self.topicmodeling.set_companion_writer(companion_writer)

            df_abstract = data_manager.frames.df_abstract
            df_metadata = data_manager.frames.df_paper_metadata
            df_forbidden_entries = data_manager.frames.df_forbidden_entries
            df_paper_author = data_manager.frames.df_paper_author
            df_author = data_manager.frames.df_author
            
            # Update graph and calculate centralities
            data_manager.update_graph()
            graph_processing = data_manager.graph_processing
            graph_processing.calculate_centrality()
            centralities = data_manager.graph.get_all_paper_centralities(data_manager=data_manager)

            forbidden_dois = df_forbidden_entries[df_forbidden_entries["textProcessing"] == True]["doi"].tolist()

            # Extract analysis data using enhanced processing
            df_abstract_extended, df_forbidden_dois_metadata, df_merge_meta_centralities_topics = self.extract_analysis_data(
                df_abstract=df_abstract,
                df_metadata=df_metadata,
                df_paper_author=df_paper_author,
                df_author=df_author,
                forbidden_dois=forbidden_dois,
                centralities=centralities,
                model_types=model_types,
                logger=logger
            )

            # Store the analysis results
            self.analysis = {
                "df_merge_meta_centralities_topics": df_merge_meta_centralities_topics,
                "df_forbidden_dois_metadata": df_forbidden_dois_metadata
            }

            # Generate plots after analysis            
            self.plot_full_analysis(
                df_abstract_extended=df_abstract_extended, 
                logger=logger,
                figure_folder=figure_folder,
                timestamp_final_pkl=timestamp_final_pkl,
                model_types=model_types
            )

            # Generate and save the report based on the analysis
            self.generate_report(
                timestamp_final_pkl=timestamp_final_pkl, 
                experiment_file_name=experiment_file_name, 
                xlsx_folder=xlsx_folder, 
                vault_folder=vault_folder, 
                logger=logger
            )

            logger.info("Analysis and report generation completed successfully with new architecture.")

        except Exception as e:
            logger.error(f"An error occurred during analysis and report generation: {e}")
            raise

    def extract_analysis_data(self,
                              df_abstract,
                              df_metadata,
                              df_paper_author,
                              df_author,
                              forbidden_dois,
                              centralities,
                              logger,
                              model_types=['NMF', 'LDA']):
        """
        Enhanced data extraction using strategy-based topic modeling.
        """
        logger.info("Extracting analysis data with new strategy-based approach.")

        # Process forbidden papers
        forbidden_paper_ids = df_metadata[df_metadata['doi'].isin(forbidden_dois)]['paperId'].tolist()
        df_forbidden_dois_metadata = df_metadata[df_metadata['doi'].isin(forbidden_dois)]
        df_metadata = df_metadata[~df_metadata['doi'].isin(forbidden_dois)]
        df_abstract = df_abstract[~df_abstract['paperId'].isin(forbidden_paper_ids)]
        centralities = centralities[~centralities['paperId'].isin(forbidden_paper_ids)]

        # Validate filtered data
        if df_metadata.empty:
            logger.warning("Filtered df_metadata is empty after removing forbidden DOIs!")
        if df_abstract.empty:
            logger.warning("Filtered df_abstract is empty after removing forbidden papers!")
        if centralities.empty:
            logger.warning("Filtered centralities is empty after removing forbidden papers!")

        # Step 1: Process Abstracts
        df_abstract_extended = self.preprocessing.process_abstracts(df_abstract, logger=logger)
        df_abstract_trimmed_processed = self.preprocessing.filter_and_stem_abstracts_by_language(
            df_abstract_extended, logger=logger
        )

        # Step 2: Perform Vectorization (both TFIDF and COUNT for strategy flexibility)
        self.transformations.vectorize_and_extract(df_abstract_trimmed_processed, model_type='TFIDF', logger=logger)
        self.transformations.vectorize_and_extract(df_abstract_trimmed_processed, model_type='COUNT', logger=logger)

        # Step 3: Apply Topic Modeling using strategies
        for model_type in model_types:
            logger.info(f"Applying {model_type} topic modeling strategy")
            self.topicmodeling.apply_topic_modeling(
                transformation_instance=self.transformations, 
                model_type=model_type,
                logger=logger
            )
            df_abstract_extended = self.topicmodeling.add_topic_columns(
                df=df_abstract_extended, 
                model_type=model_type,
                logger=logger
            )

        # Step 4: Merge with metadata
        df_abstract_extended = pd.merge(
            df_abstract_extended,
            df_metadata[['paperId', 'year']],
            on='paperId',
            how='left'
        )

        # Step 5: Create final merged dataframe
        columns_to_merge = ['paperId', 'language', 'valid']
        for model_type in model_types:
            columns_to_merge.append(f'{model_type.lower()}_topic')

        df_meta_merged = pd.merge(df_metadata, df_abstract_extended[columns_to_merge], on='paperId', how='left')
        df_meta_merged = self._attach_author_names(
            df_meta_merged,
            df_paper_author,
            df_author,
            logger=logger,
        )
        df_merge_meta_centralities_topics = pd.merge(df_meta_merged, centralities, on='paperId', how='inner')

        return df_abstract_extended, df_forbidden_dois_metadata, df_merge_meta_centralities_topics

    def plot_full_analysis(self, df_abstract_extended, 
                           logger=None,
                           figure_folder=None,
                           timestamp_final_pkl=None,
                           model_types=['NMF', 'LDA']):
        """
        Enhanced visualization generation using strategy-based topic modeling.
        """
        logger.info("Generating visualizations with new strategy-based approach.")
        
        for model_type in model_types:
            if self.topicmodeling.check_model(model_type, logger):
                logger.info(f"Generating visualizations for {model_type}")
                
                # Generate word clouds
                self.topicmodeling.visualize_word_cloud(
                    model_type=model_type,
                    logger=logger,
                    figure_folder=figure_folder,
                    timestamp_final_pkl=timestamp_final_pkl
                )

                # Generate bar plots
                self.topicmodeling.visualize_top_words_barplot(
                    model_type=model_type,
                    logger=logger,
                    figure_folder=figure_folder,
                    timestamp_final_pkl=timestamp_final_pkl
                )
                
                # Generate temporal evolution plots
                self.topicmodeling.visualize_temporal_topic_evolution(
                    df_abstract_extended, 
                    model_type=model_type,
                    logger=logger,
                    figure_folder=figure_folder,
                    timestamp_final_pkl=timestamp_final_pkl
                )
            else:
                logger.warning(f"Skipping visualization for {model_type} - model not fitted")

    def _get_paper_url(self, paper_id: str) -> str:
        return self.url_builder.build_url(paper_id, self.api_provider_type)

    def generate_report(self, timestamp_final_pkl, experiment_file_name, xlsx_folder, vault_folder, logger=None):
        """Generate the report and save it in both Excel and Markdown formats."""
        try:
            logger.info("Generating report...")

            df_merge = self.analysis["df_merge_meta_centralities_topics"]
            df_forbidden_dois_metadata = self.analysis["df_forbidden_dois_metadata"]

            filename = f"{experiment_file_name}_{timestamp_final_pkl}"
            filename_md = f"{experiment_file_name}_table_{timestamp_final_pkl}"
            filename_md_seed = f"{experiment_file_name}_seed_{timestamp_final_pkl}"
            filename_md_forbidden = f"{experiment_file_name}_forbidden_{timestamp_final_pkl}"

            parquet_folder = os.path.join(vault_folder, "parquet")
            annotations_folder = os.path.join(vault_folder, "annotations")

            excel_path = self.save_to_excel(df_merge, xlsx_folder, filename, logger=logger)
            parquet_path = self.save_to_parquet(df_merge, parquet_folder, logger=logger)
            annotations_path = self.ensure_annotations_store(annotations_folder, logger=logger)
            markdown_path = self.save_to_markdown(
                df_merge,
                vault_folder,
                filename_md,
                logger=logger,
                job_id=experiment_file_name,
            )
            seed_markdown_path = self.save_seed_papers_to_markdown(
                df_merge,
                vault_folder,
                filename_md_seed,
                logger=logger,
                job_id=experiment_file_name,
            )

            forbidden_markdown_path = self.save_forbidden_papers_to_markdown(
                df_forbidden_dois_metadata,
                vault_folder,
                filename_md_forbidden,
                logger=logger,
                job_id=experiment_file_name,
            )

            logger.info(
                "Report generated successfully:\n"
                f"Excel: {excel_path}\n"
                f"Markdown: {markdown_path}\n"
                f"Parquet: {parquet_path}\n"
                f"Annotations store: {annotations_path}"
            )
            return seed_markdown_path, forbidden_markdown_path
        except Exception as e:
            logger.error(f"An error occurred during report generation: {e}")
            raise

    def save_to_excel(self, df, folder, filename, logger=None):
        """Save the DataFrame to an Excel file."""
        try:
            os.makedirs(folder, exist_ok=True)
            file_path = os.path.join(folder, f"{filename}.xlsx")
            with pd.ExcelWriter(file_path, engine='xlsxwriter') as writer:
                df.to_excel(writer, sheet_name='AnalysisResults', index=False)
            logger.info(f"DataFrame saved as an Excel file at {file_path}")
            return file_path
        except Exception as e:
            logger.error(f"An error occurred while saving to Excel: {e}")
            raise

    def save_to_markdown(self, df, folder, filename, logger=None, job_id=None, run_file="../run.md"):
        try:
            from tabulate import tabulate
            os.makedirs(folder, exist_ok=True)
            file_path = os.path.join(folder, f"{filename}.md")

            df = df.copy()
            
            def make_paper_id_link(paper_id, title):
                url = self._get_paper_url(paper_id)
                return f"[{title}]({url})"

            df = df[["paperId", "venue", "year", "title", "centrality (in)", "centrality (out)", "selected", "isSeed"]]
            df["paperId"] = df.apply(lambda row: make_paper_id_link(row["paperId"], row["title"]), axis=1)

            sections = []

            important_refs = (
                df[df['selected'] != True]
                .sort_values(by="centrality (in)", ascending=False)
                .head(10)
            )
            sections.append(
                "## Section 1: Papers with Important References (not yet selected)\n\n"
                + tabulate(
                    important_refs[["paperId", "venue", "year", "centrality (in)", "centrality (out)"]],
                    headers=["Paper ID (Title)", "Venue", "Year", "Centrality (In)", "Centrality (Out)"],
                    tablefmt="pipe",
                    showindex=False,
                )
            )

            influential_papers = (
                df[df['selected'] != True]
                .sort_values(by="centrality (out)", ascending=False)
                .head(10)
            )
            sections.append(
                "## Section 2: Highly Influential Papers (not yet selected)\n\n"
                + tabulate(
                    influential_papers[["paperId", "venue", "year", "centrality (in)", "centrality (out)"]],
                    headers=["Paper ID (Title)", "Venue", "Year", "Centrality (In)", "Centrality (Out)"],
                    tablefmt="pipe",
                    showindex=False,
                )
            )

            sections.append("\nFor more, please refer to the Excel file and view it as a table.\n")

            content = "# Analysis Results\n\n" + "\n\n".join(sections)
            metadata_yaml = yaml.safe_dump(
                {
                    "job_id": job_id or "unknown",
                    "generated_at": datetime.now(timezone.utc).isoformat(),
                    "type": "analysis_table",
                    "run_file": run_file,
                },
                sort_keys=False,
                allow_unicode=True,
            ).strip()
            with open(file_path, 'w', encoding='utf-8') as md_file:
                md_file.write(f"---\n{metadata_yaml}\n---\n\n{content}")

            logger.info(f"Markdown file saved at {file_path}")
            return file_path

        except Exception as e:
            logger.error(f"An error occurred while saving to Markdown: {e}")
            raise

    def save_to_parquet(self, df, folder, filename="papers", logger=None):
        """Persist the merged catalog to a parquet file for downstream consumption."""
        try:
            os.makedirs(folder, exist_ok=True)
            file_path = os.path.join(folder, f"{filename}.parquet")
            df_prepared = self._prepare_dataframe_for_parquet(df, logger=logger)
            df_prepared.to_parquet(file_path, index=False)
            if logger:
                logger.info(f"DataFrame saved as a Parquet file at {file_path}")
            return file_path
        except Exception as e:
            if logger:
                logger.error(f"An error occurred while saving to Parquet: {e}")
            raise

    def ensure_annotations_store(self, folder, filename="paper_marks.json", logger=None):
        """Ensure the annotations directory and JSON store exist for paper marks."""
        try:
            os.makedirs(folder, exist_ok=True)
            file_path = os.path.join(folder, filename)
            if not os.path.exists(file_path):
                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump({}, f)
                if logger:
                    logger.info(f"Initialized annotations store at {file_path}")
            return file_path
        except Exception as e:
            if logger:
                logger.error(f"An error occurred while preparing the annotations store: {e}")
            raise

    def _prepare_dataframe_for_parquet(self, df, logger=None):
        """Normalize DataFrame columns prior to Parquet export."""
        df_parquet = df.copy()
        bool_columns = [
            "isSeed",
            "selected",
            "isKeyAuthor",
            "processed",
            "textProcessing",
            "isRetracted",
            "retracted",
            "is_retracted",
        ]
        for column in bool_columns:
            if column in df_parquet.columns:
                df_parquet[column] = df_parquet[column].apply(self._coerce_to_bool)
        return df_parquet

    @staticmethod
    def _coerce_to_bool(value):
        """Convert mixed representations into strict booleans."""
        if isinstance(value, bool):
            return value
        if value is None or (isinstance(value, float) and pd.isna(value)):
            return False
        if isinstance(value, (int, float)):
            return value != 0
        str_value = str(value).strip().lower()
        if str_value in {"true", "1", "yes", "y", "selected"}:
            return True
        if str_value in {"false", "0", "no", "n", "", "none"}:
            return False
        return bool(str_value)

    def save_seed_papers_to_markdown(self, df, folder, filename, logger=None, job_id=None, run_file="../run.md"):
        try:
            from tabulate import tabulate
            os.makedirs(folder, exist_ok=True)
            file_path = os.path.join(folder, f"{filename}.md")

            df = df.copy()

            def make_paper_id_link(paper_id):
                url = self._get_paper_url(paper_id)
                return f"[{paper_id}]({url})"

            df = df[["paperId", "venue", "year", "title", "centrality (in)", "centrality (out)", "isSeed"]]
            df["paperId"] = df["paperId"].apply(make_paper_id_link)

            seed_papers = df[df["isSeed"] == True].sort_values(by="centrality (out)", ascending=False)

            if len(seed_papers) > 0:
                section = (
                    "## Section 1: All Seed Papers\n\n"
                    + tabulate(
                        seed_papers[
                            ["paperId", "venue", "year", "title", "centrality (in)", "centrality (out)"]
                        ],
                        headers="keys",
                        tablefmt="pipe",
                        showindex=False,
                    )
                )
            else:
                section = "## Section 1: All Seed Papers\n\nNo seed papers found.\n"

            metadata_yaml = yaml.safe_dump(
                {
                    "job_id": job_id or "unknown",
                    "generated_at": datetime.now(timezone.utc).isoformat(),
                    "type": "seed_table",
                    "run_file": run_file,
                },
                sort_keys=False,
                allow_unicode=True,
            ).strip()
            with open(file_path, 'w', encoding='utf-8') as md_file:
                md_file.write(f"---\n{metadata_yaml}\n---\n\n# Seed Papers\n\n{section}")

            logger.info(f"Seed papers Markdown file saved at {file_path}")
            return file_path

        except Exception as e:
            logger.error(f"An error occurred while saving seed papers to Markdown: {e}")
            raise


    def save_forbidden_papers_to_markdown(self, df_forbidden_dois_metadata, folder, filename, logger=None, job_id=None, run_file="../run.md"):
        """
        Save forbidden papers to a Markdown file.
        
        Args:
            df_forbidden_dois_metadata: DataFrame with forbidden papers metadata
            folder: Folder path to save the file
            filename: Name of the output file (without extension)
            logger: Optional logger instance
            
        Returns:
            str: Path to the saved Markdown file
        """
        try:
            folder = Path(folder)
            folder.mkdir(parents=True, exist_ok=True)
            file_path = str(folder / f"{filename}.md")
            
            # Handle empty DataFrame case
            if df_forbidden_dois_metadata.empty:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write("# Forbidden Papers\n\n")
                    f.write("No forbidden papers found.\n")
                
                if logger:
                    logger.info(f"Forbidden papers Markdown file saved at {file_path} (empty)")
                return file_path
            
            # Helper function to create clickable links
            def make_paper_id_link(paper_id, title):
                url = f"https://openalex.org/{paper_id}"
                return f"[{title}]({url})"
            
            # Select and reorder columns
            df_forbidden_dois_metadata = df_forbidden_dois_metadata[
                ["paperId", "venue", "year", "title", "doi"]
            ].copy()  # Use .copy() to avoid SettingWithCopyWarning
            
            # Create clickable links for paper IDs
            df_forbidden_dois_metadata["paperId"] = df_forbidden_dois_metadata.apply(
                lambda row: make_paper_id_link(row["paperId"], row["title"]), axis=1
            )
            
            # Convert to Markdown table
            from tabulate import tabulate
            markdown_table = tabulate(
                df_forbidden_dois_metadata, 
                headers="keys", 
                tablefmt="pipe", 
                showindex=False
            )
            
            metadata_yaml = yaml.safe_dump(
                {
                    "job_id": job_id or "unknown",
                    "generated_at": datetime.now(timezone.utc).isoformat(),
                    "type": "forbidden_table",
                    "run_file": run_file,
                },
                sort_keys=False,
                allow_unicode=True,
            ).strip()

            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(f"---\n{metadata_yaml}\n---\n\n# Forbidden Papers\n\n{markdown_table}")
            
            if logger:
                logger.info(f"Forbidden papers Markdown file saved at {file_path}")
            
            return file_path
            
        except Exception as e:
            if logger:
                logger.error(f"An error occurred while saving forbidden papers to Markdown: {e}")
            raise

    def _attach_author_names(self, df_meta, df_paper_author, df_author, logger=None):
        """
        Attach aggregated author names to the merged metadata DataFrame.

        Produces a list column `authors_display` for downstream consumers.
        """
        df_result = df_meta.copy()

        if (
            df_paper_author is None
            or df_author is None
            or df_paper_author.empty
            or df_author.empty
        ):
            if logger:
                logger.info("Author metadata missing; defaulting to empty author lists.")
            df_result["authors_display"] = [[] for _ in range(len(df_result))]
            return df_result

        try:
            df_author_subset = df_author[["authorId", "authorName"]].copy()
        except KeyError:
            if logger:
                logger.warning("Author DataFrame missing expected columns; skipping author enrichment.")
            df_result["authors_display"] = [[] for _ in range(len(df_result))]
            return df_result

        try:
            df_paper_author_subset = df_paper_author[["paperId", "authorId"]].copy()
        except KeyError:
            if logger:
                logger.warning("Paper-author DataFrame missing expected columns; skipping author enrichment.")
            df_result["authors_display"] = [[] for _ in range(len(df_result))]
            return df_result

        merged = pd.merge(df_paper_author_subset, df_author_subset, on="authorId", how="left")
        merged = merged.dropna(subset=["authorName"])

        if merged.empty:
            df_result["authors_display"] = [[] for _ in range(len(df_result))]
            return df_result

        grouped = (
            merged.groupby("paperId")["authorName"]
            .apply(
                lambda values: [
                    str(name).strip()
                    for name in values
                    if isinstance(name, str) and str(name).strip()
                ]
            )
        )

        df_result["authors_display"] = df_result["paperId"].map(grouped)
        df_result["authors_display"] = df_result["authors_display"].apply(
            lambda names: names if isinstance(names, list) else []
        )
        return df_result
