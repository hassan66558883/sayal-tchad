from fastapi import HTTPException, status

from app.models.product import Uom


def convert_qty(qty: float, from_uom: Uom, to_uom: Uom) -> float:
    """Converts a quantity between two units of the same category, e.g.
    10 "Sac de 50 kg" (factor=50) -> 500 "Kilogramme" (factor=1): qty is
    expressed in reference-unit terms via from_uom.factor, then divided
    back down by to_uom.factor.
    """

    if from_uom.category_id != to_uom.category_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Conversion impossible : unites de categories differentes.",
        )
    return qty * from_uom.factor / to_uom.factor
