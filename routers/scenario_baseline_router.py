from typing import Any

from fastapi import (
    APIRouter,
    Depends
)
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database import get_db
from services.scenario.scenario_baseline_service import (
    ScenarioBaselineService
)


router = APIRouter(
    prefix="/api/scenario-baselines",
    tags=["Scenario Baselines"]
)

service = ScenarioBaselineService()


class CaptureBaselineRequest(BaseModel):

    successful_response: Any = None
    endpoint_flow: dict | None = None


@router.post("/capture/{scenario_id}")
def capture_baseline(
    scenario_id: int,
    request: CaptureBaselineRequest,
    db: Session = Depends(get_db)
):

    return service.capture(
        db=db,
        scenario_id=scenario_id,
        successful_response=request.successful_response,
        endpoint_flow=request.endpoint_flow
    )


@router.get("/latest/{scenario_id}")
def get_latest_baseline(
    scenario_id: int,
    db: Session = Depends(get_db)
):

    return service.get_latest(
        db=db,
        scenario_id=scenario_id
    )


@router.get("/history/{scenario_id}")
def get_baseline_history(
    scenario_id: int,
    db: Session = Depends(get_db)
):

    return service.get_history(
        db=db,
        scenario_id=scenario_id
    )