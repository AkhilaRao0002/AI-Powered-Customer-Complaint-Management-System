
# ============================================================
# AIVOA AI - COMPLAINT ASSESSMENT
# ============================================================

from langchain_groq import ChatGroq
from ..config import GROQ_API_KEY

import json
import re


# ============================================================
# GROQ LLM
# ============================================================

llm = ChatGroq(
    model="llama-3.1-8b-instant",
    temperature=0,
    groq_api_key=GROQ_API_KEY
)


# ============================================================
# ASSESS COMPLAINT
# ============================================================

def assess_complaint(
    complaint_text,
    customer_name=None,
    product_name=None,
    product_strength=None,
    product_type=None,
    batch_number=None,
    manufacturing_date=None,
    expiry_date=None,
    quantity_affected=None,
    complaint_category=None,
    complaint_date=None,
    description=None
):
    """
    Performs AI assessment after complaint information
    is considered complete.

    Returns:
        complaint_category
        risk_severity
        risk_level
        suggested_next_action
        possible_root_causes
        capa

    The function supports both:
        product_strength
        product_type

    for compatibility with the existing graph and routes.
    """

    # --------------------------------------------------------
    # PRODUCT STRENGTH COMPATIBILITY
    # --------------------------------------------------------

    if not product_strength:
        product_strength = product_type

    # --------------------------------------------------------
    # AI PROMPT
    # --------------------------------------------------------

    prompt = f"""
You are a pharmaceutical Quality Management System (QMS)
complaint assessment assistant.

Analyze the following customer complaint.

Your job is to:

1. Categorize the complaint.
2. Assess the severity of the risk.
3. Suggest the next appropriate action.
4. Identify possible root causes.
5. Suggest CAPA (Corrective and Preventive Action).

IMPORTANT:

- Do not invent facts that are not supported by the complaint.
- Possible root causes must be clearly presented as POSSIBLE causes,
  not confirmed causes.
- CAPA recommendations must be proposed actions, not claims that
  an investigation has already confirmed the root cause.
- The final assessment should support a QMS complaint investigation.
- Be concise but useful.
- Return ONLY valid JSON.
- Do not return markdown.
- Do not return ```json.
- Do not add explanations outside JSON.

Complaint Information:

Customer Name:
{customer_name}

Product Name:
{product_name}

Product Strength:
{product_strength}

Batch Number:
{batch_number}

Manufacturing Date:
{manufacturing_date}

Expiry Date:
{expiry_date}

Quantity Affected:
{quantity_affected}

Complaint Category:
{complaint_category}

Complaint Date:
{complaint_date}

Detailed Complaint Description:
{description}

Original Complaint:
{complaint_text}

------------------------------------------------------------
RISK SEVERITY
------------------------------------------------------------

risk_severity MUST be exactly one of:

Low
Medium
High
Critical

Use the following general interpretation:

Low:
Minor issue with little or no expected impact on product quality,
safety, efficacy, or patient health.

Medium:
Potential quality issue that requires investigation but does not
indicate an immediate serious patient or product risk.

High:
Potential significant product quality, safety, efficacy, or
patient impact requiring prompt investigation and action.

Critical:
Potential serious or life-threatening patient impact, major
product quality failure, contamination, incorrect product,
serious adverse impact, or another issue requiring immediate
escalation.

Do not exaggerate severity without evidence.

------------------------------------------------------------
REQUIRED JSON
------------------------------------------------------------

Return EXACTLY this structure:

{{
    "complaint_category": "string",

    "risk_severity": "Low",

    "suggested_next_action": "string",

    "possible_root_causes": [
        "possible cause 1",
        "possible cause 2"
    ],

    "capa": {{
        "corrective_action": "string",
        "preventive_action": "string"
    }}
}}

Rules:

- complaint_category must be a concise category.
- risk_severity must be Low, Medium, High, or Critical.
- suggested_next_action must explain what should happen next.
- possible_root_causes must be a JSON array.
- Do not state possible causes as confirmed facts.
- capa must contain both corrective_action and preventive_action.
"""

    # ========================================================
    # CALL GROQ
    # ========================================================

    try:

        response = llm.invoke(prompt)

        content = response.content

        if not content:
            raise ValueError(
                "LLM returned an empty response."
            )

        content = content.strip()

        print(
            "\n========== AI ASSESSMENT RESPONSE =========="
        )
        print(content)
        print(
            "=============================================\n"
        )

        # ====================================================
        # REMOVE MARKDOWN CODE FENCES
        # ====================================================

        content = re.sub(
            r"```json\s*",
            "",
            content,
            flags=re.IGNORECASE
        )

        content = re.sub(
            r"```\s*",
            "",
            content
        )

        content = content.strip()

        # ====================================================
        # EXTRACT JSON OBJECT
        # ====================================================

        match = re.search(
            r"\{.*\}",
            content,
            re.DOTALL
        )

        if not match:

            raise ValueError(
                "LLM did not return a valid JSON object."
            )

        json_text = match.group(0)

        # ====================================================
        # PARSE JSON
        # ====================================================

        result = json.loads(json_text)

        # ====================================================
        # EXTRACT COMPLAINT CATEGORY
        # ====================================================

        complaint_category_result = result.get(
            "complaint_category"
        )

        if not complaint_category_result:

            complaint_category_result = (
                "General Complaint"
            )

        # ====================================================
        # EXTRACT RISK
        # ====================================================

        risk_severity = result.get(
            "risk_severity"
        )

        if not risk_severity:

            # Compatibility with older graph/LLM output
            risk_severity = result.get(
                "risk_level"
            )

        if not risk_severity:

            risk_severity = "Medium"

        # ====================================================
        # EXTRACT NEXT ACTION
        # ====================================================

        suggested_next_action = result.get(
            "suggested_next_action"
        )

        if not suggested_next_action:

            suggested_next_action = (
                "Perform a formal complaint investigation "
                "and review the available product and batch "
                "information."
            )

        # ====================================================
        # EXTRACT POSSIBLE ROOT CAUSES
        # ====================================================

        possible_root_causes = result.get(
            "possible_root_causes"
        )

        if not isinstance(
            possible_root_causes,
            list
        ):

            possible_root_causes = [
                "Root cause requires investigation."
            ]

        # ====================================================
        # EXTRACT CAPA
        # ====================================================

        capa = result.get(
            "capa"
        )

        if not isinstance(capa, dict):

            capa = {
                "corrective_action": (
                    "Investigate the complaint and determine "
                    "the confirmed root cause."
                ),
                "preventive_action": (
                    "Review applicable procedures and implement "
                    "preventive controls based on investigation "
                    "findings."
                )
            }

        # ====================================================
        # CORRECTIVE ACTION
        # ====================================================

        corrective_action = capa.get(
            "corrective_action"
        )

        if not corrective_action:

            corrective_action = (
                "Investigate the complaint and determine "
                "the confirmed root cause."
            )

        # ====================================================
        # PREVENTIVE ACTION
        # ====================================================

        preventive_action = capa.get(
            "preventive_action"
        )

        if not preventive_action:

            preventive_action = (
                "Review applicable procedures and implement "
                "preventive controls based on investigation "
                "findings."
            )

        # ====================================================
        # NORMALIZE RISK
        # ====================================================

        allowed_risks = {
            "Low",
            "Medium",
            "High",
            "Critical"
        }

        normalized_risk = str(
            risk_severity
        ).strip().capitalize()

        if normalized_risk not in allowed_risks:

            normalized_risk = "Medium"

        # ====================================================
        # NORMALIZE ROOT CAUSES
        # ====================================================

        normalized_root_causes = [
            str(cause).strip()
            for cause in possible_root_causes
            if cause
        ]

        if not normalized_root_causes:

            normalized_root_causes = [
                "Root cause requires investigation."
            ]

        # ====================================================
        # FINAL RESULT
        # ====================================================

        final_result = {

            "complaint_category":
                str(
                    complaint_category_result
                ).strip(),

            # New canonical field
            "risk_severity":
                normalized_risk,

            # Compatibility field used by existing ai.py
            "risk_level":
                normalized_risk,

            "suggested_next_action":
                str(
                    suggested_next_action
                ).strip(),

            "possible_root_causes":
                normalized_root_causes,

            "capa": {

                "corrective_action":
                    str(
                        corrective_action
                    ).strip(),

                "preventive_action":
                    str(
                        preventive_action
                    ).strip()
            }
        }

        print(
            "\n========== FINAL AI ASSESSMENT =========="
        )

        print(
            json.dumps(
                final_result,
                indent=4
            )
        )

        print(
            "=========================================\n"
        )

        return final_result

    # ========================================================
    # ERROR HANDLING
    # ========================================================

    except Exception as e:

        print(
            "\n========== AI ASSESSMENT ERROR =========="
        )

        print(str(e))

        print(
            "=========================================\n"
        )

        # Never crash the API because of malformed
        # LLM output.

        fallback_result = {

            "complaint_category":
                "General Complaint",

            "risk_severity":
                "Medium",

            # Compatibility with ai.py
            "risk_level":
                "Medium",

            "suggested_next_action":
                (
                    "Perform manual complaint investigation "
                    "and review all available information."
                ),

            "possible_root_causes":
                [
                    "Root cause could not be determined automatically."
                ],

            "capa": {

                "corrective_action":
                    (
                        "Perform a formal investigation to "
                        "determine the confirmed root cause."
                    ),

                "preventive_action":
                    (
                        "Review applicable procedures and "
                        "implement preventive measures based "
                        "on investigation findings."
                    )
            }
        }

        return fallback_result
