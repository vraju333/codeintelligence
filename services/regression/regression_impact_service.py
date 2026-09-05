from sqlalchemy.orm import Session

from baseline_models import ScenarioBaseline
from services.regression.git_diff_service import (
    GitDiffService
)


class RegressionImpactService:

    def __init__(self):

        self.git_diff_service = (
            GitDiffService()
        )

    def analyse(
        self,
        db: Session
    ):

        changes = (
            self.git_diff_service
            .analyse_changes()
        )

        active_baselines = (
            db.query(ScenarioBaseline)
            .filter(
                ScenarioBaseline.is_active
                .is_(True)
            )
            .all()
        )

        changed_classes = set()

        changed_methods = []

        for changed_file in changes[
            "changed_files"
        ]:

            class_name = changed_file[
                "class_name"
            ]

            changed_classes.add(
                class_name
            )

            for method in changed_file[
                "changed_methods"
            ]:

                changed_methods.append(
                    {
                        "class_name": class_name,
                        "method_name": method[
                            "method_name"
                        ],
                        "changed_lines": method[
                            "changed_lines"
                        ]
                    }
                )

        affected_scenarios = []

        for baseline in active_baselines:

            involved_classes = (
                baseline.involved_classes
                or []
            )

            matched_classes = sorted(
                set(involved_classes)
                .intersection(
                    changed_classes
                )
            )

            if not matched_classes:
                continue

            scenario_methods = [
                method
                for method in changed_methods
                if method["class_name"]
                in matched_classes
            ]

            affected_scenarios.append(
                {
                    "scenario_id":
                        baseline.scenario_id,

                    "scenario_code":
                        baseline.scenario_code,

                    "baseline_version":
                        baseline.baseline_version,

                    "http_method":
                        baseline.http_method,

                    "endpoint":
                        baseline.endpoint,

                    "impact_status":
                        "POTENTIAL_REGRESSION",

                    "matched_classes":
                        matched_classes,

                    "changed_methods":
                        scenario_methods
                }
            )

        return {
            "status": (
                "CHANGES_DETECTED"
                if changes[
                    "total_changed_java_files"
                ] > 0
                else "NO_CHANGES"
            ),

            "total_changed_java_files":
                changes[
                    "total_changed_java_files"
                ],

            "changed_classes":
                sorted(
                    changed_classes
                ),

            "changed_methods":
                changed_methods,

            "total_affected_scenarios":
                len(
                    affected_scenarios
                ),

            "affected_scenarios":
                affected_scenarios,

            "git_changes":
                changes
        }