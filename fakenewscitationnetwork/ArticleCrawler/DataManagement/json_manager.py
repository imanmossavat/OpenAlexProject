import pandas as pd
import json
import logging
import hashlib
import os
import pickle

class JsonConverter:
    """
    Converts data from multiple DataFrames into a JSON format representing nodes and relationships.
    To be used for interfacing with NEO4J.

    Args:
    - logger (Logger): The logger object for logging messages.
    - frames (FrameManager): An instance of the FrameManager class containing multiple DataFrames.
    - filename (str): The filename to save the JSON output.

    Attributes:
    - filename (str): The filename to save the JSON output.
    - logger (Logger): The logger object for logging messages.
    - frames (FrameManager): An instance of the FrameManager class containing multiple DataFrames.
    - unique_paper_ids (set): A set containing unique paper IDs.
    - unique_author_ids (set): A set containing unique author IDs.
    - unique_venue_ids (set): A set containing unique venue IDs.
    - df_venues (DataFrame): DataFrame to store venue information.
    - relationship_id (int): ID counter for relationships.
    - data (dict): Dictionary structure to store node and relationship data.

    Methods:
    - add_node(node_type, id, labels, properties): Adds a node to the data structure.
    - add_relationship(start, end, label, properties): Adds a relationship between nodes.
    - add_venue(venue): Adds a venue node if it doesn't exist already.
    - add_paper_venue_relationship(paper_id, paper_title, venue, year): Adds a relationship between a paper and a venue.
    - _is_valid_meta_data_row(row): Validates if the paper row contains necessary information.
    - _get_abstract_for_paper(paper_id): Retrieves the abstract for a given paper ID.
    - _process_meta_data_row(row): Processes metadata rows from the DataFrame.
    - _process_paper_author_row(row): Processes rows related to paper authors.
    - process_author_nodes(): Processes author nodes and their relationships.
    - process_meta_data(): Processes metadata information.
    - _process_paper_references_row(row): Processes paper reference rows.
    - add_paper_references_relationships(): Adds relationships for paper references.
    - _process_paper_citations_row(row): Processes paper citation rows.
    - add_paper_citations_relationships(): Adds relationships for paper citations.
    - df2json(): Converts paper metadata to JSON format.
    - save_json(): Saves the generated JSON data to a file.
    """
 
    def __init__(self, frames, filename, logger= None):
        self.filename = filename
        self.logger = logger or logging.getLogger(__name__)

        self.frames = frames # an instance of the FrameManager class, this contains multiple dataframes 

        self.unique_paper_ids = set()
        self.unique_author_ids = set()
        self.hashed_venues = set() # check if a venue should be hashed or not
        self.unique_venue_ids = set() # this is redundant, for now we check both and use it for consistency check, it is probably faster too, at a minimal memory cost (todo, only use PD)
        self.df_venues = pd.DataFrame(columns = ['venue', 'id'])
        self.relationship_id = 0
        self.data = []

    def add_node(self, node_type, id, properties):
        """
        Adds a node to the data structure.

        Args:
        - node_type (str): Type of the node being added (e.g., "paper", "venue", "author").
        - properties (dict): Dictionary containing attributes specific to the node being added.

        Example:
        To add a paper node:
        add_node("paper", {"datasource": "semanticscholar", "paperid": "12345", "title": "Sample Paper"})
        """
        
        if self._check_uniqueness(node_type, id):
            
            if node_type == "venue":
                self.unique_venue_ids.add(id)
            elif node_type == "author":
                self.unique_author_ids.add(id)
            
            self.data.append({
                "type": 'node',
                "id": id,
                "labels": [node_type],
                "properties": properties
            })

    def _check_uniqueness(self, node_type, id):
        
        identifier = id 
        if node_type == "author":
            unique_set = self.unique_author_ids  
        elif node_type == 'venue':
            unique_set =  self.unique_venue_ids
        else:
            return True  # no checks for non-author and non-venue papers for now (no check for paper nodes) 
 

        if identifier and identifier not in unique_set:
            unique_set.add(identifier)
            return True  # Identifier is non-empty and unique, node added
        else:
            return False
       
    
    def add_relationship(self, start, end, label, properties):


        self.data.append({
            "type": "relationship",
            "id": str(self.relationship_id),
            "label": label,
            "properties": properties,
            "start": start,
            "end": end
        })

        self.relationship_id += 1

    def add_venue(self, venue):
        if venue not in self.hashed_venues: # otherwise it is already added 
            hashed_object = hashlib.md5(venue.encode())
            venue_id = hashed_object.hexdigest()

            # Assuming add_node takes properties, id, and labels arguments
            self.add_node(node_type="venue", properties={"venue": venue}, id=venue_id)
            self.unique_venue_ids.add(venue_id)
            self.hashed_venues.add(venue)

            #self.df_venues = self.df_venues.append({'venue': venue, 'id': venue_id}, ignore_index=True)
            new_row = pd.DataFrame({'venue': [venue], 'id': [venue_id]})
            self.df_venues = pd.concat([self.df_venues, new_row], ignore_index=True)
            try:
                assert set(self.df_venues['venue']) == self.hashed_venues, "Assertion failed: The sets do not match: hashed_venues not matching data-frame"
                assert set(self.df_venues['id']) == self.unique_venue_ids, "Assertion failed: The sets do not match: unique_venue_ids not matching data-frame"
            except AssertionError as e:
                self.logger.error(f'Assertion failed: {e}')



    def add_paper_venue_relationship(self, paper_id, venue):
        
        row_venue = self.df_venues.loc[self.df_venues['venue'] == venue]
        
        try:
            assert not row_venue.empty, f"No ID found for {venue} in unique_venue_ids"
            venue_id = row_venue.iloc[0]['id']

            properties = {} 

            # Assuming add_relationship takes start, end, label, and properties arguments
            self.add_relationship(
                start={"id": paper_id, "labels": ["paper"]},
                end={"id": venue_id, "labels": ["venue"]},
                label="PUBLISHED_BY",
                properties=properties
            )

        except AssertionError as e:
            self.logger.error(f'Assertion failed: {e}')

   
    
    def process_author_nodes(self):
        filtered_paper_author = self.frames.df_paper_author[self.frames.df_paper_author['paperId'].isin(self.unique_paper_ids)]

        filtered_paper_author.apply(self._process_paper_author_row, axis=1)

    def process_meta_data(self):
        self.frames.df_paper_metadata.apply(self._process_meta_data_row, axis=1)

     
    def add_paper_references_relationships(self):
            self.frames.df_paper_references.apply(self._process_paper_refrences_row, axis=1)


    
    def add_paper_citations_relationships(self):
            self.frames.df_paper_citations.apply(self._process_paper_citations_row, axis=1)


    def df2json(self):

        self.process_meta_data()
        self.process_author_nodes()

        self.add_paper_references_relationships()
        self.add_paper_citations_relationships()
        
    def save_json(self):
        with open(self.filename, 'w') as file:
            for entry in self.data:
                json.dump(entry, file)
                file.write('\n')


    def _process_paper_author_row(self, row):
        author_id = row['authorId']
        paper_id = row['paperId']

        # add author node if needed
        if author_id not in self.unique_author_ids:
            author_row = self.frames.df_author[self.frames.df_author['authorId'] == author_id]
            if author_row.empty:
                self.logger.error(f"No author found for authorId {author_id} in df_author.")
                return

            author_name = author_row.iloc[0]['authorName']
            self.add_node(node_type='author', id=author_id, properties={"name": author_name})
            self.unique_author_ids.add(author_id)
            
        self.add_relationship(start={'id': paper_id, 'labels': ['paper']},
                              end={'id': author_id, 'labels': ['author']},
                              label='AUTHORED_BY', properties={})

    def _process_paper_refrences_row(self,row):
         if row['paperId'] in self.unique_paper_ids and row['referencePaperId'] in self.unique_paper_ids:
                self.add_relationship(start={'id':  row['paperId'], 'labels': ['paper']},   
                                      end={'id':  row['referencePaperId'], 'labels': ['paper']},  
                                      label="CITE", 
                                      properties={})


    def _process_paper_citations_row(self,row):
        if row['paperId'] in self.unique_paper_ids and row['citedPaperId'] in self.unique_paper_ids:
            self.add_relationship(start = {'id':  row['citedPaperId'], 'labels': ['paper']} ,
                                  end= {'id':  row['paperId'], 'labels': ['paper']} ,
                                  label="CITE",
                                  properties={})

    def _is_valid_meta_data_row(self, row):
        if pd.isnull(row['paperId']) or not row['paperId']:
            title_info = f" with title '{row['title']}'" if not pd.isnull(row['title']) else ''
            self.logger.warning(f"Paper has no ID{title_info}, skipping.")
            return False
        elif pd.isnull(row['title']) or not row['title']:
            self.logger.warning(f"Paper '{row['paperId']}' has no title, skipping.")
            return False
        elif row['paperId'] in self.unique_paper_ids:
            self.logger.warning(f"Paper '{row['paperId']}' and {row['title']} is repeated, skipping.")
            return False
        return True

    def _get_abstract_for_paper(self, paper_id):
            abstract_row = self.frames.df_abstract[self.frames.df_abstract['paperId'] == paper_id]
            if abstract_row.empty:
                return None  # or raise an error, based on your logic
            return abstract_row.iloc[0]['abstract']
    
    def _process_meta_data_row(self, row):
        if self._is_valid_meta_data_row(row):
            
            if row['processed']:
                abstract = self._get_abstract_for_paper(row['paperId'])
                paper_properties = {
                    "title": [row['title']],
                    "year": row['year'],
                    "processed": row['processed'],
                    "abstract": abstract
                }
            else:
                paper_properties = {
                    "title": [row['title']],
                    "year": row['year'],
                    "processed": row['processed'],
                }

            self.add_node(node_type="paper", properties = paper_properties, id = row['paperId'])
            self.unique_paper_ids.add(row['paperId'])

            venue = self._is_valid_venue(row['venue'])
            if  venue:
                self.add_venue(venue)
                self.add_paper_venue_relationship(row['paperId'], venue)


    def _is_valid_venue(self, venue):
        # checks if the venue is valid AND returns the cleaned lowercase venue value if valid. 
        # This returned value can be used directly where needed:
        meaningless_strings = ['na', 'tba', 'n/a', 'undefined', 'empty', 'not provided', 'placeholder',
                            'unspecified', 'tbd', 'unknown', 'not found', 'not applicable', 'invalid',
                            'unavailable', 'missing', 'none', 'empty string', 'default', 'no value',
                            'no data', 'no information', 'not applicable', 'not specified', 'no entry',
                            'not recorded', 'not given', 'not supplied', 'not defined', 'www']
        
        if venue and not pd.isnull(venue):
            venue= venue.lower().strip()
            if venue not in meaningless_strings:
                return venue
        return False
    

    
