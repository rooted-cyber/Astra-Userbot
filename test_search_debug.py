import asyncio
from utils.search import perform_search

async def test_search():
    print("Testing Google Search...")
    res = await perform_search("paman7647", engines=["google"])
    if res:
        print(f"✅ Google Success via {res.get('instance')}")
        for i, r in enumerate(res.get('results', []), 1):
            print(f"{i}. {r.get('title')}")
    else:
        print("❌ Google Failed")

    print("\nTesting DDG Search...")
    res = await perform_search("telegram", engines=["duckduckgo"])
    if res:
        print(f"✅ DDG Success via {res.get('instance')}")
        for i, r in enumerate(res.get('results', []), 1):
            print(f"{i}. {r.get('title')}")
    else:
        print("❌ DDG Failed")

if __name__ == "__main__":
    asyncio.run(test_search())
