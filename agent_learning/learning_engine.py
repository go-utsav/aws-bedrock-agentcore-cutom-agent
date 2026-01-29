"""
Learning Engine for AI Agent Twins
Handles agent learning from real conversations and style adaptation
"""

import json
import re
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import logging
from collections import Counter
import numpy as np

from .memory_manager import MemoryManager, MemoryEntry
from .style_analyzer import StyleAnalyzer

logger = logging.getLogger(__name__)

@dataclass
class LearningPattern:
    """Pattern learned from conversations"""
    pattern_type: str  # 'communication_style', 'technical_depth', 'response_format'
    pattern_data: Dict[str, Any]
    confidence: float
    sample_size: int
    last_updated: datetime

@dataclass
class AgentPersonality:
    """Agent's learned personality traits"""
    agent_id: str
    communication_style: Dict[str, Any]
    technical_preferences: Dict[str, Any]
    response_patterns: Dict[str, Any]
    learned_phrases: List[str]
    expertise_areas: List[str]
    last_updated: datetime

class LearningEngine:
    """Engine for learning from conversations and adapting agent behavior"""
    
    def __init__(self, memory_manager: MemoryManager):
        self.memory_manager = memory_manager
        self.style_analyzer = StyleAnalyzer()
        self.agent_personalities = {}  # Cache for agent personalities
        self.learning_patterns = {}    # Cache for learning patterns
    
    def learn_from_conversation(self, agent_id: str, user_message: str, 
                               agent_response: str, user_id: Optional[str] = None,
                               conversation_context: Optional[Dict] = None):
        """Learn from a single conversation exchange"""
        
        logger.info(f"🧠 Learning from conversation for {agent_id}")
        
        # Store the conversation in memory
        self.memory_manager.store_memory(
            agent_id=agent_id,
            content=f"User: {user_message}\nAgent: {agent_response}",
            memory_type='conversation',
            user_id=user_id,
            importance=0.7,
            metadata=conversation_context or {}
        )
        
        # Analyze communication patterns
        self._analyze_communication_patterns(agent_id, user_message, agent_response, user_id)
        
        # Update agent personality
        self._update_agent_personality(agent_id, user_message, agent_response, user_id)
        
        # Learn technical preferences
        self._learn_technical_preferences(agent_id, user_message, agent_response)
        
        # Extract and store knowledge
        self._extract_and_store_knowledge(agent_id, user_message, agent_response)
    
    def _analyze_communication_patterns(self, agent_id: str, user_message: str, 
                                      agent_response: str, user_id: Optional[str]):
        """Analyze communication patterns from conversation"""
        
        # Analyze user's communication style
        user_style = self.style_analyzer.analyze_style(user_message)
        
        # Convert StyleAnalysis object to dictionary for JSON serialization
        user_style_dict = {
            'formality_score': user_style.formality_score,
            'technical_depth': user_style.technical_depth,
            'response_length': user_style.response_length,
            'communication_tone': user_style.communication_tone,
            'common_patterns': user_style.common_patterns,
            'personality_traits': user_style.personality_traits
        }
        
        # Store user style preferences
        if user_id:
            self.memory_manager.store_memory(
                agent_id=agent_id,
                content=json.dumps(user_style_dict),
                memory_type='user_style',
                user_id=user_id,
                importance=0.8,
                metadata={'analysis_type': 'communication_style'}
            )
        
        # Analyze response effectiveness (simplified)
        response_effectiveness = self._assess_response_effectiveness(user_message, agent_response)
        
        # Store response pattern
        self.memory_manager.store_memory(
            agent_id=agent_id,
            content=json.dumps({
                'user_style': user_style_dict if user_id else None,
                'response_effectiveness': response_effectiveness,
                'response_length': len(agent_response.split()),
                'technical_terms_used': self._count_technical_terms(agent_response)
            }),
            memory_type='response_pattern',
            user_id=user_id,
            importance=0.6
        )
    
    def _update_agent_personality(self, agent_id: str, user_message: str, 
                                 agent_response: str, user_id: Optional[str]):
        """Update agent personality based on conversation"""
        
        # Get current personality or create new one
        if agent_id not in self.agent_personalities:
            self.agent_personalities[agent_id] = AgentPersonality(
                agent_id=agent_id,
                communication_style={},
                technical_preferences={},
                response_patterns={},
                learned_phrases=[],
                expertise_areas=[],
                last_updated=datetime.utcnow()
            )
        
        personality = self.agent_personalities[agent_id]
        
        # Learn common phrases from user
        user_phrases = self._extract_common_phrases(user_message)
        personality.learned_phrases.extend(user_phrases)
        
        # Update communication style
        personality.communication_style = self._update_communication_style(
            personality.communication_style, user_message, agent_response
        )
        
        # Update technical preferences
        personality.technical_preferences = self._update_technical_preferences(
            personality.technical_preferences, user_message, agent_response
        )
        
        personality.last_updated = datetime.utcnow()
        
        # Store updated personality
        self.memory_manager.store_memory(
            agent_id=agent_id,
            content=json.dumps({
                'communication_style': personality.communication_style,
                'technical_preferences': personality.technical_preferences,
                'learned_phrases': personality.learned_phrases[-10:],  # Last 10 phrases
                'expertise_areas': personality.expertise_areas
            }),
            memory_type='personality_update',
            user_id=user_id,
            importance=0.9
        )
    
    def _learn_technical_preferences(self, agent_id: str, user_message: str, agent_response: str):
        """Learn technical preferences from conversation"""
        
        # Extract technical terms and concepts
        user_tech_terms = self._extract_technical_terms(user_message)
        response_tech_terms = self._extract_technical_terms(agent_response)
        
        # Store technical learning
        if user_tech_terms or response_tech_terms:
            self.memory_manager.store_memory(
                agent_id=agent_id,
                content=json.dumps({
                    'user_tech_terms': user_tech_terms,
                    'response_tech_terms': response_tech_terms,
                    'tech_depth': self._assess_technical_depth(user_message, agent_response)
                }),
                memory_type='technical_learning',
                importance=0.8
            )
    
    def _extract_and_store_knowledge(self, agent_id: str, user_message: str, agent_response: str):
        """Extract and store knowledge from conversation"""
        
        # Extract knowledge snippets
        knowledge_snippets = self._extract_knowledge_snippets(user_message, agent_response)
        
        for snippet in knowledge_snippets:
            self.memory_manager.store_memory(
                agent_id=agent_id,
                content=snippet['content'],
                memory_type='knowledge',
                importance=snippet['importance'],
                metadata=snippet['metadata'],
                tags=snippet['tags']
            )
    
    def get_enhanced_system_prompt(self, agent_id: str, base_prompt: str, 
                                 user_id: Optional[str] = None) -> str:
        """Get enhanced system prompt with learned personality"""
        
        # Get agent personality
        personality = self._get_agent_personality(agent_id)
        
        # Get recent context
        context_window = self.memory_manager.get_context_window(agent_id, user_id)
        
        # Build enhanced prompt
        enhanced_prompt = base_prompt
        
        # Add personality traits
        if personality:
            enhanced_prompt += f"\n\n## Your Learned Personality:\n"
            enhanced_prompt += f"Communication Style: {json.dumps(personality.communication_style)}\n"
            enhanced_prompt += f"Technical Preferences: {json.dumps(personality.technical_preferences)}\n"
            
            if personality.learned_phrases:
                enhanced_prompt += f"Common phrases you use: {', '.join(personality.learned_phrases[-5:])}\n"
        
        # Add recent context
        if context_window.recent_conversations:
            enhanced_prompt += f"\n\n## Recent Context:\n"
            for conv in context_window.recent_conversations[:3]:
                enhanced_prompt += f"- {conv.content[:200]}...\n"
        
        # Add relevant knowledge
        if context_window.relevant_knowledge:
            enhanced_prompt += f"\n\n## Relevant Knowledge:\n"
            for knowledge in context_window.relevant_knowledge[:2]:
                enhanced_prompt += f"- {knowledge.content[:200]}...\n"
        
        # Add current topic context
        if context_window.current_topic:
            enhanced_prompt += f"\n\n## Current Topic: {context_window.current_topic}\n"
        
        return enhanced_prompt
    
    def _get_agent_personality(self, agent_id: str) -> Optional[AgentPersonality]:
        """Get agent personality from memory"""
        
        # Check cache first
        if agent_id in self.agent_personalities:
            return self.agent_personalities[agent_id]
        
        # Load from memory
        personality_memories = self.memory_manager.retrieve_memories(
            agent_id=agent_id,
            memory_type='personality_update',
            limit=1
        )
        
        if personality_memories:
            try:
                data = json.loads(personality_memories[0].content)
                personality = AgentPersonality(
                    agent_id=agent_id,
                    communication_style=data.get('communication_style', {}),
                    technical_preferences=data.get('technical_preferences', {}),
                    response_patterns=data.get('response_patterns', {}),
                    learned_phrases=data.get('learned_phrases', []),
                    expertise_areas=data.get('expertise_areas', []),
                    last_updated=personality_memories[0].timestamp
                )
                self.agent_personalities[agent_id] = personality
                return personality
            except Exception as e:
                logger.error(f"❌ Failed to load personality for {agent_id}: {e}")
        
        return None
    
    def _assess_response_effectiveness(self, user_message: str, agent_response: str) -> float:
        """Assess how effective the agent response was (simplified)"""
        
        # Simple heuristics for response effectiveness
        score = 0.5  # Base score
        
        # Length appropriateness
        user_length = len(user_message.split())
        response_length = len(agent_response.split())
        
        if 0.5 <= response_length / max(user_length, 1) <= 2.0:
            score += 0.2
        
        # Technical depth match
        user_tech_terms = self._count_technical_terms(user_message)
        response_tech_terms = self._count_technical_terms(agent_response)
        
        if user_tech_terms > 0 and response_tech_terms > 0:
            score += 0.2
        
        # Question answering
        if '?' in user_message and ('yes' in agent_response.lower() or 'no' in agent_response.lower()):
            score += 0.1
        
        return min(score, 1.0)
    
    def _count_technical_terms(self, text: str) -> int:
        """Count technical terms in text"""
        tech_terms = [
            'api', 'database', 'server', 'client', 'frontend', 'backend',
            'react', 'node', 'python', 'javascript', 'sql', 'aws', 'cloud',
            'docker', 'kubernetes', 'microservices', 'architecture'
        ]
        
        text_lower = text.lower()
        return sum(1 for term in tech_terms if term in text_lower)
    
    def _extract_common_phrases(self, text: str) -> List[str]:
        """Extract common phrases from text"""
        # Simple phrase extraction - in production, use NLP
        phrases = []
        
        # Extract 2-3 word phrases
        words = text.lower().split()
        for i in range(len(words) - 1):
            phrase = f"{words[i]} {words[i+1]}"
            if len(phrase) > 5:  # Filter out very short phrases
                phrases.append(phrase)
        
        return phrases[:5]  # Return top 5 phrases
    
    def _update_communication_style(self, current_style: Dict, user_message: str, 
                                   agent_response: str) -> Dict:
        """Update communication style based on conversation"""
        
        # Analyze formality
        formality_score = self.style_analyzer._analyze_formality(user_message.lower())
        
        # Update style preferences
        if 'formality' not in current_style:
            current_style['formality'] = []
        
        current_style['formality'].append(formality_score)
        
        # Keep only last 10 scores
        if len(current_style['formality']) > 10:
            current_style['formality'] = current_style['formality'][-10:]
        
        # Calculate average
        current_style['avg_formality'] = np.mean(current_style['formality'])
        
        return current_style
    
    def _update_technical_preferences(self, current_prefs: Dict, user_message: str, 
                                    agent_response: str) -> Dict:
        """Update technical preferences based on conversation"""
        
        # Extract technical terms
        tech_terms = self._extract_technical_terms(user_message)
        
        if 'preferred_terms' not in current_prefs:
            current_prefs['preferred_terms'] = Counter()
        
        for term in tech_terms:
            current_prefs['preferred_terms'][term] += 1
        
        # Keep only top 20 terms
        current_prefs['preferred_terms'] = Counter(dict(current_prefs['preferred_terms'].most_common(20)))
        
        return current_prefs
    
    def _extract_technical_terms(self, text: str) -> List[str]:
        """Extract technical terms from text"""
        tech_terms = [
            'api', 'database', 'server', 'client', 'frontend', 'backend',
            'react', 'node', 'python', 'javascript', 'sql', 'aws', 'cloud',
            'docker', 'kubernetes', 'microservices', 'architecture', 'deployment',
            'scalability', 'performance', 'security', 'authentication', 'authorization'
        ]
        
        text_lower = text.lower()
        found_terms = [term for term in tech_terms if term in text_lower]
        
        return found_terms
    
    def _assess_technical_depth(self, user_message: str, agent_response: str) -> str:
        """Assess technical depth of conversation"""
        user_tech_count = self._count_technical_terms(user_message)
        response_tech_count = self._count_technical_terms(agent_response)
        
        total_tech_terms = user_tech_count + response_tech_count
        
        if total_tech_terms >= 5:
            return 'high'
        elif total_tech_terms >= 2:
            return 'medium'
        else:
            return 'low'
    
    def _extract_knowledge_snippets(self, user_message: str, agent_response: str) -> List[Dict]:
        """Extract knowledge snippets from conversation"""
        snippets = []
        
        # Look for code snippets
        code_pattern = r'```[\s\S]*?```'
        code_matches = re.findall(code_pattern, agent_response)
        
        for code in code_matches:
            snippets.append({
                'content': code,
                'importance': 0.9,
                'metadata': {'type': 'code_snippet'},
                'tags': ['code', 'technical']
            })
        
        # Look for URLs/links
        url_pattern = r'https?://[^\s]+'
        url_matches = re.findall(url_pattern, agent_response)
        
        for url in url_matches:
            snippets.append({
                'content': url,
                'importance': 0.7,
                'metadata': {'type': 'reference_url'},
                'tags': ['reference', 'external']
            })
        
        # Look for technical explanations (simplified)
        if len(agent_response.split()) > 50:  # Substantial response
            snippets.append({
                'content': agent_response[:500] + '...',
                'importance': 0.6,
                'metadata': {'type': 'technical_explanation'},
                'tags': ['explanation', 'technical']
            })
        
        return snippets
