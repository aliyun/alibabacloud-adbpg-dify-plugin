## AnalyticDB for PostgreSQL (Dify Tools Plugin)

### Introduction

`adbpg-tool` is the **Tools plugin** in this repo. It exposes Alibaba Cloud **AnalyticDB for PostgreSQL** knowledge-base and retrieval capabilities as Dify tools, so you can build workflows for:

- **Knowledge base lifecycle**: list/create KBs, delete documents, check ingestion jobs
- **Data ingestion**: upload documents (auto parse & chunk), upsert custom chunks
- **Retrieval & Q&A**: text retrieval (vector/full-text/hybrid), image retrieval, streaming KB chat
- **Atomic ops**: text embedding, rerank

### Typical use cases

- **Enterprise RAG**: ingest docs → retrieve → rerank → generate
- **Hybrid search**: fuse full-text + vector search (RRF/Weight/Cascaded)
- **Multimodal retrieval**: image-to-image search
- **Offline parsing**: parse into chunks first, then decide how/when to upsert

### Configuration (credentials)

Fill in credentials in Dify plugin settings (schema is defined in `adbpg_tool/provider/adbpg.yaml`):

| Key | Description | Required |
|---|---|---|
| `ANALYTICDB_KEY_ID` | Alibaba Cloud AccessKey ID | Yes |
| `ANALYTICDB_KEY_SECRET` | Alibaba Cloud AccessKey Secret | Yes |
| `ANALYTICDB_REGION_ID` | Region (e.g. `cn-hangzhou`) | Yes |
| `ANALYTICDB_DBINSTANCE_ID` | AnalyticDB for PostgreSQL instance ID (e.g. `gp-xxxxxx`) | Yes |
| `ANALYTICDB_MANAGER_ACCOUNT` | Manager account | Yes |
| `ANALYTICDB_MANAGER_ACCOUNT_PASSWORD` | Manager password | Yes |
| `ANALYTICDB_NAMESPACE` | Namespace (database name) | Yes |
| `ANALYTICDB_NAMESPACE_PASSWORD` | Namespace password | Yes |
| `ANALYTICDB_ENDPOINT` | API endpoint (default is usually fine) | No |

### Tools (source-of-truth list)

Tool names and parameter names below are taken from `adbpg_tool/provider/adbpg.yaml` and `adbpg_tool/tools/*/*.yaml`.

#### Knowledge base management

- **`listKnowledgeBases`**: list all knowledge bases (document collections).
- **`createDocumentCollection`**: create a knowledge base / collection and configure embedding, full-text fields, metadata, indexes, and optional knowledge graph.
  - **Key params**: `knowledgebase`, `embedding_model`, `metadata`, `full_text_retrieval_fields`, `metadata_indices`
  - **Knowledge graph**: when `enable_graph=true`, provide `entity_types` and `relationship_types` (and optionally `llmmodel` / `language`)
- **`deleteDocument`**: delete a document by `file_name`.

#### Ingestion & parsing

- **`uploadDocumentAsync`**: upload a file (URL or local path), parse → chunk → embed → ingest, returns `JobId`.
  - **Key params**: `knowledgebase`, `filename`, `fileurl`
  - **Parsing/chunking**: `document_loader_name`, `text_splitter_name`, `chunksize`, `chunk_overlap`, `separators`, `zh_title_enhance`, `vl_enhance`, `splitter_model`
  - **Dry run**: `dry_run=true` validates parsing/chunking without ingesting
- **`getUploadDocumentJob`**: query an ingest job by `jobid`; `wait_until_finish=true` will poll until completion (every 3s, 30min timeout).
- **`adbpgDocParser`**: parse a file into chunks **without storing**.
- **`upsertChunks`**: upsert your pre-built chunks into a knowledge base.
  - **Key params**: `knowledgebase`, `file_name`, `text_chunks` (JSON array; each item may include `Content` / `Id` / `Metadata` / `Filter`)

#### Retrieval & chat

- **`queryContentText`**: text retrieval with vector/full-text/hybrid, filters, recall window, optional file URL.
  - **Key params**: `knowledgebase`, `query`, `top_k`
  - **Full-text**: `use_full_text_retrieval=true`
  - **Hybrid**: `hybrid_search` = `RRF` / `Weight` / `Cascaded` (plus `hybrid_search_k` / `hybrid_search_alpha`)
  - **Rerank**: `rerank_factor`
- **`queryContentImage`**: image retrieval (image-to-image).
  - **Key params**: `knowledgebase`, `file_name`, `file_url`, `top_k`
- **`chatWithKnowledgeBaseStream`**: retrieval + generation, streaming response.
  - **Key params**: `query`, `llm_model` (optional `knowledgebase`, `top_k`, `use_full_text_retrieval`, `rerank_factor`, `graph_enhance`)

#### Atomic ops

- **`textEmbedding`**: convert texts (JSON array string) into embeddings; optional `embedding_model`, `dimension`.
- **`rerank`**: rerank documents (JSON array string); optional `rerank_model`, `topk`, `return_documents`.

### Suggested workflows

- **Build a KB and chat**: `createDocumentCollection` → `uploadDocumentAsync` → `getUploadDocumentJob(wait_until_finish=true)` → `queryContentText(hybrid_search="RRF")` → `chatWithKnowledgeBaseStream`
- **Parse first, ingest later**: `adbpgDocParser` → enrich `Metadata/Filter` in workflow → `upsertChunks`

### References

- Create AccessKey: `https://www.alibabacloud.com/help/ram/user-guide/create-an-accesskey-pair`
- Console: `https://gpdbnext.console.aliyun.com/gpdb`

