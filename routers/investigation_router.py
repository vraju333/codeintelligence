from typing import Any

from fastapi import APIRouter, Query
from pydantic import BaseModel

from graph.investigation_graph import InvestigationGraph


router = APIRouter(
    prefix="/api/investigation",
    tags=["Investigation"]
)

investigation_graph = InvestigationGraph()


class InvestigationRequest(BaseModel):
    expected: Any
    actual: Any


@router.post("/analyse")
def analyse_defect(
    request: InvestigationRequest,
    http_method: str = Query(...),
    endpoint: str = Query(...)
):

    return investigation_graph.investigate(
        http_method=http_method,
        endpoint=endpoint,
        expected=request.expected,
        actual=request.actual
    )