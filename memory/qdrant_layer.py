"""
Qdrant Layer for Vector Storage and Semantic Search
"""

import json
from typing import Any, Optional, List, Dict
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance, VectorParams, PointStruct, Filter, FieldCondition,
    MatchValue, Range, SearchParams
)


class QdrantLayer:
    """Qdrant vector database client for semantic memory"""
    
    def __init__(
        self, 
        url: str = 'http://localhost:6333',
        api_key: Optional[str] = None
    ):
        self.url = url
        self.api_key = api_key
        self.client: Optional[QdrantClient] = None
    
    def connect(self):
        """Initialize Qdrant connection"""
        self.client = QdrantClient(
            url=self.url,
            api_key=self.api_key
        )
        print(f"✓ Connected to Qdrant at {self.url}")
    
    def create_collection(
        self,
        collection_name: str,
        vector_size: int = 768,
        distance: str = 'COSINE'
    ):
        """Create a new collection"""
        distance_enum = getattr(Distance, distance)
        
        try:
            self.client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(
                    size=vector_size,
                    distance=distance_enum
                )
            )
            print(f"✓ Created collection: {collection_name}")
        except Exception as e:
            if 'already exists' in str(e).lower():
                print(f"ℹ Collection {collection_name} already exists")
            else:
                raise
    
    def upsert(
        self,
        collection_name: str,
        points: List[Dict[str, Any]]
    ):
        """Insert or update points"""
        formatted_points = []
        for p in points:
            point = PointStruct(
                id=p['id'],
                vector=p['vector'],
                payload=p.get('payload', {})
            )
            formatted_points.append(point)
        
        self.client.upsert(
            collection_name=collection_name,
            points=formatted_points
        )
        return len(points)
    
    def search(
        self,
        collection_name: str,
        query_vector: List[float],
        limit: int = 5,
        filter_conditions: Optional[Dict] = None
    ) -> List[Dict]:
        """Search for similar vectors"""
        search_filter = None
        if filter_conditions:
            conditions = []
            for field, value in filter_conditions.items():
                conditions.append(
                    FieldCondition(
                        key=field,
                        match=MatchValue(value=value)
                    )
                )
            search_filter = Filter(must=conditions)
        
        results = self.client.search(
            collection_name=collection_name,
            query_vector=query_vector,
            limit=limit,
            query_filter=search_filter,
            search_params=SearchParams(hnsw_ef=128, exact=False)
        )
        
        return [
            {
                'id': r.id,
                'score': r.score,
                'payload': r.payload,
                'vector': r.vector
            }
            for r in results
        ]
    
    def retrieve(
        self,
        collection_name: str,
        ids: List[int],
        with_vectors: bool = True
    ) -> List[Dict]:
        """Retrieve points by ID"""
        records = self.client.retrieve(
            collection_name=collection_name,
            ids=ids,
            with_payload=True,
            with_vectors=with_vectors
        )
        
        return [
            {
                'id': r.id,
                'payload': r.payload,
                'vector': r.vector if with_vectors else None
            }
            for r in records
        ]
    
    def delete(
        self,
        collection_name: str,
        ids: Optional[List[int]] = None,
        filter_conditions: Optional[Dict] = None
    ):
        """Delete points"""
        if ids:
            self.client.delete(
                collection_name=collection_name,
                points_selector=ids
            )
        
        if filter_conditions:
            conditions = []
            for field, value in filter_conditions.items():
                conditions.append(
                    FieldCondition(
                        key=field,
                        match=MatchValue(value=value)
                    )
                )
            self.client.delete(
                collection_name=collection_name,
                points_selector=Filter(must=conditions)
            )
    
    def count(
        self,
        collection_name: str,
        filter_conditions: Optional[Dict] = None
    ) -> int:
        """Count points matching filter"""
        search_filter = None
        if filter_conditions:
            conditions = []
            for field, value in filter_conditions.items():
                conditions.append(
                    FieldCondition(
                        key=field,
                        match=MatchValue(value=value)
                    )
                )
            search_filter = Filter(must=conditions)
        
        result = self.client.count(
            collection_name=collection_name,
            count_filter=search_filter
        )
        return result.count
    
    def get_collection_info(self, collection_name: str) -> Dict:
        """Get collection information"""
        info = self.client.get_collection(collection_name)
        return {
            'name': collection_name,
            'vectors_count': info.vectors_count,
            'points_count': info.points_count,
            'status': info.status,
            'vector_size': info.config.params.vectors.size,
            'distance': str(info.config.params.vectors.distance)
        }
    
    def list_collections(self) -> List[str]:
        """List all collections"""
        collections = self.client.get_collections()
        return [c.name for c in collections.collections]
    
    def delete_collection(self, collection_name: str):
        """Delete a collection"""
        self.client.delete_collection(collection_name=collection_name)
        print(f"✓ Deleted collection: {collection_name}")
    
    def health_check(self) -> Dict:
        """Check Qdrant health"""
        try:
            collections = self.list_collections()
            return {
                'status': 'healthy',
                'collections_count': len(collections),
                'collections': collections
            }
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e)
            }


# Singleton instance
_qdrant_layer: Optional[QdrantLayer] = None


def get_qdrant_layer() -> QdrantLayer:
    """Get or create Qdrant layer singleton"""
    global _qdrant_layer
    if _qdrant_layer is None:
        _qdrant_layer = QdrantLayer()
    return _qdrant_layer
