import os
import pickle
from datetime import datetime
import glob

class DataStorage:
    def __init__(self, storage_and_logging_options,logger):
        self.logger = logger
        self.storage_and_logging_options = storage_and_logging_options
        self.temp_folder = os.path.join(storage_and_logging_options.pkl_folder, 'temp')  # Temp folder path
        self.perm_folder = os.path.join(storage_and_logging_options.pkl_folder, 'perm')  # Perm folder path
        self.timestamp = None
        

    def save_intermediate_file(self, obj, iteration):
        # Create the temp folder if it doesn't exist
        os.makedirs(self.temp_folder, exist_ok=True)

        # Generate the file name for the intermediate file
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        filename = f'intermediate_{iteration}_{timestamp}.pkl'
        filepath = os.path.join(self.temp_folder, filename)

        # Save the object to the intermediate file using pickle
        with open(filepath, 'wb') as file:
            pickle.dump(obj, file)

        # Log the filename
        self.logger.info(f'Saved intermediate file: {filename}')

        # Remove the previous intermediate files
        self.remove_previous_intermediate_files()

    def remove_previous_intermediate_files(self):
        # Generate the file pattern for previous intermediate files
        pattern = f'intermediate_*_*.pkl'
        filepath_pattern = os.path.join(self.temp_folder, pattern)

        # Find previous intermediate files and sort them based on modification time
        prev_files = glob.glob(filepath_pattern)
        prev_files.sort(key=os.path.getmtime)

        # Remove all previous intermediate files except the latest one
        for file in prev_files[:-1]:
            os.remove(file)


    def save_final_file(self, obj, experiment_file_name):
        # Create the perm folder if it doesn't exist
        os.makedirs(self.perm_folder, exist_ok=True)

        # Generate a unique filename for the final file
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        filename = f'{experiment_file_name}_{timestamp}.pkl'
        filepath = os.path.join(self.perm_folder, filename)

        # Save data_manager to the final file
        # Save the object to the intermediate file using pickle
        with open(filepath, 'wb') as file:
            pickle.dump(obj, file)

        # Remove the previous intermediate files
        self.remove_previous_intermediate_files()
        fullpath = filepath

        # Log the filename
        self.logger.info('Final file moved: %s', fullpath)
        
        # update the options storage_and_logging_options globally
        # self.storage_and_logging_options.filepath_final_pkl= fullpath
        # self.storage_and_logging_options.timestamp_final_pkl= timestamp

        return fullpath, timestamp   