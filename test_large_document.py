#!/usr/bin/env python3
"""
Test with a larger document to verify chunking and progress
"""
import asyncio
import httpx
import time

async def test_large_document():
    """Test with a document that will create multiple chunks"""
    
    print("🧪 Testing Large Document Processing")
    print("=" * 50)
    
    # API configuration
    base_url = "http://localhost:8000"
    
    # Test credentials
    username = "demo"
    password = "demo123"
    
    # Create a large test document (should generate multiple chunks)
    large_content = """
    COMPREHENSIVE BUSINESS STRATEGY GUIDE
    
    Chapter 1: Market Analysis and Research
    Understanding your market is crucial for business success. Market analysis involves studying industry trends, customer behavior, competitive landscape, and economic factors that could impact your business. This process helps identify opportunities and threats in the market environment.
    
    Market research should be an ongoing process, not a one-time activity. Regular analysis of customer feedback, sales data, and market trends provides valuable insights for strategic decision-making. Companies that invest in thorough market research are better positioned to make informed decisions and adapt to changing market conditions.
    
    Chapter 2: Customer Segmentation and Targeting
    Effective customer segmentation is the foundation of successful marketing strategies. By dividing your market into distinct groups based on demographics, psychographics, behavior patterns, and needs, you can develop targeted approaches that resonate with specific customer segments.
    
    Customer personas are detailed profiles of your ideal customers within each segment. These personas should include demographic information, pain points, goals, preferences, and buying behaviors. Well-developed personas guide product development, marketing messaging, and customer service strategies.
    
    Chapter 3: Value Proposition Development
    Your value proposition is what sets you apart from competitors and explains why customers should choose your product or service. A strong value proposition clearly communicates the unique benefits you offer and addresses specific customer pain points.
    
    Developing an effective value proposition requires deep understanding of customer needs, competitive analysis, and clear articulation of your unique strengths. The best value propositions are specific, measurable, and directly tied to customer outcomes.
    
    Chapter 4: Marketing and Sales Strategy
    Integrated marketing and sales strategies align your entire organization around customer acquisition and retention goals. This alignment ensures consistent messaging across all customer touchpoints and maximizes the effectiveness of your marketing investments.
    
    Digital marketing channels offer unprecedented opportunities for targeted customer engagement. Social media, content marketing, email campaigns, and search engine optimization can work together to create comprehensive customer acquisition funnels.
    
    Chapter 5: Operational Excellence
    Operational excellence involves continuously improving your business processes to deliver maximum value to customers while minimizing waste and inefficiency. This requires systematic analysis of workflows, technology optimization, and employee training programs.
    
    Process automation can significantly improve operational efficiency and reduce human error. However, automation should be implemented thoughtfully, with consideration for employee impact and customer experience implications.
    
    Chapter 6: Financial Management and Growth
    Sound financial management is essential for sustainable business growth. This includes cash flow management, budgeting, financial reporting, and strategic investment decisions. Regular financial analysis helps identify trends and potential issues before they become critical problems.
    
    Growth strategies should be carefully planned and executed with adequate financial resources and risk management considerations. Rapid growth without proper financial controls can lead to cash flow problems and operational challenges.
    
    Chapter 7: Leadership and Team Development
    Strong leadership is critical for business success. Effective leaders inspire their teams, communicate vision clearly, and create environments where employees can thrive and contribute their best work.
    
    Team development involves ongoing training, skill building, and career advancement opportunities. Companies that invest in their people typically see higher employee satisfaction, lower turnover, and better business results.
    
    Chapter 8: Technology and Innovation
    Technology adoption should align with business objectives and customer needs. The most successful technology implementations solve real business problems and provide measurable value to the organization.
    
    Innovation requires a culture that encourages experimentation, learning from failure, and continuous improvement. Organizations that foster innovation are better positioned to adapt to changing market conditions and emerging opportunities.
    
    Chapter 9: Risk Management and Compliance
    Comprehensive risk management identifies potential threats to your business and develops strategies to mitigate those risks. This includes operational risks, financial risks, regulatory compliance, and cybersecurity considerations.
    
    Regular risk assessments should be conducted to identify new threats and evaluate the effectiveness of existing risk mitigation strategies. Business continuity planning ensures your organization can continue operating during unexpected disruptions.
    
    Chapter 10: Measuring Success and Continuous Improvement
    Key performance indicators (KPIs) should align with your business objectives and provide actionable insights for decision-making. Regular monitoring of these metrics helps track progress toward goals and identify areas for improvement.
    
    Continuous improvement is an ongoing process of evaluating performance, identifying opportunities for enhancement, and implementing changes. Organizations that embrace continuous improvement are more agile and better able to respond to market changes.
    
    Conclusion: Implementing Comprehensive Business Strategy
    Successful business strategy implementation requires commitment, resources, and ongoing attention from leadership. The strategies outlined in this guide provide a framework for building a resilient, profitable business that can adapt to changing market conditions while delivering consistent value to customers.
    
    Remember that business strategy is not a one-time exercise but an ongoing process of analysis, planning, implementation, and adjustment. Regular strategy reviews ensure your business remains aligned with market opportunities and customer needs.
    """
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        # 1. Login
        print("\n1. Logging in...")
        login_response = await client.post(
            f"{base_url}/auth/login",
            data={"username": username, "password": password}
        )
        
        if login_response.status_code != 200:
            print(f"❌ Login failed: {login_response.status_code}")
            return
        
        auth_data = login_response.json()
        token = auth_data["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        print(f"✅ Logged in successfully")
        
        # 2. Get personas
        print("\n2. Getting personas...")
        personas_response = await client.get(
            f"{base_url}/personas/list",
            headers=headers
        )
        
        if personas_response.status_code != 200:
            print(f"❌ Failed to get personas: {personas_response.status_code}")
            return
        
        personas = personas_response.json()
        if not personas.get("personas"):
            print("❌ No personas found")
            return
        
        persona_list = personas["personas"]
        persona_id = persona_list[0]["id"]
        persona_name = persona_list[0]["name"]
        print(f"✅ Using persona: {persona_name} (ID: {persona_id})")
        
        # 3. Upload large document
        print(f"\n3. Uploading large document ({len(large_content)} characters)...")
        files = [
            ("files", ("business_strategy_guide.txt", large_content.encode(), "text/plain"))
        ]
        
        upload_response = await client.post(
            f"{base_url}/personas/{persona_id}/files",
            headers=headers,
            files=files
        )
        
        if upload_response.status_code != 201:
            print(f"❌ Upload failed: {upload_response.status_code}")
            print(f"Response: {upload_response.text}")
            return
        
        upload_data = upload_response.json()
        job_id = upload_data["id"]
        print(f"✅ Upload successful, job ID: {job_id}")
        
        # 4. Monitor progress
        print("\n4. Monitoring processing status...")
        max_attempts = 60  # 2 minutes timeout
        attempt = 0
        
        while attempt < max_attempts:
            await asyncio.sleep(2)
            
            status_response = await client.get(
                f"{base_url}/personas/{persona_id}/files/{job_id}/status",
                headers=headers
            )
            
            if status_response.status_code != 200:
                print(f"❌ Status check failed: {status_response.status_code}")
                return
            
            status_data = status_response.json()
            progress = status_data.get("progress", 0)
            status = status_data.get("status", "unknown")
            message = status_data.get("message", "")
            
            print(f"   Progress: {progress}% - {message}")
            
            if status == "completed":
                chunks = status_data.get("chunks", 0)
                print(f"\n✅ Processing completed successfully!")
                print(f"   Created {chunks} chunks from the document")
                
                if chunks > 1:
                    print(f"🎉 SUCCESS: Large document created {chunks} chunks as expected!")
                else:
                    print(f"⚠️  WARNING: Expected multiple chunks, got {chunks}")
                
                return
            
            elif status == "failed":
                print(f"\n❌ Processing failed: {message}")
                return
            
            attempt += 1
        
        print("\n❌ Timeout: Processing did not complete within expected time")

if __name__ == "__main__":
    asyncio.run(test_large_document()) 