"""Deterministic engineering insights API.

Engineering Intelligence Platform (EIP)
Component: Backend API

Responsibilities:
    - Retrieve published Gold analytical facts.
    - Support custom UTC reporting periods.
    - Return metrics, comparisons, coverage and evidence.
    - Keep numerical calculations independent of the LLM.
"""

from datetime import date, timedelta
from pathlib import Path
from typing import Annotated

from dotenv import dotenv_values
from fastapi import APIRouter, HTTPException, Query

from backend.data_engineering.database.connection import open_database
from backend.data_engineering.transformations.gold.github_gold import (
    GOLD_FACTS,
    GOLD_LIFECYCLE,
    RUN_TABLE,
    build_period_facts,
)

router = APIRouter(
    prefix="/api/v1",
    tags=["Engineering Insights"],
)


@router.get("/insights")
def get_insights(
    period_start: Annotated[date | None, Query(alias="periodStart")] = None,
    period_end: Annotated[date | None, Query(alias="periodEndExclusive")] = None,
):
    """Return deterministic engineering insights for a UTC period."""

    environment = dotenv_values(".env")

    database_path = Path(environment.get("DATABASE_PATH") or "data/eip.db")

    repository = environment.get("GITHUB_REPOSITORY")

    if not database_path.is_file() or not repository:
        raise HTTPException(
            status_code=503,
            detail="Analytics data is not available.",
        )

    with open_database(database_path) as connection:
        # Use one consistent read transaction.
        connection.execute("PRAGMA query_only = ON")
        connection.execute("BEGIN")

        # 01. Resolve the published Gold snapshot.

        run = connection.execute(
            f"""
            SELECT r.*
            FROM {RUN_TABLE} AS r
            WHERE r.repositoryFullName = ? COLLATE NOCASE
              AND r.runStatus = 'SUCCEEDED'
              AND EXISTS (
                  SELECT 1
                  FROM {GOLD_FACTS} AS f
                  WHERE f.ingestionRunId = r.ingestionRunId
              )
            ORDER BY r.completedAt DESC
            LIMIT 1
            """,
            (repository,),
        ).fetchone()

        if run is None:
            raise HTTPException(
                status_code=503,
                detail="No published analytical snapshot.",
            )

        # 02. Load metric and pipeline definitions.

        config = dict(
            connection.execute("""
            SELECT configKey, configValue
            FROM eip_vw_control_pipelineConfig_static
            WHERE isActive = 1
        """).fetchall()
        )

        registry = connection.execute("""
            SELECT *
            FROM eip_vw_control_metricRegistry_static
            WHERE isActive = 1
            ORDER BY displaySequence
        """).fetchall()

        # 03. Resolve requested reporting boundaries.

        coverage_start = date.fromisoformat(run["coverageStartAt"][:10])

        coverage_end = date.fromisoformat(run["coverageEndAt"][:10])

        default_days = int(config["reportingPeriodDays"])

        if (period_start is None) != (period_end is None):
            raise HTTPException(
                status_code=422,
                detail="Provide both reporting dates or neither.",
            )

        start = period_start or (coverage_end - timedelta(days=default_days))

        end = period_end or coverage_end

        if not coverage_start <= start < end <= coverage_end:
            raise HTTPException(
                status_code=422,
                detail="Requested period is outside available history.",
            )

        # 04. Retrieve materialized Gold facts.

        facts = [
            dict(row)
            for row in connection.execute(
                f"""
                SELECT *
                FROM {GOLD_FACTS}
                WHERE ingestionRunId = ?
                  AND periodStart = ?
                  AND periodEndExclusive = ?
                """,
                (
                    run["ingestionRunId"],
                    start.isoformat(),
                    end.isoformat(),
                ),
            ).fetchall()
        ]

        # 05. Calculate custom periods from Gold lifecycle data.
        # Reuse existing analytical logic.

        if not facts:
            lifecycle = connection.execute(
                f"""
                SELECT *
                FROM {GOLD_LIFECYCLE}
                WHERE ingestionRunId = ?
                """,
                (run["ingestionRunId"],),
            ).fetchall()

            calculated_at = connection.execute(
                f"""
                SELECT MAX(calculatedAt)
                FROM {GOLD_FACTS}
                WHERE ingestionRunId = ?
                """,
                (run["ingestionRunId"],),
            ).fetchone()[0]

            facts = build_period_facts(
                lifecycle=lifecycle,
                run=run,
                metrics=registry,
                start=start,
                end=end,
                benchmark_count=int(config["benchmarkPeriodCount"]),
                calculated_at=calculated_at,
                cache={},
            )

        # 06. Attach metric metadata.

        definitions = {row["metricId"]: dict(row) for row in registry}

        for fact in facts:
            definition = definitions[fact["metricId"]]

            fact.update(
                {
                    "metricName": definition["metricName"],
                    "metricCategory": definition["metricCategory"],
                    "metricDescription": definition["metricDescription"],
                    "calculationDefinition": definition["calculationDefinition"],
                    "performanceDirection": definition["performanceDirection"],
                    "interpretationGuidance": definition["interpretationGuidance"],
                }
            )

        facts.sort(key=lambda fact: definitions[fact["metricId"]]["displaySequence"])

        # 07. Construct the deterministic response.

        previous_start = start - (end - start)

        return {
            "repository": repository,
            "repositoryId": run["repositoryId"],
            "ingestionRunId": run["ingestionRunId"],
            "periodStart": start.isoformat(),
            "periodEndExclusive": end.isoformat(),
            "previousPeriodStart": previous_start.isoformat(),
            "previousPeriodEndExclusive": start.isoformat(),
            "reportingTimezone": "UTC",
            "sourceCoverage": run["coverageStatus"],
            "dataRefreshedAt": run["completedAt"],
            "availableHistory": {
                "start": run["coverageStartAt"],
                "endExclusive": run["coverageEndAt"],
                "enrichmentStart": run["enrichmentStartAt"],
            },
            "metricCount": len(facts),
            "metrics": facts,
        }
