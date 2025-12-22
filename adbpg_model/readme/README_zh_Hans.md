## AnalyticDB for PostgreSQL（Dify 模型插件）

### 简介

`adbpg-model` 是本仓库的 **Dify 模型（Models）插件**，作为 Dify 的模型供应商（Model Provider），提供：

- **LLM（对话大模型）**
- **Text Embedding（文本向量化）**
- **Rerank（文本精排）**

该插件把 AnalyticDB for PostgreSQL 的 AI 能力以 Dify 统一模型接口暴露出来，方便你在 Dify 中直接选择并使用预置模型，或按需配置自定义模型。

### 配置说明（凭证）

在 Dify 模型供应商配置中填写（字段名以 `adbpg_model/models/adbpg.yaml` 为准）：

| 配置项 | 说明 | 必填 |
|---|---|---|
| `ANALYTICDB_KEY_ID` | 阿里云 AccessKey ID | 是 |
| `ANALYTICDB_KEY_SECRET` | 阿里云 AccessKey Secret | 是 |
| `ANALYTICDB_REGION_ID` | 实例地域（如 `cn-hangzhou`） | 是 |
| `ANALYTICDB_DBINSTANCE_ID` | AnalyticDB for PostgreSQL 实例 ID（如 `gp-xxxxxx`） | 是 |
| `ANALYTICDB_ENDPOINT` | API Endpoint（默认一般即可） | 否 |

### 预置模型列表（当前仓库内置）

模型清单以 `adbpg_model/models/**.yaml` 为准。

### 能力说明

- **流式输出（Streaming）**：LLM 支持流式返回（用于 Dify 聊天/工作流流式展示）。
- **工具调用（Tool calling）**：部分 LLM 标注支持多工具调用/流式工具调用（以对应 `models/llm/*.yaml` 的 `features` 为准）。
- **计费与限流**：若模型 YAML 含 `pricing` 字段，Dify 会用于成本估算；实际价格与限流以云端服务为准。

### 使用建议

- **RAG 组合**：通常建议搭配本仓库的 `adbpg-tool`（管理/检索/入库工具）一起使用。
- **Embedding 维度**：选择 embedding 模型时，注意与知识库创建时的向量维度/模型保持一致。

### 参考

- 控制台：`https://gpdbnext.console.aliyun.com/gpdb`

