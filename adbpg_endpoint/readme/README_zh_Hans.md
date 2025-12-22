## AnalyticDB for PostgreSQL（Dify 外部端点插件 / External Knowledge Base）

### 简介

`adbpg-endpoint` 是本仓库的 **Dify Endpoint 插件**，用于对接 Dify 的 **External Knowledge Base**（外部知识库）。

该端点对外暴露一个 HTTP 接口：

- `POST /retrieval`

用于把 Dify 的检索请求转发到 AnalyticDB for PostgreSQL 的检索 API，并返回 Dify 需要的 `records` 结构。

### 配置说明（凭证）

在 Dify Endpoint 插件配置中填写（字段名以 `adbpg_endpoint/provider/adbpg.yaml` 为准）：

| 配置项 | 说明 | 必填 |
|---|---|---|
| `ANALYTICDB_KEY_ID` | 阿里云 AccessKey ID | 是 |
| `ANALYTICDB_KEY_SECRET` | 阿里云 AccessKey Secret | 是 |
| `ANALYTICDB_REGION_ID` | 实例地域（如 `cn-hangzhou`） | 是 |
| `ANALYTICDB_DBINSTANCE_ID` | AnalyticDB for PostgreSQL 实例 ID（如 `gp-xxxxxx`） | 是 |
| `ANALYTICDB_NAMESPACE` | 命名空间（数据库名） | 是 |
| `ANALYTICDB_NAMESPACE_PASSWORD` | 命名空间密码 | 是 |
| `ANALYTICDB_ENDPOINT` | API Endpoint（默认一般即可） | 否 |

### 接口协议

#### 1）健康检查 / 校验请求

Dify 在配置外部知识库时可能会发起“校验请求”（空 body 或空 JSON）。本端点会返回 200：

- 响应示例：`{"status":"ok","message":"Endpoint is ready"}`

#### 2）检索请求：`POST /retrieval`

**请求体（JSON）**

| 字段 | 类型 | 说明 | 必填 |
|---|---|---|---|
| `knowledge_id` | string | 知识库 ID（本实现直接作为 AnalyticDB 的 `collection` 使用） | 是 |
| `query` | string | 查询文本 | 是 |
| `retrieval_setting.top_k` | number | 返回条数（默认 10） | 否 |
| `retrieval_setting.score_threshold` | number | 分数阈值（默认 0.0） | 否 |

**响应体（JSON）**

返回结构满足 Dify External Knowledge Base 要求：

- `records`: array
  - `title`: string（本实现使用匹配项的 `FileName`）
  - `content`: string
  - `score`: number（0~1）
  - `metadata`: object

### 检索策略（实现细节）

当前实现为了“开箱即用”，在端点内部使用固定检索策略（见 `adbpg_endpoint/endpoints/adbpg.py`）：

- **启用全文检索**：`use_full_text_retrieval=true`
- **混合检索**：`hybrid_search="RRF"`
- **精排强度**：`rerank_factor=2.0`

> 说明：请求体里目前只开放 `top_k` 和 `score_threshold`，其余检索参数在端点代码中固定，便于减少配置复杂度。

### 评分归一化（score）

AnalyticDB 返回的 `RerankScore`（若缺失则退回 `Score`）会做 sigmoid 归一化：

\[
score = \frac{1}{1 + e^{-raw\_score}}
\]

然后再按 `score_threshold` 过滤，并最终截断到 `top_k`。

### 示例

#### 请求示例

```json
{
  "knowledge_id": "company_docs",
  "query": "报销流程是什么？",
  "retrieval_setting": {
    "top_k": 5,
    "score_threshold": 0.6
  }
}
```

#### 响应示例

```json
{
  "records": [
    {
      "title": "员工手册.pdf",
      "content": "……",
      "score": 0.82,
      "metadata": {
        "page": "12"
      }
    }
  ]
}
```

### 注意事项

- **`knowledge_id` 的含义**：本实现把 `knowledge_id` 直接当作 AnalyticDB 的 `collection`（知识库/文档库名）使用，请确保两边命名一致。
- **阈值含义**：`score_threshold` 是归一化后的 0~1 分数阈值，不是原始分数。

### 参考

- 控制台：`https://gpdbnext.console.aliyun.com/gpdb`

