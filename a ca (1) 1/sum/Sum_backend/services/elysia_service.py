# services/elysia_service.py

import os
import logging
from typing import Any, Dict

# --- Weaviate v4 Import ---
try:
    import weaviate
    from weaviate.classes.init import Auth
except ImportError:
    raise ImportError(
        "Missing dependency: weaviate-client. Install using: pip install weaviate-client>=4.0.0"
    )

logger = logging.getLogger(__name__)

class ElysiaWrapper:
    """
    Direct Weaviate Wrapper.
    Replaces the broken 'elysia' library with standard Weaviate v4 search.
    """

    def __init__(
        self,
        weaviate_url: str | None = None,
        weaviate_api_key: str | None = None,
        elysia_config: Dict | None = None
    ):
        # 1. Read Configs
        self.weaviate_url = weaviate_url or os.environ.get("WEAVIATE_URL")
        self.weaviate_api_key = weaviate_api_key or os.environ.get("WEAVIATE_API_KEY")

        if not self.weaviate_url:
            raise ValueError("WEAVIATE_URL is required.")

        # 2. Initialize Weaviate Client
        logger.info(f"Connecting to Weaviate cluster: {self.weaviate_url}")
        
        try:
            # Standard Weaviate v4 Cloud connection
            self.client = weaviate.connect_to_weaviate_cloud(
                cluster_url=self.weaviate_url,
                auth_credentials=Auth.api_key(self.weaviate_api_key) if self.weaviate_api_key else None,
                skip_init_checks=True # Keeps the Windows SSL fix
            )
        except Exception as e:
            logger.exception("Failed to connect to Weaviate.")
            # We don't raise here, so the app can start even if DB is down.
            # The rag_query method handles the missing client gracefully.
            self.client = None

    def rag_query(self, query: str, top_k: int = 5) -> Dict[str, Any]:
        """
        Direct Weaviate Search.
        Searches a 'Document' or 'Chunk' collection if it exists.
        """
        if not query:
            return {"error": "Query cannot be empty."}

        if not self.client:
            logger.warning("Weaviate client not connected. Skipping RAG.")
            return {"results": []}

        try:
            logger.info(f"Running Direct Weaviate RAG query → {query}")
            
            # 1. Inspect Collections (Debug helper)
            collections = self.client.collections.list_all()
            if not collections:
                logger.info("No collections found in Weaviate.")
                return {"results": []}

            # 2. Guess the collection name (First available, or 'Document' if present)
            target_collection_name = list(collections.keys())[0]
            if "Document" in collections:
                target_collection_name = "Document"
            
            # 3. Perform Hybrid Search
            collection = self.client.collections.get(target_collection_name)
            response = collection.query.hybrid(
                query=query,
                limit=top_k
            )

            # 4. Format Results
            results = []
            for obj in response.objects:
                results.append({
                    "text": obj.properties.get("content") or obj.properties.get("text") or str(obj.properties),
                    "score": obj.metadata.score
                })

            return {"results": results}

        except Exception as e:
            logger.error(f"Weaviate search failed: {e}")
            # Return empty results so the app doesn't crash
            return {"results": []}

    def close(self):
        if self.client:
            self.client.close()