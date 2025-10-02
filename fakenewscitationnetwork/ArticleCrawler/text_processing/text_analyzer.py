import os
import logging
import pandas as pd
from .preprocessing import TextPreProcessing
from .vectorization import TextTransformation
from .topic_modeling import TopicModeling

class TextAnalysisManager:
    """
    Enhanced text analysis manager using the new strategy-based architecture.
    
    This class orchestrates the end-to-end text analysis workflow with improved
    separation of concerns and strategy-based topic modeling.
    """
    
    def __init__(self, config=None, retraction_watch_manager=None):
        """
        Initialize the text analysis manager.
        
        Args:
            config: Text processing configuration
            retraction_watch_manager: Manager for retraction validation
        """
        self.config = config
        self.retraction_watch_manager = retraction_watch_manager
        
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
            df_abstract = data_manager.frames.df_abstract
            df_metadata = data_manager.frames.df_paper_metadata
            df_forbidden_entries = data_manager.frames.df_forbidden_entries
            
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

    # Keep all existing report generation methods unchanged for backward compatibility
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

            excel_path = self.save_to_excel(df_merge, xlsx_folder, filename, logger=logger)
            markdown_path = self.save_to_markdown(df_merge, vault_folder, filename_md, logger=logger)
            seed_markdown_path = self.save_seed_papers_to_markdown(
                df_merge, vault_folder, filename_md_seed, logger=logger)
            
            forbidden_markdown_path = self.save_forbidden_papers_to_markdown(
                df_forbidden_dois_metadata, vault_folder, filename_md_forbidden, logger=logger)

            logger.info(f"Report generated successfully:\nExcel: {excel_path}\nMarkdown: {markdown_path}")
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

    def save_to_markdown(self, df, folder, filename, logger=None):
        """Save subsets of the DataFrame as Markdown sections in a .md file."""
        try:
            from tabulate import tabulate
            os.makedirs(folder, exist_ok=True)
            file_path = os.path.join(folder, f"{filename}.md")

            df = df.copy()
            
            def make_paper_id_link(paper_id, title):
                return f"[{title}](https://www.semanticscholar.org/paper/{paper_id})"

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

            with open(file_path, 'w', encoding='utf-8') as md_file:
                md_file.write("# Analysis Results\n\n")
                md_file.write("\n\n".join(sections))

            logger.info(f"Markdown file saved at {file_path}")
            return file_path

        except Exception as e:
            logger.error(f"An error occurred while saving to Markdown: {e}")
            raise

    def save_seed_papers_to_markdown(self, df, folder, filename, logger=None):
        """Save seed papers as a Markdown file with a subsection."""
        try:
            from tabulate import tabulate
            os.makedirs(folder, exist_ok=True)
            file_path = os.path.join(folder, f"{filename}.md")

            df = df.copy()

            def make_paper_id_link(paper_id):
                return f"[{paper_id}](https://www.semanticscholar.org/paper/{paper_id})"

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

            with open(file_path, 'w', encoding='utf-8') as md_file:
                md_file.write("# Seed Papers\n\n")
                md_file.write(section)

            logger.info(f"Seed papers Markdown file saved at {file_path}")
            return file_path

        except Exception as e:
            logger.error(f"An error occurred while saving seed papers to Markdown: {e}")
            raise

    def save_forbidden_papers_to_markdown(self, df_forbidden_dois_metadata, folder, filename, logger=None):
        """Save forbidden papers as a Markdown file with a subsection."""
        try:
            from tabulate import tabulate
            os.makedirs(folder, exist_ok=True)
            file_path = os.path.join(folder, f"{filename}.md")

            df_forbidden_dois_metadata = df_forbidden_dois_metadata.copy()

            def make_paper_id_link(paper_id, title):
                return f"[{title}](https://www.semanticscholar.org/paper/{paper_id})"

            df_forbidden_dois_metadata = df_forbidden_dois_metadata[["paperId", "venue", "year", "title", "doi"]]
            df_forbidden_dois_metadata["paperId"] = df_forbidden_dois_metadata.apply(
                lambda row: make_paper_id_link(row["paperId"], row["title"]), axis=1
            )

            forbidden_papers = df_forbidden_dois_metadata.sort_values(by="year", ascending=False)

            if len(forbidden_papers) > 0:
                section = (
                    "## Section 1: All Forbidden Papers\n\n"
                    + tabulate(
                        forbidden_papers[
                            ["paperId", "venue", "year", "title", "doi"]
                        ],
                        headers="keys",
                        tablefmt="pipe",
                        showindex=False,
                    )
                )
            else:
                section = "## Section 1: All Forbidden Papers\n\nNo forbidden papers found.\n"

            with open(file_path, 'w', encoding='utf-8') as md_file:
                md_file.write("# Forbidden Papers\n\n")
                md_file.write(section)

            logger.info(f"Forbidden papers Markdown file saved at {file_path}")
            return file_path

        except Exception as e:
            logger.error(f"An error occurred while saving forbidden papers to Markdown: {e}")
            raise