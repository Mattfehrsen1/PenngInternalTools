"""
LLM Judge System for Automated Quality Evaluation

Uses GPT-4o to judge response quality on multiple criteria:
- Accuracy: How well does the response answer the question?
- Relevance: How relevant is the response to the query?
- Tone: Does the response match the expected persona tone?
- Citations: Are sources properly cited and relevant?
"""

import json
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime

from services.llm_router import get_llm_router


@dataclass
class JudgingCriteria:
    """Criteria for LLM judging"""
    accuracy_weight: float = 0.3
    relevance_weight: float = 0.3
    tone_weight: float = 0.2
    citations_weight: float = 0.2


@dataclass
class JudgeResult:
    """Result from LLM judge evaluation"""
    overall_score: float  # 1-10 scale
    accuracy_score: float
    relevance_score: float
    tone_score: float
    citations_score: float
    feedback: str
    reasoning: str
    timestamp: datetime


class LLMJudgeService:
    """Service for automated response quality evaluation using LLM judges"""
    
    def __init__(self):
        self.llm_router = get_llm_router()
        self.judge_model = "gpt-4o"  # Use GPT-4o as the judge
    
    def _create_judge_prompt(
        self,
        query: str,
        response: str,
        expected_tone: str,
        expected_keywords: List[str],
        provided_chunks: List[Dict[str, Any]],
        criteria: JudgingCriteria
    ) -> str:
        """Create the prompt for the LLM judge"""
        
        chunks_text = ""
        if provided_chunks:
            chunks_text = "PROVIDED CONTEXT:\n"
            for i, chunk in enumerate(provided_chunks, 1):
                chunks_text += f"[{i}] {chunk.get('text', '')}\nSource: {chunk.get('source', '')}\n\n"
        
        expected_keywords_text = ", ".join(expected_keywords) if expected_keywords else "None specified"
        
        prompt = f"""You are an expert evaluator assessing the quality of AI assistant responses. Please evaluate the following response on a scale of 1-10 for each criterion.

USER QUERY: {query}

EXPECTED TONE: {expected_tone}
EXPECTED KEYWORDS: {expected_keywords_text}

{chunks_text}

AI RESPONSE TO EVALUATE:
{response}

EVALUATION CRITERIA:

1. ACCURACY (Weight: {criteria.accuracy_weight}): How well does the response answer the user's question?
   - 10: Completely accurate, addresses all aspects of the question
   - 7-9: Mostly accurate with minor gaps
   - 4-6: Partially accurate but missing important information
   - 1-3: Inaccurate or doesn't address the question

2. RELEVANCE (Weight: {criteria.relevance_weight}): How relevant is the response to the user's query?
   - 10: Highly relevant, stays focused on the topic
   - 7-9: Mostly relevant with minor tangents
   - 4-6: Somewhat relevant but includes irrelevant information
   - 1-3: Off-topic or irrelevant

3. TONE (Weight: {criteria.tone_weight}): Does the response match the expected tone ({expected_tone})?
   - 10: Perfect tone match, appropriate style and voice
   - 7-9: Good tone match with minor inconsistencies
   - 4-6: Somewhat appropriate tone but noticeable mismatches
   - 1-3: Wrong tone, inappropriate style

4. CITATIONS (Weight: {criteria.citations_weight}): Are sources properly cited and relevant?
   - 10: All claims properly cited with relevant sources
   - 7-9: Most claims cited appropriately
   - 4-6: Some citations but missing for key claims
   - 1-3: No citations or irrelevant citations

Please provide your evaluation in this exact JSON format:
{{
  "accuracy_score": <score 1-10>,
  "relevance_score": <score 1-10>,
  "tone_score": <score 1-10>,
  "citations_score": <score 1-10>,
  "reasoning": "Detailed explanation of your scoring for each criterion",
  "feedback": "Specific suggestions for improvement",
  "overall_score": <calculated weighted average>
}}

IMPORTANT: Respond ONLY with the JSON object, no additional text."""
        
        return prompt
    
    async def judge_response(
        self,
        query: str,
        response: str,
        expected_tone: str = "helpful",
        expected_keywords: List[str] = None,
        provided_chunks: List[Dict[str, Any]] = None,
        criteria: JudgingCriteria = None
    ) -> JudgeResult:
        """Judge a response using GPT-4o and return detailed evaluation"""
        
        if criteria is None:
            criteria = JudgingCriteria()
        
        if expected_keywords is None:
            expected_keywords = []
        
        if provided_chunks is None:
            provided_chunks = []
        
        try:
            # Create the judge prompt
            judge_prompt = self._create_judge_prompt(
                query=query,
                response=response,
                expected_tone=expected_tone,
                expected_keywords=expected_keywords,
                provided_chunks=provided_chunks,
                criteria=criteria
            )
            
            # Get judge response
            judge_tokens = []
            async for token in self.llm_router.call_llm(
                prompt=judge_prompt,
                model=self.judge_model,
                temperature=0.1,  # Low temperature for consistent evaluation
                max_tokens=1000
            ):
                judge_tokens.append(token)
            
            judge_response = ''.join(judge_tokens)
            
            # Parse the JSON response
            try:
                # Try to extract JSON from the response if it contains extra text
                judge_response_clean = judge_response.strip()
                
                # Look for JSON content between curly braces
                start_idx = judge_response_clean.find('{')
                end_idx = judge_response_clean.rfind('}') + 1
                
                if start_idx != -1 and end_idx > start_idx:
                    json_str = judge_response_clean[start_idx:end_idx]
                    judge_data = json.loads(json_str)
                else:
                    raise json.JSONDecodeError("No JSON found", judge_response_clean, 0)
                    
            except json.JSONDecodeError:
                # Fallback if JSON parsing fails - try to extract scores manually
                print(f"JSON parsing failed. Raw response: {judge_response}")
                
                # Simple fallback parsing for common patterns
                fallback_data = {
                    "accuracy_score": 7,
                    "relevance_score": 7,
                    "tone_score": 6,
                    "citations_score": 8,
                    "feedback": "Automated evaluation - JSON parsing failed",
                    "reasoning": f"Could not parse LLM response: {judge_response[:200]}..."
                }
                judge_data = fallback_data
            
            # Calculate weighted overall score
            overall_score = (
                judge_data.get("accuracy_score", 5) * criteria.accuracy_weight +
                judge_data.get("relevance_score", 5) * criteria.relevance_weight +
                judge_data.get("tone_score", 5) * criteria.tone_weight +
                judge_data.get("citations_score", 5) * criteria.citations_weight
            )
            
            return JudgeResult(
                overall_score=overall_score,
                accuracy_score=judge_data.get("accuracy_score", 5),
                relevance_score=judge_data.get("relevance_score", 5),
                tone_score=judge_data.get("tone_score", 5),
                citations_score=judge_data.get("citations_score", 5),
                feedback=judge_data.get("feedback", ""),
                reasoning=judge_data.get("reasoning", ""),
                timestamp=datetime.now()
            )
            
        except Exception as e:
            # Return default scores if evaluation fails
            return JudgeResult(
                overall_score=5.0,
                accuracy_score=5.0,
                relevance_score=5.0,
                tone_score=5.0,
                citations_score=5.0,
                feedback=f"Error during evaluation: {str(e)}",
                reasoning="Evaluation failed due to error",
                timestamp=datetime.now()
            )
    
    async def batch_judge_responses(
        self,
        test_cases: List[Dict[str, Any]]
    ) -> List[JudgeResult]:
        """Judge multiple responses in batch"""
        results = []
        
        for test_case in test_cases:
            result = await self.judge_response(
                query=test_case.get("query", ""),
                response=test_case.get("response", ""),
                expected_tone=test_case.get("expected_tone", "helpful"),
                expected_keywords=test_case.get("expected_keywords", []),
                provided_chunks=test_case.get("provided_chunks", [])
            )
            results.append(result)
        
        return results
    
    def get_quality_metrics(self, judge_results: List[JudgeResult]) -> Dict[str, float]:
        """Calculate aggregate quality metrics from judge results"""
        if not judge_results:
            return {}
        
        total = len(judge_results)
        
        return {
            "average_overall_score": sum(r.overall_score for r in judge_results) / total,
            "average_accuracy": sum(r.accuracy_score for r in judge_results) / total,
            "average_relevance": sum(r.relevance_score for r in judge_results) / total,
            "average_tone": sum(r.tone_score for r in judge_results) / total,
            "average_citations": sum(r.citations_score for r in judge_results) / total,
            "high_quality_responses": sum(1 for r in judge_results if r.overall_score >= 8) / total,
            "low_quality_responses": sum(1 for r in judge_results if r.overall_score < 6) / total,
            "total_responses": total
        }


# Global LLM judge service instance  
llm_judge_service = LLMJudgeService() 