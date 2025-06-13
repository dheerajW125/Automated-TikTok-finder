import http.client

def fetch_tiktok_user_info(unique_id):
    conn = http.client.HTTPSConnection("tiktok-api23.p.rapidapi.com")
    headers = {
        'x-rapidapi-key': "api_key_here",  # Replace with your actual API key",
        'x-rapidapi-host': "host_here"  # Replace with the actual host if needed
    }
    
    # Prepare the path with the uniqueId query parameter
    path = f"/api/user/info-with-region?uniqueId={unique_id}"
    
    conn.request("GET", path, headers=headers)
    res = conn.getresponse()
    data = res.read()
    return data.decode("utf-8")

# Example usage:
# print(fetch_tiktok_user_info("some_tiktok_username"))
