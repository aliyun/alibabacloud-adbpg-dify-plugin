## adbpg-endpoint

**Author:** aliyun-adbpg
**Version:** 1.0.0
**Type:** endpoint

### Description

`adbpg-endpoint` is the **Endpoint plugin** in this repo. It is designed for Dify **External Knowledge Base** integration.

It exposes one HTTP endpoint:

- `POST /retrieval`

It receives Dify retrieval requests, queries AnalyticDB for PostgreSQL, and returns the `records` structure expected by Dify.

### Configuration (credentials)

Configure credentials in Dify (schema is defined in `adbpg_endpoint/provider/adbpg.yaml`):

| Key | Description | Required |
|---|---|---|
| `ANALYTICDB_KEY_ID` | Alibaba Cloud AccessKey ID | Yes |
| `ANALYTICDB_KEY_SECRET` | Alibaba Cloud AccessKey Secret | Yes |
| `ANALYTICDB_REGION_ID` | Region (e.g. `cn-hangzhou`) | Yes |
| `ANALYTICDB_DBINSTANCE_ID` | AnalyticDB for PostgreSQL instance ID (e.g. `gp-xxxxxx`) | Yes |
| `ANALYTICDB_NAMESPACE` | Namespace (database name) | Yes |
| `ANALYTICDB_NAMESPACE_PASSWORD` | Namespace password | Yes |
| `ANALYTICDB_ENDPOINT` | API endpoint (default is usually fine) | No |

### API contract

#### 1) Validation / health check

Dify may send validation requests with an empty body or empty JSON. This endpoint responds with HTTP 200:

- Example: `{"status":"ok","message":"Endpoint is ready"}`

#### 2) Retrieval: `POST /retrieval`

**Request body (JSON)**

| Field | Type | Notes | Required |
|---|---|---|---|
| `knowledge_id` | string | Knowledge base ID (used as AnalyticDB `collection` in this implementation) | Yes |
| `query` | string | Query text | Yes |
| `retrieval_setting.top_k` | number | Top K results (default 10) | No |
| `retrieval_setting.score_threshold` | number | Score threshold (default 0.0) | No |

**Response body (JSON)**

- `records`: array
  - `title`: string (uses match `FileName`)
  - `content`: string
  - `score`: number (0~1)
  - `metadata`: object

### Retrieval strategy (implementation notes)

For an “easy out-of-the-box” experience, the endpoint uses fixed retrieval settings (see `adbpg_endpoint/endpoints/adbpg.py`):

- **Full-text enabled**: `use_full_text_retrieval=true`
- **Hybrid search**: `hybrid_search="RRF"`
- **Rerank strength**: `rerank_factor=2.0`

Only `top_k` and `score_threshold` are configurable via request today.

### Score normalization

The endpoint prefers `RerankScore` (falls back to `Score`) and normalizes it with sigmoid:

\[
score = \frac{1}{1 + e^{-raw\_score}}
\]

Then it filters by `score_threshold` and truncates to `top_k`.

### Examples

#### Request

```json
{
  "knowledge_id": "company_docs",
  "query": "What is the expense reimbursement process?",
  "retrieval_setting": {
    "top_k": 5,
    "score_threshold": 0.6
  }
}
```

#### Response

```json
{
  "records": [
    {
      "title": "Employee_Handbook.pdf",
      "content": "...",
      "score": 0.82,
      "metadata": {
        "page": "12"
      }
    }
  ]
}
```

### Notes

- **Meaning of `knowledge_id`**: this implementation treats it as AnalyticDB `collection`. Make sure naming matches your AnalyticDB knowledge base.
- **Threshold**: `score_threshold` is applied on the normalized 0~1 score, not the raw score.

### Reference

- Console: `https://gpdbnext.console.aliyun.com/gpdb`

