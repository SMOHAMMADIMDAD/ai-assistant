import asyncio
from google import genai

from app.config import settings


MODELS = [
    "gemini-3.8-flash",
    "gemini-flash-latest",
    "gemini-flash-lite-latest",
    "gemini-pro-latest",
    "gemini-2.5-flash",
]


async def test_model(client, model):
    print(f"\nTesting: {model}")

    try:
        response = await client.aio.models.generate_content(
            model=model,
            contents="Reply with exactly: MODEL WORKS",
        )

        print("✅ SUCCESS")
        print("Response:", response.text)

    except Exception as e:
        print("❌ FAILED")
        print(type(e).__name__)
        print(e)


async def main():
    client = genai.Client(
        api_key=settings.GOOGLE_API_KEY
    )

    for model in MODELS:
        await test_model(client, model)


if __name__ == "__main__":
    asyncio.run(main())