import asyncio
import httpx

from google import genai
from app.config import settings


async def test_gemini():
    print("\n========== GEMINI API ==========")

    try:
        client = genai.Client(api_key=settings.GOOGLE_API_KEY)

        # This tests authentication without depending on one specific model.
        models = await client.aio.models.list()

        count = 0
        print("Available models:")

        async for model in models:
            print(" -", model.name)
            count += 1

            # Don't print hundreds of models.
            if count >= 10:
                break

        print("\n✅ GEMINI API KEY IS WORKING")

    except Exception as e:
        print("\n❌ GEMINI API KEY FAILED")
        print(type(e).__name__)
        print(e)


async def test_google_search():
    print("\n========== GOOGLE SEARCH API ==========")

    url = "https://www.googleapis.com/customsearch/v1"

    params = {
        "key": settings.GOOGLE_SEARCH_API_KEY,
        "cx": settings.GOOGLE_SEARCH_ENGINE_ID,
        "q": "OpenAI",
        "num": 1,
    }

    try:
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.get(url, params=params)

        print("HTTP status:", response.status_code)

        if response.status_code == 200:
            data = response.json()

            print("✅ GOOGLE SEARCH API KEY IS WORKING")
            print("Search results:", len(data.get("items", [])))

            if data.get("items"):
                print("First result:", data["items"][0].get("title"))

        else:
            print("❌ GOOGLE SEARCH API FAILED")
            print(response.text)

    except Exception as e:
        print("❌ GOOGLE SEARCH TEST FAILED")
        print(type(e).__name__)
        print(e)


async def main():
    await test_gemini()
    await test_google_search()


if __name__ == "__main__":
    asyncio.run(main())