## AnalyticDB for PostgreSQL（Dify 工具插件）

### 简介

`adbpg-tool` 是本仓库的 **Dify 工具（Tools）插件**，用于把阿里云 **AnalyticDB for PostgreSQL** 的知识库/向量检索能力以 Dify 工具形式暴露出来，便于在工作流里完成：

- **知识库生命周期管理**：列出/创建知识库、删除文档、任务查询
- **数据导入**：文档上传（自动解析与分块）、分块直传（Upsert）
- **检索与问答**：文本检索（可全文/混合检索）、图片检索、流式知识库问答
- **原子能力**：文本向量化、文本精排（Rerank）

### 适用场景

- **企业知识库问答（RAG）**：上传文档 → 检索召回 → 重排 → 生成回答
- **混合检索**：全文检索 + 向量检索融合（如 RRF/Weight/Cascaded）
- **多模态检索**：以图搜图、图文场景的内容召回
- **离线解析/预处理**：先把文件解析为 chunks，再选择是否写入知识库

### 配置说明（凭证）

在 Dify 插件凭证配置中填写（字段名以 `adbpg_tool/provider/adbpg.yaml` 为准）：

| 配置项 | 说明 | 必填 |
|---|---|---|
| `ANALYTICDB_KEY_ID` | 阿里云 AccessKey ID | 是 |
| `ANALYTICDB_KEY_SECRET` | 阿里云 AccessKey Secret | 是 |
| `ANALYTICDB_REGION_ID` | 实例地域（如 `cn-hangzhou`） | 是 |
| `ANALYTICDB_DBINSTANCE_ID` | AnalyticDB for PostgreSQL 实例 ID（如 `gp-xxxxxx`） | 是 |
| `ANALYTICDB_MANAGER_ACCOUNT` | 管理员账户 | 是 |
| `ANALYTICDB_MANAGER_ACCOUNT_PASSWORD` | 管理员密码 | 是 |
| `ANALYTICDB_NAMESPACE` | 命名空间（数据库名，不存在会自动创建） | 是 |
| `ANALYTICDB_NAMESPACE_PASSWORD` | 命名空间密码（存在时会更新） | 是 |
| `ANALYTICDB_ENDPOINT` | 服务 Endpoint（一般用默认值即可） | 否 |

### 工具列表（以当前代码为准）

下面工具名/参数名来自 `adbpg_tool/provider/adbpg.yaml` 与 `adbpg_tool/tools/*/*.yaml`（避免 readme 过期）。

#### 知识库管理

- **知识库列表(`listKnowledgeBases`)**：列出实例下的所有知识库（文档库）。
- **创建知识库(`createDocumentCollection`)**：创建知识库/集合，并配置向量模型、全文检索、元数据、索引、（可选）知识图谱等。
  - **关键参数**：`knowledgebase`、`embedding_model`、`metadata`、`full_text_retrieval_fields`、`metadata_indices`
  - **知识图谱**：`enable_graph=true` 时建议同时提供 `entity_types` 与 `relationship_types`，并可设置 `llmmodel`/`language`
- **删除文档(`deleteDocument`)**：按 `file_name` 删除知识库中的文档。

#### 文档导入/解析

- **文档上传(`uploadDocumentAsync`)**：上传文件（URL 或本地路径），自动解析→切分→向量化→入库，返回 `JobId`。
  - **关键参数**：`knowledgebase`、`filename`、`fileurl`
  - **解析/切分配置**：`document_loader_name`、`text_splitter_name`、`chunksize`、`chunk_overlap`、`separators`、`zh_title_enhance`、`vl_enhance`、`splitter_model`
  - **试运行**：`dry_run=true` 可用于只验证解析/切分参数（不实际上传）
- **查询上传任务(`getUploadDocumentJob`)**：按 `jobid` 查询上传任务；可设置 `wait_until_finish=true` 轮询等待完成（每 3 秒一次，超时 30 分钟）。
- **文档解析(`adbpgDocParser`)**：只做解析与分块 **不入库**，用于“先解析→再决定如何写入”的流程。
  - **关键参数**：`filename`、`fileurl`（其余解析/切分参数与 `uploadDocumentAsync` 类似）
- **上传切分后的文档(`upsertChunks`)**：把你已准备好的 chunks 直接写入知识库。
  - **关键参数**：`knowledgebase`、`file_name`、`text_chunks`（JSON 数组，元素可含 `Content`/`Id`/`Metadata`/`Filter`）

#### 检索 / 问答

- **文本召回(`queryContentText`)**：文本检索（向量/全文/混合），支持过滤、窗口召回、返回文件 URL 等。
  - **关键参数**：`knowledgebase`、`query`、`top_k`
  - **全文检索**：`use_full_text_retrieval=true`
  - **混合检索**：`hybrid_search` 可选 `RRF` / `Weight` / `Cascaded`；可配 `hybrid_search_k` / `hybrid_search_alpha`
  - **重排**：`rerank_factor`（数值越大通常会更“精排”）
  - **过滤**：`filter`（结构由 AnalyticDB 接口定义）
  - **窗口召回**：`recall_window`（例如 `-3,6`）
- **图片召回(`queryContentImage`)**：以图搜图（图片文件 URL 或本地路径）。
  - **关键参数**：`knowledgebase`、`file_name`、`file_url`、`top_k`
- **知识库问答（流式）(`chatWithKnowledgeBaseStream`)**：检索 + 生成一体的流式问答输出。
  - **关键参数**：`query`、`llm_model`；可选 `knowledgebase`、`top_k`、`use_full_text_retrieval`、`rerank_factor`、`graph_enhance`
  - **生成参数**：`system`、`temperature`、`top_p`、`max_tokens`、`seed`、`presence_penalty`

#### 原子能力

- **文本向量化(`textEmbedding`)**：把输入文本（JSON 数组字符串）转成向量；可选 `embedding_model` 与 `dimension`。
- **文本精排(`rerank`)**：对文档列表（JSON 数组字符串）做精排；可选 `rerank_model`、`topk`、`return_documents`。

### 推荐工作流（示例）

#### 1）从 0 构建知识库并问答

- **创建知识库(`createDocumentCollection`)**
- **文档上传(`uploadDocumentAsync`)** → 得到 `JobId`
- **查询上传任务(`getUploadDocumentJob`, wait_until_finish=true)**（轮询等待完成）
- **文本召回(`queryContentText`, hybrid_search="RRF")**
- **知识库问答（流式）(`chatWithKnowledgeBaseStream`)**

#### 2）先解析后入库（可控分块）

- **文档解析(`adbpgDocParser`)**（拿到 chunks）
- **自定义清洗/打标签**：在工作流中加工 `Metadata/Filter`
- **上传切分后的文档(`upsertChunks`)**

### 注意事项

- **知识库命名**：`knowledgebase` 需符合 PostgreSQL 对象名限制（建议只用字母/数字/下划线）。
- **向量模型与维度**：创建知识库选择的 `embedding_model` 与维度要与后续写入/检索一致。
- **全文检索字段**：`full_text_retrieval_fields` 里的字段必须先在 `metadata` 中定义。

### 参考

- **创建 AccessKey**：`https://www.alibabacloud.com/help/zh/ram/user-guide/create-an-accesskey-pair`
- **控制台**：`https://gpdbnext.console.aliyun.com/gpdb`