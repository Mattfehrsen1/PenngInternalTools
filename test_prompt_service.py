#!/usr/bin/env python3
"""
Test script for the new three-layer prompt architecture
"""

import sys
import os
sys.path.append('backend')

from backend.services.prompt_service import prompt_service


def test_prompt_service():
    """Test the prompt service functionality"""
    print("🧪 Testing Three-Layer Prompt Architecture")
    print("=" * 50)
    
    # Test version info
    print("\n1. Testing version info...")
    version_info = prompt_service.get_version_info()
    print(f"Version: {version_info['version']}")
    print(f"Available templates: {version_info['available_templates']}")
    
    # Test available templates
    print("\n2. Testing available templates...")
    templates = prompt_service.get_available_templates()
    print(f"System templates: {templates['system']}")
    print(f"RAG templates: {templates['rag']}")
    
    # Test prompt building with sample data
    print("\n3. Testing prompt building...")
    
    sample_chunks = [
        {
            "text": "Machine learning is a subset of artificial intelligence that focuses on algorithms that learn from data.",
            "source": "AI Handbook Chapter 1",
            "source_type": "document",
            "metadata": {
                "topic_tags": ["AI", "ML"],
                "created": "2025-06-10"
            }
        },
        {
            "text": "Neural networks are inspired by biological neural networks and consist of interconnected nodes.",
            "source": "Neural Networks Guide",
            "source_type": "document", 
            "metadata": {
                "topic_tags": ["neural networks"],
                "created": "2025-06-10"
            }
        }
    ]
    
    # Test default persona
    print("\n3a. Testing default persona...")
    prompt_layers = prompt_service.build_complete_prompt(
        persona_name="AI Helper",
        description="A friendly AI assistant that helps with questions about artificial intelligence",
        user_query="What is machine learning?",
        chunks=sample_chunks,
        persona_type="default"
    )
    
    print("System layer:")
    print(prompt_layers.system[:200] + "...")
    print("\nRAG context layer:")
    print(prompt_layers.rag_context[:200] + "...")
    print("\nUser query:")
    print(prompt_layers.user_query)
    
    # Test technical persona
    print("\n3b. Testing technical persona...")
    tech_prompt_layers = prompt_service.build_complete_prompt(
        persona_name="Dr. Tech Expert",
        description="An expert in machine learning and artificial intelligence with deep technical knowledge",
        user_query="Explain the mathematical foundations of neural networks",
        chunks=sample_chunks,
        persona_type="technical"
    )
    
    print("Technical system layer:")
    print(tech_prompt_layers.system[:200] + "...")
    
    # Test complete prompt formatting
    print("\n4. Testing complete prompt formatting...")
    complete_prompt = prompt_service.format_for_llm(prompt_layers)
    print("Complete prompt (first 300 chars):")
    print(complete_prompt[:300] + "...")
    
    print("\n✅ All tests completed successfully!")
    return True


if __name__ == "__main__":
    try:
        test_prompt_service()
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1) 