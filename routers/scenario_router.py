from typing import List

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from database import get_db
from schemas import ScenarioRequest, ScenarioResponse
from services.scenario.scenario_service import ScenarioService


router = APIRouter(
    prefix="/api/scenarios",
    tags=["Scenario Registry"]
)

service = ScenarioService()


@router.get("", response_model=List[ScenarioResponse])
def get_scenarios(db: Session = Depends(get_db)):
    return service.get_all(db)


@router.get("/{scenario_id}", response_model=ScenarioResponse)
def get_scenario(scenario_id: int, db: Session = Depends(get_db)):
    return service.get_by_id(db, scenario_id)


@router.post("", response_model=ScenarioResponse, status_code=status.HTTP_201_CREATED)
def create_scenario(request: ScenarioRequest, db: Session = Depends(get_db)):
    return service.create(db, request)


@router.delete("/{scenario_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_scenario(scenario_id: int, db: Session = Depends(get_db)):
    service.delete(db, scenario_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
