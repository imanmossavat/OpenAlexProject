"""

from LogManager.crawler_logger import  CrawlerLogger

# Create an instance of CrawlerLogger
logger = CrawlerLogger()

# Set up logging
logger.setup_logging()

# Log an info level message
logger.info('This is an info message.')

# Set up logging for a specific iteration
iteration = 1
logger.set_iteration_logging(iteration)

# Log reporting information
data_manager = DataManager()  # Assuming you have a DataManager object
logger.log_reporting_information(data_manager, iteration)

# Change the log level
logger.logger.setLevel(logging.WARNING)

"""

import logging
from logging.handlers import RotatingFileHandler
import os


class CrawlerLogger:
    def __init__(self, options):
        """
        Initializes the CrawlerLogger class.

        Args:
        - options: An instance of the StorageAndLoggingOptions class containing the storage and logging options.
        """
        self.options = options
        self.logger = logging.getLogger(options.logger_name)
        self.logger.setLevel(getattr(logging, options.log_level))

        self.logging_setup_done = False  # Flag to track setup status
        self.setup_logging()


    def setup_logging(self):
        """
        Sets up the logging configuration.

        Creates a log folder if it doesn't exist and configures a file handler
        that rotates log files based on size and count.
        """
        if self.logging_setup_done:
            return  # Skip if already set up
        
        # Create the log folder if it doesn't exist
        os.makedirs(self.options.log_folder, exist_ok=True)

        # Create a file handler that rotates log files
        log_file = os.path.join(self.options.log_folder, self.options.log_file)
        file_handler = RotatingFileHandler(log_file, maxBytes=self.options.max_log_size, backupCount=self.options.log_backup_count)
        file_handler.setLevel(getattr(logging, self.options.log_level))

        # Define the log format
        formatter = logging.Formatter(self.options.log_format)
        file_handler.setFormatter(formatter)

        # Add the file handler to the logger
        self.logger.addHandler(file_handler)
        self.logging_setup_done = True  # Mark setup as done


    def set_iteration_logging(self, iteration):
        """
        Sets up logging for a specific iteration.

        Creates a new log file for each iteration, with a unique log file name.

        Args:
        - iteration: The current iteration number.
        """
        # Create the log folder if it doesn't exist
        log_folder = 'log'
        os.makedirs(log_folder, exist_ok=True)

        # Create a new file handler with a unique log file name for each iteration
        log_file_name = f'iteration_{iteration}.log'
        log_file_path = os.path.join(log_folder, log_file_name)
        file_handler = logging.FileHandler(log_file_path)

        # Set the log level and formatter
        file_handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)

        # Remove the existing file handlers from the logger
        for handler in self.logger.handlers:
            self.logger.removeHandler(handler)

        # Add the new file handler to the logger
        self.logger.addHandler(file_handler)

    def log_reporting_information(self, data_manager, iteration=None):
        """
        Logs reporting information to the log file.

        Logs various information related to dataframes, graph, processed papers, and centrality statistics.

        Args:
        - data_manager: The DataManager object containing the relevant data.
        - iteration: The current iteration number (optional).
        """
        # Shapes of dataframes in frames
        if iteration:
            self.logger.info(f'iteration: {iteration}')
        df_shapes = data_manager.frames.get_dataframes_shapes()
        self.logger.info('DataFrame Shapes: %s', df_shapes)

        # Number of processed papers
        num_processed_papers, _ = data_manager.frames.get_num_processed_papers()
        self.logger.info('Number of Processed Papers: %d', num_processed_papers)

        # Number of nodes and edges in the graph
        graph_info = data_manager.graph.get_graph_info()
        self.logger.info(f'Graph no. nodes: {graph_info[0]}, no. Edges: {graph_info[1]}')

        # # Summary statistics of centralities
        # centrality_stats = data_manager.graph.get_centrality_statistics(data_manager)
        # self.logger.info('Centrality Statistics: %s', centrality_stats)

    def info(self, message, *args, **kwargs):
        """
        Logs an info level message.

        Args:
        - message: The log message.
        - *args, **kwargs: Additional arguments and keyword arguments.
        """
        self.logger.info(message, *args, **kwargs)
    
    def error(self, message, *args, **kwargs):
        """
        Logs an info level message.

        Args:
        - message: The log message.
        - *args, **kwargs: Additional arguments and keyword arguments.
        """
        self.logger.error(message, *args, **kwargs)


    def warning(self, message, *args, **kwargs):
        """
        Logs an info level message.

        Args:
        - message: The log message.
        - *args, **kwargs: Additional arguments and keyword arguments.
        """
        self.logger.warning(message, *args, **kwargs)

    def debug(self, message, *args, **kwargs):
        """
        Logs an info level message.

        Args:
        - message: The log message.
        - *args, **kwargs: Additional arguments and keyword arguments.
        """
        self.logger.debug(message, *args, **kwargs)
        
    def set_iteration(self, iteration):
        """
        Sets up logging for a specific iteration.

        Creates a new logger for the current iteration.

        Args:
        - iteration: The current iteration number.
        """
        iteration_logger_name = f'iteration_{iteration}'
        self.iteration_logger = logging.getLogger(iteration_logger_name)
    
    def shutdown(self):
        logging.shutdown()

