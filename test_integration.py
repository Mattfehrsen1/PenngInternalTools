#!/usr/bin/env python3
"""
Clone Advisor Backend Integration Test

This script verifies that the backend APIs are properly integrated
and ready for the frontend to connect.
"""

import asyncio
import json
from pathlib import Path
import sys

# Add backend to path
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

async def test_integration():
    """Test key integration points"""
    
    print("🚀 Clone Advisor Backend Integration Test")
    print("=" * 50)
    
    try:
        # Test 1: Import main app
        print("1. Testing app imports...")
        from main import app
        print("   ✅ FastAPI app imports successfully")
        
        # Test 2: Check route registration
        print("\n2. Testing route registration...")
        routes = [str(route.path) for route in app.routes if hasattr(route, 'path')]
        
        expected_routes = [
            "/api/personas/{persona_id}/prompts",
            "/api/personas/{persona_id}/files", 
            "/api/personas/templates",
            "/persona/list"
        ]
        
        for expected in expected_routes:
            # Check if any route matches the pattern (ignoring path parameters)
            base_route = expected.replace("{persona_id}", "").replace("//", "/")
            if any(base_route in route for route in routes):
                print(f"   ✅ {expected}")
            else:
                print(f"   ❌ {expected}")
        
        # Test 3: Template loading
        print("\n3. Testing template system...")
        from services.persona_prompt_service import persona_prompt_service
        
        templates = await persona_prompt_service.get_available_templates()
        if templates:
            print(f"   ✅ Found {len(templates)} templates:")
            for template in templates:
                print(f"      - {template['name']}")
        else:
            print("   ❌ No templates found")
        
        # Test 4: Check template content
        print("\n4. Testing template content...")
        templates_dir = Path(__file__).parent / "prompts" / "templates"
        if templates_dir.exists():
            for template_dir in templates_dir.iterdir():
                if template_dir.is_dir():
                    required_files = ["system.txt", "rag.txt", "user.txt", "metadata.json"]
                    missing = []
                    for req_file in required_files:
                        if not (template_dir / req_file).exists():
                            missing.append(req_file)
                    
                    if missing:
                        print(f"   ❌ {template_dir.name}: Missing {missing}")
                    else:
                        print(f"   ✅ {template_dir.name}: All files present")
        
        # Test 5: Document API import
        print("\n5. Testing document API...")
        try:
            from api.documents import router as doc_router
            print("   ✅ Documents API imports successfully")
        except Exception as e:
            print(f"   ❌ Documents API import failed: {e}")
        
        print("\n" + "=" * 50)
        print("🎉 INTEGRATION TEST COMPLETE!")
        print("\nNext steps:")
        print("1. Start backend: cd backend && uvicorn main:app --reload")
        print("2. Start frontend: cd frontend && npm run dev") 
        print("3. Test /prompts/{persona} and /files/{persona} pages")
        print("\n📝 See INTEGRATION_STATUS.md for full details")
        
    except Exception as e:
        print(f"\n❌ Integration test failed: {e}")
        print(f"Error details: {type(e).__name__}: {str(e)}")
        return False
    
    return True

if __name__ == "__main__":
    success = asyncio.run(test_integration())
    sys.exit(0 if success else 1) 