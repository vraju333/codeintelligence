
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from services.regression.regression_impact_service import (
    RegressionImpactService
)


class RegressionReportService:

    def __init__(self):

        self.regression_impact_service = (
            RegressionImpactService()
        )

    def generate(
        self,
        db: Session
    ):

        regression = (
            self.regression_impact_service
            .analyse(db)
        )

        changed_methods = (
            regression.get(
                "changed_methods",
                []
            )
        )

        affected_scenarios = (
            regression.get(
                "affected_scenarios",
                []
            )
        )

        changed_classes = (
            regression.get(
                "changed_classes",
                []
            )
        )

        report_status = (
            self._determine_report_status(
                regression
            )
        )

        scenario_reports = []

        for scenario in affected_scenarios:

            scenario_reports.append(
                self._build_scenario_report(
                    scenario
                )
            )

        report = {
            "report_type":
                "REGRESSION_ANALYSIS",

            "generated_at":
                datetime.now(
                    timezone.utc
                ).isoformat(),

            "status":
                report_status,

            "summary": {
                "changed_java_files":
                    regression.get(
                        "total_changed_java_files",
                        0
                    ),

                "changed_classes":
                    len(
                        changed_classes
                    ),

                "changed_methods":
                    len(
                        changed_methods
                    ),

                "affected_scenarios":
                    len(
                        affected_scenarios
                    )
            },

            "changed_classes":
                changed_classes,

            "changed_methods":
                changed_methods,

            "scenarios":
                scenario_reports
        }

        report[
            "report_text"
        ] = self._build_text_report(
            report
        )

        return report

    def _build_scenario_report(
        self,
        scenario: dict
    ):

        changed_methods = (
            scenario.get(
                "changed_methods",
                []
            )
        )

        method_names = []

        for method in changed_methods:

            class_name = method.get(
                "class_name",
                ""
            )

            method_name = method.get(
                "method_name",
                ""
            )

            if class_name and method_name:

                method_names.append(
                    f"{class_name}.{method_name}"
                )

        return {
            "scenario_id":
                scenario.get(
                    "scenario_id"
                ),

            "scenario_code":
                scenario.get(
                    "scenario_code"
                ),

            "baseline_version":
                scenario.get(
                    "baseline_version"
                ),

            "http_method":
                scenario.get(
                    "http_method"
                ),

            "endpoint":
                scenario.get(
                    "endpoint"
                ),

            "impact_status":
                scenario.get(
                    "impact_status"
                ),

            "matched_classes":
                scenario.get(
                    "matched_classes",
                    []
                ),

            "changed_methods":
                changed_methods,

            "changed_method_names":
                method_names,

            "reason":
                self._build_reason(
                    scenario
                )
        }

    def _build_reason(
        self,
        scenario: dict
    ):

        matched_classes = (
            scenario.get(
                "matched_classes",
                []
            )
        )

        if not matched_classes:

            return (
                "No changed classes matched "
                "this scenario baseline."
            )

        classes = ", ".join(
            matched_classes
        )

        return (
            "The scenario baseline depends on "
            f"changed class(es): {classes}."
        )

    def _determine_report_status(
        self,
        regression: dict
    ):

        if (
            regression.get(
                "status"
            )
            == "NO_CHANGES"
        ):

            return "NO_CHANGES"

        if (
            regression.get(
                "total_affected_scenarios",
                0
            )
            > 0
        ):

            return (
                "REGRESSION_RISK_DETECTED"
            )

        return (
            "CHANGES_WITH_NO_REGISTERED_IMPACT"
        )

    def _build_text_report(
        self,
        report: dict
    ):

        lines = []

        lines.append(
            "REGRESSION ANALYSIS REPORT"
        )

        lines.append(
            "=" * 30
        )

        lines.append("")

        lines.append(
            f"Status: "
            f"{report['status']}"
        )

        lines.append(
            f"Generated At: "
            f"{report['generated_at']}"
        )

        lines.append("")

        summary = report[
            "summary"
        ]

        lines.append(
            "SUMMARY"
        )

        lines.append(
            "-" * 20
        )

        lines.append(
            "Changed Java Files: "
            f"{summary['changed_java_files']}"
        )

        lines.append(
            "Changed Classes: "
            f"{summary['changed_classes']}"
        )

        lines.append(
            "Changed Methods: "
            f"{summary['changed_methods']}"
        )

        lines.append(
            "Affected Scenarios: "
            f"{summary['affected_scenarios']}"
        )

        lines.append("")

        if report[
            "changed_methods"
        ]:

            lines.append(
                "CHANGED METHODS"
            )

            lines.append(
                "-" * 20
            )

            for method in report[
                "changed_methods"
            ]:

                class_name = (
                    method.get(
                        "class_name",
                        ""
                    )
                )

                method_name = (
                    method.get(
                        "method_name",
                        ""
                    )
                )

                changed_lines = (
                    method.get(
                        "changed_lines",
                        []
                    )
                )

                lines.append(
                    f"- {class_name}."
                    f"{method_name} "
                    f"(lines: "
                    f"{', '.join(map(str, changed_lines))})"
                )

            lines.append("")

        if report[
            "scenarios"
        ]:

            lines.append(
                "AFFECTED SCENARIOS"
            )

            lines.append(
                "-" * 20
            )

            for scenario in report[
                "scenarios"
            ]:

                lines.append(
                    f"Scenario: "
                    f"{scenario['scenario_code']}"
                )

                lines.append(
                    f"Endpoint: "
                    f"{scenario['http_method']} "
                    f"{scenario['endpoint']}"
                )

                lines.append(
                    f"Baseline: "
                    f"Version "
                    f"{scenario['baseline_version']}"
                )

                lines.append(
                    f"Impact: "
                    f"{scenario['impact_status']}"
                )

                lines.append(
                    f"Reason: "
                    f"{scenario['reason']}"
                )

                if scenario[
                    "changed_method_names"
                ]:

                    lines.append(
                        "Changed Methods:"
                    )

                    for method_name in scenario[
                        "changed_method_names"
                    ]:

                        lines.append(
                            f"  - {method_name}"
                        )

                lines.append("")

        if not report[
            "scenarios"
        ]:

            lines.append(
                "No registered scenarios "
                "are currently affected."
            )

        return "\n".join(
            lines
        )