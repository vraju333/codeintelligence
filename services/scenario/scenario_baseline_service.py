import json
from typing import Any

from fastapi import HTTPException
from sqlalchemy.orm import Session

from baseline_models import ScenarioBaseline
from repositories.scenario_baseline_repository import (
    ScenarioBaselineRepository
)
from repositories.scenario_repository import ScenarioRepository


class ScenarioBaselineService:

    def __init__(self):
        self.scenario_repository = ScenarioRepository()
        self.baseline_repository = (
            ScenarioBaselineRepository()
        )

    def capture(
        self,
        db: Session,
        scenario_id: int,
        successful_response: Any = None,
        endpoint_flow: dict | None = None
    ):

        scenario = (
            self.scenario_repository.find_by_id(
                db,
                scenario_id
            )
        )

        if not scenario:
            raise HTTPException(
                status_code=404,
                detail="Scenario not found"
            )

        latest = (
            self.baseline_repository.find_latest(
                db,
                scenario_id
            )
        )

        next_version = (
            latest.baseline_version + 1
            if latest
            else 1
        )

        self.baseline_repository.deactivate_existing(
            db,
            scenario_id
        )

        baseline = ScenarioBaseline(
            scenario_id=scenario.id,
            scenario_code=scenario.scenario_code,
            baseline_version=next_version,
            http_method=scenario.http_method,
            endpoint=scenario.endpoint,
            expected_response_json=self._normalize_json(
                scenario.expected_response_json
            ),
            successful_response_json=self._normalize_json(
                successful_response
            ),
            expected_db_effect=scenario.expected_db_effect,
            involved_classes=self._normalize_list(
                scenario.involved_classes
            ),
            endpoint_flow=endpoint_flow,
            is_active=True
        )

        return self.baseline_repository.create(
            db,
            baseline
        )

    def get_latest(
        self,
        db: Session,
        scenario_id: int
    ):

        scenario = (
            self.scenario_repository.find_by_id(
                db,
                scenario_id
            )
        )

        if not scenario:
            raise HTTPException(
                status_code=404,
                detail="Scenario not found"
            )

        baseline = (
            self.baseline_repository.find_active(
                db,
                scenario_id
            )
        )

        if not baseline:
            raise HTTPException(
                status_code=404,
                detail="No baseline found for scenario"
            )

        return baseline

    def get_history(
        self,
        db: Session,
        scenario_id: int
    ):

        scenario = (
            self.scenario_repository.find_by_id(
                db,
                scenario_id
            )
        )

        if not scenario:
            raise HTTPException(
                status_code=404,
                detail="Scenario not found"
            )

        return (
            self.baseline_repository
            .find_all_for_scenario(
                db,
                scenario_id
            )
        )

    def _normalize_json(
        self,
        value: Any
    ):

        if value is None:
            return None

        if isinstance(
            value,
            (dict, list)
        ):
            return value

        if isinstance(value, str):

            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return {
                    "value": value
                }

        return {
            "value": value
        }

    def _normalize_list(
        self,
        value: Any
    ):

        if value is None:
            return []

        if isinstance(value, list):
            return value

        if isinstance(value, str):

            try:
                parsed = json.loads(value)

                if isinstance(parsed, list):
                    return parsed

            except json.JSONDecodeError:
                pass

            return [
                item.strip()
                for item in value.split(",")
                if item.strip()
            ]

        return [str(value)]