from fastapi import HTTPException
from sqlalchemy.orm import Session

from repositories.scenario_repository import ScenarioRepository
from schemas import ScenarioRequest


class ScenarioService:

    def __init__(self):
        self.repository = ScenarioRepository()

    def get_all(self, db: Session):
        return self.repository.find_all(db)

    def get_by_id(self, db: Session, scenario_id: int):
        scenario = self.repository.find_by_id(db, scenario_id)
        if not scenario:
            raise HTTPException(status_code=404, detail="Scenario not found")
        return scenario

    def create(self, db: Session, request: ScenarioRequest):
        existing = self.repository.find_by_code(db, request.scenario_code)
        if existing:
            raise HTTPException(status_code=409, detail="Scenario code already exists")
        return self.repository.create(db, request)

    def delete(self, db: Session, scenario_id: int):
        scenario = self.get_by_id(db, scenario_id)
        self.repository.delete(db, scenario)
