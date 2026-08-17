"""
Semantic Memory - Vector-based Knowledge Storage and Retrieval
"""

import hashlib
from typing import Any, Dict, List, Optional
from datetime import datetime


class SemanticMemory:
    """Semantic memory using Qdrant for vector storage and retrieval"""
    
    def __init__(self, qdrant_layer=None):
        self.qdrant = qdrant_layer
        self.collection_name = 'semantic_memory'
        self.vector_size = 768  # Default embedding size
    
    def initialize(self, vector_size: int = 768):
        """Initialize semantic memory collections"""
        if not self.qdrant:
            print("⚠ Qdrant layer not available, using simulation mode")
            return
        
        self.vector_size = vector_size
        self.qdrant.create_collection(
            collection_name=self.collection_name,
            vector_size=vector_size,
            distance='COSINE'
        )
    
    def store(
        self,
        content: str,
        embedding: List[float],
        metadata: Optional[Dict] = None
    ) -> str:
        """Store semantic memory with embedding"""
        memory_id = hashlib.sha256(
            f"{content}_{datetime.now().isoformat()}".encode()
        ).hexdigest()[:16]
        
        point = {
            'id': int(memory_id, 16) % (2**63),  # Convert to valid Qdrant ID
            'vector': embedding,
            'payload': {
                'content': content,
                'metadata': metadata or {},
                'created_at': datetime.now().isoformat(),
                'memory_type': 'semantic'
            }
        }
        
        if self.qdrant:
            self.qdrant.upsert(
                collection_name=self.collection_name,
                points=[point]
            )
        else:
            print(f"ℹ Stored memory (simulation): {memory_id}")
        
        return memory_id
    
    def search(
        self,
        query_embedding: List[float],
        limit: int = 5,
        filters: Optional[Dict] = None
    ) -> List[Dict]:
        """Search for similar memories"""
        if not self.qdrant:
            print("ℹ Search (simulation)")
            return []
        
        results = self.qdrant.search(
            collection_name=self.collection_name,
            query_vector=query_embedding,
            limit=limit,
            filter_conditions=filters
        )
        
        return [
            {
                'id': r['id'],
                'content': r['payload'].get('content'),
                'metadata': r['payload'].get('metadata'),
                'score': r['score'],
                'created_at': r['payload'].get('created_at')
            }
            for r in results
        ]
    
    def retrieve_by_id(self, memory_id: str) -> Optional[Dict]:
        """Retrieve specific memory by ID"""
        if not self.qdrant:
            print(f"ℹ Retrieve by ID (simulation): {memory_id}")
            return None
        
        numeric_id = int(memory_id, 16) % (2**63)
        results = self.qdrant.retrieve(
            collection_name=self.collection_name,
            ids=[numeric_id],
            with_vectors=False
        )
        
        if results:
            r = results[0]
            return {
                'id': memory_id,
                'content': r['payload'].get('content'),
                'metadata': r['payload'].get('metadata'),
                'created_at': r['payload'].get('created_at')
            }
        return None
    
    def delete(self, memory_id: str):
        """Delete memory by ID"""
        if not self.qdrant:
            print(f"ℹ Delete memory (simulation): {memory_id}")
            return
        
        numeric_id = int(memory_id, 16) % (2**63)
        self.qdrant.delete(
            collection_name=self.collection_name,
            ids=[numeric_id]
        )
    
    def update_metadata(self, memory_id: str, metadata: Dict):
        """Update memory metadata"""
        # In Qdrant, we need to upsert with updated payload
        existing = self.retrieve_by_id(memory_id)
        if existing:
            numeric_id = int(memory_id, 16) % (2**63)
            # Would need to retrieve vector and re-upsert
            print(f"ℹ Update metadata (simulation): {memory_id}")
    
    def count(self) -> int:
        """Get total memory count"""
        if not self.qdrant:
            return 0
        
        return self.qdrant.count(
            collection_name=self.collection_name
        )
    
    def get_memories_by_type(
        self,
        memory_type: str,
        limit: int = 100
    ) -> List[Dict]:
        """Get memories filtered by type"""
        if not self.qdrant:
            return []
        
        # Note: This requires Qdrant filter support
        return self.search(
            query_embedding=[0.0] * self.vector_size,  # Dummy query
            limit=limit,
            filters={'memory_type': memory_type}
        )
    
    def get_recent_memories(self, limit: int = 10) -> List[Dict]:
        """Get most recently created memories"""
        # This would require time-based filtering in Qdrant
        print("ℹ Get recent memories (simulation)")
        return []
    
    def clear(self):
        """Clear all semantic memories"""
        if not self.qdrant:
            print("ℹ Clear all memories (simulation)")
            return
        
        self.qdrant.delete_collection(self.collection_name)
        self.initialize(self.vector_size)
    
    def stats(self) -> Dict:
        """Get memory statistics"""
        if not self.qdrant:
            return {
                'count': 0,
                'collection': self.collection_name,
                'vector_size': self.vector_size
            }
        
        info = self.qdrant.get_collection_info(self.collection_name)
        return {
            'count': info.get('points_count', 0),
            'vectors_count': info.get('vectors_count', 0),
            'collection': info.get('name', self.collection_name),
            'vector_size': info.get('vector_size', self.vector_size),
            'status': info.get('status', 'unknown')
        }
    
    def export_memories(self) -> List[Dict]:
        """Export all memories for backup"""
        # Implementation depends on Qdrant scan capabilities
        print("ℹ Export memories (simulation)")
        return []
    
    def import_memories(self, memories: List[Dict]):
        """Import memories from backup"""
        if not self.qdrant or not memories:
            print(f"ℹ Import {len(memories)} memories (simulation)")
            return
        
        points = []
        for mem in memories:
            points.append({
                'id': int(mem['id'], 16) % (2**63),
                'vector': mem.get('embedding', [0.0] * self.vector_size),
                'payload': {
                    'content': mem.get('content'),
                    'metadata': mem.get('metadata', {}),
                    'created_at': mem.get('created_at'),
                    'memory_type': mem.get('memory_type', 'semantic')
                }
            })
        
        self.qdrant.upsert(
            collection_name=self.collection_name,
            points=points
        )


# Singleton instance
_semantic_memory: Optional[SemanticMemory] = None


def get_semantic_memory(qdrant_layer=None) -> SemanticMemory:
    """Get or create semantic memory singleton"""
    global _semantic_memory
    if _semantic_memory is None:
        _semantic_memory = SemanticMemory(qdrant_layer=qdrant_layer)
    return _semantic_memory
