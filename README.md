[中文版](README_ZH.md)

# AnalyticDB for PostgreSQL × Dify Plugin

This repository is a **Dify Plugin Bundle** that integrates Alibaba Cloud **AnalyticDB for PostgreSQL** retrieval, vector, and knowledge base capabilities into Dify workflows and applications. It covers the complete RAG lifecycle from "Ingestion → Retrieval → Generation/QA."

### What is this?

The bundle contains 3 plugins (corresponding to the three types in the Dify plugin system):

- **Tools Plugin**: `adbpg_tool/`  
  Provides tools for knowledge base management, document upload/parsing, retrieval, QA, Embedding, Rerank, etc., within Dify workflows.
- **Models Plugin**: `adbpg_model/`  
  Acts as a Dify Model Provider, offering LLM / Text Embedding / Rerank preset models and a unified calling interface.
- **Endpoint Plugin**: `adbpg_endpoint/`  
  Used for Dify External Knowledge Base, providing a `POST /retrieval` endpoint.

### Scenarios Addressed

- **Enterprise/Team Knowledge Base QA (RAG)**: Ingest PDF/Word/webpage files into the knowledge base, supporting hybrid retrieval (full-text + vector) and reranking to improve recall quality and answer consistency.
- **Hybrid Retrieval and Controlled Recall**: Supports advanced parameters such as RRF/Weight/Cascaded hybrid retrieval strategies, filtering, and window recall (primarily exposed in Tools).
- **Multi-modal Retrieval**: Supports image recall capabilities like image-to-image search (`queryContentImage` in Tools).
- **Document Parsing**: In Dify `Workflow Orchestration`, use the `adbpg_doc_parser` tool instead of Dify's `General Text Chunking` tool.

### Technical Solution

- **Dify Plugin SDK (Python)**: Implements Tool/Model/Endpoint plugin types.
- **Alibaba Cloud AnalyticDB for PostgreSQL API**: Calls cloud APIs for knowledge base management, retrieval, vectorization, and reranking.
- **Unified Data Structure Adaptation**:
  - **Tools**: Capabilities and parameters are defined using the Dify Tool schema (`tools/*.yaml`).
  - **Endpoint**: Maps AnalyticDB retrieval results to the `records` structure of Dify External Knowledge Base and normalizes scores.
  - **Models**: Provides LLM/Embedding/Rerank through the Dify Model Provider interface.

### Quick Start

1. **Import Plugin Bundle in Dify**: Use the `*.difybndl` files located in the `build/` directory.
2. **Configure Credentials**:
   - Tools: See `adbpg_tool/readme/README_en_US.md`
   - Models: See `adbpg_model/readme/README_en_US.md`
   - Endpoint: See `adbpg_endpoint/readme/README_en_US.md`
3. **Recommended Usage**:
   - Use Tools for ingestion/retrieval/QA within workflows.
   - Use `adbpg-model` as the provider for LLM/Embedding/Rerank.
   - Use `adbpg-endpoint` to provide `/retrieval` for external knowledge base scenarios.

### Document Index

- **Tools**: `adbpg_tool/readme/README_en_US.md` / `adbpg_tool/readme/README_zh_Hans.md`
- **Models**: `adbpg_model/readme/README_en_US.md` / `adbpg_model/readme/README_zh_Hans.md`
- **Endpoint**: `adbpg_endpoint/readme/README_en_US.md` / `adbpg_endpoint/readme/README_zh_Hans.md`

### Need Help?

- [AnalyticDB for PostgreSQL API Documentation](https://help.aliyun.com/zh/analyticdb/analyticdb-for-postgresql/developer-reference/api-gpdb-2016-05-03-initvectordatabase?spm=a2c4g.11186623.0.i1)
- [Contact Alibaba Cloud Support (Submit a Ticket)](https://www.aliyun.com/service)
  - Please provide your plugin logs, located in the Dify plugin sidecar container:
    - `/tmp/adbpg_tools.log`
    - `/tmp/adbpg_models.log`
    - `/tmp/adbpg_endpoint.log`
