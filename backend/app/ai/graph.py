
# ============================================================
# AIVOA AI - COMPLAINT LANGGRAPH WORKFLOW
# ============================================================

import os
import re
from datetime import datetime
from typing import TypedDict, Optional, List

from dotenv import load_dotenv
from pydantic import BaseModel, Field

from langgraph.graph import StateGraph, START, END
from langchain_groq import ChatGroq


# ============================================================
# ENVIRONMENT
# ============================================================

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY is not configured.")


# ============================================================
# LLM
# ============================================================

llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    temperature=0,
    groq_api_key=GROQ_API_KEY
)


# ============================================================
# 1. COMPLAINT EXTRACTION STRUCTURE
# ============================================================

class ComplaintExtraction(BaseModel):

    complaint_source: Optional[str] = None
    customer_name: Optional[str] = None

    product_name: Optional[str] = None
    product_strength: Optional[str] = None
    batch_number: Optional[str] = None

    manufacturing_date: Optional[str] = None
    expiry_date: Optional[str] = None

    quantity_affected: Optional[int] = None

    complaint_date: Optional[str] = None

    description: Optional[str] = None


# ============================================================
# 2. EDIT STRUCTURE
# ============================================================

class ComplaintEdit(BaseModel):

    complaint_source: Optional[str] = None
    customer_name: Optional[str] = None

    product_name: Optional[str] = None
    product_strength: Optional[str] = None
    batch_number: Optional[str] = None

    manufacturing_date: Optional[str] = None
    expiry_date: Optional[str] = None

    quantity_affected: Optional[int] = None

    complaint_date: Optional[str] = None

    description: Optional[str] = None


# ============================================================
# 3. CAPA STRUCTURE
# ============================================================

class CAPA(BaseModel):

    corrective_action: str = Field(
        description=(
            "Specific proposed corrective action to address "
            "the complaint and investigate the issue."
        )
    )

    preventive_action: str = Field(
        description=(
            "Specific proposed preventive action to prevent "
            "recurrence of the complaint."
        )
    )


# ============================================================
# 4. AI ASSESSMENT STRUCTURE
# ============================================================

class ComplaintAssessment(BaseModel):

    complaint_category: str = Field(
        description=(
            "AI-determined pharmaceutical complaint category "
            "such as Product Quality, Packaging, Labeling, "
            "Delivery, Adverse Event, Product Availability, "
            "Manufacturing, Storage, or Other."
        )
    )

    severity_of_risk: str = Field(
        description=(
            "Risk severity. Must be exactly "
            "Low, Medium, High, or Critical."
        )
    )

    risk_reason: str = Field(
        description="Reason for assigned risk severity."
    )

    suggested_next_action: str = Field(
        description="Recommended next action."
    )

    possible_root_causes: List[str] = Field(
        description=(
            "Possible root causes. These are hypotheses only "
            "and must not be treated as confirmed causes."
        )
    )

    capa: CAPA = Field(
        description=(
            "Proposed corrective and preventive actions. "
            "Both fields are mandatory."
        )
    )


# ============================================================
# 5. SHARED LANGGRAPH STATE
# ============================================================

class ComplaintState(TypedDict, total=False):

    complaint_text: str
    user_message: str
    edit_prompt: Optional[str]

    origin: Optional[str]
    complaint_source: Optional[str]

    customer_name: Optional[str]

    product_name: Optional[str]
    product_strength: Optional[str]
    batch_number: Optional[str]

    manufacturing_date: Optional[str]
    expiry_date: Optional[str]

    quantity_affected: Optional[int]

    complaint_category: Optional[str]
    complaint_date: Optional[str]

    description: Optional[str]

    severity: Optional[str]
    severity_of_risk: Optional[str]
    risk_level: Optional[str]
    risk_severity: Optional[str]

    risk_reason: Optional[str]

    suggested_next_action: Optional[str]

    possible_root_causes: List[str]

    capa: Optional[dict]

    corrective_action: Optional[str]
    preventive_action: Optional[str]

    missing_fields: List[str]
    completeness_status: str
    clarification_question: Optional[str]

    workflow_stage: str
    message: Optional[str]


# ============================================================
# 6. STRUCTURED LLMs
# ============================================================

structured_extractor = llm.with_structured_output(
    ComplaintExtraction
)

structured_editor = llm.with_structured_output(
    ComplaintEdit
)

structured_assessment = llm.with_structured_output(
    ComplaintAssessment
)


# ============================================================
# 7. HELPERS
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
# ROBUST DATE NORMALIZATION
# ============================================================

def normalize_date(value):

    """
    Convert common date formats into YYYY-MM-DD.

    Supported examples:

    2026-08-08
    2026/08/08
    08-08-2026
    08/08/2026
    8-8-2026
    8/8/2026
    August 8 2026
    August 8, 2026
    8 August 2026
    """

    value = clean_value(value)

    if not value:
        return None

    value = str(value).strip()

    # Remove ordinal suffixes:
    # 1st, 2nd, 3rd, 4th
    value = re.sub(
        r"(\d{1,2})(st|nd|rd|th)",
        r"\1",
        value,
        flags=re.IGNORECASE
    )

    # Remove commas
    value = value.replace(",", "")

    # --------------------------------------------------------
    # YYYY-MM-DD
    # --------------------------------------------------------

    formats = [

        "%Y-%m-%d",
        "%Y/%m/%d",

        "%d-%m-%Y",
        "%d/%m/%Y",

        "%m-%d-%Y",
        "%m/%d/%Y",

        "%d-%m-%y",
        "%d/%m/%y",

        "%B %d %Y",
        "%b %d %Y",

        "%d %B %Y",
        "%d %b %Y"
    ]

    for fmt in formats:

        try:

            parsed = datetime.strptime(
                value,
                fmt
            )

            return parsed.strftime(
                "%Y-%m-%d"
            )

        except ValueError:
            continue

    # --------------------------------------------------------
    # Search inside longer text
    # --------------------------------------------------------

    date_patterns = [

        r"\b\d{4}-\d{1,2}-\d{1,2}\b",

        r"\b\d{4}/\d{1,2}/\d{1,2}\b",

        r"\b\d{1,2}-\d{1,2}-\d{4}\b",

        r"\b\d{1,2}/\d{1,2}/\d{4}\b",

        r"\b[A-Za-z]+\s+\d{1,2}\s+\d{4}\b",

        r"\b\d{1,2}\s+[A-Za-z]+\s+\d{4}\b"
    ]

    for pattern in date_patterns:

        match = re.search(
            pattern,
            value
        )

        if match:

            candidate = match.group(0)

            normalized = normalize_date(
                candidate
            )

            if normalized:
                return normalized

    # If it cannot be safely normalized,
    # return original cleaned value.
    return value


# ============================================================
# EXPLICIT COMPLAINT DATE EXTRACTION
# ============================================================

def extract_complaint_date_from_text(text):

    """
    Deterministic fallback for complaint date.

    This is used when the LLM does not return
    complaint_date.

    Examples:

    Complaint date: 15/07/2026
    Complaint Date - 15-07-2026
    Complaint received on 15 July 2026
    Received on August 8, 2026
    Reported on 2026-08-08
    Submitted on 08/08/2026
    """

    if not text:
        return None

    text = str(text).strip()

    # --------------------------------------------------------
    # 1. Explicit complaint date
    # --------------------------------------------------------

    patterns = [

        r"(?:complaint\s+date|date\s+of\s+complaint)"
        r"\s*(?:is|was|:|-)?\s*"
        r"([0-9]{1,2}[/-][0-9]{1,2}[/-][0-9]{2,4})",

        r"(?:complaint\s+date|date\s+of\s+complaint)"
        r"\s*(?:is|was|:|-)?\s*"
        r"([A-Za-z]+\s+[0-9]{1,2}(?:st|nd|rd|th)?"
        r"\s*,?\s*[0-9]{4})",

        r"(?:complaint\s+date|date\s+of\s+complaint)"
        r"\s*(?:is|was|:|-)?\s*"
        r"([0-9]{1,2}(?:st|nd|rd|th)?\s+"
        r"[A-Za-z]+\s+[0-9]{4})"
    ]

    for pattern in patterns:

        match = re.search(
            pattern,
            text,
            flags=re.IGNORECASE
        )

        if match:

            normalized = normalize_date(
                match.group(1)
            )

            if normalized:
                return normalized

    # --------------------------------------------------------
    # 2. Complaint received/reported/submitted
    # --------------------------------------------------------

    received_patterns = [

        r"(?:complaint\s+)?"
        r"(?:received|reported|submitted|lodged|made)"
        r"(?:\s+by\s+[A-Za-z]+)?"
        r"\s+(?:on\s+)?"
        r"([0-9]{1,2}[/-][0-9]{1,2}[/-][0-9]{2,4})",

        r"(?:complaint\s+)?"
        r"(?:received|reported|submitted|lodged|made)"
        r"(?:\s+by\s+[A-Za-z]+)?"
        r"\s+(?:on\s+)?"
        r"([A-Za-z]+\s+[0-9]{1,2}(?:st|nd|rd|th)?"
        r"\s*,?\s*[0-9]{4})",

        r"(?:complaint\s+)?"
        r"(?:received|reported|submitted|lodged|made)"
        r"(?:\s+by\s+[A-Za-z]+)?"
        r"\s+(?:on\s+)?"
        r"([0-9]{1,2}(?:st|nd|rd|th)?\s+"
        r"[A-Za-z]+\s+[0-9]{4})"
    ]

    for pattern in received_patterns:

        match = re.search(
            pattern,
            text,
            flags=re.IGNORECASE
        )

        if match:

            normalized = normalize_date(
                match.group(1)
            )

            if normalized:
                return normalized

    return None


# ============================================================
# SOURCE
# ============================================================

def get_source(state):

    return clean_value(
        state.get("complaint_source")
        or state.get("origin")
    )


# ============================================================
# EXISTING DATA
# ============================================================

def has_existing_complaint_data(state):

    fields = [

        "complaint_source",
        "origin",
        "customer_name",

        "product_name",
        "product_strength",
        "batch_number",

        "manufacturing_date",
        "expiry_date",

        "quantity_affected",

        "complaint_date",
        "description"
    ]

    return any(
        clean_value(state.get(field)) is not None
        for field in fields
    )


# ============================================================
# 8. EXTRACTION NODE
# ============================================================

def extraction_node(state: ComplaintState):

    complaint_text = (
        state.get("complaint_text")
        or state.get("user_message")
        or ""
    )

    prompt = f"""
You are the complaint intake AI for a pharmaceutical
Quality Management System.

Extract factual information from the complaint below.

COMPLAINT:
{complaint_text}

Extract ONLY information explicitly present.

FIELDS:

1. Complaint source
2. Customer name
3. Product name
4. Product strength
5. Batch number
6. Manufacturing date
7. Expiry date
8. Quantity affected
9. Complaint date
10. Detailed complaint description


============================================================
VERY IMPORTANT - COMPLAINT DATE
============================================================

Complaint date means the date on which the complaint
was received, reported, submitted, lodged, or made.

Examples:

"Complaint date: 15/07/2026"
-> complaint_date = "2026-07-15"

"Complaint received on 15/07/2026"
-> complaint_date = "2026-07-15"

"Complaint was reported on August 8, 2026"
-> complaint_date = "2026-08-08"

"Complaint submitted by email on 2026-08-08"
-> complaint_date = "2026-08-08"

"Manufactured on 01/01/2026 and expires on 01/01/2028.
Complaint received on 05/08/2026."

-> manufacturing_date = "2026-01-01"
-> expiry_date = "2028-01-01"
-> complaint_date = "2026-08-05"


IMPORTANT:

- Extract manufacturing date separately.
- Extract expiry date separately.
- Extract complaint date separately.
- Do NOT confuse complaint date with manufacturing date.
- Do NOT confuse complaint date with expiry date.
- If multiple dates exist, identify what each date refers to.
- If the text explicitly says received/reported/submitted/made
  on a date, that date is the complaint date.
- Missing information must be null.
- Never guess a missing date.

Quantity must be numeric when explicitly available.

Do NOT determine complaint category here.

Do NOT generate risk assessment.

Do NOT generate root causes.

Do NOT generate CAPA.

Return structured data only.
"""

    result = structured_extractor.invoke(
        prompt
    )

    # ========================================================
    # LLM EXTRACTION
    # ========================================================

    source = clean_value(
        result.complaint_source
    )

    complaint_date = normalize_date(
        result.complaint_date
    )

    # ========================================================
    # DETERMINISTIC FALLBACK
    # ========================================================

    if not complaint_date:

        complaint_date = (
            extract_complaint_date_from_text(
                complaint_text
            )
        )

    extracted = {

        "origin":
            source,

        "complaint_source":
            source,

        "customer_name":
            clean_value(
                result.customer_name
            ),

        "product_name":
            clean_value(
                result.product_name
            ),

        "product_strength":
            clean_value(
                result.product_strength
            ),

        "batch_number":
            clean_value(
                result.batch_number
            ),

        "manufacturing_date":
            normalize_date(
                result.manufacturing_date
            ),

        "expiry_date":
            normalize_date(
                result.expiry_date
            ),

        "quantity_affected":
            result.quantity_affected,

        "complaint_date":
            complaint_date,

        "description":
            clean_value(
                result.description
            ),

        "workflow_stage":
            "Extraction"
    }

    # ========================================================
    # MERGE INTO STATE
    # ========================================================

    merged = dict(state)

    for key, value in extracted.items():

        if value is not None:

            merged[key] = value

    # ========================================================
    # PRESERVE SOURCE
    # ========================================================

    source = clean_value(
        merged.get("complaint_source")
        or merged.get("origin")
    )

    merged["origin"] = source
    merged["complaint_source"] = source

    # ========================================================
    # DEBUG
    # ========================================================

    print(
        "\n========== EXTRACTION RESULT =========="
    )

    print(
        "Complaint Date:",
        merged.get("complaint_date")
    )

    print(
        "Manufacturing Date:",
        merged.get("manufacturing_date")
    )

    print(
        "Expiry Date:",
        merged.get("expiry_date")
    )

    print(
        "=======================================\n"
    )

    return merged


# ============================================================
# 9. EDIT NODE
# ============================================================

def edit_node(state: ComplaintState):

    edit_prompt = (
        state.get("edit_prompt")
        or state.get("user_message")
        or ""
    )

    prompt = f"""
You are editing an existing pharmaceutical complaint.

CURRENT DATA:

Complaint Source:
{get_source(state)}

Customer:
{state.get("customer_name")}

Product:
{state.get("product_name")}

Strength:
{state.get("product_strength")}

Batch:
{state.get("batch_number")}

Manufacturing Date:
{state.get("manufacturing_date")}

Expiry Date:
{state.get("expiry_date")}

Quantity:
{state.get("quantity_affected")}

Complaint Date:
{state.get("complaint_date")}

Description:
{state.get("description")}

USER REQUEST:
{edit_prompt}

Rules:

1. Change ONLY what the user requests.
2. Preserve all other fields.
3. Never invent information.
4. Never set an existing field to null unless explicitly requested.
5. If the user changes the complaint date, return the new date.
6. If the user does not mention the complaint date,
   preserve the existing complaint date.
7. Return the complete updated complaint record.

Return structured data only.
"""

    result = structured_editor.invoke(
        prompt
    )

    updated = dict(state)

    fields = {

        "complaint_source":
            clean_value(
                result.complaint_source
            ),

        "customer_name":
            clean_value(
                result.customer_name
            ),

        "product_name":
            clean_value(
                result.product_name
            ),

        "product_strength":
            clean_value(
                result.product_strength
            ),

        "batch_number":
            clean_value(
                result.batch_number
            ),

        "manufacturing_date":
            normalize_date(
                result.manufacturing_date
            ),

        "expiry_date":
            normalize_date(
                result.expiry_date
            ),

        "quantity_affected":
            result.quantity_affected,

        "complaint_date":
            normalize_date(
                result.complaint_date
            ),

        "description":
            clean_value(
                result.description
            )
    }

    # ========================================================
    # APPLY ONLY NON-EMPTY VALUES
    # ========================================================

    for key, value in fields.items():

        if value is not None:

            updated[key] = value

    # ========================================================
    # FALLBACK FOR DATE EDIT
    # ========================================================

    if not updated.get("complaint_date"):

        fallback_date = (
            extract_complaint_date_from_text(
                edit_prompt
            )
        )

        if fallback_date:

            updated["complaint_date"] = (
                fallback_date
            )

    # ========================================================
    # SOURCE
    # ========================================================

    source = clean_value(
        updated.get("complaint_source")
        or updated.get("origin")
    )

    updated["origin"] = source
    updated["complaint_source"] = source

    updated["workflow_stage"] = "Updated"

    print(
        "\n========== EDIT RESULT =========="
    )

    print(
        "Complaint Date:",
        updated.get("complaint_date")
    )

    print(
        "=================================\n"
    )

    return updated


# ============================================================
# 10. COMPLETENESS
# ============================================================

def completeness_node(state: ComplaintState):

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

    missing = []

    for field, display_name in required_fields.items():

        value = state.get(field)

        if value is None:

            missing.append(
                display_name
            )

        elif (
            isinstance(value, str)
            and not value.strip()
        ):

            missing.append(
                display_name
            )

    if missing:

        question = (
            "I have extracted the available complaint "
            "information. Before I continue with the AI "
            "assessment, please provide: "
            + ", ".join(missing)
            + "."
        )

        return {

            "missing_fields":
                missing,

            "completeness_status":
                "Incomplete",

            "clarification_question":
                question,

            "workflow_stage":
                "Completeness Check",

            "message":
                question
        }

    return {

        "missing_fields":
            [],

        "completeness_status":
            "Complete",

        "clarification_question":
            None,

        "workflow_stage":
            "Completeness Check"
    }


# ============================================================
# 11. AI ASSESSMENT
# ============================================================

def assessment_node(state: ComplaintState):

    prompt = f"""
You are a pharmaceutical Quality Management System
complaint assessment specialist.

Analyze this complete complaint.

Complaint Source:
{get_source(state)}

Customer Name:
{state.get("customer_name")}

Product Name:
{state.get("product_name")}

Product Strength:
{state.get("product_strength")}

Batch Number:
{state.get("batch_number")}

Manufacturing Date:
{state.get("manufacturing_date")}

Expiry Date:
{state.get("expiry_date")}

Quantity Affected:
{state.get("quantity_affected")}

Complaint Date:
{state.get("complaint_date")}

Complaint Description:
{state.get("description")}


PERFORM THE FOLLOWING:

1. Determine the appropriate complaint category.
2. Assess risk severity.
3. Explain why that severity was selected.
4. Recommend the next investigation/action.
5. Identify possible root causes.
6. Generate CAPA.

The complaint category must be determined by AI.

Possible categories include:

- Product Quality
- Packaging
- Labeling
- Delivery
- Product Availability
- Adverse Event
- Manufacturing
- Storage
- Other

Risk severity MUST be exactly:

Low
Medium
High
Critical

Root causes are hypotheses only.

Do not claim that a root cause is confirmed.

CAPA MUST contain:

1. Corrective Action
2. Preventive Action

Do not invent laboratory results,
investigation results, or confirmed causes.

Return structured data only.
"""

    result = structured_assessment.invoke(
        prompt
    )

    risk = clean_value(
        result.severity_of_risk
    )

    allowed_risks = {
        "Low",
        "Medium",
        "High",
        "Critical"
    }

    if risk not in allowed_risks:

        risk = "Medium"

    root_causes = (
        result.possible_root_causes
        or []
    )

    root_causes = [

        str(cause).strip()

        for cause in root_causes

        if str(cause).strip()
    ]

    if not root_causes:

        root_causes = [
            "Root cause requires formal investigation."
        ]

    corrective = clean_value(
        result.capa.corrective_action
    )

    preventive = clean_value(
        result.capa.preventive_action
    )

    if not corrective:

        corrective = (
            "Investigate the complaint, inspect the "
            "affected batch, and determine the confirmed "
            "root cause."
        )

    if not preventive:

        preventive = (
            "Review relevant manufacturing, handling, "
            "storage, packaging, and transportation "
            "procedures and implement improvements as "
            "appropriate to prevent recurrence."
        )

    assessment = {

        "complaint_category":
            clean_value(
                result.complaint_category
            ),

        "severity":
            risk,

        "severity_of_risk":
            risk,

        "risk_level":
            risk,

        "risk_severity":
            risk,

        "risk_reason":
            clean_value(
                result.risk_reason
            ),

        "suggested_next_action":
            clean_value(
                result.suggested_next_action
            ),

        "possible_root_causes":
            root_causes,

        "capa": {

            "corrective_action":
                corrective,

            "preventive_action":
                preventive
        },

        "corrective_action":
            corrective,

        "preventive_action":
            preventive,

        "workflow_stage":
            "AI Assessment"
    }

    print(
        "\n========== AI ASSESSMENT =========="
    )

    print(
        "Complaint Date:",
        state.get("complaint_date")
    )

    print(
        "Category:",
        assessment.get(
            "complaint_category"
        )
    )

    print(
        "Risk:",
        assessment.get(
            "risk_severity"
        )
    )

    print(
        "===================================\n"
    )

    return assessment


# ============================================================
# 12. ROUTING
# ============================================================

def route_after_change(state):

    if (
        state.get("completeness_status")
        == "Incomplete"
    ):

        return "incomplete"

    return "assessment"


def incomplete_node(state):

    return {

        "workflow_stage":
            "Waiting for Information",

        "message":
            state.get(
                "clarification_question",
                "Please provide the missing complaint information."
            )
    }


# ============================================================
# 13. START ROUTING
# ============================================================

def route_from_start(state):

    message = (
        state.get("user_message")
        or state.get("complaint_text")
        or ""
    )

    has_existing_data = (
        has_existing_complaint_data(state)
    )

    explicit_edit = state.get(
        "edit_prompt"
    )

    if explicit_edit and has_existing_data:

        return "edit"

    if not has_existing_data:

        return "extraction"

    classification_prompt = f"""
Classify the user's latest message.

Existing complaint:

Customer:
{state.get("customer_name")}

Product:
{state.get("product_name")}

Batch:
{state.get("batch_number")}

Quantity:
{state.get("quantity_affected")}

Complaint Date:
{state.get("complaint_date")}

Description:
{state.get("description")}

USER MESSAGE:
{message}

Return ONLY:

EDIT

or

ADD

EDIT means the user wants to change an existing value.

ADD means the user is providing missing/additional information.
"""

    try:

        response = llm.invoke(
            classification_prompt
        )

        classification = (
            response.content
            or ""
        ).strip().upper()

    except Exception:

        classification = "ADD"

    if "EDIT" in classification:

        return "edit"

    return "extraction"


# ============================================================
# 14. BUILD GRAPH
# ============================================================

builder = StateGraph(
    ComplaintState
)


builder.add_node(
    "extraction",
    extraction_node
)

builder.add_node(
    "edit",
    edit_node
)

builder.add_node(
    "completeness",
    completeness_node
)

builder.add_node(
    "incomplete",
    incomplete_node
)

builder.add_node(
    "assessment",
    assessment_node
)


# ============================================================
# START
# ============================================================

builder.add_conditional_edges(

    START,

    route_from_start,

    {

        "extraction":
            "extraction",

        "edit":
            "edit"
    }
)


# ============================================================
# EXTRACTION / EDIT
# ============================================================

builder.add_edge(
    "extraction",
    "completeness"
)

builder.add_edge(
    "edit",
    "completeness"
)


# ============================================================
# COMPLETENESS
# ============================================================

builder.add_conditional_edges(

    "completeness",

    route_after_change,

    {

        "incomplete":
            "incomplete",

        "assessment":
            "assessment"
    }
)


# ============================================================
# END
# ============================================================

builder.add_edge(
    "incomplete",
    END
)

builder.add_edge(
    "assessment",
    END
)


# ============================================================
# COMPILE
# ============================================================

graph = builder.compile()
