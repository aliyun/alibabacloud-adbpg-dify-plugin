import json
import math
from typing import Mapping

from dify_plugin import Endpoint
from endpoints.api_helper import AnalyticDBAPIHelper, logger
from werkzeug import Request, Response


class AdbpgEndpoint(Endpoint):

    def _invoke(self, r: Request, values: Mapping, settings: Mapping) -> Response:
        """
        Invokes the endpoint with the given request.
        This endpoint is designed to work with Dify's External Knowledge Base.
        """
        # Check if request body is empty (validation request)
        request_data = r.get_data()
        if not request_data or len(request_data.strip(b" \t\n\r")) == 0:
            # Empty request body - this is a validation request from Dify
            # Return 200 to indicate the endpoint is ready
            logger.info("Received validation request (empty body)")
            return Response(
                response=json.dumps({"status": "ok", "message": "Endpoint is ready"}),
                status=200,
                content_type="application/json",
            )

        # Parse JSON from the incoming request
        try:
            body = r.get_json(force=True)
        except Exception as e:
            logger.error(f"Failed to parse JSON: {str(e)}")
            return Response(
                response=json.dumps(
                    {"error_code": 1002, "error_msg": f"Invalid JSON: {str(e)}"}
                ),
                status=200,
                content_type="application/json",
            )

        # If body is None or empty dict, treat as validation request
        if body is None or (isinstance(body, dict) and len(body) == 0):
            logger.info("Received validation request (empty JSON)")
            return Response(
                response=json.dumps({"status": "ok", "message": "Endpoint is ready"}),
                status=200,
                content_type="application/json",
            )

        logger.info(f"Received request body: {json.dumps(body, ensure_ascii=False)}")

        knowledge_id = body.get("knowledge_id")
        query = body.get("query")

        # Extract retrieval settings with sensible defaults
        retrieval_settings = body.get("retrieval_setting", {})
        top_k = retrieval_settings.get("top_k", 10)
        score_threshold = retrieval_settings.get("score_threshold", 0.0)

        logger.info(
            f"Processing retrieval request: knowledge_id={knowledge_id}, "
            f"query={query}, top_k={top_k}, score_threshold={score_threshold}"
        )

        # Log settings (without secrets)
        logger.info(
            f"Settings: region_id={settings.get('ANALYTICDB_REGION_ID')}, "
            f"dbinstance_id={settings.get('ANALYTICDB_DBINSTANCE_ID')}, "
            f"namespace={settings.get('ANALYTICDB_NAMESPACE')}"
        )

        # Validate required fields
        if not query:
            return Response(
                response=json.dumps(
                    {"error_code": 1002, "error_msg": "query is required"}
                ),
                status=400,
                content_type="application/json",
            )

        if not knowledge_id:
            return Response(
                response=json.dumps(
                    {"error_code": 1002, "error_msg": "knowledge_id is required"}
                ),
                status=400,
                content_type="application/json",
            )

        # Call the AnalyticDB API
        try:
            api_helper = AnalyticDBAPIHelper(settings)

            # Use fixed retrieval config: UseFullTextRetrieval, RRF hybrid search, rerank_factor=2.0
            response = api_helper.query_content_text(
                knowledgebase=knowledge_id,
                query=query,
                top_k=top_k,
                use_full_text_retrieval=True,
                hybrid_search="RRF",
                rerank_factor=2.0,
            )

            logger.info(f"API response: {response}")

        except Exception as e:
            error_str = str(e)
            logger.error(f"API call failed: {error_str}")

            # Check if it's a NotFound error
            if "NotFound" in error_str:
                return Response(
                    response=json.dumps({"error_code": 2001, "error_msg": error_str}),
                    status=400,
                    content_type="application/json",
                )

            # For other errors, return error_code 1002
            return Response(
                response=json.dumps({"error_code": 1002, "error_msg": error_str}),
                status=400,
                content_type="application/json",
            )

        # Process the matches from API response
        matches = response.get("Matches", {}).get("MatchList", [])
        records = []

        for match in matches:
            # Get the score - prefer RerankScore, fallback to Score
            raw_score = match.get("RerankScore")
            if raw_score is None:
                raw_score = match.get("Score", 0.0)

            # Apply sigmoid normalization: 1 / (1 + exp(-score))
            normalized_score = 1.0 / (1.0 + math.exp(-raw_score))

            # Filter by score threshold
            if normalized_score < score_threshold:
                continue

            # Build the record with FileName as title
            record = {
                "title": match.get("FileName", ""),
                "content": match.get("Content", ""),
                "score": normalized_score,
                "metadata": match.get("Metadata", {}),
            }

            records.append(record)
        records = records[:top_k]

        logger.info(
            f"Returning {len(records)} results "
            f"(filtered from {len(matches)} total, threshold={score_threshold}, top_k={top_k})"
        )

        # Construct and return the response
        return Response(
            response=json.dumps({"records": records}, ensure_ascii=False),
            status=200,
            content_type="application/json",
        )
