from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from .. import models, schemas


router = APIRouter(
    prefix="/complaints",
    tags=["Complaints"]
)


@router.post("/", response_model=schemas.ComplaintResponse)
def create_complaint(
    complaint: schemas.ComplaintCreate,
    db: Session = Depends(get_db)
):
    new_complaint = models.Complaint(
        complaint_id=complaint.complaint_id,
        customer_name=complaint.customer_name,
        product_name=complaint.product_name,
        product_type=complaint.product_type,
        batch_number=complaint.batch_number,
        complaint_category=complaint.complaint_category,
        description=complaint.description,
        quantity_affected=complaint.quantity_affected
    )

    db.add(new_complaint)
    db.commit()
    db.refresh(new_complaint)

    return new_complaint