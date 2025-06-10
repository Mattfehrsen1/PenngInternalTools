import os
from typing import AsyncIterator, Dict, Optional, List
from openai import AsyncOpenAI
import anthropic
from anthropic import AsyncAnthropic
import logging
from fastapi import HTTPException
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)

# Global clients for connection reuse
_openai_client = None
_anthropic_client = None

@asynccontextmanager
async def get_openai_client():
    """Get a shared OpenAI client with proper lifecycle management"""
    global _openai_client
    
    if _openai_client is None:
        openai_key = os.getenv("OPENAI_API_KEY")
        if not openai_key:
            raise ValueError("OpenAI API key not found")
        _openai_client = AsyncOpenAI(api_key=openai_key)
    
    try:
        yield _openai_client
    except Exception as e:
        logger.error(f"Error with OpenAI client: {e}")
        raise

@asynccontextmanager
async def get_anthropic_client():
    """Get a shared Anthropic client with proper lifecycle management"""
    global _anthropic_client
    
    if _anthropic_client is None:
        anthropic_key = os.getenv("ANTHROPIC_API_KEY")
        if not anthropic_key:
            raise ValueError("Anthropic API key not found")
        _anthropic_client = AsyncAnthropic(api_key=anthropic_key)
    
    try:
        yield _anthropic_client
    except Exception as e:
        logger.error(f"Error with Anthropic client: {e}")
        raise

class LLMRouter:
    def __init__(self):
        # Check if API keys exist
        self.has_openai = bool(os.getenv("OPENAI_API_KEY"))
        self.has_anthropic = bool(os.getenv("ANTHROPIC_API_KEY"))
        
        if not self.has_openai:
            logger.warning("OpenAI API key not found")
        if not self.has_anthropic:
            logger.warning("Anthropic API key not found")
        
        # Model mapping
        self.model_map = {
            "gpt-4o": "gpt-4o",  # Use actual gpt-4o model
            "gpt-4": "gpt-4",
            "gpt-3.5": "gpt-3.5-turbo",
            "claude-3": "claude-3-opus-20240229",
            "claude-3-opus": "claude-3-opus-20240229",
            "claude-3-sonnet": "claude-3-sonnet-20240229",
            "claude-3-haiku": "claude-3-haiku-20240307"
        }
        
        # Pricing per 1K tokens (input/output)
        self.pricing = {
            "gpt-4-1106-preview": {"input": 0.01, "output": 0.03},
            "gpt-4": {"input": 0.03, "output": 0.06},
            "gpt-3.5-turbo": {"input": 0.0005, "output": 0.0015},
            "claude-3-opus-20240229": {"input": 0.015, "output": 0.075},
            "claude-3-sonnet-20240229": {"input": 0.003, "output": 0.015},
            "claude-3-haiku-20240307": {"input": 0.00025, "output": 0.00125}
        }
    
    async def call_llm(
        self,
        prompt: str,
        model: str = "auto",
        temperature: float = 0.7,
        max_tokens: int = 2000,
        system_prompt: Optional[str] = None
    ) -> AsyncIterator[str]:
        """
        Route LLM calls to appropriate provider and stream responses
        
        Args:
            prompt: User prompt
            model: Model choice or "auto"
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            system_prompt: Optional system prompt
        
        Yields:
            Token strings as they are generated
        """
        # Auto-select model if needed
        if model == "auto":
            model = "gpt-4o"  # Default to GPT-4o for best quality/cost ratio
        
        # Route to appropriate provider
        if model.startswith("gpt"):
            if not self.has_openai:
                raise HTTPException(503, "OpenAI client not configured")
            async for token in self._call_openai(prompt, model, temperature, max_tokens, system_prompt):
                yield token
                
        elif model.startswith("claude"):
            if not self.has_anthropic:
                raise HTTPException(503, "Anthropic client not configured")
            async for token in self._call_anthropic(prompt, model, temperature, max_tokens, system_prompt):
                yield token
        else:
            raise HTTPException(400, f"Unknown model: {model}")
    
    async def _call_openai(
        self,
        prompt: str,
        model: str,
        temperature: float,
        max_tokens: int,
        system_prompt: Optional[str]
    ) -> AsyncIterator[str]:
        """Call OpenAI API and stream response"""
        try:
            actual_model = self.model_map.get(model, model)
            
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            async with get_openai_client() as client:
                stream = await client.chat.completions.create(
                    model=actual_model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    stream=True
                )
                
                async for chunk in stream:
                    if chunk.choices[0].delta.content:
                        yield chunk.choices[0].delta.content
                    
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            raise HTTPException(500, f"OpenAI API error: {str(e)}")
    
    async def _call_anthropic(
        self,
        prompt: str,
        model: str,
        temperature: float,
        max_tokens: int,
        system_prompt: Optional[str]
    ) -> AsyncIterator[str]:
        """Call Anthropic API and stream response"""
        try:
            actual_model = self.model_map.get(model, model)
            
            # Anthropic uses a different message format
            kwargs = {
                "model": actual_model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": temperature,
                "max_tokens": max_tokens,
                "stream": True
            }
            
            if system_prompt:
                kwargs["system"] = system_prompt
            
            async with get_anthropic_client() as client:
                stream = await client.messages.create(**kwargs)
                
                async for chunk in stream:
                    if chunk.type == "content_block_delta":
                        yield chunk.delta.text
                    
        except Exception as e:
            logger.error(f"Anthropic API error: {e}")
            raise HTTPException(500, f"Anthropic API error: {str(e)}")
    
    def estimate_cost(
        self,
        model: str,
        input_tokens: int,
        output_tokens: int
    ) -> Dict[str, float]:
        """
        Estimate cost for a completion
        
        Args:
            model: Model name
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
        
        Returns:
            Dict with cost breakdown
        """
        actual_model = self.model_map.get(model, model)
        
        if actual_model not in self.pricing:
            return {
                "input_cost": 0.0,
                "output_cost": 0.0,
                "total_cost": 0.0,
                "model": model
            }
        
        prices = self.pricing[actual_model]
        input_cost = (input_tokens / 1000) * prices["input"]
        output_cost = (output_tokens / 1000) * prices["output"]
        
        return {
            "input_cost": round(input_cost, 6),
            "output_cost": round(output_cost, 6),
            "total_cost": round(input_cost + output_cost, 6),
            "model": actual_model
        }
    
    async def create_rag_prompt(
        self,
        question: str,
        chunks: List[Dict],
        persona_name: str = "Assistant",
        style: str = "helpful and informative"
    ) -> str:
        """
        Create a RAG prompt with context and citations
        
        Args:
            question: User question
            chunks: Retrieved chunks with metadata
            persona_name: Name of the persona
            style: Speaking style
        
        Returns:
            Formatted prompt
        """
        context_parts = []
        for i, chunk in enumerate(chunks):
            # Extract text from chunk metadata or use the chunk directly
            text = chunk.get("metadata", {}).get("text", chunk.get("text", ""))
            context_parts.append(f"[{i+1}] {text}")
        
        context = "\n\n".join(context_parts)
        
        prompt = f"""You are {persona_name}. Please speak in a {style} manner.

CONTEXT:
{context}

USER QUESTION: {question}

INSTRUCTIONS:
1. Answer the question based on the provided context
2. Cite your sources using [1], [2], etc. format
3. If the context doesn't contain enough information to fully answer the question, say "I don't have enough information in my knowledge to answer that completely"
4. Be concise but thorough

ANSWER:"""
        
        return prompt

# Singleton instance
_llm_router = None

def get_llm_router() -> LLMRouter:
    """Get or create singleton LLM router"""
    global _llm_router
    if _llm_router is None:
        _llm_router = LLMRouter()
    return _llm_router
