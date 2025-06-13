import requests
import time
import os
from requests.exceptions import RequestException

def test_brightdata_proxy():
    """Test BrightData SERP proxy connectivity"""
    
    # BrightData proxy configuration
    proxy_host = os.getenv("SERP_HOST", "brd.superproxy.io")
    proxy_port = os.getenv("SERP_PORT", "33335")
    proxy_user = os.getenv("SERP_USER", "brd-customer-hl_4d770a19-zone-serp_api1")
    proxy_pass = os.getenv("SERP_PASSWORD", "05mk0h7h29hh")
    
    # Create session ID
    session_id = f"session-rand{int(time.time())}"
    proxy_url = f"http://{proxy_user}-{session_id}:{proxy_pass}@{proxy_host}:{proxy_port}"
    
    proxies = {
        "http": proxy_url,
        "https": proxy_url
    }
    
    print("Testing BrightData Proxy...")
    print(f"Proxy Host: {proxy_host}")
    print(f"Proxy Port: {proxy_port}")
    print(f"Session ID: {session_id}")
    print("-" * 50)
    
    try:
        # Test with a simple Google search
        test_url = "https://www.google.com/search"
        params = {
            "q": "test query",
            "num": 5
        }
        
        print("Sending test request...")
        response = requests.get(
            test_url,
            params=params,
            proxies=proxies,
            verify=False,
            timeout=30
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        print(f"Response Length: {len(response.text)} characters")
        print("-" * 50)
        
        if response.status_code == 200:
            print("✅ PROXY TEST SUCCESSFUL!")
            print("First 500 characters of response:")
            print(response.text[:500])
        else:
            print("❌ PROXY TEST FAILED!")
            print("Response content:")
            print(response.text[:1000])
            
    except RequestException as e:
        print("❌ PROXY CONNECTION FAILED!")
        print(f"Error: {e}")
    except Exception as e:
        print("❌ UNEXPECTED ERROR!")
        print(f"Error: {e}")

if __name__ == "__main__":
    test_brightdata_proxy()