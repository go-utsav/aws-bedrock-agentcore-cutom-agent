"""
Style Analyzer for AI Agent Twins
Analyzes communication patterns and styles from conversations
"""

import re
import json
from typing import Dict, List, Any, Tuple
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

@dataclass
class StyleAnalysis:
    """Analysis of communication style"""
    formality_score: float  # 0.0 (casual) to 1.0 (formal)
    technical_depth: str    # 'low', 'medium', 'high'
    response_length: str    # 'short', 'medium', 'long'
    communication_tone: str # 'friendly', 'professional', 'technical'
    common_patterns: List[str]
    personality_traits: List[str]

class StyleAnalyzer:
    """Analyzes communication style and patterns"""
    
    def __init__(self):
        # Formal language patterns
        self.formal_patterns = [
            r'\b(please|thank you|appreciate|regards|sincerely)\b',
            r'\b(would|could|should|might)\b',
            r'\b(however|therefore|furthermore|moreover)\b',
            r'\b(utilize|implement|facilitate|endeavor)\b'
        ]
        
        # Casual language patterns
        self.casual_patterns = [
            r'\b(hey|hi|hello|yo)\b',
            r'\b(yeah|yep|nope|nah)\b',
            r'\b(cool|awesome|great|nice)\b',
            r'\b(btw|fyi|imo|tbh)\b',
            r'\b(lol|haha|lmao)\b'
        ]
        
        # Technical terms by category
        self.technical_categories = {
            'programming': ['code', 'function', 'variable', 'class', 'method', 'algorithm'],
            'web_dev': ['html', 'css', 'javascript', 'react', 'angular', 'vue'],
            'backend': ['api', 'server', 'database', 'sql', 'nosql', 'rest'],
            'cloud': ['aws', 'azure', 'gcp', 'docker', 'kubernetes', 'deployment'],
            'mobile': ['ios', 'android', 'react native', 'flutter', 'swift', 'kotlin'],
            'ai_ml': ['machine learning', 'neural network', 'model', 'training', 'inference']
        }
        
        # Personality indicators
        self.personality_indicators = {
            'detail_oriented': ['specifically', 'precisely', 'exactly', 'detailed', 'thorough'],
            'collaborative': ['team', 'together', 'collaborate', 'discuss', 'input'],
            'solution_focused': ['solution', 'fix', 'resolve', 'solve', 'address'],
            'creative': ['creative', 'innovative', 'unique', 'different', 'approach'],
            'analytical': ['analyze', 'data', 'metrics', 'measure', 'evaluate']
        }
    
    def analyze_style(self, text: str) -> StyleAnalysis:
        """Analyze communication style from text"""
        
        text_lower = text.lower()
        
        # Analyze formality
        formality_score = self._analyze_formality(text_lower)
        
        # Analyze technical depth
        technical_depth = self._analyze_technical_depth(text_lower)
        
        # Analyze response length
        response_length = self._analyze_response_length(text)
        
        # Analyze communication tone
        communication_tone = self._analyze_communication_tone(text_lower)
        
        # Extract common patterns
        common_patterns = self._extract_common_patterns(text_lower)
        
        # Analyze personality traits
        personality_traits = self._analyze_personality_traits(text_lower)
        
        return StyleAnalysis(
            formality_score=formality_score,
            technical_depth=technical_depth,
            response_length=response_length,
            communication_tone=communication_tone,
            common_patterns=common_patterns,
            personality_traits=personality_traits
        )
    
    def _analyze_formality(self, text: str) -> float:
        """Analyze formality level (0.0 = casual, 1.0 = formal)"""
        
        formal_count = 0
        casual_count = 0
        
        # Count formal patterns
        for pattern in self.formal_patterns:
            formal_count += len(re.findall(pattern, text))
        
        # Count casual patterns
        for pattern in self.casual_patterns:
            casual_count += len(re.findall(pattern, text))
        
        # Calculate formality score
        total_patterns = formal_count + casual_count
        if total_patterns == 0:
            return 0.5  # Neutral if no patterns found
        
        return formal_count / total_patterns
    
    def _analyze_technical_depth(self, text: str) -> str:
        """Analyze technical depth of the text"""
        
        total_tech_terms = 0
        category_counts = {}
        
        # Count technical terms by category
        for category, terms in self.technical_categories.items():
            count = sum(1 for term in terms if term in text)
            category_counts[category] = count
            total_tech_terms += count
        
        # Determine technical depth
        if total_tech_terms >= 5:
            return 'high'
        elif total_tech_terms >= 2:
            return 'medium'
        else:
            return 'low'
    
    def _analyze_response_length(self, text: str) -> str:
        """Analyze response length category"""
        
        word_count = len(text.split())
        
        if word_count <= 20:
            return 'short'
        elif word_count <= 100:
            return 'medium'
        else:
            return 'long'
    
    def _analyze_communication_tone(self, text: str) -> str:
        """Analyze communication tone"""
        
        # Friendly indicators
        friendly_indicators = ['great', 'awesome', 'cool', 'nice', 'good', 'excellent', 'wonderful']
        friendly_count = sum(1 for indicator in friendly_indicators if indicator in text)
        
        # Professional indicators
        professional_indicators = ['please', 'thank you', 'regards', 'sincerely', 'appreciate']
        professional_count = sum(1 for indicator in professional_indicators if indicator in text)
        
        # Technical indicators
        technical_indicators = ['api', 'database', 'server', 'code', 'function', 'algorithm']
        technical_count = sum(1 for indicator in technical_indicators if indicator in text)
        
        # Determine dominant tone
        if technical_count > friendly_count and technical_count > professional_count:
            return 'technical'
        elif professional_count > friendly_count:
            return 'professional'
        else:
            return 'friendly'
    
    def _extract_common_patterns(self, text: str) -> List[str]:
        """Extract common communication patterns"""
        
        patterns = []
        
        # Question patterns
        if '?' in text:
            patterns.append('asks_questions')
        
        # Exclamation patterns
        if '!' in text:
            patterns.append('uses_exclamations')
        
        # List patterns
        if re.search(r'\d+\.\s', text) or re.search(r'[-*]\s', text):
            patterns.append('uses_lists')
        
        # Code patterns
        if '```' in text or re.search(r'`[^`]+`', text):
            patterns.append('includes_code')
        
        # URL patterns
        if re.search(r'https?://', text):
            patterns.append('shares_links')
        
        # Emoji patterns
        if re.search(r'[😀-🙏]', text):
            patterns.append('uses_emojis')
        
        return patterns
    
    def _analyze_personality_traits(self, text: str) -> List[str]:
        """Analyze personality traits from text"""
        
        traits = []
        
        for trait, indicators in self.personality_indicators.items():
            count = sum(1 for indicator in indicators if indicator in text)
            if count >= 2:  # Threshold for trait detection
                traits.append(trait)
        
        return traits
    
    def compare_styles(self, style1: StyleAnalysis, style2: StyleAnalysis) -> Dict[str, Any]:
        """Compare two communication styles"""
        
        return {
            'formality_difference': abs(style1.formality_score - style2.formality_score),
            'technical_depth_match': style1.technical_depth == style2.technical_depth,
            'response_length_match': style1.response_length == style2.response_length,
            'tone_match': style1.communication_tone == style2.communication_tone,
            'common_patterns_overlap': len(set(style1.common_patterns) & set(style2.common_patterns)),
            'personality_traits_overlap': len(set(style1.personality_traits) & set(style2.personality_traits))
        }
    
    def generate_style_adaptation_prompt(self, target_style: StyleAnalysis, 
                                       current_style: StyleAnalysis) -> str:
        """Generate prompt for adapting to target style"""
        
        adaptations = []
        
        # Formality adaptation
        if target_style.formality_score > current_style.formality_score:
            adaptations.append("Use more formal language and professional tone")
        elif target_style.formality_score < current_style.formality_score:
            adaptations.append("Use more casual and friendly language")
        
        # Technical depth adaptation
        if target_style.technical_depth == 'high' and current_style.technical_depth != 'high':
            adaptations.append("Include more technical details and terminology")
        elif target_style.technical_depth == 'low' and current_style.technical_depth != 'low':
            adaptations.append("Use simpler language and fewer technical terms")
        
        # Response length adaptation
        if target_style.response_length == 'long' and current_style.response_length != 'long':
            adaptations.append("Provide more detailed and comprehensive responses")
        elif target_style.response_length == 'short' and current_style.response_length != 'short':
            adaptations.append("Keep responses concise and to the point")
        
        # Tone adaptation
        if target_style.communication_tone != current_style.communication_tone:
            adaptations.append(f"Adopt a {target_style.communication_tone} communication tone")
        
        # Pattern adaptations
        for pattern in target_style.common_patterns:
            if pattern not in current_style.common_patterns:
                if pattern == 'asks_questions':
                    adaptations.append("Ask clarifying questions when appropriate")
                elif pattern == 'uses_lists':
                    adaptations.append("Use bullet points or numbered lists for clarity")
                elif pattern == 'includes_code':
                    adaptations.append("Include code examples when relevant")
        
        if adaptations:
            return "Adapt your communication style: " + "; ".join(adaptations)
        else:
            return "Maintain your current communication style"
    
    def extract_learning_insights(self, conversations: List[str]) -> Dict[str, Any]:
        """Extract learning insights from multiple conversations"""
        
        if not conversations:
            return {}
        
        # Analyze all conversations
        analyses = [self.analyze_style(conv) for conv in conversations]
        
        # Calculate averages
        avg_formality = sum(a.formality_score for a in analyses) / len(analyses)
        
        # Most common technical depth
        tech_depths = [a.technical_depth for a in analyses]
        most_common_tech_depth = max(set(tech_depths), key=tech_depths.count)
        
        # Most common response length
        response_lengths = [a.response_length for a in analyses]
        most_common_response_length = max(set(response_lengths), key=response_lengths.count)
        
        # Most common tone
        tones = [a.communication_tone for a in analyses]
        most_common_tone = max(set(tones), key=tones.count)
        
        # Aggregate patterns
        all_patterns = []
        for analysis in analyses:
            all_patterns.extend(analysis.common_patterns)
        
        common_patterns = list(set(all_patterns))
        
        # Aggregate personality traits
        all_traits = []
        for analysis in analyses:
            all_traits.extend(analysis.personality_traits)
        
        personality_traits = list(set(all_traits))
        
        return {
            'avg_formality': avg_formality,
            'preferred_technical_depth': most_common_tech_depth,
            'preferred_response_length': most_common_response_length,
            'preferred_tone': most_common_tone,
            'common_patterns': common_patterns,
            'personality_traits': personality_traits,
            'conversation_count': len(conversations)
        }
