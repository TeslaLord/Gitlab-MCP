"""
Test GitLab API connection directly (without MCP server)
This helps diagnose connection issues
"""

import os
import asyncio
import httpx


async def test_gitlab_api():
    """Test direct connection to GitLab API."""
    
    gitlab_url = os.getenv("GITLAB_URL", "https://gitlab.com")
    gitlab_token = os.getenv("GITLAB_TOKEN", "")
    
    print("=" * 80)
    print("GitLab API Connection Test")
    print("=" * 80)
    print()
    print(f"GitLab URL: {gitlab_url}")
    print(f"Token set: {'Yes' if gitlab_token else 'No'}")
    
    if not gitlab_token:
        print()
        print("❌ ERROR: GITLAB_TOKEN is not set!")
        print()
        print("Set it with:")
        print("  PowerShell: $env:GITLAB_TOKEN='your-token-here'")
        print("  CMD: set GITLAB_TOKEN=your-token-here")
        return
    
    print(f"Token preview: {gitlab_token[:15]}...")
    print()
    
    # Test 1: Get current user
    print("=" * 80)
    print("TEST 1: Get Current User Info")
    print("=" * 80)
    
    api_url = f"{gitlab_url.rstrip('/')}/api/v4/user"
    headers = {
        "PRIVATE-TOKEN": gitlab_token,
        "Content-Type": "application/json"
    }
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            print(f"Requesting: {api_url}")
            response = await client.get(api_url, headers=headers)
            
            print(f"Status Code: {response.status_code}")
            print()
            
            if response.status_code == 200:
                user_data = response.json()
                print("✅ SUCCESS! Connected to GitLab")
                print()
                print(f"User: {user_data.get('username')}")
                print(f"Name: {user_data.get('name')}")
                print(f"Email: {user_data.get('email')}")
                print(f"ID: {user_data.get('id')}")
                print()
                
                # Test 2: List projects
                print("=" * 80)
                print("TEST 2: List Projects")
                print("=" * 80)
                
                projects_url = f"{gitlab_url.rstrip('/')}/api/v4/projects?membership=true&per_page=5"
                print(f"Requesting: {projects_url}")
                
                proj_response = await client.get(projects_url, headers=headers)
                print(f"Status Code: {proj_response.status_code}")
                print()
                
                if proj_response.status_code == 200:
                    projects = proj_response.json()
                    print(f"✅ Found {len(projects)} projects (showing first 5)")
                    print()
                    
                    for i, proj in enumerate(projects, 1):
                        print(f"{i}. {proj.get('name')} (ID: {proj.get('id')})")
                        print(f"   Path: {proj.get('path_with_namespace')}")
                        print(f"   URL: {proj.get('web_url')}")
                        print()
                    
                    print("=" * 80)
                    print("✅ ALL TESTS PASSED")
                    print("=" * 80)
                    print()
                    print("Your GitLab connection is working!")
                    print("The issue is likely with how the MCP server is configured.")
                    print()
                else:
                    print(f"❌ Failed to list projects")
                    print(f"Response: {proj_response.text}")
                
            elif response.status_code == 401:
                print("❌ AUTHENTICATION FAILED")
                print()
                print("Your token is invalid or expired.")
                print()
                print("To fix:")
                print(f"1. Go to {gitlab_url}/-/user_settings/personal_access_tokens")
                print("2. Create a new token with 'api' scope")
                print("3. Set it with: $env:GITLAB_TOKEN='your-new-token'")
                
            else:
                print(f"❌ ERROR: Unexpected status code {response.status_code}")
                print()
                print(f"Response: {response.text}")
                
    except httpx.ConnectError as e:
        print(f"❌ CONNECTION ERROR: Cannot connect to {gitlab_url}")
        print()
        print(f"Error: {e}")
        print()
        print("Possible issues:")
        print("1. GitLab server is not running")
        print("2. Wrong URL (check if it should be http:// or https://)")
        print("3. Port is incorrect")
        print("4. Firewall blocking the connection")
        print()
        print(f"Current URL: {gitlab_url}")
        print("Make sure this is correct!")
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_gitlab_api())
