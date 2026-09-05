from fastapi import (
    APIRouter,
    HTTPException,
    Query
)

from services.lineage.attribute_lineage_service import (
    AttributeLineageService
)


router = APIRouter(
    prefix="/api/attribute-lineage",
    tags=["Attribute Lineage"]
)


@router.get("/analyze")
def analyze_attribute(
    attribute: str = Query(...)
):

    try:

        service = (
            AttributeLineageService()
        )

        return service.analyze(
            attribute_name=attribute
        )

    except RuntimeError as exception:

        raise HTTPException(
            status_code=400,
            detail=str(exception)
        )

    except Exception as exception:

        raise HTTPException(
            status_code=500,
            detail=str(exception)
        )