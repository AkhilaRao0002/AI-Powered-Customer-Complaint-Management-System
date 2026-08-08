# ============================================================
# AIVOA AI - AI COPILOT ROUTES
# ============================================================

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    UploadFile,
    File,
    Form
)
from pydantic import BaseModel, field_validator
from sqlalchemy.orm import Session

from typing import Optional, Any
import uuid
import json
import re
from pypdf import PdfReader
from ..ai.graph import graph
from ..database import SessionLocal
from ..models import Complaint


# ============================================================
# ROUTER
# ============================================================

router = APIRouter(
    prefix="/ai",
    tags=["AI"]
)


# ============================================================
# DATABASE
# ============================================================

def get_db():
    """
    Creates a database session for a FastAPI request.
    """

    db = SessionLocal()

    try:
        yield db

    finally:
        db.close()


# ============================================================
# COMPLAINT DATA MODEL
# ============================================================

class ComplaintData(BaseModel):

    complaint_source: Optional[str] = None
    customer_name: Optional[str] = None

    product_name: Optional[str] = None
    product_strength: Optional[str] = None
    batch_number: Optional[str] = None

    manufacturing_date: Optional[str] = None
    expiry_date: Optional[str] = None

    quantity_affected: Optional[int] = None

    complaint_category: Optional[str] = None
    complaint_date: Optional[str] = None

    description: Optional[str] = None

    risk_severity: Optional[str] = None
    risk_reason: Optional[str] = None

    suggested_next_action: Optional[str] = None

    possible_root_causes: Optional[list] = None

    capa: Optional[dict] = None

    corrective_action: Optional[str] = None
    preventive_action: Optional[str] = None

    @field_validator(
        "quantity_affected",
        mode="before"
    )
    @classmethod
    def empty_quantity_to_none(cls, value):

        if value == "":
            return None

        if value is None:
            return None

        # Handle accidental numeric strings safely
        if isinstance(value, str):

            value = value.strip()

            if value == "":
                return None

            if value.isdigit():
                return int(value)

        return value


# ============================================================
# COPILOT INPUT
# ============================================================

class CopilotInput(BaseModel):

    message: str

    current_data: Optional[ComplaintData] = None


# ============================================================
# SAVE INPUT
# ============================================================

class ComplaintSaveInput(BaseModel):

    complaint_text: Optional[str] = None

    # --------------------------------------------------------
    # ORIGIN & CUSTOMER
    # --------------------------------------------------------

    complaint_source: Optional[str] = None
    customer_name: Optional[str] = None

    # --------------------------------------------------------
    # PRODUCT
    # --------------------------------------------------------

    product_name: Optional[str] = None
    product_strength: Optional[str] = None
    batch_number: Optional[str] = None

    manufacturing_date: Optional[str] = None
    expiry_date: Optional[str] = None

    quantity_affected: Optional[int] = None

    # --------------------------------------------------------
    # COMPLAINT
    # --------------------------------------------------------

    complaint_category: Optional[str] = None
    complaint_date: Optional[str] = None
    description: Optional[str] = None

    # --------------------------------------------------------
    # AI ASSESSMENT
    # --------------------------------------------------------

    risk_severity: Optional[str] = None
    risk_reason: Optional[str] = None

    suggested_next_action: Optional[str] = None

    possible_root_causes: Optional[Any] = None

    corrective_action: Optional[str] = None
    preventive_action: Optional[str] = None

    @field_validator(
        "quantity_affected",
        mode="before"
    )
    @classmethod
    def empty_quantity_to_none(cls, value):

        if value == "":
            return None

        if value is None:
            return None

        if isinstance(value, str):

            value = value.strip()

            if value == "":
                return None

            if value.isdigit():
                return int(value)

        return value


# ============================================================
# HELPER - CLEAN VALUE
# ============================================================

def clean_value(value):

    if value is None:
        return None

    if isinstance(value, str):

        value = value.strip()

        if not value:
            return None

        if value.lower() in {
            "null",
            "none",
            "not provided",
            "not mentioned",
            "unknown",
            "n/a",
            "na"
        }:
            return None

    return value

# ============================================================
# PDF TEXT EXTRACTION
# ============================================================

def extract_text_from_pdf(file: UploadFile) -> str:

    try:

        reader = PdfReader(file.file)

        pages = []

        for page in reader.pages:

            text = page.extract_text()

            if text:
                pages.append(text)

        extracted_text = "\n\n".join(pages).strip()

        if not extracted_text:

            raise HTTPException(
                status_code=400,
                detail=(
                    "No readable text was found in the PDF. "
                    "The PDF may be scanned/image-based."
                )
            )

        return extracted_text

    except HTTPException:
        raise

    except Exception as e:

        raise HTTPException(
            status_code=400,
            detail=f"Failed to extract PDF text: {str(e)}"
        )
# ============================================================
# HELPER - SERIALIZE ROOT CAUSES
# ============================================================

def serialize_root_causes(value):

    if value is None:
        return None

    if isinstance(value, list):

        cleaned = [
            str(item).strip()
            for item in value
            if item
        ]

        return json.dumps(cleaned)

    if isinstance(value, dict):

        return json.dumps(value)

    return str(value)


# ============================================================
# HELPER - NORMALIZE GRAPH RESULT
# ============================================================

def normalize_data(result):

    return {

        "complaint_source":
            result.get("complaint_source"),

        "customer_name":
            result.get("customer_name"),

        "product_name":
            result.get("product_name"),

        "product_strength":
            result.get("product_strength"),

        "batch_number":
            result.get("batch_number"),

        "manufacturing_date":
            result.get("manufacturing_date"),

        "expiry_date":
            result.get("expiry_date"),

        "quantity_affected":
            result.get("quantity_affected"),

        "complaint_category":
            result.get("complaint_category"),

        "complaint_date":
            result.get("complaint_date"),

        "description":
            result.get("description"),

        "risk_severity":
            result.get("risk_severity")
            or result.get("severity_of_risk")
            or result.get("severity"),

        "risk_reason":
            result.get("risk_reason"),

        "suggested_next_action":
            result.get(
                "suggested_next_action"
            ),

        "possible_root_causes":
            result.get(
                "possible_root_causes"
            ),

        "capa":
            result.get("capa"),

        "corrective_action":
            result.get(
                "corrective_action"
            ),

        "preventive_action":
            result.get(
                "preventive_action"
            )
    }


# ============================================================
# COMPLETENESS CHECK
# IMPORTANT:
# complaint_category IS NOT REQUIRED HERE.
# AI WILL DETERMINE IT DURING ASSESSMENT.
# ============================================================

def check_completeness(data: dict) -> dict:

    required_fields = {

        "complaint_source":
            "Complaint Source",

        "customer_name":
            "Customer Name",

        "product_name":
            "Product Name",

        "product_strength":
            "Product Strength",

        "batch_number":
            "Batch Number",

        "manufacturing_date":
            "Manufacturing Date",

        "expiry_date":
            "Expiry Date",

        "quantity_affected":
            "Quantity Affected",

        "complaint_date":
            "Complaint Date",

        "description":
            "Detailed Complaint Description"
    }

    missing_fields = []

    for field, label in required_fields.items():

        value = data.get(field)

        if value is None:

            missing_fields.append(label)

            continue

        if isinstance(value, str) and not value.strip():

            missing_fields.append(label)

    return {

        "is_complete":
            len(missing_fields) == 0,

        "missing_fields":
            missing_fields
    }


# ============================================================
# DETERMINE WHETHER MESSAGE IS AN EDIT
# ============================================================

def is_edit_request(message: str) -> bool:

    text = message.lower().strip()

    edit_patterns = [

        r"\bchange\b",
        r"\bedit\b",
        r"\bupdate\b",
        r"\bcorrect\b",
        r"\bmodify\b",
        r"\breplace\b",
        r"\bfix\b",
        r"\bincorrect\b",
        r"\bwrong\b",
        r"\bactually\b",
        r"\bshould be\b",
        r"\bset\b",
        r"\bremove\b",
        r"\bclear\b"
    ]

    return any(
        re.search(pattern, text)
        for pattern in edit_patterns
    )


# ============================================================
# MERGE CURRENT DATA
# ============================================================

def merge_existing_data(
    extracted: dict,
    current_data: dict
) -> dict:

    merged = dict(extracted)

    for key, value in current_data.items():

        if key not in merged:

            merged[key] = value

            continue

        if (
            merged[key] is None
            and value is not None
        ):

            merged[key] = value

    return merged


# ============================================================
# AI COPILOT
# ============================================================

@router.post("/copilot")
def ai_copilot(data: CopilotInput):

    # ========================================================
    # VALIDATE MESSAGE
    # ========================================================

    if not data.message or not data.message.strip():

        raise HTTPException(
            status_code=400,
            detail="Message cannot be empty."
        )

    user_message = data.message.strip()

    # ========================================================
    # CURRENT DATA
    # ========================================================

    current_data = {}

    if data.current_data:

        current_data = data.current_data.model_dump(
            exclude_none=True
        )

    # ========================================================
    # DETERMINE INTERACTION
    # ========================================================

    has_existing_data = bool(current_data)

    edit_request = (
        has_existing_data
        and is_edit_request(user_message)
    )

    # ========================================================
    # GRAPH INPUT
    # ========================================================

    graph_input = {

        "complaint_text":
            user_message,

        "user_message":
            user_message,

        "edit_prompt":
            user_message
            if edit_request
            else None,

        # ----------------------------------------------------
        # COMPLAINT
        # ----------------------------------------------------

        "complaint_source":
            current_data.get(
                "complaint_source"
            ),

        "origin":
            current_data.get(
                "complaint_source"
            ),

        "customer_name":
            current_data.get(
                "customer_name"
            ),

        "product_name":
            current_data.get(
                "product_name"
            ),

        "product_strength":
            current_data.get(
                "product_strength"
            ),

        "batch_number":
            current_data.get(
                "batch_number"
            ),

        "manufacturing_date":
            current_data.get(
                "manufacturing_date"
            ),

        "expiry_date":
            current_data.get(
                "expiry_date"
            ),

        "quantity_affected":
            current_data.get(
                "quantity_affected"
            ),

        "complaint_category":
            current_data.get(
                "complaint_category"
            ),

        "complaint_date":
            current_data.get(
                "complaint_date"
            ),

        "description":
            current_data.get(
                "description"
            ),

        # ----------------------------------------------------
        # ASSESSMENT
        # ----------------------------------------------------

        "risk_severity":
            current_data.get(
                "risk_severity"
            ),

        "severity_of_risk":
            current_data.get(
                "risk_severity"
            ),

        "risk_reason":
            current_data.get(
                "risk_reason"
            ),

        "suggested_next_action":
            current_data.get(
                "suggested_next_action"
            ),

        "possible_root_causes":
            current_data.get(
                "possible_root_causes"
            ),

        "capa":
            current_data.get(
                "capa"
            ),

        "corrective_action":
            current_data.get(
                "corrective_action"
            ),

        "preventive_action":
            current_data.get(
                "preventive_action"
            )
    }

    # ========================================================
    # RUN GRAPH
    # ========================================================

    try:

        result = graph.invoke(
            graph_input
        )

    except Exception as e:

        print(
            "\n========== COPILOT ERROR =========="
        )

        print(str(e))

        print(
            "===================================\n"
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "AI processing failed: "
                f"{str(e)}"
            )
        )

    # ========================================================
    # DEBUG
    # ========================================================

    print(
        "\n========== GRAPH RESULT =========="
    )

    print(result)

    print(
        "==================================\n"
    )

    # ========================================================
    # NORMALIZE
    # ========================================================

    extracted = normalize_data(
        result
    )

    # ========================================================
    # MERGE EXISTING DATA
    # ========================================================

    extracted = merge_existing_data(
        extracted,
        current_data
    )

    # ========================================================
    # COMPLETENESS
    #
    # Category is deliberately NOT checked.
    # ========================================================

    completeness = check_completeness(
        extracted
    )

    # ========================================================
    # INCOMPLETE
    # ========================================================

    if not completeness["is_complete"]:

        missing = ", ".join(
            completeness["missing_fields"]
        )

        assistant_message = (
            "I have extracted the available "
            "complaint information. Before I "
            "continue with the AI assessment, "
            "please provide: "
            f"{missing}."
        )

        return {

            "message":
                assistant_message,

            "data":
                extracted,

            "is_complete":
                False,

            "missing_fields":
                completeness[
                    "missing_fields"
                ],

            "ready_for_assessment":
                False,

            "ready_for_qms":
                False,

            "workflow_stage":
                "Waiting for Information",

            "interaction_type":
                "edit"
                if edit_request
                else "extraction"
        }

    # ========================================================
    # COMPLETE
    # ========================================================

    # At this point graph.py should already have run
    # the assessment node.

    if not extracted.get(
        "complaint_category"
    ):

        raise HTTPException(

            status_code=500,

            detail=(
                "AI assessment completed but "
                "complaint category was not generated."
            )
        )

    if not extracted.get(
        "risk_severity"
    ):

        raise HTTPException(

            status_code=500,

            detail=(
                "AI assessment completed but "
                "risk severity was not generated."
            )
        )

    # ========================================================
    # FINAL MESSAGE
    # ========================================================

    assistant_message = (
        "All required complaint information is "
        "available. The AI has determined the "
        "complaint category and completed the "
        "risk assessment, root cause analysis, "
        "corrective action, and preventive action."
    )

    return {

        "message":
            assistant_message,

        "data":
            extracted,

        "is_complete":
            True,

        "missing_fields":
            [],

        "ready_for_assessment":
            True,

        "ready_for_qms":
            True,

        "workflow_stage":
            result.get(
                "workflow_stage"
            )
            or "AI Assessment",

        "interaction_type":
            "edit"
            if edit_request
            else "extraction"
    }

# ============================================================
# PDF / FILE COPILOT
# ============================================================

@router.post("/copilot/file")
async def ai_copilot_file(
    file: UploadFile = File(...),
    message: str = Form(""),
    current_data: str = Form("{}")
):

    # ========================================================
    # VALIDATE FILE
    # ========================================================

    if not file.filename:

        raise HTTPException(
            status_code=400,
            detail="No file was provided."
        )

    # ========================================================
    # VALIDATE PDF
    # ========================================================

    filename = file.filename.lower()

    if not filename.endswith(".pdf"):

        raise HTTPException(
            status_code=400,
            detail="Only PDF files are currently supported."
        )

    # ========================================================
    # EXTRACT PDF TEXT
    # ========================================================

    pdf_text = extract_text_from_pdf(file)

    # ========================================================
    # PARSE CURRENT DATA
    # ========================================================

    try:

        parsed_current_data = json.loads(
            current_data or "{}"
        )

    except json.JSONDecodeError:

        raise HTTPException(
            status_code=400,
            detail="Invalid current_data JSON."
        )

    if not isinstance(parsed_current_data, dict):

        raise HTTPException(
            status_code=400,
            detail="current_data must be a JSON object."
        )

    # ========================================================
    # USER MESSAGE
    # ========================================================

    user_message = message.strip()

    # If the user typed something along with the PDF,
    # keep it as additional context.

    if user_message:

        complaint_text = (
            f"USER INSTRUCTION:\n"
            f"{user_message}\n\n"
            f"PDF COMPLAINT CONTENT:\n"
            f"{pdf_text}"
        )

    else:

        complaint_text = pdf_text

    # ========================================================
    # EXISTING DATA
    # ========================================================

    current_data = {
        key: value
        for key, value in parsed_current_data.items()
        if value is not None
        and value != ""
    }

    # ========================================================
    # EDIT DETECTION
    # ========================================================

    has_existing_data = bool(current_data)

    edit_request = (
        has_existing_data
        and user_message
        and is_edit_request(user_message)
    )

    # ========================================================
    # GRAPH INPUT
    # ========================================================

    graph_input = {

        "complaint_text":
            complaint_text,

        "user_message":
            user_message or pdf_text,

        "edit_prompt":
            user_message
            if edit_request
            else None,

        # ----------------------------------------------------
        # COMPLAINT
        # ----------------------------------------------------

        "complaint_source":
            current_data.get(
                "complaint_source"
            ),

        "origin":
            current_data.get(
                "complaint_source"
            ),

        "customer_name":
            current_data.get(
                "customer_name"
            ),

        "product_name":
            current_data.get(
                "product_name"
            ),

        "product_strength":
            current_data.get(
                "product_strength"
            ),

        "batch_number":
            current_data.get(
                "batch_number"
            ),

        "manufacturing_date":
            current_data.get(
                "manufacturing_date"
            ),

        "expiry_date":
            current_data.get(
                "expiry_date"
            ),

        "quantity_affected":
            current_data.get(
                "quantity_affected"
            ),

        "complaint_category":
            current_data.get(
                "complaint_category"
            ),

        "complaint_date":
            current_data.get(
                "complaint_date"
            ),

        "description":
            current_data.get(
                "description"
            ),

        # ----------------------------------------------------
        # ASSESSMENT
        # ----------------------------------------------------

        "risk_severity":
            current_data.get(
                "risk_severity"
            ),

        "severity_of_risk":
            current_data.get(
                "risk_severity"
            ),

        "risk_reason":
            current_data.get(
                "risk_reason"
            ),

        "suggested_next_action":
            current_data.get(
                "suggested_next_action"
            ),

        "possible_root_causes":
            current_data.get(
                "possible_root_causes"
            ),

        "capa":
            current_data.get(
                "capa"
            ),

        "corrective_action":
            current_data.get(
                "corrective_action"
            ),

        "preventive_action":
            current_data.get(
                "preventive_action"
            )
    }

    # ========================================================
    # RUN SAME LANGGRAPH
    # ========================================================

    try:

        result = graph.invoke(
            graph_input
        )

    except Exception as e:

        print(
            "\n========== PDF COPILOT ERROR =========="
        )

        print(str(e))

        print(
            "=======================================\n"
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "AI processing of PDF failed: "
                f"{str(e)}"
            )
        )

    # ========================================================
    # DEBUG
    # ========================================================

    print(
        "\n========== PDF GRAPH RESULT =========="
    )

    print(result)

    print(
        "======================================\n"
    )

    # ========================================================
    # NORMALIZE
    # ========================================================

    extracted = normalize_data(
        result
    )

    # ========================================================
    # MERGE CURRENT DATA
    # ========================================================

    extracted = merge_existing_data(
        extracted,
        current_data
    )

    # ========================================================
    # COMPLETENESS
    # ========================================================

    completeness = check_completeness(
        extracted
    )

    # ========================================================
    # INCOMPLETE
    # ========================================================

    if not completeness["is_complete"]:

        missing = ", ".join(
            completeness["missing_fields"]
        )

        assistant_message = (
            "I extracted the available complaint "
            "information from the PDF. Before I "
            "continue with the AI assessment, "
            "please provide: "
            f"{missing}."
        )

        return {

            "message":
                assistant_message,

            "data":
                extracted,

            "is_complete":
                False,

            "missing_fields":
                completeness[
                    "missing_fields"
                ],

            "ready_for_assessment":
                False,

            "ready_for_qms":
                False,

            "workflow_stage":
                "Waiting for Information",

            "interaction_type":
                "file"
        }

    # ========================================================
    # COMPLETE
    # ========================================================

    if not extracted.get(
        "complaint_category"
    ):

        raise HTTPException(
            status_code=500,
            detail=(
                "AI assessment completed but "
                "complaint category was not generated."
            )
        )

    if not extracted.get(
        "risk_severity"
    ):

        raise HTTPException(
            status_code=500,
            detail=(
                "AI assessment completed but "
                "risk severity was not generated."
            )
        )

    # ========================================================
    # FINAL RESPONSE
    # ========================================================

    assistant_message = (
        "The PDF complaint has been extracted "
        "and the AI has determined the complaint "
        "category and completed the risk assessment, "
        "root cause analysis, corrective action, "
        "and preventive action."
    )

    return {

        "message":
            assistant_message,

        "data":
            extracted,

        "is_complete":
            True,

        "missing_fields":
            [],

        "ready_for_assessment":
            True,

        "ready_for_qms":
            True,

        "workflow_stage":
            result.get(
                "workflow_stage"
            )
            or "AI Assessment",

        "interaction_type":
            "file"
    }
# ============================================================
# SAVE / COMMIT TO QMS
# ============================================================

@router.post("/save")
def save_complaint(
    data: ComplaintSaveInput,
    db: Session = Depends(get_db)
):

    # ========================================================
    # PREPARE DATA FOR COMPLETENESS
    # ========================================================

    complaint_data = {

        "complaint_source":
            data.complaint_source,

        "customer_name":
            data.customer_name,

        "product_name":
            data.product_name,

        "product_strength":
            data.product_strength,

        "batch_number":
            data.batch_number,

        "manufacturing_date":
            data.manufacturing_date,

        "expiry_date":
            data.expiry_date,

        "quantity_affected":
            data.quantity_affected,

        "complaint_date":
            data.complaint_date,

        "description":
            data.description
    }

    # ========================================================
    # CHECK REQUIRED COMPLAINT INFORMATION
    #
    # Category is NOT part of this check because AI
    # determines it.
    # ========================================================

    completeness = check_completeness(
        complaint_data
    )

    if not completeness["is_complete"]:

        raise HTTPException(

            status_code=400,

            detail={

                "message":
                    (
                        "Complaint is incomplete. "
                        "Please provide all required "
                        "information before committing "
                        "to QMS."
                    ),

                "missing_fields":
                    completeness[
                        "missing_fields"
                    ]
            }
        )

    # ========================================================
    # AI CATEGORY
    # ========================================================

    if not data.complaint_category:

        raise HTTPException(

            status_code=400,

            detail=(
                "AI-generated complaint category "
                "is missing. Please run the AI "
                "assessment before saving."
            )
        )

    # ========================================================
    # AI RISK
    # ========================================================

    if not data.risk_severity:

        raise HTTPException(

            status_code=400,

            detail=(
                "AI-generated risk severity "
                "is missing. Please run the AI "
                "assessment before saving."
            )
        )

    # ========================================================
    # VALIDATE RISK
    # ========================================================

    allowed_risks = {
        "Low",
        "Medium",
        "High",
        "Critical"
    }

    risk = str(
        data.risk_severity
    ).strip().capitalize()

    if risk not in allowed_risks:

        raise HTTPException(

            status_code=400,

            detail=(
                "Risk severity must be "
                "Low, Medium, High, or Critical."
            )
        )

    # ========================================================
    # GENERATE COMPLAINT ID
    # ========================================================

    complaint_id = (
        f"CMP-{uuid.uuid4().hex[:8].upper()}"
    )

    # ========================================================
    # ROOT CAUSES
    # ========================================================

    root_causes = serialize_root_causes(
        data.possible_root_causes
    )

    # ========================================================
    # CREATE DATABASE RECORD
    # ========================================================

    complaint = Complaint(

        complaint_id=
            complaint_id,

        complaint_text=
            data.complaint_text,

        # ----------------------------------------------------
        # ORIGIN
        # ----------------------------------------------------

        complaint_source=
            data.complaint_source,

        customer_name=
            data.customer_name,

        # ----------------------------------------------------
        # PRODUCT
        # ----------------------------------------------------

        product_name=
            data.product_name,

        product_strength=
            data.product_strength,

        batch_number=
            data.batch_number,

        manufacturing_date=
            data.manufacturing_date,

        expiry_date=
            data.expiry_date,

        quantity_affected=
            data.quantity_affected,

        # ----------------------------------------------------
        # COMPLAINT
        # ----------------------------------------------------

        complaint_category=
            data.complaint_category,

        complaint_date=
            data.complaint_date,

        description=
            data.description,

        # ----------------------------------------------------
        # AI ASSESSMENT
        # ----------------------------------------------------

        risk_severity=
            risk,

        risk_reason=
            data.risk_reason,

        suggested_next_action=
            data.suggested_next_action,

        possible_root_causes=
            root_causes,

        # ----------------------------------------------------
        # CAPA
        # ----------------------------------------------------

        corrective_action=
            data.corrective_action,

        preventive_action=
            data.preventive_action,

        # ----------------------------------------------------
        # STATUS
        # ----------------------------------------------------

        status=
            "New"
    )

    # ========================================================
    # DATABASE COMMIT
    # ========================================================

    try:

        db.add(complaint)

        db.commit()

        db.refresh(complaint)

    except Exception as e:

        db.rollback()

        print(
            "\n========== QMS DATABASE ERROR =========="
        )

        print(str(e))

        print(
            "========================================\n"
        )

        raise HTTPException(

            status_code=500,

            detail=(
                "Failed to commit complaint "
                f"to QMS: {str(e)}"
            )
        )

    # ========================================================
    # RESPONSE
    # ========================================================

    return {

        "message":
            "Complaint successfully committed to QMS.",

        "complaint_id":
            complaint_id,

        "status":
            "New",

        "data": {

            "complaint_source":
                data.complaint_source,

            "customer_name":
                data.customer_name,

            "product_name":
                data.product_name,

            "product_strength":
                data.product_strength,

            "batch_number":
                data.batch_number,

            "manufacturing_date":
                data.manufacturing_date,

            "expiry_date":
                data.expiry_date,

            "quantity_affected":
                data.quantity_affected,

            "complaint_category":
                data.complaint_category,

            "complaint_date":
                data.complaint_date,

            "description":
                data.description,

            "risk_severity":
                risk,

            "risk_reason":
                data.risk_reason,

            "suggested_next_action":
                data.suggested_next_action,

            "possible_root_causes":
                data.possible_root_causes,

            "corrective_action":
                data.corrective_action,

            "preventive_action":
                data.preventive_action
        }
    }
