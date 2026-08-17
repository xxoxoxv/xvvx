---
scope: agent_hierarchy_definitions
owner: agent_orchestration
created: 2026-08-17
last_modified: 2026-08-17
purpose: Agent hierarchy and organizational structure definitions
---

"""
Agent Hierarchy for AMOS Federation

This module defines the hierarchical structure and organizational relationships
between different agent types in the federation.
"""

from typing import Dict, Any, List, Optional
from enum import Enum


class AgentLevel(Enum):
    """Hierarchical levels for agents."""
    SOVEREIGN = "sovereign"
    SUPERVISOR = "supervisor"
    COORDINATOR = "coordinator"
    WORKER = "worker"
    SPECIALIST = "specialist"


class AgentHierarchy:
    """Manages agent hierarchy and reporting relationships."""
    
    def __init__(self):
        self.hierarchy: Dict[str, List[str]] = {}
        
    def add_agent(self, agent_id: str, level: AgentLevel, reports_to: Optional[str] = None):
        """Add an agent to the hierarchy."""
        if reports_to and reports_to not in self.hierarchy:
            raise ValueError(f"Supervisor {reports_to} not found in hierarchy")
            
        if reports_to not in self.hierarchy:
            self.hierarchy[reports_to] = []
            
        self.hierarchy[reports_to].append(agent_id)
        
    def get_subordinates(self, agent_id: str) -> List[str]:
        """Get all direct subordinates of an agent."""
        return self.hierarchy.get(agent_id, [])
