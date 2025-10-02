from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer

class TextTransformation:
    """
    Text vectorization component for converting text to numerical features.
    
    This class handles all vectorization operations including TF-IDF and
    count-based vectorization for different topic modeling strategies.
    """
    
    def __init__(self, config=None):
        """
        Initialize text transformation.
        
        Args:
            config: Configuration object with vectorization parameters
        """
        self.config = config

        # Class variables for vectorizer outputs
        self.tfidf_vectorizer = None
        self.tfidf_matrix = None
        self.tfidf_feature_names = None

        self.count_vectorizer = None
        self.count_matrix = None
        self.count_feature_names = None

    def vectorize_and_extract(self, input_df, logger=None, model_type='TFIDF'):
        """
        Perform vectorization (TF-IDF or Count) and extract feature names.

        Args:
            input_df (DataFrame): DataFrame containing processed abstracts
            model_type (str): 'TFIDF' for TfidfVectorizer, 'COUNT' for CountVectorizer
            logger: Logger for progress tracking

        Returns:
            vectorizer, matrix, feature_names: The fitted vectorizer, matrix, and feature names
        """
        stopwords = self.config.stopwords

        if model_type == 'TFIDF':
            vectorizer = TfidfVectorizer(stop_words=stopwords, ngram_range=(1, 2))
        elif model_type == 'COUNT':
            vectorizer = CountVectorizer(stop_words=stopwords, ngram_range=(1, 2))
        else:
            raise ValueError("Invalid model_type. Use 'TFIDF' or 'COUNT'.")

        # Perform vectorization
        matrix = vectorizer.fit_transform(input_df['abstract'])

        # Extract feature names
        if hasattr(vectorizer, 'get_feature_names_out'):
            feature_names = vectorizer.get_feature_names_out()
        else:
            raise ValueError("Unable to extract feature names from vectorizer.")

        # Populate class variables
        if model_type == 'TFIDF':
            self.tfidf_vectorizer = vectorizer
            self.tfidf_matrix = matrix
            self.tfidf_feature_names = feature_names
        elif model_type == 'COUNT':
            self.count_vectorizer = vectorizer
            self.count_matrix = matrix
            self.count_feature_names = feature_names

        if logger:
            logger.info(f"Completed {model_type} vectorization with {len(feature_names)} features")

        return vectorizer, matrix, feature_names