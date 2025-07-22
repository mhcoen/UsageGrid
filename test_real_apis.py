#!/usr/bin/env python3
"""
Test script to discover real API endpoints and data structures
"""
import os
import sys
import asyncio
import aiohttp
import json
from datetime import datetime

# Add src to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


async def test_openai_endpoints():
    """Test various OpenAI endpoints to find usage data"""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("No OPENAI_API_KEY found")
        return
        
    print("\n=== Testing OpenAI Endpoints ===")
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    # Add org header if available
    org_id = os.getenv("OPENAI_ORG_ID")
    if org_id:
        headers["OpenAI-Organization"] = org_id
    
    endpoints = [
        # Platform/account endpoints
        ("GET", "https://api.openai.com/v1/organization", None),
        ("GET", "https://api.openai.com/v1/organizations", None),
        ("GET", "https://api.openai.com/v1/usage", None),
        ("GET", "https://api.openai.com/v1/dashboard/usage", None),
        ("GET", "https://api.openai.com/v1/billing/usage", None),
        ("GET", "https://api.openai.com/v1/billing/subscription", None),
        ("GET", "https://api.openai.com/v1/credits", None),
        ("GET", "https://api.openai.com/v1/account", None),
        
        # Models endpoint (we know this works)
        ("GET", "https://api.openai.com/v1/models", None),
    ]
    
    async with aiohttp.ClientSession() as session:
        for method, url, data in endpoints:
            try:
                print(f"\nTrying {method} {url}")
                
                kwargs = {"headers": headers}
                if data:
                    kwargs["json"] = data
                
                async with session.request(method, url, **kwargs) as response:
                    status = response.status
                    text = await response.text()
                    
                    print(f"Status: {status}")
                    
                    if status == 200:
                        try:
                            data = json.loads(text)
                            print(f"Success! Response structure:")
                            print(json.dumps(data, indent=2)[:500] + "..." if len(json.dumps(data)) > 500 else json.dumps(data, indent=2))
                        except:
                            print(f"Response: {text[:200]}")
                    else:
                        print(f"Error response: {text[:200]}")
                        
            except Exception as e:
                print(f"Exception: {type(e).__name__}: {e}")


async def test_anthropic_endpoints():
    """Test various Anthropic endpoints to find usage data"""
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("No ANTHROPIC_API_KEY found")
        return
        
    print("\n=== Testing Anthropic Endpoints ===")
    
    headers = {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "Content-Type": "application/json"
    }
    
    endpoints = [
        # Possible usage/billing endpoints
        ("GET", "https://api.anthropic.com/v1/usage", None),
        ("GET", "https://api.anthropic.com/v1/billing", None),
        ("GET", "https://api.anthropic.com/v1/organization/usage", None),
        ("GET", "https://api.anthropic.com/v1/credits", None),
        ("GET", "https://api.anthropic.com/v1/account", None),
        ("GET", "https://api.anthropic.com/v1/dashboard", None),
        
        # Console API endpoints
        ("GET", "https://console.anthropic.com/api/usage", None),
        ("GET", "https://console.anthropic.com/api/billing", None),
    ]
    
    async with aiohttp.ClientSession() as session:
        for method, url, data in endpoints:
            try:
                print(f"\nTrying {method} {url}")
                
                kwargs = {"headers": headers}
                if data:
                    kwargs["json"] = data
                
                async with session.request(method, url, **kwargs) as response:
                    status = response.status
                    text = await response.text()
                    
                    print(f"Status: {status}")
                    
                    if status == 200:
                        try:
                            data = json.loads(text)
                            print(f"Success! Response structure:")
                            print(json.dumps(data, indent=2)[:500] + "..." if len(json.dumps(data)) > 500 else json.dumps(data, indent=2))
                        except:
                            print(f"Response: {text[:200]}")
                    else:
                        print(f"Error response: {text[:200]}")
                        
            except Exception as e:
                print(f"Exception: {type(e).__name__}: {e}")


async def test_openrouter_endpoints():
    """Test OpenRouter endpoints"""
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        print("No OPENROUTER_API_KEY found")
        return
        
    print("\n=== Testing OpenRouter Endpoints ===")
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://llm-cost-monitor.app",
        "X-Title": "LLM Cost Monitor"
    }
    
    endpoints = [
        # Known endpoint
        ("GET", "https://openrouter.ai/api/v1/auth/key", None),
        
        # Possible usage endpoints
        ("GET", "https://openrouter.ai/api/v1/usage", None),
        ("GET", "https://openrouter.ai/api/v1/credits", None),
        ("GET", "https://openrouter.ai/api/v1/billing", None),
    ]
    
    async with aiohttp.ClientSession() as session:
        for method, url, data in endpoints:
            try:
                print(f"\nTrying {method} {url}")
                
                kwargs = {"headers": headers}
                if data:
                    kwargs["json"] = data
                
                async with session.request(method, url, **kwargs) as response:
                    status = response.status
                    text = await response.text()
                    
                    print(f"Status: {status}")
                    
                    if status == 200:
                        try:
                            data = json.loads(text)
                            print(f"Success! Response structure:")
                            print(json.dumps(data, indent=2))
                        except:
                            print(f"Response: {text[:200]}")
                    else:
                        print(f"Error response: {text[:200]}")
                        
            except Exception as e:
                print(f"Exception: {type(e).__name__}: {e}")


async def test_huggingface_endpoints():
    """Test HuggingFace endpoints"""
    api_key = os.getenv("HUGGINGFACE_API_TOKEN") or os.getenv("HF_TOKEN")
    if not api_key:
        print("No HUGGINGFACE_API_TOKEN or HF_TOKEN found")
        return
        
    print("\n=== Testing HuggingFace Endpoints ===")
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    endpoints = [
        # Known endpoint
        ("GET", "https://huggingface.co/api/whoami", None),
        
        # Possible usage/billing endpoints
        ("GET", "https://huggingface.co/api/usage", None),
        ("GET", "https://huggingface.co/api/billing", None),
        ("GET", "https://huggingface.co/api/billing/usage", None),
        ("GET", "https://huggingface.co/api/billing/subscription", None),
        ("GET", "https://huggingface.co/api/credits", None),
        ("GET", "https://huggingface.co/api/compute", None),
    ]
    
    async with aiohttp.ClientSession() as session:
        for method, url, data in endpoints:
            try:
                print(f"\nTrying {method} {url}")
                
                kwargs = {"headers": headers}
                if data:
                    kwargs["json"] = data
                
                async with session.request(method, url, **kwargs) as response:
                    status = response.status
                    text = await response.text()
                    
                    print(f"Status: {status}")
                    
                    if status == 200:
                        try:
                            data = json.loads(text)
                            print(f"Success! Response structure:")
                            print(json.dumps(data, indent=2)[:500] + "..." if len(json.dumps(data)) > 500 else json.dumps(data, indent=2))
                        except:
                            print(f"Response: {text[:200]}")
                    else:
                        print(f"Error response: {text[:200]}")
                        
            except Exception as e:
                print(f"Exception: {type(e).__name__}: {e}")


async def main():
    """Run all tests"""
    print("Testing Real API Endpoints")
    print("=" * 50)
    print(f"Testing at: {datetime.now().isoformat()}")
    
    # Test each provider
    await test_openai_endpoints()
    await test_anthropic_endpoints()
    await test_openrouter_endpoints()
    await test_huggingface_endpoints()
    
    print("\n" + "=" * 50)
    print("Testing complete!")


if __name__ == "__main__":
    asyncio.run(main())