from sqlalchemy.orm import Session

from db_models import Scenario
from schemas import ScenarioRequest


class ScenarioRepository:

    def find_all(self, db: Session):
        return db.query(Scenario).order_by(Scenario.id).all()

    def find_by_id(self, db: Session, scenario_id: int):
        return db.query(Scenario).filter(Scenario.id == scenario_id).first()

    def find_by_code(self, db: Session, scenario_code: str):
        return db.query(Scenario).filter(Scenario.scenario_code == scenario_code).first()

    def create(self, db: Session, request: ScenarioRequest):
        scenario = Scenario(**request.model_dump())
        db.add(scenario)
        db.commit()
        db.refresh(scenario)
        return scenario

    def delete(self, db: Session, scenario: Scenario):
        db.delete(scenario)
        db.commit()
