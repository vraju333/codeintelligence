from sqlalchemy import desc
from sqlalchemy.orm import Session

from baseline_models import ScenarioBaseline


class ScenarioBaselineRepository:

    def find_all_for_scenario(
        self,
        db: Session,
        scenario_id: int
    ):
        return (
            db.query(ScenarioBaseline)
            .filter(
                ScenarioBaseline.scenario_id == scenario_id
            )
            .order_by(
                desc(ScenarioBaseline.baseline_version)
            )
            .all()
        )

    def find_latest(
        self,
        db: Session,
        scenario_id: int
    ):
        return (
            db.query(ScenarioBaseline)
            .filter(
                ScenarioBaseline.scenario_id == scenario_id
            )
            .order_by(
                desc(ScenarioBaseline.baseline_version)
            )
            .first()
        )

    def find_active(
        self,
        db: Session,
        scenario_id: int
    ):
        return (
            db.query(ScenarioBaseline)
            .filter(
                ScenarioBaseline.scenario_id == scenario_id,
                ScenarioBaseline.is_active.is_(True)
            )
            .first()
        )

    def deactivate_existing(
        self,
        db: Session,
        scenario_id: int
    ):
        baselines = (
            db.query(ScenarioBaseline)
            .filter(
                ScenarioBaseline.scenario_id == scenario_id,
                ScenarioBaseline.is_active.is_(True)
            )
            .all()
        )

        for baseline in baselines:
            baseline.is_active = False

        db.flush()

    def create(
        self,
        db: Session,
        baseline: ScenarioBaseline
    ):
        db.add(baseline)
        db.commit()
        db.refresh(baseline)

        return baseline