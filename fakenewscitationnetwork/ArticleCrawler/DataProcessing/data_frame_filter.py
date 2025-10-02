# data_frame_filter.py

import logging
import pandas as pd
import re

# Define an emoji pattern for filtering
emoji_pattern = re.compile(
    "[\U0001F600-\U0001F64F"  # Emoticons
    "\U0001F300-\U0001F5FF"  # Symbols & Pictographs
    "\U0001F680-\U0001F6FF"  # Transport & Map Symbols
    "\U0001F700-\U0001F77F"  # Alchemical Symbols
    "\U0001F780-\U0001F7FF"  # Geometric Shapes Extended
    "\U0001F800-\U0001F8FF"  # Supplemental Arrows-C
    "\U0001F900-\U0001F9FF"  # Supplemental Symbols and Pictographs
    "\U0001FA00-\U0001FA6F"  # Chess Symbols
    "\U0001FA70-\U0001FAFF"  # Symbols and Pictographs Extended-A
    "\U00002702-\U000027B0"  # Dingbats
    "\U000024C2-\U0001F251"  # Enclosed characters
    "]+", 
    flags=re.UNICODE
)

class Node:
    """Base class for all AST nodes."""
    pass

class TermNode(Node):
    """Represents a term (like 'X', 'Y', etc.)"""
    def __init__(self, term):
        self.term = term

    def __repr__(self):
        return f"TermNode({self.term})"

class NotNode(Node):
    """Represents a NOT operation."""
    def __init__(self, operand):
        self.operand = operand

    def __repr__(self):
        return f"NotNode({self.operand})"

class AndNode(Node):
    """Represents an AND operation."""
    def __init__(self, left, right):
        self.left = left
        self.right = right

    def __repr__(self):
        return f"AndNode({self.left}, {self.right})"

class OrNode(Node):
    """Represents an OR operation."""
    def __init__(self, left, right):
        self.left = left
        self.right = right

    def __repr__(self):
        return f"OrNode({self.left}, {self.right})"

# Function to evaluate the AST
def evaluate_ast(node: Node, row: pd.Series, colname='title') -> bool:
    """Evaluate the AST against a DataFrame row."""
    title_value = row[colname]
    if title_value is None or pd.isna(title_value):
        return False  # Excludes papers with missing titles
    title = title_value.lower()  # Convert title to lowercase for case-insensitive comparison
    if isinstance(node, TermNode):
        # Check if the title contains the term (case insensitive)
        return node.term.lower() in title
    elif isinstance(node, NotNode):
        return not evaluate_ast(node.operand, row)
    elif isinstance(node, AndNode):
        return evaluate_ast(node.left, row) and evaluate_ast(node.right, row)
    elif isinstance(node, OrNode):
        return evaluate_ast(node.left, row) or evaluate_ast(node.right, row)

# Tokenizer for splitting the expression
def tokenize(expression, emoji_pattern):
    """Tokenize the input expression into a list of tokens."""
#    pattern = r'\(|\)|AND|OR|NOT|' + emoji_pattern.pattern + r'|"(.*?)"|[A-Za-z0-9+_.$#?!*€&-]+'
    pattern = r'\(|\)|AND|OR|NOT|' + emoji_pattern.pattern + r'|"(?:\\.|[^"\\])*"|[A-Za-z0-9+_.$#?!*€&-]+'

#    pattern = r'\(|\)|AND|OR|NOT|' + emoji_pattern.pattern + r'|[A-Za-z0-9+_.$#?!*€&-]+'
    tokens = re.findall(pattern, expression)

    return [token.upper() if token.upper() in {"AND", "OR", "NOT"} else token for token in tokens]

# Parser to create the AST
class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.position = 0

    def parse(self) -> Node:
        return self.parse_expression()

    def parse_expression(self) -> Node:
        node = self.parse_term()
        while self.position < len(self.tokens):
            token = self.tokens[self.position]
            if token == "AND":
                self.position += 1
                node = AndNode(node, self.parse_term())
            elif token == "OR":
                self.position += 1
                node = OrNode(node, self.parse_term())
            else:
                break
        return node

    def parse_term(self) -> Node:
        token = self.tokens[self.position]
        
        if token == "NOT":
            self.position += 1
            return NotNode(self.parse_term())
        
        elif token == "(":
            self.position += 1
            node = self.parse_expression()
            self.position += 1  # Skip ')'
            return node
        
        else:  # It's a term
            self.position += 1
            return TermNode(token)

class DataFrameFilter:
    def __init__(self, df, keywords=None, logger=None):
        self.df = df
        self.keywords = keywords or []
        self.logger = logger or logging.getLogger(__name__)

    def filter_by_keywords(self, column_name):
        """Filter DataFrame rows containing any of the specified keywords."""
        if not self.keywords:
            self.logger.warning("No keywords provided for filtering.")
            return self.df
        
        # Create regex pattern for keywords
        pattern = '|'.join(map(re.escape, self.keywords))
        filtered_df = self.df[self.df[column_name].str.contains(pattern, case=False, na=False)]
        self.logger.info(f"Filtered DataFrame by keywords")
        return filtered_df['paperId']

    def filter_by_expression(self, column_name):
        """Filter DataFrame based on a logical expression using a list of keyword expressions and return unique paperIds as a Series."""
        unique_paper_ids = set()  # Use a set to store unique paper IDs

        for expression in self.keywords:  # Iterate over each expression in keywords
            tokens = tokenize(expression, emoji_pattern)  # Tokenize the current expression
            parser = Parser(tokens)  # Create a parser instance
            ast = parser.parse()  # Parse the expression to generate the AST

            # Filter the DataFrame using the current expression
            filtered_ids = self.df[self.df.apply(lambda row: self.evaluate_expression(ast, row, column_name), axis=1)]['paperId']
            
            # Update the set with the unique paper IDs from the filtered results
            unique_paper_ids.update(filtered_ids.unique())  # Use unique() to avoid adding duplicates

            # Convert the set of unique paper IDs to a Pandas Series and return it
        return pd.Series(list(unique_paper_ids), name='paperId')


    def filter_by_keywords_and_expression(self, column_name):
        """Filter DataFrame by both keywords and expression, then merge results, removing duplicates."""
        # Apply both filters separately
        keyword_filtered_paperId = self.filter_by_keywords(column_name)
        self.logger.info(f"Number of papers after keyword filtering: {len(keyword_filtered_paperId)}")

        expression_filtered_paperId = self.filter_by_expression(column_name)
        self.logger.info(f"Number of papers after expression filtering: {len(expression_filtered_paperId)}")

        # Combine and remove duplicates
        combined_df = pd.concat([keyword_filtered_paperId, expression_filtered_paperId]).drop_duplicates()
#        combined_df = pd.concat([keyword_filtered_paperId, expression_filtered_paperId]).drop_duplicates().reset_index(drop=True)
        self.logger.info(f"Total number of unique papers after combining filters: {len(combined_df)}")

        self.logger.info("Combined DataFrame filtered by both keywords and expression, duplicates removed.")
        return combined_df

    def evaluate_expression(self, ast, row, column_name):
        """Evaluate the AST against a DataFrame row."""
        return evaluate_ast(ast, row,column_name)

# Example usage (this should be placed in a separate script)
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    # Sample DataFrame
    data = {
        'title': [
            'Revolutionizing Molecular Design for Innovative Therapeutic Applications through Artificial Intelligence',
            'Revolutionizing Research Methodologies: The Emergence of Research 5.0 through AI, Automation, and Blockchain',
            'Revolutionizing Research Methodologies: The Emergence of Research through AI',
            'C++ vs Java: A Comparison',
            'Getting Started with .Net',
            'Understanding Advanced Algorithms',
            'Advanced C++??'
        ],
        'abstract': [
            'A comprehensive guide to C++.',
            'Exploring .Net in detail.',
            'Deep dive into advanced Python features.',
            'A comparison of two major programming languages.',
            None,
            'Algorithms and data structures.',
            'An advanced look at C++ techniques.'
        ]
    }

    df = pd.DataFrame(data)

    # Create an instance of the DataFrameFilter class

    # Filter the DataFrame by an expression
    keywords = ["(\"Research 5.0\" OR Blockchain)"]
    keywords = [".net OR C++"]
    filter = DataFrameFilter(df, keywords= keywords)

    filtered_df_by_expression = filter.filter_by_keywords_and_expression('title')
    print("\nFiltered DataFrame by expression:")
    print(filtered_df_by_expression)

    print('--'*40)

    for i, row in filtered_df_by_expression.iterrows():
        print(row.title)
