## AnalyticDB for PostgreSQL (Dify Models Plugin)

### Introduction

`adbpg-model` is the **Models plugin** in this repo. It works as a Dify model provider and exposes:

- **LLM (chat)**
- **Text Embedding**
- **Rerank**

This lets you pick predefined models shipped in this repo (or configure custom ones) using Dify’s standard model interfaces.

### Configuration (credentials)

Fill in provider credentials in Dify (schema is defined in `adbpg_model/models/adbpg.yaml`):

| Key | Description | Required |
|---|---|---|
| `ANALYTICDB_KEY_ID` | Alibaba Cloud AccessKey ID | Yes |
| `ANALYTICDB_KEY_SECRET` | Alibaba Cloud AccessKey Secret | Yes |
| `ANALYTICDB_REGION_ID` | Region (e.g. `cn-hangzhou`) | Yes |
| `ANALYTICDB_DBINSTANCE_ID` | AnalyticDB for PostgreSQL instance ID (e.g. `gp-xxxxxx`) | Yes |
| `ANALYTICDB_ENDPOINT` | API endpoint (default is usually fine) | No |

### Predefined models (shipped with this repo)

The source-of-truth list is `adbpg_model/models/**.yaml`.

### Notes

- **Streaming**: LLM supports streaming responses in Dify.
- **Tool calling**: some LLMs declare multi-tool-call features (see each `models/llm/*.yaml`).
- **Pricing/limits**: YAML pricing is for estimation; actual pricing and limits follow the cloud service.

### Reference

- Console: `https://gpdbnext.console.aliyun.com/gpdb`

