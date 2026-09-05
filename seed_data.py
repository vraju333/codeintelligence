import json

from database import SessionLocal
from repositories.scenario_repository import ScenarioRepository
from schemas import ScenarioRequest


repository = ScenarioRepository()


def seed_scenarios():
    db = SessionLocal()

    scenarios = [
        ScenarioRequest(
            scenario_code="ADD_EMPLOYEE",
            scenario_name="Add Employee",
            http_method="POST",
            endpoint="/api/employees",
            description="Creates an employee with all supported child objects.",
            request_json=json.dumps({
                "employeeCode": "EMP001",
                "firstName": "Raju",
                "lastName": "M",
                "department": "Engineering"
            }),
            expected_db_effect="Employee and supplied child records are persisted.",
            involved_classes="EmployeeController,EmployeeService,EmployeeMapper,EmployeeRepository,Employee"
        ),
        ScenarioRequest(
            scenario_code="UPDATE_PHONE_CONTACT",
            scenario_name="Update Phone Contact",
            http_method="PUT",
            endpoint="/api/employees/{id}/phone-contact-details",
            description="Updates phone contact details through generic child update service.",
            request_json=json.dumps({
                "primaryContact": "9000000001",
                "secondaryContact": "9000000002"
            }),
            expected_db_effect="PhoneContactDetails for the employee is updated.",
            involved_classes="EmployeeController,EmployeeService,PhoneContactDetailsService,AbstractEmployeeChildService,EmployeeRepository,PhoneContactDetails"
        ),
        ScenarioRequest(
            scenario_code="UPDATE_EMAIL_DETAILS",
            scenario_name="Update Email Details",
            http_method="PUT",
            endpoint="/api/employees/{id}/email-details",
            description="Updates email details through generic child update service.",
            request_json=json.dumps({
                "primaryEmail": "new.raju@example.com",
                "secondaryEmail": "backup.raju@example.com"
            }),
            expected_db_effect="EmailDetails for the employee is updated.",
            involved_classes="EmployeeController,EmployeeService,EmailDetailsService,AbstractEmployeeChildService,EmployeeRepository,EmailDetails"
        )
    ]

    try:
        for scenario in scenarios:
            existing = repository.find_by_code(db, scenario.scenario_code)
            if not existing:
                repository.create(db, scenario)
    finally:
        db.close()
