import asyncio
from ultrarag.modules.embedding import EmbClient
from ultrarag.modules.database.jiuyuan import JiuyuanVectorStore

async def main():
    encoder=EmbClient(url_or_path="embedding_url")
    vector_store = JiuyuanVectorStore(
        host="localhost",
        port=5432,
        user="postgres",
        password="your_password",
        db_name="your_db",
        encoder=encoder
    )

    collection = "demo_collection"
    await vector_store.create(collection_name=collection, dimension=1024)

    sample_data = [
        {"id": 1, "text": "Apple is a fruit"},
        {"id": 2, "text": "The sky is blue"},
        {"id": 3, "text": "I love pizza"},
    ]

    def extract_text(item):
        return item["text"]

    def report_progress(pct):
        print(f"Insertion progress: {pct:.2f}%")

    await vector_store.insert(
        collection=collection,
        payloads=sample_data,
        func=extract_text,
        callback=report_progress,
        batch_size=1
    )

    print("\nSearch Results:")
    results = await vector_store.search(
        collection=collection,
        query="What color is the sky?",
        topn=3
    )
    for result in results:
        print(f"- {result.content} | Score: {result.score:.4f}")

    await vector_store.remove(collection)
    print("\nCollection removed.")

# Run the example
if __name__ == "__main__":
    asyncio.run(main())