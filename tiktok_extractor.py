import requests
import re
import urllib.parse
import time
import os
from bs4 import BeautifulSoup
from difflib import SequenceMatcher
from urllib.parse import urlparse
from requests.exceptions import RequestException
from profile_matcher import TikTokProfileMatcher
import json
from rapid_api import fetch_tiktok_user_info
import pprint

class TikTokDataExtractor:
    def __init__(self):
        self.api_calls = {"brightdata_search": 0}
        self.metadata_cache = {}
        self.profile_already_processed = set()
        self.system_pages = ["login", "signup", "explore", "tag", "music", "video"]

        # BrightData Proxy config from environment variables or defaults
        self.proxy_host = os.getenv("SERP_HOST", "brd.superproxy.io")
        self.proxy_port = os.getenv("SERP_PORT", "33335")
        self.proxy_user = os.getenv("SERP_USER", "brd-customer-hl_4d770a19-zone-serp_api1")
        self.proxy_pass = os.getenv("SERP_PASSWORD", "05mk0h7h29hh")

    def _get_proxy_session(self):
        session_id = f"session-{int(time.time())}"
        proxy_url = f"http://{self.proxy_user}-{session_id}:{self.proxy_pass}@{self.proxy_host}:{self.proxy_port}"
        return {
            "http": proxy_url,
            "https": proxy_url
        }

    def batch_search_tiktok_profiles(self, name, location="", email=""):
        result = self.single_optimized_search(name, location, email)
        print(result)
        return result['usernames'], result['metadata'], [{
            "query": f"Optimized TikTok query for {name}",
            "usernames": result['usernames'],
            "urls": result['urls']
        }]

    def single_optimized_search(self, name, location="", email=""):
        profile_key = f"{name}_{location}_{email}"
        if profile_key in self.profile_already_processed:
            print(f"[SKIP] Already processed: {name}")
            return self.metadata_cache.get(profile_key, {'usernames': [], 'metadata': {}, 'urls': []})

        self.profile_already_processed.add(profile_key)

        query = f"site:tiktok.com @{name}"
        if location:
            query += f" {location}"
        query += " tiktok"

        print(f"[INFO] Searching TikTok for: {name}")
        self.api_calls["brightdata_search"] += 1

        result = self._search_with_proxy(query, name, location, email)
        self.metadata_cache[profile_key] = result
        return result

    def _search_with_proxy(self, query, name, location, email):
        try:
            search_url = f"https://www.google.com/search?q={urllib.parse.quote_plus(query)}"
            proxies = self._get_proxy_session()
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
            }

            response = requests.get(
                search_url,
                headers=headers,
                proxies=proxies,
                verify=False,
                timeout=30
            )

            response.raise_for_status()
            return self.extract_all_profile_data(response.text, name, location, email)

        except RequestException as e:
            print(f"[ERROR] Proxy connection failed: {e}")
            return {'usernames': [], 'metadata': {}, 'urls': []}

    def extract_all_profile_data(self, html_content, name, location, email):
        soup = BeautifulSoup(html_content, 'html.parser')
        tiktok_profiles = {}
        all_urls = []

        for a in soup.find_all('a', href=True):
            raw_url = a['href']
            
            # Handle Google's redirect format
            if raw_url.startswith("/url?q="):
                raw_url = raw_url[7:]
                raw_url = raw_url.split("&")[0]

            raw_url = urllib.parse.unquote(raw_url)

            # Check for TikTok profile URL
            if "tiktok.com/@" not in raw_url:
                continue

            parsed = urlparse(raw_url)
            username_match = re.search(r'tiktok\.com/@([^/?]+)', raw_url)
            if not username_match:
                continue

            username = username_match.group(1).lower()
            if username in tiktok_profiles:
                continue

            context_text = a.get_text()
            metadata = self.extract_profile_metadata(username, context_text, name, location, email)
            tiktok_profiles[username] = metadata
            all_urls.append(raw_url)

        print(f"[RESULT] Found {len(tiktok_profiles)} TikTok profiles for '{name}'")
        return {
            'usernames': list(tiktok_profiles.keys()),
            'metadata': tiktok_profiles,
            'urls': all_urls
        }

    def extract_profile_metadata(self, username, context_text, name, location, email):
        metadata = {
            "username": username,
            "full_name": "",
            "biography": "",
            "followers": "",
            "likes": "",
            "following": "",
            "is_verified": "false",
            "is_business": "false",
            "public_email": "",
            "location_match": "false",
            "email_match": "false",
            "name_similarity": 0.0,
            "metadata_source": "search_result",
            "search_snippet": context_text[:250],
            "popular_videos": []
        }

        # Check verification (usually appears as a blue checkmark in the text)
        if "verified" in context_text.lower() or "✓" in context_text:
            metadata["is_verified"] = "true"

        # Extract follower count (handling both "Cr" for crore and standard formats)
        follower_match = re.search(r"([\d,.]+Cr\+|[\d,.]+[MK]?\+?)\s*(followers|Followers|Follower|follower)", context_text)
        if follower_match:
            followers = follower_match.group(1)
            # Convert Cr (crore) to millions if needed
            if "Cr" in followers:
                metadata["followers"] = str(float(followers.replace("Cr+", "").replace(",", "")) * 10 + "M")
            else:
                metadata["followers"] = followers.replace("+", "")

        # Extract likes count
        likes_match = re.search(r"([\d,.]+[BMK]?)\s*(Likes|likes|Like|like)", context_text)
        if likes_match:
            metadata["likes"] = likes_match.group(1)

        # Extract popular videos (looking for quoted text that might be video titles)
        video_matches = re.findall(r'"(.*?)"', context_text)
        if video_matches:
            metadata["popular_videos"] = [v for v in video_matches if len(v) > 10][:3]  # Take up to 3 plausible video titles

        # Check for full name (if it appears in format "Name (@username)")
        name_match = re.search(r"([A-Z][a-z]+ [A-Z][a-z]+)\s*\(@", context_text)
        if name_match:
            metadata["full_name"] = name_match.group(1)

        if location and location.lower() in context_text.lower():
            metadata["location_match"] = "true"

        email_match = re.search(r'[\w\.-]+@[\w\.-]+', context_text)
        if email_match:
            metadata["public_email"] = email_match.group(0)

        if email and email.lower() in context_text.lower():
            metadata["email_match"] = "true"

        metadata["name_similarity"] = self.calculate_name_similarity(name, username)

        return metadata

    def calculate_name_similarity(self, input_name, username):
        def normalize(s):
            return re.sub(r'[^a-z0-9]', '', s.lower())

        input_name_norm = normalize(input_name)
        username_norm = normalize(username)
        return round(SequenceMatcher(None, input_name_norm, username_norm).ratio(), 2)


if __name__ == "__main__":
      # Make sure this matches your filename

    extractor = TikTokDataExtractor()
    name_to_search = "Nicci Robinson"
    usernames, metadata, logs = extractor.batch_search_tiktok_profiles(name_to_search)
    print(extractor.batch_search_tiktok_profiles(name_to_search))
    print("\n[TIKTOK PROFILES FOUND]")
    for user in usernames:
        print(f"Profile_url - https://www.tiktok.com/@{user}")
        for key, value in metadata[user].items():
            print(f"  {key}: {value}")
        print()

    # 🔁 Send to Gemini AI for ranking
    matcher = TikTokProfileMatcher()
    gemini_result = matcher.evaluate_profiles_with_gemini(name=name_to_search, location="", usernames_with_metadata=metadata)

    print("\n[🔍 GEMINI AI EVALUATION]")
    gemini_result_json = json.dumps(gemini_result, indent=2)
    print("-----")
    print(gemini_result_json)
    print("----- ")
    payload_data = gemini_result["best_match"]

    print(payload_data)
    result_data = (fetch_tiktok_user_info(payload_data))
    # Assuming your TikTok API JSON is in `json_data`
    data = json.loads(result_data)

    user = data['userInfo']['user']
    stats = data['userInfo']['statsV2']  # Use 'statsV2' for string values
    share = data.get('shareMeta', {})

    extracted = {
        "id": user.get("id"),
        "name": user.get("uniqueId"),
        "uniqueId": user.get("uniqueId"),
        "nickname": user.get("nickname"),
        "email": None,  # Not available in API response
        "verified": user.get("verified"),
        "bioLink": user.get("bioLink", {}).get("link"),
        "privateAccount": user.get("privateAccount"),
        "location": user.get("region"),
        "followerCount": stats.get("followerCount"),
        "followingCount": stats.get("followingCount"),
        "heartCount": stats.get("heartCount"),
        "videoCount": stats.get("videoCount"),
        "diggCount": stats.get("diggCount"),
        "friendCount": stats.get("friendCount"),
        "share_title": share.get("title"),
        "share_desc": share.get("desc"),
        "gemini_best_match": payload_data,
        "confidence_score": gemini_result["confidence_score"],
        "reasoning": gemini_result["reasoning"]
    }

    print(extracted)

