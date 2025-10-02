import pandas as pd
import re
from langdetect import detect

class TextPreProcessing:
    """
    Text preprocessing component for cleaning and preparing text data.
    
    This class handles all text preprocessing operations including
    special character removal, language detection, and stemming.
    """
    
    def __init__(self, config=None):
        """
        Initialize text preprocessing.
        
        Args:
            config: Configuration object with preprocessing parameters
        """
        self.config = config

    def process_abstracts(self, df_in, logger):
        """
        Enhanced abstract processing for OpenAlex data.
        Process the abstracts in a DataFrame, detect the language, and mark the valid rows.
        """
        logger.info('Starting abstract processing for enhanced data compatibility...')

        # Filter out None abstracts first (common in OpenAlex)
        initial_count = len(df_in)
        df_in = df_in.dropna(subset=['abstract'])
        df_in = df_in[df_in['abstract'].str.strip() != '']
        
        logger.info(f'Filtered out {initial_count - len(df_in)} papers without abstracts')
        
        if df_in.empty:
            logger.warning("No papers with abstracts remaining after filtering!")
            return df_in

        logger.info('Removing special characters from abstracts...')
        df_in['abstract'] = self.remove_special_characters(df_in['abstract'], logger=logger)
        
        logger.info('Finding invalid abstracts')
        valid_indices = self.get_valid_indices(df_in['abstract'], logger=logger)

        df_in['language'] = ''
        df_in['valid'] = False

        for i, row in df_in.iterrows():
            try:
                if i in valid_indices:
                    df_in.at[i, 'language'] = detect(row['abstract'])
                    df_in.at[i, 'valid'] = True
            except Exception as e:
                logger.error(f"Error occurred at row {i}: {e}", exc_info=True)

        return df_in
        
    def remove_special_characters(self, text, logger=None):
        """
        Remove special characters and specified patterns from a given text.
        """
        patterns = self.config.special_characters
    
        if isinstance(text, str):
            cleaned_text = text
            for pattern in patterns:
                cleaned_text = re.sub(pattern, '', cleaned_text)
        elif isinstance(text, pd.Series):
            cleaned_text = text.copy()
            for pattern in patterns:
                cleaned_text = cleaned_text.apply(lambda x: re.sub(pattern, '', x) if x is not None else x)
        else:
            raise TypeError("Input type not supported. Expected str or pd.Series.")

        return cleaned_text
    
    def get_invalid_indices(self, abstract_column, logger):
        """
        Get the indices of invalid elements in the abstract column.
        """
        logger.info('Identifying invalid abstract indices...')

        nan_indices = abstract_column[abstract_column.isnull() | abstract_column.astype(str).str.lower().str.contains('none')].index
        invalid_indices = nan_indices.copy()
        
        min_length = self.config.abstract_min_length
        logger.info(f'min length for abstract is {min_length}')

        if min_length > 0:
            short_indices = abstract_column[abstract_column.str.len() < min_length].index
            invalid_indices = invalid_indices.union(short_indices)

        return list(invalid_indices)

    def get_valid_indices(self, abstract_column, logger):
        """
        Get the indices of valid elements in the abstract column.
        """
        invalid_indices = self.get_invalid_indices(abstract_column, logger=logger)
        return list(set(abstract_column.index) - set(invalid_indices))
    
    def filter_and_stem_abstracts_by_language(self, df_abstract_extended, logger):
        """
        Filter abstracts by language and apply stemming.
        """
        lang = self.config.language
        if lang == 'en':
            logger.info('Filtering and processing valid English abstracts...')
        else:
            logger.info(f'Filtering and processing valid {lang} abstracts...')

        df_abstract_trimmed_processed = df_abstract_extended[
            (df_abstract_extended['valid']) & (df_abstract_extended['language'] == lang)
        ].copy()
        
        df_abstract_trimmed_processed['abstract'] = self.text_to_stem(
            df_abstract_trimmed_processed['abstract'], logger=logger)
        return df_abstract_trimmed_processed
    
    def text_to_stem(self, abstract_column, logger):
        """
        Apply a basic NLP pipeline to process abstracts.
        """
        stemmer = self.config.stemmer
        processed_abstracts = []
        
        for abstract in abstract_column:
            tokens = abstract.lower().split()
            
            if stemmer:
                filtered_tokens = [stemmer.stem(token) for token in tokens]
            else:
                filtered_tokens = [token for token in tokens]
            
            processed_abstracts.append(' '.join(filtered_tokens))
    
        if stemmer:
            logger.info(f'Stemming applied with {stemmer.__class__.__name__}.')
        else:
            logger.info('No stemming applied')
        return processed_abstracts