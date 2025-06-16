"""
Automated Testing Framework for Prompt Evaluation

Handles running test cases against different prompt versions and collecting results
for regression testing and A/B testing of prompt variations.
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime
import re

from services.prompt_service import prompt_service
from services.llm_router import get_llm_router
from services.llm_judge_service import llm_judge_service


@dataclass
class TestCase:
    """Individual test case definition"""
    id: str
    category: str
    query: str
    expected_keywords: List[str]
    expected_tone: str
    success_criteria: Dict[str, Any]
    sample_chunks: List[Dict[str, Any]]


@dataclass 
class TestResult:
    """Result of running a single test case"""
    test_id: str
    persona_type: str
    prompt_version: str
    query: str
    response: str
    timestamp: datetime
    llm_judge_score: Optional[float] = None
    keyword_score: Optional[float] = None
    citation_check: Optional[bool] = None
    tone_check: Optional[bool] = None
    overall_score: Optional[float] = None
    passed: Optional[bool] = None
    errors: List[str] = None


@dataclass
class TestSuite:
    """Collection of test cases for a persona type"""
    test_set_name: str
    persona_type: str
    created_at: str
    description: str
    test_cases: List[TestCase]


class TestingService:
    """Service for managing automated prompt testing"""
    
    def __init__(self, tests_base_path: str = "../tests"):
        """Initialize the testing service with configurable test path"""
        # Handle both local development and container environments
        if Path("/app").exists():  # Container environment
            self.tests_base_path = Path("/app/tests")
        else:  # Local development
            current_dir = Path(__file__).parent.parent.parent  # Go up to clone-advisor root
            self.tests_base_path = current_dir / "tests"
        
        self.results_path = self.tests_base_path / "results"
        
        # Create directories if they don't exist
        try:
            self.results_path.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            print(f"Warning: Could not create results directory: {e}")
    
    def load_test_suite(self, persona_type: str) -> Optional[TestSuite]:
        """Load test suite for a specific persona type"""
        try:
            test_file = self.tests_base_path / "prompts" / f"{persona_type}_tests.json"
            with open(test_file, 'r') as f:
                data = json.load(f)
            
            test_cases = []
            for case_data in data["test_cases"]:
                test_cases.append(TestCase(**case_data))
            
            return TestSuite(
                test_set_name=data["test_set_name"],
                persona_type=data["persona_type"],
                created_at=data["created_at"],
                description=data["description"],
                test_cases=test_cases
            )
        except Exception as e:
            print(f"Error loading test suite for {persona_type}: {e}")
            return None
    
    def get_available_test_suites(self) -> List[str]:
        """Get list of available test suites"""
        try:
            test_files = list((self.tests_base_path / "prompts").glob("*_tests.json"))
            return [f.stem.replace("_tests", "") for f in test_files]
        except Exception:
            return []
    
    async def run_single_test(
        self,
        test_case: TestCase,
        persona_name: str = "Test Persona",
        persona_description: str = "A helpful AI assistant for testing",
        persona_type: str = "default"
    ) -> TestResult:
        """Run a single test case and return results"""
        errors = []
        
        try:
            # Build the prompt using the prompt service
            prompt_layers = prompt_service.build_complete_prompt(
                persona_name=persona_name,
                description=persona_description,
                user_query=test_case.query,
                chunks=test_case.sample_chunks,
                persona_type=persona_type
            )
            
            complete_prompt = prompt_service.format_for_llm(prompt_layers)
            
            # Get LLM response
            llm_router = get_llm_router()
            response_tokens = []
            
            async for token in llm_router.call_llm(
                prompt=complete_prompt,
                model="gpt-4o",
                temperature=0.7,
                max_tokens=1000
            ):
                response_tokens.append(token)
            
            response = ''.join(response_tokens)
            
            # Create test result
            result = TestResult(
                test_id=test_case.id,
                persona_type=persona_type,
                prompt_version=prompt_service.get_version_info()["version"],
                query=test_case.query,
                response=response,
                timestamp=datetime.now(),
                errors=errors
            )
            
            # Evaluate the response using both basic evaluation and LLM judge
            await self._evaluate_response(result, test_case)
            
            # Get LLM judge evaluation
            judge_result = await llm_judge_service.judge_response(
                query=test_case.query,
                response=response,
                expected_tone=test_case.expected_tone,
                expected_keywords=test_case.expected_keywords,
                provided_chunks=test_case.sample_chunks
            )
            
            # Add LLM judge scores to result
            result.llm_judge_score = judge_result.overall_score
            
            return result
            
        except Exception as e:
            errors.append(str(e))
            return TestResult(
                test_id=test_case.id,
                persona_type=persona_type,
                prompt_version=prompt_service.get_version_info()["version"],
                query=test_case.query,
                response="",
                timestamp=datetime.now(),
                errors=errors,
                passed=False
            )
    
    async def _evaluate_response(self, result: TestResult, test_case: TestCase):
        """Evaluate the response against test criteria"""
        try:
            # Keyword evaluation
            result.keyword_score = self._evaluate_keywords(result.response, test_case.expected_keywords)
            
            # Citation check
            result.citation_check = self._check_citations(result.response)
            
            # Tone check (basic implementation)
            result.tone_check = self._check_tone(result.response, test_case.expected_tone)
            
            # Calculate overall score
            scores = [s for s in [result.keyword_score, result.citation_check, result.tone_check] if s is not None]
            if scores:
                result.overall_score = sum(scores) / len(scores)
            
            # Determine if test passed
            min_score = test_case.success_criteria.get("min_score", 6) / 10.0  # Convert to 0-1 scale
            result.passed = (result.overall_score or 0) >= min_score
            
        except Exception as e:
            if result.errors is None:
                result.errors = []
            result.errors.append(f"Evaluation error: {str(e)}")
    
    def _evaluate_keywords(self, response: str, expected_keywords: List[str]) -> float:
        """Evaluate how many expected keywords are present in the response"""
        if not expected_keywords:
            return 1.0
        
        response_lower = response.lower()
        found_keywords = sum(1 for keyword in expected_keywords if keyword.lower() in response_lower)
        return found_keywords / len(expected_keywords)
    
    def _check_citations(self, response: str) -> bool:
        """Check if response includes proper citations (basic pattern matching)"""
        citation_pattern = r'\[\d+\]'
        return bool(re.search(citation_pattern, response))
    
    def _check_tone(self, response: str, expected_tone: str) -> float:
        """Basic tone evaluation (simplified implementation)"""
        tone_keywords = {
            "technical": ["implementation", "algorithm", "optimize", "architecture", "performance"],
            "creative": ["imagine", "inspire", "story", "vivid", "compelling"],
            "helpful": ["help", "assist", "recommend", "suggest", "guide"]
        }
        
        keywords = tone_keywords.get(expected_tone, [])
        if not keywords:
            return 1.0  # Default to passing if no tone keywords defined
        
        response_lower = response.lower()
        found = sum(1 for keyword in keywords if keyword in response_lower)
        return min(found / len(keywords), 1.0)
    
    async def run_test_suite(
        self,
        persona_type: str,
        persona_name: str = "Test Persona",
        persona_description: str = "A helpful AI assistant for testing"
    ) -> List[TestResult]:
        """Run all test cases for a persona type"""
        test_suite = self.load_test_suite(persona_type)
        if not test_suite:
            return []
        
        results = []
        for test_case in test_suite.test_cases:
            result = await self.run_single_test(
                test_case,
                persona_name,
                persona_description,
                persona_type
            )
            results.append(result)
        
        # Save results
        await self._save_results(results, persona_type)
        
        return results
    
    async def _save_results(self, results: List[TestResult], persona_type: str):
        """Save test results to file"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{persona_type}_results_{timestamp}.json"
            filepath = self.results_path / filename
            
            # Convert results to dict format
            results_data = {
                "test_run": {
                    "persona_type": persona_type,
                    "timestamp": timestamp,
                    "prompt_version": prompt_service.get_version_info()["version"],
                    "total_tests": len(results),
                    "passed_tests": sum(1 for r in results if r.passed),
                    "failed_tests": sum(1 for r in results if not r.passed)
                },
                "results": [asdict(result) for result in results]
            }
            
            with open(filepath, 'w') as f:
                json.dump(results_data, f, indent=2, default=str)
                
        except Exception as e:
            print(f"Error saving test results: {e}")
    
    def get_test_summary(self, results: List[TestResult]) -> Dict[str, Any]:
        """Generate a summary of test results"""
        if not results:
            return {}
        
        total = len(results)
        passed = sum(1 for r in results if r.passed)
        failed = total - passed
        
        avg_score = sum(r.overall_score or 0 for r in results) / total if total > 0 else 0
        avg_keyword_score = sum(r.keyword_score or 0 for r in results) / total if total > 0 else 0
        
        return {
            "total_tests": total,
            "passed": passed,
            "failed": failed,
            "pass_rate": passed / total if total > 0 else 0,
            "average_score": avg_score,
            "average_keyword_score": avg_keyword_score,
            "test_ids": [r.test_id for r in results],
            "failed_tests": [r.test_id for r in results if not r.passed]
        }


# Global testing service instance
testing_service = TestingService() 