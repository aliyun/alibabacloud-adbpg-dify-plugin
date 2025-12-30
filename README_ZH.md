[English](README.md)

## AnalyticDB for PostgreSQL × Dify 插件

本仓库是一个 **Dify 插件 Bundle**，用于把阿里云 **AnalyticDB for PostgreSQL** 的检索/向量/知识库能力接入 Dify 工作流与应用，覆盖 RAG 从“入库 → 检索 → 生成/问答”的完整链路。

### 这是什么

Bundle 内包含 3 个插件（对应 Dify 插件体系的三种类型）：

- **Tools 插件**：`adbpg_tool/`  
  在 Dify 工作流中提供知识库管理、文档上传/解析、检索、问答、Embedding、Rerank 等工具。
- **Models 插件**：`adbpg_model/`  
  作为 Dify Model Provider，提供 LLM / Text Embedding / Rerank 预置模型与统一调用接口。
- **Endpoint 插件**：`adbpg_endpoint/`  
  用于 Dify External Knowledge Base，对外提供 `POST /retrieval` 检索端点。

### 解决什么场景问题

- **企业/团队知识库问答（RAG）**：把 PDF/Word/网页等资料入库，支持混合检索（全文 + 向量）与精排，提升召回质量与答案一致性。
- **混合检索与可控召回**：支持 RRF/Weight/Cascaded 等混合检索策略、过滤、窗口召回等高级参数（主要在 Tools 侧暴露）。
- **多模态检索**：支持以图搜图等图片召回能力（Tools 侧 `queryContentImage`）。
- **文档解析**：在dify`工作流编排`中，使用adbpg文档解析工具adbpg_doc_parser替代dify的`通用文本分块`工具。

### 技术方案

- **Dify 插件 SDK（Python）**：实现 Tool/Model/Endpoint 三类插件。
- **阿里云 AnalyticDB for PostgreSQL API**：通过云端 API 完成知识库管理、检索、向量化、精排等能力调用。
- **统一数据结构适配**：
  - Tools：以 Dify Tool schema（`tools/*.yaml`）定义能力与参数。
  - Endpoint：将 AnalyticDB 检索结果映射为 Dify External Knowledge Base 的 `records` 结构，并对分数做归一化。
  - Models：以 Dify Model Provider 接口提供 LLM/Embedding/Rerank。

### 快速开始

1. **在 Dify 导入插件 Bundle**：使用 `build/` 下的 `*.difybndl`。
2. **配置凭证**：
   - Tools：见 `adbpg_tool/readme/README_zh_Hans.md`
   - Models：见 `adbpg_model/readme/README_zh_Hans.md`
   - Endpoint：见 `adbpg_endpoint/readme/README_zh_Hans.md`
3. **推荐搭配方式**：
   - 工作流内用 Tools 做入库/检索/问答
   - 模型侧用 `adbpg-model` 提供 LLM/Embedding/Rerank
   - 外部知识库场景用 `adbpg-endpoint` 提供 `/retrieval`

### 文档索引

- **Tools**：`adbpg_tool/readme/README_zh_Hans.md` / `adbpg_tool/readme/README_en_US.md`
- **Models**：`adbpg_model/readme/README_zh_Hans.md` / `adbpg_model/readme/README_en_US.md`
- **Endpoint**：`adbpg_endpoint/readme/README_zh_Hans.md` / `adbpg_endpoint/readme/README_en_US.md`

### 需要帮助？

- [AnalyticDB for PostgreSQL接口文档](https://help.aliyun.com/zh/analyticdb/analyticdb-for-postgresql/developer-reference/api-gpdb-2016-05-03-initvectordatabase?spm=a2c4g.11186623.0.i1)
- [联系阿里云售后支持提交工单](https://www.aliyun.com/service)
  - 请携带您的插件日志，位于dify插件守护容器：
    - `/tmp/adbpg_tools.log`
    - `/tmp/adbpg_models.log`
    - `/tmp/adbpg_endpoint.log`