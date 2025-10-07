

from pyzotero import zotero
import os
from dotenv import load_dotenv
import logging
from typing import List, Dict, Optional
import time


class ZoteroClient:
    """
    Client for interacting with Zotero API.
    Single Responsibility: Zotero API communication and rate limiting.
    """
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        """Initialize Zotero client with credentials from environment."""
        load_dotenv()
        
        self.library_id = os.getenv('ZOTERO_LIBRARY_ID')
        self.library_type = os.getenv('ZOTERO_LIBRARY_TYPE', 'user')
        self.api_key = os.getenv('ZOTERO_API_KEY')
        
        if not self.library_id or not self.api_key:
            raise ValueError(
                "ZOTERO_LIBRARY_ID and ZOTERO_API_KEY must be set in .env file\n"
                "Get your API key from: https://www.zotero.org/settings/keys"
            )
        
        self.logger = logger or logging.getLogger(__name__)
        self.zot = zotero.Zotero(self.library_id, self.library_type, self.api_key)
        self.last_request_time = 0
        self.min_delay = 0.5
        
        self.logger.info(f"Zotero client initialized (library: {self.library_id})")
    
    def _rate_limit(self):
        """Enforce rate limiting between API requests."""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.min_delay:
            time.sleep(self.min_delay - elapsed)
        self.last_request_time = time.time()
    
    def get_collections(self) -> List[Dict]:
        """Retrieve all collections from the Zotero library."""
        self._rate_limit()
        
        try:
            collections = self.zot.collections()
            
            processed_collections = []
            for col in collections:
                processed_collections.append({
                    'key': col['data']['key'],
                    'name': col['data']['name'],
                    'data': col['data']
                })
            
            self.logger.info(f"Retrieved {len(processed_collections)} collections")
            return processed_collections
            
        except Exception as e:
            self.logger.error(f"Error retrieving collections: {e}")
            raise
    
    def get_collection_items(self, collection_key: str) -> List[Dict]:
        """Retrieve all bibliographic items from a collection."""
        self._rate_limit()
        
        try:
            items = self.zot.collection_items(collection_key)
            
            bibliographic_items = []
            for item in items:
                item_type = item['data'].get('itemType', '')
                if item_type not in ('attachment', 'note'):
                    bibliographic_items.append(item)
            
            self.logger.info(
                f"Retrieved {len(bibliographic_items)} bibliographic items "
                f"from collection {collection_key}"
            )
            return bibliographic_items
            
        except Exception as e:
            self.logger.error(f"Error retrieving collection items: {e}")
            raise