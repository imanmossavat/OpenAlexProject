
import json
from datetime import datetime, timezone
from pathlib import Path
import os

import numpy as np
import pandas as pd
import yaml
from ArticleCrawler.utils.url_builder import PaperURLBuilder
from ArticleCrawler.library.models import PaperData
class MarkdownFileGenerator:
    """
    Class responsible for generating markdown files based on provided dataframes.
    
    Attributes:
    - vault_path (str or Path): The base path of the vault.
    - experiment_file_name (str): The name of the experiment or project.
    - abstracts_folder (Path): Path to the folder where paper notes will be stored.
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
        self.summary_structured_folder = getattr(
            storage_and_logging_options,
            'summary_structured_folder',
            self.summary_folder / 'structured'
        )
        self.api_provider_type = api_provider_type.lower()
        self.url_builder = PaperURLBuilder()
        self.job_id = self.experiment_file_name
        self._run_file_reference = "../run.md"
        self.manifest_folder = getattr(storage_and_logging_options, 'manifest_folder', self.vault_folder)
        self.manifest_writer = VaultManifestWriter(
            manifest_folder=self.manifest_folder,
            experiment_name=self.experiment_file_name,
            storage_options=storage_and_logging_options,
        )



    def create_folders(self):
        """
        Creates necessary directory structure for abstracts storage.
        """
        self.abstracts_folder.mkdir(parents=True, exist_ok=True)
        self.figure_folder.mkdir(parents=True, exist_ok=True)
        self.metadata_folder.mkdir(parents=True, exist_ok=True)
        self.summary_folder.mkdir(parents=True, exist_ok=True)
        self.summary_structured_folder.mkdir(parents=True, exist_ok=True)
        

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
        Retrieve normalized metadata for the specified paper.
        """
        metadata_row = df_meta[df_meta['paperId'] == paper_id]
        if metadata_row.empty:
            metadata = {
                'paper_id': paper_id,
                'title': None,
                'venue': None,
                'year': None,
                'doi': None,
                'abstract': None,
                'isSeed': False,
                'selected': False,
                'isKeyAuthor': False,
                'processed': False,
                'retracted': False,
            }
        else:
            row = metadata_row.iloc[0]
            metadata = {
                'paper_id': row.get('paperId'),
                'title': row.get('title'),
                'venue': row.get('venue'),
                'year': row.get('year'),
                'doi': row.get('doi'),
                'abstract': row.get('abstract'),
                'isSeed': bool(row.get('isSeed', False)),
                'selected': bool(row.get('selected', False)),
                'isKeyAuthor': bool(row.get('isKeyAuthor', False)),
                'processed': bool(row.get('processed', False)),
                'retracted': bool(row.get('retracted', row.get('is_retracted', False))),
            }
        metadata['url'] = row.get('url') or self._get_paper_url(paper_id)
        metadata['authors'] = self._resolve_author_metadata(paper_id, df_paper_author, df_author)
        metadata['concepts'] = self._extract_structured_list(row.get('concepts'), ['id', 'display_name', 'level', 'score'])
        metadata['topics'] = self._extract_structured_list(row.get('topics'), ['id', 'display_name', 'score'])
        metadata['subfields'] = self._extract_structured_list(row.get('subfields'), ['id', 'display_name', 'score'])
        metadata['fields'] = self._extract_structured_list(row.get('fields'), ['id', 'display_name', 'score'])
        metadata['domains'] = self._extract_structured_list(row.get('domains'), ['id', 'display_name', 'score'])
        return metadata
    
    def _get_paper_url(self, paper_id: str) -> str:
        return self.url_builder.build_url(paper_id, self.api_provider_type)

    def _resolve_author_metadata(self, paper_id, df_paper_author, df_author):
        """
        Resolve author identifiers and names for the paper.
        """
        author_entries = df_paper_author[df_paper_author['paperId'] == paper_id]
        if author_entries.empty:
            return []
        merged = author_entries.merge(df_author, on='authorId', how='left')
        authors = []
        for _, row in merged.iterrows():
            authors.append({
                'id': row.get('authorId'),
                'name': row.get('authorName'),
            })
        return authors

    def _extract_structured_list(self, items, keys):
        """
        Normalize stored structured metadata into a list of dictionaries.
        """
        if not items or (isinstance(items, float) and pd.isna(items)):
            return []
        normalized = []
        for item in items:
            entry = {}
            for key in keys:
                value = None
                if isinstance(item, dict):
                    value = item.get(key)
                elif hasattr(item, key):
                    value = getattr(item, key, None)
                if value not in (None, ''):
                    entry[key] = value
            if entry:
                normalized.append(entry)
        return normalized

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
        Compose markdown content for a paper with a rich YAML frontmatter.
        """
        metadata_with_abstract = dict(paper_metadata)
        metadata_with_abstract['abstract'] = abstract
        frontmatter = self._build_paper_frontmatter(metadata_with_abstract)
        body = self._build_paper_body(abstract, metadata_with_abstract)
        return f"---\n{frontmatter}---\n\n{body}"

    def _build_paper_frontmatter(self, paper_metadata):
        """
        Build YAML frontmatter for the paper note.
        """
        payload = {
            'paper_id': paper_metadata.get('paper_id'),
            'openalex_id': paper_metadata.get('paper_id'),
            'title': paper_metadata.get('title'),
            'doi': paper_metadata.get('doi'),
            'venue': paper_metadata.get('venue'),
            'year': paper_metadata.get('year'),
            'abstract': paper_metadata.get('abstract'),
            'authors': paper_metadata.get('authors') or [],
            'url': paper_metadata.get('url'),
            'concepts': paper_metadata.get('concepts') or [],
            'topics': paper_metadata.get('topics') or [],
            'subfields': paper_metadata.get('subfields') or [],
            'fields': paper_metadata.get('fields') or [],
            'domains': paper_metadata.get('domains') or [],
            'job': {
                'id': self.job_id,
                'experiment': self.experiment_file_name,
            },
            'is_seed': bool(paper_metadata.get('isSeed')),
            'is_selected': bool(paper_metadata.get('selected')),
            'is_key_author': bool(paper_metadata.get('isKeyAuthor')),
            'processed': bool(paper_metadata.get('processed')),
            'retracted': bool(paper_metadata.get('retracted')),
            'annotation': {
                'status': 'standard',
                'updated_at': None,
            },
            'notes': [],
            'run_file': self._run_file_reference,
            'generated_at': self._current_timestamp(),
        }
        return yaml.safe_dump(
            self._normalize_for_yaml(payload),
            sort_keys=False,
            allow_unicode=True,
        )

    def _build_paper_body(self, abstract, paper_metadata):
        """
        Construct the markdown body including annotation placeholders.
        """
        paper_id = paper_metadata.get('paper_id')
        title = paper_metadata.get('title') or paper_id or 'Unknown title'
        paper_url = paper_metadata.get('url') or (self._get_paper_url(paper_id) if paper_id else '')
        body_parts = []
        if paper_url:
            body_parts.append(f"# [{title}]({paper_url})\n\n")
        else:
            body_parts.append(f"# {title}\n\n")

        authors = [a.get('name') for a in paper_metadata.get('authors') or [] if a.get('name')]
        venue = paper_metadata.get('venue')
        year = paper_metadata.get('year')
        doi = paper_metadata.get('doi')
        info_lines = ["> [!info] Paper Info"]
        if authors:
            info_lines.append(f"> **Authors:** {', '.join(authors)}  ")
        info_tokens = []
        if year:
            info_tokens.append(f"**Year:** {year}")
        if venue:
            info_tokens.append(f"**Venue:** {venue}")
        if info_tokens:
            info_lines.append("> " + " | ".join(info_tokens) + "  ")
        if doi:
            info_lines.append(f"> **DOI:** [{doi}](https://doi.org/{doi})  ")
        if paper_url:
            info_lines.append(f"> **OpenAlex:** [{paper_metadata.get('paper_id')}]({paper_url})")
        body_parts.append("\n".join(info_lines) + "\n\n")

        body_parts.append("## Abstract\n\n")
        body_parts.append(f"{abstract}\n\n" if abstract else "*No abstract available*\n\n")
        body_parts.append("---\n\n")

        body_parts.append(self._build_research_context_block(paper_metadata))

        body_parts.append("## Annotation\n\n")
        body_parts.append("*Status:* standard\n\n")

        body_parts.append("## Notes\n\n")
        body_parts.append("> [!note] My Notes\n")
        if paper_id:
            body_parts.append(f"> This paper's note can be found here:  \n> [[notes/{paper_id}_Notes]]\n")
        else:
            body_parts.append("> No notes recorded yet.\n")

        return ''.join(body_parts)

    def _current_timestamp(self):
        return datetime.now(timezone.utc).isoformat()

    def _build_research_context_block(self, metadata):
        """
        Construct the research context callout using structured metadata.
        """
        lines = ["> [!abstract] Research Context"]
        added = False

        top_concepts = self._format_name_list(metadata.get('concepts'), limit=6, separator=' • ')
        if top_concepts:
            lines.append(f"> **Top Concepts:** {top_concepts}")
            added = True

        fields = self._format_name_list(metadata.get('fields'), limit=5)
        if fields:
            lines.append(f"> **Fields:** {fields}")
            added = True

        subfields = self._format_name_list(metadata.get('subfields'), limit=5)
        if subfields:
            lines.append(f"> **Subfields:** {subfields}")
            added = True

        domains = self._format_name_list(metadata.get('domains'), limit=5)
        if domains:
            lines.append(f"> **Domains:** {domains}")
            added = True

        if not added:
            lines.append("> Structured metadata not available.")

        lines.append("")
        return "\n".join(lines)

    def _format_name_list(self, items, limit=5, separator=', '):
        """
        Format the display_name field from a structured metadata list.
        """
        if items is None or (isinstance(items, float) and pd.isna(items)):
            return ""
        names = []
        for item in items[:limit]:
            if isinstance(item, dict):
                name = item.get('display_name')
            elif hasattr(item, 'display_name'):
                name = getattr(item, 'display_name', None)
            else:
                name = str(item)
            if name:
                names.append(name)
        return separator.join(names)

    def _with_summary_frontmatter(self, markdown_body: str, summary_type: str) -> str:
        metadata = {
            "job_id": self.job_id,
            "generated_at": self._current_timestamp(),
            "type": summary_type,
            "run_file": self._run_file_reference,
        }
        frontmatter = yaml.safe_dump(metadata, sort_keys=False, allow_unicode=True).strip()
        return f"---\n{frontmatter}\n---\n\n{markdown_body}"

    def _normalize_for_yaml(self, value):
        """
        Recursively convert numpy/pandas scalars to native Python types for YAML.
        """
        if isinstance(value, dict):
            return {k: self._normalize_for_yaml(v) for k, v in value.items()}
        if isinstance(value, (list, tuple, set)):
            return [self._normalize_for_yaml(v) for v in value]
        if isinstance(value, (np.integer, np.int64, np.int32)):
            return int(value)
        if isinstance(value, (np.floating, np.float64, np.float32)):
            return float(value)
        if isinstance(value, (np.bool_,)):
            return bool(value)
        if pd.isna(value):
            return None
        return value


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

    def _convert_scalar_for_json(self, value):
        if value is None:
            return None
        if isinstance(value, (np.integer, np.int64, np.int32)):
            return int(value)
        if isinstance(value, (np.floating, np.float64, np.float32)):
            return float(value)
        if isinstance(value, (np.bool_,)):
            return bool(value)
        if pd.isna(value):
            return None
        return value

    def _prepare_top_authors_payload(self, top_authors):
        payload = []
        for _, row in top_authors.iterrows():
            payload.append({
                "author_id": self._convert_scalar_for_json(row.get('authorId')),
                "author_name": row.get('authorName'),
                "max_citations": self._convert_scalar_for_json(row.get('max_citations')),
                "avg_citations": self._convert_scalar_for_json(row.get('avg_citations')),
                "num_citations": self._convert_scalar_for_json(row.get('num_citations')),
                "paper_count": self._convert_scalar_for_json(row.get('num_papers')),
            })
        return payload

    def _prepare_top_venues_payload(self, top_venues):
        payload = []
        for _, row in top_venues.iterrows():
            payload.append({
                "venue": row.get('venue'),
                "venue_id": self._convert_scalar_for_json(row.get('venue_id')),
                "total_papers": self._convert_scalar_for_json(row.get('total_papers')),
                "self_citations": self._convert_scalar_for_json(row.get('self_citations')),
                "citing_others": self._convert_scalar_for_json(row.get('citing_others')),
                "being_cited_by_others": self._convert_scalar_for_json(row.get('being_cited_by_others')),
            })
        return payload

    def _write_structured_summary(self, payload, base_name):
        if payload is None:
            return
        self.summary_structured_folder.mkdir(parents=True, exist_ok=True)
        json_path = self.summary_structured_folder / f"{base_name}.json"
        jsonl_path = self.summary_structured_folder / f"{base_name}.jsonl"
        with open(json_path, 'w', encoding='utf-8') as json_file:
            json.dump(payload, json_file, ensure_ascii=False, indent=2)
        with open(jsonl_path, 'w', encoding='utf-8') as jsonl_file:
            for entry in payload:
                jsonl_file.write(json.dumps(entry, ensure_ascii=False) + '\n')
    
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
        authors_payload = self._prepare_top_authors_payload(top_authors)
        venues_payload = self._prepare_top_venues_payload(top_venues)
        
        # 2. Create markdown content for Top Authors and Top Venues
        top_authors_markdown = self._create_top_authors_markdown(top_authors)
        top_venues_markdown = self._create_top_venues_markdown(top_venues)
        
        # 3. Save Top Authors and Top Venues markdown files
        top_authors_file = self.summary_folder / 'top_authors.md'
        top_venues_file = self.summary_folder / 'top_venues.md'
        
        with open(top_authors_file, 'w', encoding='utf-8') as file:
            file.write(self._with_summary_frontmatter(top_authors_markdown, summary_type="top_authors"))
        
        with open(top_venues_file, 'w', encoding='utf-8') as file:
            file.write(self._with_summary_frontmatter(top_venues_markdown, summary_type="top_venues"))
        
        self._write_structured_summary(authors_payload, 'top_authors')
        self._write_structured_summary(venues_payload, 'top_venues')

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
        self.manifest_writer.write_manifests()


        self.generate_markdown_files(df_abstract, df_meta, df_paper_references, df_paper_author, df_author, df_abstract, df_venue_features)

        
        if self.open_vault_folder:
            os.startfile(self.vault_folder)

        print(f'Vault stored at {self.vault_folder}')

    

    def create_paper_markdown_with_openalex_metadata(
        self, 
        paper_data: 'PaperData',
        output_path: Path
    ) -> Path:
        """
        Create markdown file for a paper with OpenAlex metadata in YAML frontmatter.
        
        This is specifically for the library creation use case where we have
        full OpenAlex metadata including concepts, topics, fields, etc.
        
        Args:
            paper_data: PaperData object with all metadata
            output_path: Path where to save the markdown file
            
        Returns:
            Path to created markdown file
        """
        frontmatter = self._create_openalex_frontmatter(paper_data)
        
        body = self._create_paper_body_with_openalex(paper_data)
        
        content = f"---\n{frontmatter}---\n\n{body}"
        
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return output_path
    
    def _create_openalex_frontmatter(self, paper_data: 'PaperData') -> str:
        """
        Create YAML frontmatter with OpenAlex metadata.
        
        Args:
            paper_data: Paper data with metadata
            
        Returns:
            YAML frontmatter string
        """
        import yaml
        
        frontmatter_dict = {
            'paper_id': paper_data.paper_id,
            'title': paper_data.title,
            'authors': [
                {'id': a.get('authorId') or a.get('id'), 'name': a.get('name')}
                for a in paper_data.authors
            ],
            'year': paper_data.year,
            'venue': paper_data.venue,
            'doi': paper_data.doi,
            'url': paper_data.url,
            'abstract': paper_data.abstract,
        }
        if paper_data.venue_raw and paper_data.venue_raw != paper_data.venue:
            frontmatter_dict['venue_raw'] = paper_data.venue_raw
        
        if paper_data.concepts:
            frontmatter_dict['concepts'] = [
                {
                    'id': c.get('id'),
                    'display_name': c.get('display_name'),
                    'level': c.get('level'),
                    'score': c.get('score')
                }
                for c in paper_data.concepts[:10]
            ]
        
        if paper_data.topics:
            frontmatter_dict['topics'] = [
                {
                    'id': t.get('id'),
                    'display_name': t.get('display_name'),
                    'score': t.get('score')
                }
                for t in paper_data.topics[:5]
            ]
        
        if paper_data.fields:
            frontmatter_dict['fields'] = [
                {'id': f.get('id'), 'display_name': f.get('display_name')}
                for f in paper_data.fields
            ]
        
        if paper_data.subfields:
            frontmatter_dict['subfields'] = [
                {'id': s.get('id'), 'display_name': s.get('display_name')}
                for s in paper_data.subfields
            ]
        
        if paper_data.domains:
            frontmatter_dict['domains'] = [
                {'id': d.get('id'), 'display_name': d.get('display_name')}
                for d in paper_data.domains
            ]
        
        if paper_data.assigned_topic is not None:
            frontmatter_dict['assigned_topic'] = paper_data.assigned_topic
        if paper_data.topic_label:
            frontmatter_dict['topic_label'] = paper_data.topic_label
        
        return yaml.dump(frontmatter_dict, default_flow_style=False, allow_unicode=True)
    
    def _create_paper_body_with_openalex(self, paper_data: 'PaperData') -> str:
        """
        Create markdown body for paper with OpenAlex metadata sections.
        
        Args:
            paper_data: Paper data with metadata
            
        Returns:
            Markdown body string
        """
        paper_url = self._get_paper_url(paper_data.paper_id)
        
        body_parts = [
            f"# [{paper_data.title}]({paper_url})\n\n"
        ]
        
        author_names = ', '.join(a.get('name', '') for a in paper_data.authors)
        body_parts.append(f"**Authors**: {author_names}\n\n")
        
        if paper_data.year:
            body_parts.append(f"**Year**: {paper_data.year}\n\n")
        if paper_data.venue:
            body_parts.append(f"**Venue**: {paper_data.venue}\n\n")
        if paper_data.doi:
            body_parts.append(f"**DOI**: {paper_data.doi}\n\n")
        
        body_parts.append("## Abstract\n\n")
        if paper_data.abstract:
            body_parts.append(f"{paper_data.abstract}\n\n")
        else:
            body_parts.append("*No abstract available*\n\n")
        
        if paper_data.concepts:
            body_parts.append("## Concepts\n\n")
            for concept in paper_data.concepts[:10]:
                name = concept.get('display_name', 'Unknown')
                level = concept.get('level', 0)
                score = concept.get('score', 0)
                body_parts.append(f"- **{name}** (Level {level}, Score: {score:.2f})\n")
            body_parts.append("\n")
        
        if paper_data.topics:
            body_parts.append("## Topics\n\n")
            for topic in paper_data.topics[:5]:
                name = topic.get('display_name', 'Unknown')
                score = topic.get('score', 0)
                body_parts.append(f"- **{name}** (Score: {score:.2f})\n")
            body_parts.append("\n")
        
        if paper_data.fields:
            body_parts.append("## Fields\n\n")
            field_names = ', '.join(f.get('display_name', '') for f in paper_data.fields)
            body_parts.append(f"{field_names}\n\n")
        
        return ''.join(body_parts)


class VaultManifestWriter:
    """Handles writing README and run metadata files into the vault."""

    def __init__(self, manifest_folder, experiment_name, storage_options):
        self.manifest_folder = manifest_folder
        self.experiment_name = experiment_name
        self.storage_options = storage_options

    def write_manifests(self):
        self.manifest_folder.mkdir(parents=True, exist_ok=True)
        self._write_readme()
        self._write_run_description()

    def _write_readme(self):
        readme_path = self.manifest_folder / "README.md"
        content = f"""# {self.experiment_name} Vault

This vault contains crawler output for **{self.experiment_name}**.

## Structure
- `papers/`: One Markdown note per paper with metadata, abstract, annotations, notes
- `summary/`: Top authors, venues, and other aggregate insights
- `annotations/`: JSON store of user marks (`paper_marks.json`)
- `JSONL/summary/`: Structured exports of summary data
- `figures/`, `meta_data/`, `recommendation/`: Ancillary artifacts

## Notes
- Each Markdown note includes YAML front matter with provenance (`run_file` points to `run.md`)
- Annotations are synchronized between JSON and Markdown

"""
        readme_path.write_text(content, encoding="utf-8")

    def _write_run_description(self):
        run_path = self.manifest_folder / "run.md"
        config_summary = self._collect_run_metadata()
        lines = ["# Crawl Configuration\n"]
        for section, values in config_summary.items():
            lines.append(f"## {section}")
            for key, value in values.items():
                lines.append(f"- **{key}**: {value}")
            lines.append("")
        run_path.write_text("\n".join(lines), encoding="utf-8")

    def _collect_run_metadata(self):
        summary = {
            "Storage": {
                "Experiment": self.experiment_name,
                "Root": getattr(self.storage_options, "root_folder", "N/A"),
            }
        }
        config_path = getattr(self.storage_options, "config_path", None)
        if config_path:
            summary["Storage"]["Configuration File"] = str(config_path)
        return summary
