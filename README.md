# AI-Powered Pharmaceutical Complaint Management System

An AI-powered pharmaceutical complaint intake and assessment system that uses **React, FastAPI, LangGraph, LangChain, Groq LLM, and structured Pydantic outputs** to automate complaint processing.

The system allows users to enter complaints using natural language or upload complaint documents, automatically extracts structured complaint information, identifies missing information, supports natural-language editing, performs AI-based risk assessment, generates possible root causes and CAPA, and finally commits the completed complaint to the QMS.

---

## Features

* Natural-language complaint entry
* PDF/file upload
* Complaint text extraction
* AI-powered structured information extraction
* Automatic completeness checking
* Missing-information detection
* Natural-language complaint editing
* AI complaint categorization
* Risk severity assessment
* Risk reasoning
* Suggested next action
* Possible root-cause hypotheses
* Corrective Action generation
* Preventive Action generation
* AI Copilot chat interface
* Complaint review form
* QMS commitment
* Complaint ID generation
* Responsive frontend interface

---

## Architecture

```text
                    USER
                      |
                      v
               React Frontend
                      |
          +-----------+-----------+
          |                       |
      Text Input             PDF/File Upload
          |                       |
          +-----------+-----------+
                      |
                      v
               FastAPI Backend
                      |
                      v
              Text/File Processing
                      |
                      v
               LangGraph Workflow
                      |
          +-----------+-----------+
          |                       |
      Extraction                Edit
          |                       |
          +-----------+-----------+
                      |
                      v
              Completeness Check
                      |
                +-----+-----+
                |           |
           Incomplete    Complete
                |           |
                v           v
          Ask User     AI Assessment
                            |
             +--------------+--------------+
             |              |              |
          Category         Risk          CAPA
             |              |              |
             +--------------+--------------+
                            |
                            v
                     Structured JSON
                            |
                            v
                     React Frontend
                            |
                 +----------+----------+
                 |                     |
           Complaint Form        AI Assessment
                 |                     |
                 +----------+----------+
                            |
                            v
                       QMS Commit
```

---

## Technology Stack

### Frontend

* React
* JavaScript
* CSS
* Fetch API

### Backend

* Python
* FastAPI

### AI

* LangGraph
* LangChain
* ChatGroq
* Llama 3.3 70B Versatile

### Validation

* Pydantic

### Configuration

* python-dotenv

---

## Project Structure

A typical project structure is:

```text
project/
│
├── frontend/
│   ├── src/
│   │   ├── App.jsx
│   │   └── App.css
│   └── package.json
│
├── backend/
│   ├── app/
│   │   ├── routes/
│   │   │   └── ai.py
│   │   │
│   │   └── graph.py
│   │
│   ├── .env
│   └── requirements.txt
│
└── README.md
```

Adjust the folder names according to the actual project structure.

---

# Workflow

## 1. User Input

The user can enter a complaint directly into the AI Copilot.

Example:

```text
Customer ABC reported a packaging problem
with Paracetamol 500 mg from batch BTH24053.
```

The user can also upload a complaint document.

---

## 2. Frontend Request

For text input, React sends:

```text
POST /ai/copilot
```

For uploaded files:

```text
POST /ai/copilot/file
```

The frontend sends the complaint information to the FastAPI backend.

---

## 3. Backend Processing

FastAPI receives the request.

For uploaded files, the backend extracts the document text.

The resulting text is passed into the complaint processing workflow.

---

## 4. LangGraph Routing

The LangGraph workflow determines the appropriate operation.

```text
START
  |
  v
Start Router
  |
  +---- New complaint ----> Extraction
  |
  +---- Existing complaint -> Edit
```

---

## 5. Extraction

The extraction node uses the LLM with structured output to identify:

```text
Complaint Source
Customer Name
Product Name
Product Strength
Batch Number
Manufacturing Date
Expiry Date
Quantity Affected
Complaint Date
Description
```

The system does not intentionally guess missing values.

---

## 6. Completeness Check

The extracted information is checked against the required fields.

If information is missing, the system tells the user which fields are required.

Example:

```text
Please provide:
Expiry Date, Quantity Affected and Complaint Date.
```

The AI assessment is not performed until the required information is complete.

---

## 7. Editing

Users can update existing information through natural language.

Example:

```text
Change the affected quantity to 20.
```

The edit workflow updates the requested information while preserving the remaining complaint data.

---

## 8. AI Assessment

After the complaint is complete, the assessment node determines:

```text
Complaint Category
Risk Severity
Risk Reason
Suggested Next Action
Possible Root Causes
Corrective Action
Preventive Action
```

Risk severity is restricted to:

```text
Low
Medium
High
Critical
```

---

## 9. Frontend Update

The structured backend response is returned to React.

The `updateFromAI()` function updates the frontend state.

The information is displayed in:

### Log Customer Complaint

and:

### AI Assessment

The user can review the generated information before committing it.

---

## 10. QMS Commit

After completing the required fields, the user selects:

```text
Commit to QMS
```

The frontend sends the complaint to:

```text
POST /ai/save
```

The backend stores the complaint and returns a complaint ID.

---

# LangGraph Nodes

The workflow contains the following major nodes:

### `extraction`

Extracts factual complaint information.

### `edit`

Updates existing complaint information based on the user's instruction.

### `completeness`

Checks whether all required information is available.

### `incomplete`

Returns a message requesting missing information.

### `assessment`

Performs AI complaint categorization, risk assessment, root-cause hypothesis generation, and CAPA generation.

---

# Structured Models

The project uses Pydantic models for structured AI output.

## ComplaintExtraction

```text
complaint_source
customer_name
product_name
product_strength
batch_number
manufacturing_date
expiry_date
quantity_affected
complaint_date
description
```

## ComplaintEdit

Contains the same complaint fields and is used for updating existing complaint information.

## CAPA

```text
corrective_action
preventive_action
```

## ComplaintAssessment

```text
complaint_category
severity_of_risk
risk_reason
suggested_next_action
possible_root_causes
capa
```

---

# API Endpoints

| Endpoint           | Method | Purpose                           |
| ------------------ | ------ | --------------------------------- |
| `/ai/copilot`      | POST   | Process text complaint/request    |
| `/ai/copilot/file` | POST   | Process uploaded complaint file   |
| `/ai/save`         | POST   | Commit completed complaint to QMS |

---

# Environment Variables

Create a `.env` file in the backend.

```env
GROQ_API_KEY=your_groq_api_key
```

Do not commit the `.env` file to GitHub.

Add:

```text
.env
```

to `.gitignore`.

---

# Installation

## Backend

Create and activate a virtual environment:

```bash
python -m venv venv
```

Windows:

```bash
venv\Scripts\activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Configure:

```text
GROQ_API_KEY
```

Run the FastAPI application using the project's configured entry point.

---

# Frontend

Move into the frontend directory:

```bash
cd frontend
```

Install dependencies:

```bash
npm install
```

Start the React application:

```bash
npm run dev
```

The frontend will then communicate with the FastAPI backend.

---

# Example Use Case

### User enters:

```text
Customer ABC reported that Paracetamol 500 mg
batch BTH24053 has damaged packaging.
The complaint was received by email on August 8 2026.
```

### AI extracts:

```text
Complaint Source: Email
Customer Name: Customer ABC
Product Name: Paracetamol
Product Strength: 500 mg
Batch Number: BTH24053
Complaint Date: 2026-08-08
Description: Damaged packaging
```

If required fields are missing, the system asks the user for them.

After the complaint is complete, the AI generates:

```text
Complaint Category
Risk Severity
Risk Reason
Suggested Next Action
Possible Root Causes
Corrective Action
Preventive Action
```

The results are automatically populated into the complaint form and AI assessment section.

---

# PDF Workflow

```text
PDF Upload
    |
    v
React
    |
    v
/ai/copilot/file
    |
    v
FastAPI
    |
    v
Text Extraction
    |
    v
Complaint Text
    |
    v
LangGraph
    |
    v
Extraction
    |
    v
Completeness
    |
    v
Assessment
    |
    v
React Form
```

---

# Safety and Human Review

The system is designed as an AI-assisted complaint management tool.

AI-generated root causes are treated as hypotheses and should not be considered confirmed investigation results.

AI-generated corrective and preventive actions should be reviewed by appropriate personnel before implementation.

The final complaint should be reviewed by the user before QMS commitment.

---

# Future Improvements

Potential enhancements include:

* OCR for scanned PDFs
* Email ingestion
* Authentication
* Role-based access
* Audit trail
* Complaint dashboard
* Complaint search
* Complaint status tracking
* Automated notifications
* Enterprise QMS integration
* Advanced analytics
* Human approval workflow

---

# Conclusion

The AI-Powered Pharmaceutical Complaint Management System demonstrates how generative AI and LangGraph can be integrated into a structured pharmaceutical complaint-management workflow.

The application combines natural-language processing, document-based intake, structured information extraction, completeness validation, natural-language editing, AI assessment, risk analysis, root-cause hypothesis generation, CAPA generation, and QMS commitment in a single interface.

The system reduces manual data entry while maintaining a human review step before final QMS commitment.
