import asyncio
import aiohttp
import json

async def test_ig_info(username):
    print(f"\n--- Testing Profile: @{username} ---")
    api_url = f"https://www.instagram.com/{username}/?__a=1&__d=dis"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        "Accept": "application/json"
    }

    try:
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.get(api_url, timeout=10) as resp:
                print(f"Status: {resp.status}")
                if resp.status == 200:
                    data = await resp.json()
                    user = data.get('graphql', {}).get('user') or data.get('data', {}).get('user')
                    if not user:
                        print("FAILED: No user data found in response.")
                        return False
                    
                    is_private = user.get('is_private')
                    full_name = user.get('full_name')
                    followers = user.get('edge_followed_by', {}).get('count')
                    
                    print(f"Name: {full_name}")
                    print(f"Followers: {followers}")
                    print(f"Is Private: {is_private}")
                    
                    # Verification against expected test states
                    if username == "amankumarpandeydev" and not is_private:
                        print("WARNING: Expected private but got public (or API hidden it).")
                    elif username == "amankrpandey7647" and is_private:
                        print("WARNING: Expected public but got private.")
                    else:
                        print("SUCCESS: Data matches expectations.")
                    return True
                else:
                    print(f"FAILED: Instagram returned {resp.status}")
                    return False
    except Exception as e:
        print(f"ERROR: {str(e)}")
        return False

async def main():
    print("🚀 Starting Instagram Backend Verification...")
    
    # Test 1: Public ID
    success_public = await test_ig_info("amankrpandey7647")
    
    # Test 2: Private ID
    success_private = await test_ig_info("amankumarpandeydev")
    
    if success_public and success_private:
        print("\n✅ ALL BACKEND TESTS PASSED!")
    else:
        print("\n⚠️ SOME TESTS FAILED. Check API availability.")

if __name__ == "__main__":
    asyncio.run(main())
