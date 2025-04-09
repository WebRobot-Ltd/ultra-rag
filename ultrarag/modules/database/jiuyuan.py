import asyncio
from typing import Any, Callable, Dict, List, Optional, Union

from jiuyuan_db.vector.sdk import Record
from jiuyuan_db.vector.sdk.client import JiuyuanVector

from ultrarag.modules.database import BaseIndex, BaseNode
from ultrarag.modules.embedding import BaseEmbedding


class JiuyuanVectorStore(BaseIndex):
    def __init__(
            self,
            host: str,
            port: int,
            user: str,
            password: str,
            db_name: str,
            encoder: BaseEmbedding,
    ) -> None:
        """
        Initialize the vector store by creating a JiuyuanVector client.

        Args:
            host (str): Database host.
            port (int): Database port.
            user (str): Database user.
            password (str): Database password.
            db_name (str): Database name.
            encoder (BaseEmbedding): Encoder used to generate document embeddings.
        """
        super().__init__()
        self.encoder = encoder
        self.client = JiuyuanVector(
            host=host,
            port=port,
            user=user,
            password=password,
            db_name=db_name,
        )

    async def create(
            self, collection_name: str, dimension: int = 1024, index_type: str = "dense", **kwargs
    ) -> None:
        """
        Create a new vector collection with the specified dimension.

        Args:
            collection_name (str): Name of the collection.
            dimension (int): Embedding dimension for the collection.
            index_type (str): Type of vector indexing ('dense' or 'hybrid'). (Currently unused.)
            **kwargs: Additional keyword arguments.
        """
        await self.client.create_table(collection_name, dimension)

    async def insert(
            self,
            collection: str,
            payloads: List[Dict[str, Any]],
            func: Callable = lambda x: x,
            method: str = "dense",
            callback: Optional[Callable[[float], None]] = None,
            batch_size: int = 10,
    ) -> None:
        """
        Insert data into the vector database while reporting progress via a callback.

        Args:
            collection (str): Collection name.
            payloads (List[Dict[str, Any]]): List of dictionaries containing data to insert.
            func (Callable): Function to extract text content from each payload.
            method (str): Vector indexing method, e.g., 'dense' or 'hybrid'.
            callback (Optional[Callable]): Callback function for reporting insertion progress.
            batch_size (int): Number of records to insert per batch.
        """
        # Extract text content and encode embeddings.
        contents = [func(item) for item in payloads]
        data_embeddings = await self.encoder.document_encode(contents)
        if len(data_embeddings) != len(payloads):
            raise ValueError("Embedding count does not match payload count.")

        # Create Record instances from the provided data.
        records = [
            Record.from_text(text=content, embedding=embed, meta=payload)
            for content, payload, embed in zip(contents, payloads, data_embeddings)
        ]

        total_records = len(records)
        # Batch insertion and progress reporting.
        for i in range(0, total_records, batch_size):
            batch = records[i: i + batch_size]
            await self.client.insert(collection, batch)
            progress = (i + len(batch)) / total_records * 100.0
            if callback:
                callback(progress)

    async def search(
            self,
            collection: Union[str, List[str]],
            query: str,
            topn: int = 5,
            method: str = "dense",
            **kwargs,
    ) -> List[BaseNode]:
        """
        Search the vector database for similar records.

        Args:
            collection (Union[str, List[str]]): Collection name or a list of collection names.
            query (str): Query text.
            topn (int): Number of top results to return.
            method (str): Vector indexing method.
            **kwargs: Additional keyword arguments.

        Returns:
            List[Any]: A list of BaseNode objects containing content, score, and payload.
        """
        # Encode the query into an embedding
        query_embedding = await self.encoder.query_encode(query)

        # If collection is a list, execute search for each collection concurrently.
        if isinstance(collection, list):
            # Launch searches concurrently across the specified collections.
            results_list = await asyncio.gather(
                *(self.client.search(coll, query_embedding, top_k=topn) for coll in collection)
            )
            # Flatten the list of results
            all_results = [item for sublist in results_list for item in sublist]
            # Sort the aggregated results by distance (assumed lower is better)
            all_results.sort(key=lambda x: x[1])
            # Select only the top N overall
            results = all_results[:topn]
        else:
            # For a single collection, perform a normal search.
            results = await self.client.search(collection, query_embedding, top_k=topn)

        # Create the response as a list of BaseNode objects.
        response_result = [
            BaseNode(content=record.text, score=distance, payload=record.to_dict())
            for record, distance in results
        ]
        return response_result

    async def remove(self, collection: Union[str, List[str]]) -> None:
        """
        Remove (drop) the specified collection from the database.

        Args:
            collection (Union[str, List[str]]): Name of the collection to remove.
        """
        await self.client.drop_table(collection)

