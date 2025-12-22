import json
import os
from typing import Any

from alibabacloud_gpdb20160503 import models as gpdb_20160503_models
from alibabacloud_gpdb20160503.client import Client
from darabonba.runtime import RuntimeOptions
from pydantic import BaseModel
from tools.base import logger
from tools.base.api_client import build_client


def normalize_param(value):
    """Normalize parameter value: convert empty strings and empty lists to None."""
    if value is None:
        return None
    if isinstance(value, str):
        return value.strip() if value.strip() else None
    if isinstance(value, list):
        if len(value) == 1 and value[0] == "":
            return None
        return value if len(value) > 0 else None
    return value


def normalize_params(params: dict) -> dict:
    """Normalize all parameters in params dict."""
    return {k: normalize_param(v) for k, v in params.items()}


class AnalyticDBAPIHelperConfig(BaseModel):
    access_key: str
    access_secret: str
    region_id: str
    endpoint: str | None = None
    protocol: str | None = None
    read_timeout: int = 600000
    connect_timeout: int = 600000
    dbinstance_id: str
    manager_account: str
    manager_account_password: str
    namespace: str
    namespace_password: str

    def get_client_params(self) -> dict:
        return {
            "access_key": self.access_key,
            "access_secret": self.access_secret,
            "region_id": self.region_id,
            "endpoint": self.endpoint,
            "protocol": self.protocol,
            "read_timeout": self.read_timeout,
            "connect_timeout": self.connect_timeout,
        }

    def get_client(self) -> Client:
        return build_client(**self.get_client_params())

    @classmethod
    def from_credentials(
        cls, credentials: dict[str, Any]
    ) -> "AnalyticDBAPIHelperConfig":
        return cls(
            access_key=credentials.get("ANALYTICDB_KEY_ID"),
            access_secret=credentials.get("ANALYTICDB_KEY_SECRET"),
            region_id=credentials.get("ANALYTICDB_REGION_ID"),
            endpoint=credentials.get("ANALYTICDB_ENDPOINT"),
            protocol=credentials.get("ANALYTICDB_PROTOCOL"),
            manager_account=credentials.get("ANALYTICDB_MANAGER_ACCOUNT"),
            manager_account_password=credentials.get(
                "ANALYTICDB_MANAGER_ACCOUNT_PASSWORD"
            ),
            namespace=credentials.get("ANALYTICDB_NAMESPACE"),
            namespace_password=credentials.get("ANALYTICDB_NAMESPACE_PASSWORD"),
            dbinstance_id=credentials.get("ANALYTICDB_DBINSTANCE_ID"),
        )


class AnalyticDBAPIHelper:
    def __init__(self, credentials: dict[str, Any]) -> None:
        self.config = AnalyticDBAPIHelperConfig.from_credentials(credentials)
        self.client = self.config.get_client()

    def init(self):
        self.init_vector_database()
        self.ensure_namespace_exists()

    def ensure_namespace_exists(self):
        # Service behavior:
        # if namespace exists, update password according to the new namespace password;
        # if namespace does not exist, create namespace;
        self.create_namespace()

    def describe_namespace(self):
        request = gpdb_20160503_models.DescribeNamespaceRequest(
            dbinstance_id=self.config.dbinstance_id,
            namespace=self.config.namespace,
            manager_account=self.config.manager_account,
            manager_account_password=self.config.manager_account_password,
            region_id=self.config.region_id,
        )
        response = self.client.describe_namespace(request)
        logger.info(f"Describe namespace response: {response.body.to_map()}")
        return response.body.to_map()

    def list_document_collections(self):
        request = gpdb_20160503_models.ListDocumentCollectionsRequest(
            dbinstance_id=self.config.dbinstance_id,
            namespace=self.config.namespace,
            namespace_password=self.config.namespace_password,
            region_id=self.config.region_id,
        )
        response = self.client.list_document_collections(request)
        logger.info(f"List document collections response: {response.body.to_map()}")
        return response.body.to_map()

    def create_namespace(self):
        request = gpdb_20160503_models.CreateNamespaceRequest(
            dbinstance_id=self.config.dbinstance_id,
            namespace=self.config.namespace,
            namespace_password=self.config.namespace_password,
            manager_account=self.config.manager_account,
            manager_account_password=self.config.manager_account_password,
            region_id=self.config.region_id,
        )
        response = self.client.create_namespace(request)
        logger.info(f"Create namespace response: {response.body.to_map()}")
        return response.body.to_map()

    def init_vector_database(self):
        request = gpdb_20160503_models.InitVectorDatabaseRequest(
            dbinstance_id=self.config.dbinstance_id,
            manager_account=self.config.manager_account,
            manager_account_password=self.config.manager_account_password,
            region_id=self.config.region_id,
        )
        response = self.client.init_vector_database(request)
        logger.info(f"Init vector database response: {response.body.to_map()}")
        return response.body.to_map()

    def create_document_collection(
        self,
        knowledgebase: str,
        enable_graph: bool,
        llmmodel: str = None,
        language: str = None,
        entity_types: str = None,
        relationship_types: str = None,
        embedding_model: str = None,
        metadata: str = None,
        full_text_retrieval_fields: str = None,
        parser: str = None,
        metrics: str = None,
        hnsw_m: int = None,
        hnsw_ef_construction: int = None,
        pq_enable: bool = None,
        external_storage: int = None,
        metadata_indices: str = None,
        *args,
        **kwargs,
    ) -> dict:
        # Parse entity_types from comma-separated string to list
        parsed_entity_types = None
        if entity_types and isinstance(entity_types, str):
            parsed_entity_types = [
                t.strip() for t in entity_types.split(",") if t.strip()
            ]
            if not parsed_entity_types:
                parsed_entity_types = None

        # Parse relationship_types from comma-separated string to list
        parsed_relationship_types = None
        if relationship_types and isinstance(relationship_types, str):
            parsed_relationship_types = [
                t.strip() for t in relationship_types.split(",") if t.strip()
            ]
            if not parsed_relationship_types:
                parsed_relationship_types = None

        # Convert hnsw_ef_construction from int to string
        parsed_hnsw_ef_construction = None
        if hnsw_ef_construction is not None:
            parsed_hnsw_ef_construction = str(hnsw_ef_construction)

        # Convert pq_enable from boolean to int
        parsed_pq_enable = None
        if pq_enable is not None:
            parsed_pq_enable = 1 if pq_enable else 0

        request = gpdb_20160503_models.CreateDocumentCollectionRequest(
            collection=knowledgebase,
            namespace=self.config.namespace,
            manager_account=self.config.manager_account,
            manager_account_password=self.config.manager_account_password,
            region_id=self.config.region_id,
            dbinstance_id=self.config.dbinstance_id,
            enable_graph=enable_graph,
            llmmodel=llmmodel,
            language=language,
            entity_types=parsed_entity_types,
            relationship_types=parsed_relationship_types,
            embedding_model=embedding_model,
            metadata=metadata,
            full_text_retrieval_fields=full_text_retrieval_fields,
            parser=parser,
            metrics=metrics,
            hnsw_m=hnsw_m,
            hnsw_ef_construction=parsed_hnsw_ef_construction,
            pq_enable=parsed_pq_enable,
            external_storage=external_storage,
            metadata_indices=metadata_indices,
        )
        response = self.client.create_document_collection(request)
        logger.info(f"Create document collection response: {response.body.to_map()}")
        return response.body.to_map()

    def upload_document_async(
        self,
        knowledgebase: str,
        filename: str,
        fileurl: str,
        chunksize: int = None,
        document_loader_name: str = None,
        metadata: str = None,
        chunk_overlap: int = None,
        separators: str = None,
        dry_run: bool = None,
        zh_title_enhance: bool = None,
        text_splitter_name: str = None,
        vl_enhance: bool = None,
        splitter_model: str = None,
        *args,
        **kwargs,
    ) -> dict:
        # Parse separators from JSON string to list
        parsed_separators = None
        if separators and isinstance(separators, str):
            try:
                parsed_separators = json.loads(separators)
                if not isinstance(parsed_separators, list):
                    raise ValueError(
                        f"separators must be a JSON array, got: {type(parsed_separators).__name__}"
                    )
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSON format for separators: {e}")

        # Convert empty select values to None (Auto option)
        parsed_document_loader_name = (
            document_loader_name if document_loader_name else None
        )
        parsed_text_splitter_name = text_splitter_name if text_splitter_name else None
        parsed_splitter_model = splitter_model if splitter_model else None

        request = gpdb_20160503_models.UploadDocumentAsyncRequest(
            collection=knowledgebase,
            namespace=self.config.namespace,
            namespace_password=self.config.namespace_password,
            dbinstance_id=self.config.dbinstance_id,
            region_id=self.config.region_id,
            file_name=filename,
            file_url=fileurl,
            chunk_size=chunksize,
            document_loader_name=parsed_document_loader_name,
            metadata=metadata,
            chunk_overlap=chunk_overlap,
            separators=parsed_separators,
            dry_run=dry_run,
            zh_title_enhance=zh_title_enhance,
            text_splitter_name=parsed_text_splitter_name,
            vl_enhance=vl_enhance,
            splitter_model=parsed_splitter_model,
        )
        response = self.client.upload_document_async(request)
        logger.info(f"Upload document async response: {response.body.to_map()}")
        return response.body.to_map()

    def upload_document_async_advance(
        self,
        knowledgebase: str,
        filename: str,
        file_path: str,
        chunksize: int = None,
        document_loader_name: str = None,
        metadata: str = None,
        chunk_overlap: int = None,
        separators: str = None,
        dry_run: bool = None,
        zh_title_enhance: bool = None,
        text_splitter_name: str = None,
        vl_enhance: bool = None,
        splitter_model: str = None,
        *args,
        **kwargs,
    ) -> dict:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Local file not found: {file_path}")

        # Parse separators from JSON string to list
        parsed_separators = None
        if separators and isinstance(separators, str):
            try:
                parsed_separators = json.loads(separators)
                if not isinstance(parsed_separators, list):
                    raise ValueError(
                        f"separators must be a JSON array, got: {type(parsed_separators).__name__}"
                    )
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSON format for separators: {e}")

        # Convert empty select values to None (Auto option)
        parsed_document_loader_name = (
            document_loader_name if document_loader_name else None
        )
        parsed_text_splitter_name = text_splitter_name if text_splitter_name else None
        parsed_splitter_model = splitter_model if splitter_model else None

        with open(file_path, "rb") as file_obj:
            request = gpdb_20160503_models.UploadDocumentAsyncAdvanceRequest(
                collection=knowledgebase,
                namespace=self.config.namespace,
                namespace_password=self.config.namespace_password,
                dbinstance_id=self.config.dbinstance_id,
                region_id=self.config.region_id,
                file_name=filename,
                file_url_object=file_obj,
                chunk_size=chunksize,
                document_loader_name=parsed_document_loader_name,
                metadata=metadata,
                chunk_overlap=chunk_overlap,
                separators=parsed_separators,
                dry_run=dry_run,
                zh_title_enhance=zh_title_enhance,
                text_splitter_name=parsed_text_splitter_name,
                vl_enhance=vl_enhance,
                splitter_model=parsed_splitter_model,
            )
            response = self.client.upload_document_async_advance(
                request, RuntimeOptions()
            )
            logger.info(
                f"Upload document async advance response: {response.body.to_map()}"
            )
            return response.body.to_map()

    def get_upload_document_job(
        self, knowledgebase: str, jobid: str, *args, **kwargs
    ) -> dict:
        request = gpdb_20160503_models.GetUploadDocumentJobRequest(
            collection=knowledgebase,
            namespace=self.config.namespace,
            namespace_password=self.config.namespace_password,
            dbinstance_id=self.config.dbinstance_id,
            region_id=self.config.region_id,
            job_id=jobid,
        )
        response = self.client.get_upload_document_job(request)
        logger.info(f"Get upload document job response: {response.body.to_map()}")
        return response.body.to_map()

    def delete_document(
        self, knowledgebase: str, file_name: str, *args, **kwargs
    ) -> dict:
        request = gpdb_20160503_models.DeleteDocumentRequest(
            collection=knowledgebase,
            namespace=self.config.namespace,
            namespace_password=self.config.namespace_password,
            dbinstance_id=self.config.dbinstance_id,
            region_id=self.config.region_id,
            file_name=file_name,
        )
        response = self.client.delete_document(request)
        logger.info(f"Delete document response: {response.body.to_map()}")
        return response.body.to_map()

    def query_content_text(
        self,
        knowledgebase: str,
        query: str,
        top_k: int = None,
        use_full_text_retrieval: bool = None,
        rerank_factor: float = None,
        graph_enhance: bool = None,
        filter: str = None,
        recall_window: str = None,
        metrics: str = None,
        include_vector: bool = None,
        hybrid_search: str = None,
        hybrid_search_k: int = None,
        hybrid_search_alpha: float = None,
        include_metadata_fields: str = None,
        include_file_url: bool = None,
        url_expiration: int = None,
        *args,
        **kwargs,
    ) -> dict:
        # Parse recall_window from comma-separated string to list of integers
        parsed_recall_window = None
        if recall_window and isinstance(recall_window, str):
            parts = [p.strip() for p in recall_window.split(",") if p.strip()]
            if len(parts) != 2:
                raise ValueError(
                    f"recall_window must have exactly 2 comma-separated values, got: {len(parts)}"
                )
            try:
                parsed_recall_window = [int(parts[0]), int(parts[1])]
            except ValueError:
                raise ValueError(
                    f"recall_window values must be integers, got: {recall_window}"
                )

        # Convert empty metrics to None (Auto)
        parsed_metrics = metrics if metrics else None

        # Convert empty hybrid_search to None and build hybrid_search_args
        parsed_hybrid_search = hybrid_search if hybrid_search else None
        parsed_hybrid_search_args = None
        if parsed_hybrid_search == "RRF" and hybrid_search_k is not None:
            parsed_hybrid_search_args = {"RRF": {"k": int(hybrid_search_k)}}
        elif parsed_hybrid_search == "Weight" and hybrid_search_alpha is not None:
            parsed_hybrid_search_args = {
                "Weight": {"alpha": float(hybrid_search_alpha)}
            }

        request = gpdb_20160503_models.QueryContentRequest(
            collection=knowledgebase,
            namespace=self.config.namespace,
            namespace_password=self.config.namespace_password,
            dbinstance_id=self.config.dbinstance_id,
            region_id=self.config.region_id,
            content=query,
            top_k=top_k,
            use_full_text_retrieval=use_full_text_retrieval,
            rerank_factor=rerank_factor,
            graph_enhance=graph_enhance,
            filter=filter,
            recall_window=parsed_recall_window,
            metrics=parsed_metrics,
            include_vector=include_vector,
            hybrid_search=parsed_hybrid_search,
            hybrid_search_args=parsed_hybrid_search_args,
            include_metadata_fields=include_metadata_fields,
            include_file_url=include_file_url,
            url_expiration=url_expiration,
        )
        response = self.client.query_content(request)
        logger.info(f"Query content text response: {response.body.to_map()}")
        return response.body.to_map()

    def query_content_image(
        self,
        knowledgebase: str,
        file_name: str,
        file_url: str,
        top_k: int = None,
        rerank_factor: float = None,
        filter: str = None,
        recall_window: str = None,
        metrics: str = None,
        include_vector: bool = None,
        include_metadata_fields: str = None,
        include_file_url: bool = None,
        url_expiration: int = None,
        *args,
        **kwargs,
    ) -> dict:
        # Parse recall_window from comma-separated string to list of integers
        parsed_recall_window = None
        if recall_window and isinstance(recall_window, str):
            parts = [p.strip() for p in recall_window.split(",") if p.strip()]
            if len(parts) != 2:
                raise ValueError(
                    f"recall_window must have exactly 2 comma-separated values, got: {len(parts)}"
                )
            try:
                parsed_recall_window = [int(parts[0]), int(parts[1])]
            except ValueError:
                raise ValueError(
                    f"recall_window values must be integers, got: {recall_window}"
                )

        # Convert empty metrics to None (Auto)
        parsed_metrics = metrics if metrics else None

        request = gpdb_20160503_models.QueryContentRequest(
            collection=knowledgebase,
            namespace=self.config.namespace,
            namespace_password=self.config.namespace_password,
            dbinstance_id=self.config.dbinstance_id,
            region_id=self.config.region_id,
            file_name=file_name,
            file_url=file_url,
            top_k=top_k,
            rerank_factor=rerank_factor,
            filter=filter,
            recall_window=parsed_recall_window,
            metrics=parsed_metrics,
            include_vector=include_vector,
            include_metadata_fields=include_metadata_fields,
            include_file_url=include_file_url,
            url_expiration=url_expiration,
        )
        response = self.client.query_content(request)
        logger.info(f"Query content image response: {response.body.to_map()}")
        return response.body.to_map()

    def query_content_image_advance(
        self,
        knowledgebase: str,
        file_name: str,
        file_path: str,
        top_k: int = None,
        rerank_factor: float = None,
        filter: str = None,
        recall_window: str = None,
        metrics: str = None,
        include_vector: bool = None,
        include_metadata_fields: str = None,
        include_file_url: bool = None,
        url_expiration: int = None,
        *args,
        **kwargs,
    ) -> dict:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Local file not found: {file_path}")

        # Parse recall_window from comma-separated string to list of integers
        parsed_recall_window = None
        if recall_window and isinstance(recall_window, str):
            parts = [p.strip() for p in recall_window.split(",") if p.strip()]
            if len(parts) != 2:
                raise ValueError(
                    f"recall_window must have exactly 2 comma-separated values, got: {len(parts)}"
                )
            try:
                parsed_recall_window = [int(parts[0]), int(parts[1])]
            except ValueError:
                raise ValueError(
                    f"recall_window values must be integers, got: {recall_window}"
                )

        # Convert empty metrics to None (Auto)
        parsed_metrics = metrics if metrics else None

        with open(file_path, "rb") as file_obj:
            request = gpdb_20160503_models.QueryContentAdvanceRequest(
                collection=knowledgebase,
                namespace=self.config.namespace,
                namespace_password=self.config.namespace_password,
                dbinstance_id=self.config.dbinstance_id,
                region_id=self.config.region_id,
                file_name=file_name,
                file_url_object=file_obj,
                top_k=top_k,
                rerank_factor=rerank_factor,
                filter=filter,
                recall_window=parsed_recall_window,
                metrics=parsed_metrics,
                include_vector=include_vector,
                include_metadata_fields=include_metadata_fields,
                include_file_url=include_file_url,
                url_expiration=url_expiration,
            )
            response = self.client.query_content_advance(request, RuntimeOptions())
            logger.info(
                f"Query content image advance response: {response.body.to_map()}"
            )
            return response.body.to_map()

    def upsert_chunks(
        self,
        knowledgebase: str,
        file_name: str,
        text_chunks: str = None,
        should_replace_file: bool = None,
        allow_insert_with_filter: bool = None,
        filter: str = None,
        *args,
        **kwargs,
    ) -> dict:
        # Parse text_chunks from JSON string to list
        parsed_chunks = None
        if text_chunks and isinstance(text_chunks, str):
            try:
                parsed_chunks = json.loads(text_chunks)
                if not isinstance(parsed_chunks, list):
                    raise ValueError(
                        f"text_chunks must be a JSON array, got: {type(parsed_chunks).__name__}"
                    )
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSON format for text_chunks: {e}")

        chunks = []
        if parsed_chunks:
            for chunk in parsed_chunks:
                if not isinstance(chunk, dict):
                    raise ValueError(
                        f"Each chunk must be a JSON object, got: {type(chunk).__name__}"
                    )
                chunks.append(
                    gpdb_20160503_models.UpsertChunksRequestTextChunks(
                        content=chunk.get("Content"),
                        metadata=chunk.get("Metadata"),
                        filter=chunk.get("Filter"),
                    )
                )

        request = gpdb_20160503_models.UpsertChunksRequest(
            collection=knowledgebase,
            namespace=self.config.namespace,
            namespace_password=self.config.namespace_password,
            dbinstance_id=self.config.dbinstance_id,
            region_id=self.config.region_id,
            file_name=file_name,
            text_chunks=chunks,
            should_replace_file=should_replace_file,
            allow_insert_with_filter=allow_insert_with_filter,
        )
        response = self.client.upsert_chunks(request)
        logger.info(f"Upsert chunks response: {response.body.to_map()}")
        return response.body.to_map()

    def text_embedding(
        self,
        input: str,
        embedding_model: str = None,
        dimension: int = None,
        *args,
        **kwargs,
    ) -> dict:
        # Parse input from JSON string to list
        parsed_input = None
        if input and isinstance(input, str):
            try:
                parsed_input = json.loads(input)
                if not isinstance(parsed_input, list):
                    raise ValueError(
                        f"input must be a JSON array, got: {type(parsed_input).__name__}"
                    )
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSON format for input: {e}")

        request = gpdb_20160503_models.TextEmbeddingRequest(
            dbinstance_id=self.config.dbinstance_id,
            region_id=self.config.region_id,
            input=parsed_input,
            model=embedding_model,
            dimension=dimension,
        )
        response = self.client.text_embedding(request)
        logger.info(f"Text embedding response: {response.body.to_map()}")
        return response.body.to_map()

    def rerank(
        self,
        query: str,
        documents: str,
        rerank_model: str = None,
        topk: int = None,
        return_documents: bool = None,
        max_chunks_per_doc: int = None,
        *args,
        **kwargs,
    ) -> dict:
        # Parse documents from JSON string to list
        parsed_documents = None
        if documents and isinstance(documents, str):
            try:
                parsed_documents = json.loads(documents)
                if not isinstance(parsed_documents, list):
                    raise ValueError(
                        f"documents must be a JSON array, got: {type(parsed_documents).__name__}"
                    )
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSON format for documents: {e}")

        request = gpdb_20160503_models.RerankRequest(
            dbinstance_id=self.config.dbinstance_id,
            region_id=self.config.region_id,
            query=query,
            documents=parsed_documents,
            model=rerank_model,
            top_k=topk,
            return_documents=return_documents,
            max_chunks_per_doc=max_chunks_per_doc,
        )
        response = self.client.rerank(request)
        logger.info(f"Rerank response: {response.body.to_map()}")
        return response.body.to_map()

    def chat_with_knowledge_base_stream(
        self,
        query: str,
        llm_model: str,
        knowledgebase: str = None,
        top_k: int = None,
        use_full_text_retrieval: bool = None,
        rerank_factor: float = None,
        graph_enhance: bool = None,
        prompt: str = None,
        system: str = None,
        max_tokens: int = None,
        presence_penalty: float = None,
        seed: int = None,
        temperature: float = None,
        top_p: float = None,
        *args,
        **kwargs,
    ):
        messages = []
        if system:
            messages.append(
                gpdb_20160503_models.ChatWithKnowledgeBaseStreamRequestModelParamsMessages(
                    role="system", content=system
                )
            )
        messages.append(
            gpdb_20160503_models.ChatWithKnowledgeBaseStreamRequestModelParamsMessages(
                role="user", content=query
            )
        )

        knowledge_params = None
        if knowledgebase:
            source_collection = gpdb_20160503_models.ChatWithKnowledgeBaseStreamRequestKnowledgeParamsSourceCollection(
                collection=knowledgebase,
                namespace=self.config.namespace,
                namespace_password=self.config.namespace_password,
                query_params=gpdb_20160503_models.ChatWithKnowledgeBaseStreamRequestKnowledgeParamsSourceCollectionQueryParams(
                    top_k=top_k,
                    rerank_factor=rerank_factor,
                    use_full_text_retrieval=use_full_text_retrieval,
                    graph_enhance=graph_enhance,
                ),
            )
            knowledge_params = (
                gpdb_20160503_models.ChatWithKnowledgeBaseStreamRequestKnowledgeParams(
                    source_collection=[source_collection], top_k=top_k
                )
            )

        model_params = (
            gpdb_20160503_models.ChatWithKnowledgeBaseStreamRequestModelParams(
                model=llm_model,
                messages=messages,
                max_tokens=max_tokens,
                presence_penalty=presence_penalty,
                seed=seed,
                temperature=temperature,
                top_p=top_p,
            )
        )

        request = gpdb_20160503_models.ChatWithKnowledgeBaseStreamRequest(
            dbinstance_id=self.config.dbinstance_id,
            region_id=self.config.region_id,
            include_knowledge_base_results=True,
            knowledge_params=knowledge_params,
            model_params=model_params,
            prompt_params=prompt,
        )

        logger.info(f"Chat with knowledge base stream request started")
        chunks = self.client.chat_with_knowledge_base_stream_with_sse(
            request, RuntimeOptions()
        )
        return chunks
