"""
Enhanced Memory Manager for AI Agent Twins
Handles persistent memory, context awareness, and knowledge retrieval
"""

import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import logging
import boto3
from botocore.exceptions import ClientError
from decimal import Decimal

logger = logging.getLogger(__name__)

@dataclass
class MemoryEntry:
    """Individual memory entry with metadata"""
    id: str
    agent_id: str
    user_id: Optional[str]
    content: str
    memory_type: str  # 'conversation', 'learning', 'context', 'knowledge'
    importance: float  # 0.0 to 1.0
    timestamp: datetime
    metadata: Dict[str, Any]
    tags: List[str]

@dataclass
class ContextWindow:
    """Context window for agent conversations"""
    recent_conversations: List[MemoryEntry]
    relevant_knowledge: List[MemoryEntry]
    user_preferences: Dict[str, Any]
    current_topic: Optional[str]

class MemoryManager:
    """Enhanced memory management for AI agents"""
    
    def __init__(self, use_aws_memory: bool = True):
        self.use_aws_memory = use_aws_memory
        self.local_memories = {}  # Fallback for local development
        
        if use_aws_memory:
            self._setup_aws_memory()
    
    def _setup_aws_memory(self):
        """Setup AWS Bedrock Memory or DynamoDB for persistent storage"""
        try:
            # Try AWS Bedrock Memory first
            self.bedrock_client = boto3.client('bedrock-agent-runtime')
            self.memory_id = "agent_memory-b4w8CzCsaH"  # Your specific memory ID
            # Temporarily disable Bedrock Memory due to API complexity
            self.use_bedrock_memory = False
            logger.info(f"✅ Bedrock Memory configured but using DynamoDB fallback: {self.memory_id}")
        except Exception as e:
            logger.warning(f"⚠️ Bedrock Memory not available, using DynamoDB: {e}")
            self.use_bedrock_memory = False
        
        # Always setup DynamoDB as fallback
        try:
            self.dynamodb = boto3.resource('dynamodb')
            self.memory_table = self.dynamodb.Table('agent-memories')
            logger.info("✅ DynamoDB fallback initialized")
        except Exception as e:
            logger.warning(f"⚠️ DynamoDB not available, using local storage: {e}")
            self.memory_table = None
    
    def store_memory(self, agent_id: str, content: str, memory_type: str, 
                    user_id: Optional[str] = None, importance: float = 0.5,
                    metadata: Optional[Dict] = None, tags: Optional[List[str]] = None) -> str:
        """Store a memory entry"""
        memory_id = str(uuid.uuid4())
        
        entry = MemoryEntry(
            id=memory_id,
            agent_id=agent_id,
            user_id=user_id,
            content=content,
            memory_type=memory_type,
            importance=importance,
            timestamp=datetime.utcnow(),
            metadata=metadata or {},
            tags=tags or []
        )
        
        if self.use_aws_memory and self.use_bedrock_memory:
            self._store_in_bedrock_memory(entry)
        elif self.use_aws_memory:
            self._store_in_dynamodb(entry)
        else:
            self._store_locally(entry)
        
        logger.info(f"💾 Stored memory for {agent_id}: {memory_type}")
        return memory_id
    
    def _store_in_bedrock_memory(self, entry: MemoryEntry):
        """Store in AWS Bedrock Memory"""
        try:
            # Create event in Bedrock Memory
            event_timestamp = entry.timestamp
            
            # Create payload with memory data
            payload = {
                "agent_id": entry.agent_id,
                "user_id": entry.user_id,
                "content": entry.content,
                "memory_type": entry.memory_type,
                "importance": entry.importance,
                "metadata": entry.metadata,
                "tags": entry.tags
            }
            
            # Use agent_id as actor_id and create session_id
            actor_id = entry.agent_id
            session_id = f"session_{entry.user_id or 'default'}_{entry.timestamp.strftime('%Y%m%d')}"
            
            params = {
                "memoryId": self.memory_id,
                "actorId": actor_id,
                "sessionId": session_id,
                "eventTimestamp": event_timestamp,
                "payload": payload,
                "clientToken": str(uuid.uuid4()),
            }
            
            response = self.bedrock_client.create_event(**params)
            event_id = response["event"]["eventId"]
            
            logger.info(f"✅ Stored memory in Bedrock: {event_id}")
            
        except Exception as e:
            logger.error(f"❌ Bedrock Memory storage failed: {e}")
            # Fallback to DynamoDB
            self._store_in_dynamodb(entry)
    
    def _store_in_dynamodb(self, entry: MemoryEntry):
        """Store in DynamoDB"""
        try:
            if self.memory_table is None:
                logger.warning("⚠️ DynamoDB table not available, falling back to local storage")
                self._store_locally(entry)
                return
            
            self.memory_table.put_item(Item={
                'memory_id': entry.id,
                'agent_id': entry.agent_id,
                'user_id': entry.user_id or 'anonymous',
                'content': entry.content,
                'memory_type': entry.memory_type,
                'importance': Decimal(str(entry.importance)),  # Convert float to Decimal
                'timestamp': entry.timestamp.isoformat(),
                'metadata': json.dumps(entry.metadata),
                'tags': entry.tags,
                'ttl': int((datetime.utcnow() + timedelta(days=365)).timestamp())
            })
        except ClientError as e:
            logger.error(f"❌ DynamoDB storage failed: {e}")
            self._store_locally(entry)
    
    def _store_locally(self, entry: MemoryEntry):
        """Store locally for development"""
        if entry.agent_id not in self.local_memories:
            self.local_memories[entry.agent_id] = []
        
        self.local_memories[entry.agent_id].append(entry)
        
        # Keep only last 1000 entries per agent
        if len(self.local_memories[entry.agent_id]) > 1000:
            self.local_memories[entry.agent_id] = self.local_memories[entry.agent_id][-1000:]
    
    def retrieve_memories(self, agent_id: str, memory_type: Optional[str] = None,
                         user_id: Optional[str] = None, limit: int = 50,
                         importance_threshold: float = 0.0) -> List[MemoryEntry]:
        """Retrieve memories for an agent"""
        if self.use_aws_memory and self.use_bedrock_memory:
            return self._retrieve_from_bedrock_memory(agent_id, memory_type, user_id, limit, importance_threshold)
        elif self.use_aws_memory:
            return self._retrieve_from_dynamodb(agent_id, memory_type, user_id, limit, importance_threshold)
        else:
            return self._retrieve_locally(agent_id, memory_type, user_id, limit, importance_threshold)
    
    def _retrieve_from_bedrock_memory(self, agent_id: str, memory_type: Optional[str],
                                     user_id: Optional[str], limit: int, importance_threshold: float) -> List[MemoryEntry]:
        """Retrieve from AWS Bedrock Memory"""
        try:
            # For now, Bedrock Memory doesn't have a direct retrieve API for our use case
            # We'll use the retrieve_and_generate API with a simple query
            session_id = f"session_{user_id or 'default'}_{datetime.utcnow().strftime('%Y%m%d')}"
            
            # Create a simple query to retrieve memories
            query = f"agent_id:{agent_id}"
            if memory_type:
                query += f" memory_type:{memory_type}"
            if user_id:
                query += f" user_id:{user_id}"
            
            params = {
                "input": {
                    "text": query
                },
                "retrieveAndGenerateConfiguration": {
                    "type": "KNOWLEDGE_BASE",
                    "knowledgeBaseConfiguration": {
                        "knowledgeBaseId": self.memory_id,
                        "modelArn": "arn:aws:bedrock:us-east-1::foundation-model/anthropic.claude-3-5-sonnet-20241022-v2:0",
                        "retrievalConfiguration": {
                            "vectorSearchConfiguration": {
                                "numberOfResults": limit
                            }
                        }
                    }
                },
                "sessionId": session_id
            }
            
            response = self.bedrock_client.retrieve_and_generate(**params)
            
            memories = []
            for citation in response.get("citations", []):
                # Extract memory data from citations
                retrieved_references = citation.get("retrievedReferences", [])
                for ref in retrieved_references:
                    content = ref.get("content", {}).get("text", "")
                    
                    # Try to parse the content as JSON to extract our memory data
                    try:
                        memory_data = json.loads(content)
                        entry = MemoryEntry(
                            id=str(uuid.uuid4()),
                            agent_id=memory_data.get("agent_id", agent_id),
                            user_id=memory_data.get("user_id"),
                            content=memory_data.get("content", content),
                            memory_type=memory_data.get("memory_type", "conversation"),
                            importance=memory_data.get("importance", 0.5),
                            timestamp=datetime.fromisoformat(memory_data.get("timestamp", datetime.utcnow().isoformat())),
                            metadata=memory_data.get("metadata", {}),
                            tags=memory_data.get("tags", [])
                        )
                        
                        # Filter by importance threshold and memory type
                        if (entry.importance >= importance_threshold and 
                            (memory_type is None or entry.memory_type == memory_type)):
                            memories.append(entry)
                    except json.JSONDecodeError:
                        # If content is not JSON, create a simple memory entry
                        entry = MemoryEntry(
                            id=str(uuid.uuid4()),
                            agent_id=agent_id,
                            user_id=user_id,
                            content=content,
                            memory_type=memory_type or "conversation",
                            importance=0.5,
                            timestamp=datetime.utcnow(),
                            metadata={},
                            tags=[]
                        )
                        memories.append(entry)
            
            logger.info(f"✅ Retrieved {len(memories)} memories from Bedrock")
            return memories[:limit]
            
        except Exception as e:
            logger.error(f"❌ Bedrock Memory retrieval failed: {e}")
            # Fallback to DynamoDB
            return self._retrieve_from_dynamodb(agent_id, memory_type, user_id, limit, importance_threshold)
    
    def _retrieve_from_dynamodb(self, agent_id: str, memory_type: Optional[str],
                               user_id: Optional[str], limit: int, importance_threshold: float) -> List[MemoryEntry]:
        """Retrieve from DynamoDB"""
        try:
            if self.memory_table is None:
                logger.warning("⚠️ DynamoDB table not available, falling back to local storage")
                return self._retrieve_locally(agent_id, memory_type, user_id, limit, importance_threshold)
            
            # Query by agent_id
            response = self.memory_table.query(
                KeyConditionExpression='agent_id = :agent_id',
                FilterExpression='importance >= :threshold',
                ExpressionAttributeValues={
                    ':agent_id': agent_id, 
                    ':threshold': Decimal(str(importance_threshold))  # Convert float to Decimal
                },
                Limit=limit,
                ScanIndexForward=False  # Most recent first
            )
            
            memories = []
            for item in response['Items']:
                entry = MemoryEntry(
                    id=item['memory_id'],
                    agent_id=item['agent_id'],
                    user_id=item.get('user_id'),
                    content=item['content'],
                    memory_type=item['memory_type'],
                    importance=item['importance'],
                    timestamp=datetime.fromisoformat(item['timestamp']),
                    metadata=json.loads(item.get('metadata', '{}')),
                    tags=item.get('tags', [])
                )
                memories.append(entry)
            
            return memories
            
        except ClientError as e:
            logger.error(f"❌ DynamoDB retrieval failed: {e}")
            return self._retrieve_locally(agent_id, memory_type, user_id, limit, importance_threshold)
    
    def _retrieve_locally(self, agent_id: str, memory_type: Optional[str],
                         user_id: Optional[str], limit: int, importance_threshold: float) -> List[MemoryEntry]:
        """Retrieve from local storage"""
        if agent_id not in self.local_memories:
            return []
        
        memories = self.local_memories[agent_id]
        
        # Filter by criteria
        filtered = []
        for memory in memories:
            if memory_type and memory.memory_type != memory_type:
                continue
            if user_id and memory.user_id != user_id:
                continue
            if memory.importance < importance_threshold:
                continue
            filtered.append(memory)
        
        # Sort by timestamp (most recent first) and limit
        filtered.sort(key=lambda x: x.timestamp, reverse=True)
        return filtered[:limit]
    
    def get_context_window(self, agent_id: str, user_id: Optional[str] = None,
                          conversation_limit: int = 10, knowledge_limit: int = 5) -> ContextWindow:
        """Get context window for agent conversation"""
        
        # Get recent conversations
        recent_conversations = self.retrieve_memories(
            agent_id=agent_id,
            memory_type='conversation',
            user_id=user_id,
            limit=conversation_limit
        )
        
        # Get relevant knowledge
        relevant_knowledge = self.retrieve_memories(
            agent_id=agent_id,
            memory_type='knowledge',
            user_id=user_id,
            limit=knowledge_limit,
            importance_threshold=0.7
        )
        
        # Get user preferences
        user_preferences = self._get_user_preferences(agent_id, user_id)
        
        # Determine current topic from recent conversations
        current_topic = self._extract_current_topic(recent_conversations)
        
        return ContextWindow(
            recent_conversations=recent_conversations,
            relevant_knowledge=relevant_knowledge,
            user_preferences=user_preferences,
            current_topic=current_topic
        )
    
    def _get_user_preferences(self, agent_id: str, user_id: Optional[str]) -> Dict[str, Any]:
        """Get user preferences from memory"""
        if not user_id:
            return {}
        
        preferences = self.retrieve_memories(
            agent_id=agent_id,
            memory_type='preferences',
            user_id=user_id,
            limit=1
        )
        
        if preferences:
            return preferences[0].metadata
        return {}
    
    def _extract_current_topic(self, conversations: List[MemoryEntry]) -> Optional[str]:
        """Extract current topic from recent conversations"""
        if not conversations:
            return None
        
        # Simple topic extraction - in production, use NLP
        recent_content = ' '.join([conv.content for conv in conversations[:3]])
        
        # Extract keywords (simplified)
        keywords = ['mobile', 'database', 'ai', 'cloud', 'frontend', 'backend']
        for keyword in keywords:
            if keyword.lower() in recent_content.lower():
                return keyword
        
        return None
    
    def search_memories(self, agent_id: str, query: str, memory_type: Optional[str] = None,
                       limit: int = 10) -> List[MemoryEntry]:
        """Search memories by content"""
        all_memories = self.retrieve_memories(agent_id, memory_type, limit=1000)
        
        # Simple text search - in production, use vector search
        query_lower = query.lower()
        matching_memories = []
        
        for memory in all_memories:
            if query_lower in memory.content.lower():
                matching_memories.append(memory)
        
        return matching_memories[:limit]
    
    def update_memory_importance(self, memory_id: str, agent_id: str, new_importance: float):
        """Update importance of a memory entry"""
        if self.use_aws_memory and not self.use_bedrock_memory:
            try:
                self.memory_table.update_item(
                    Key={'memory_id': memory_id, 'agent_id': agent_id},
                    UpdateExpression='SET importance = :importance',
                    ExpressionAttributeValues={':importance': new_importance}
                )
            except ClientError as e:
                logger.error(f"❌ Failed to update memory importance: {e}")
        else:
            # Update locally
            if agent_id in self.local_memories:
                for memory in self.local_memories[agent_id]:
                    if memory.id == memory_id:
                        memory.importance = new_importance
                        break
    
    def delete_old_memories(self, agent_id: str, days_old: int = 30):
        """Delete memories older than specified days"""
        cutoff_date = datetime.utcnow() - timedelta(days=days_old)
        
        if self.use_aws_memory and not self.use_bedrock_memory:
            # DynamoDB TTL will handle this automatically
            pass
        else:
            # Delete locally
            if agent_id in self.local_memories:
                self.local_memories[agent_id] = [
                    memory for memory in self.local_memories[agent_id]
                    if memory.timestamp > cutoff_date
                ]
