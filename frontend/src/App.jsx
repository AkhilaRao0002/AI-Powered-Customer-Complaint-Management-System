import { useState } from "react";
import "./App.css";


const initialData = {
  complaint_source: "",
  customer_name: "",

  product_name: "",
  product_strength: "",
  batch_number: "",

  manufacturing_date: "",
  expiry_date: "",

  quantity_affected: "",

  complaint_category: "",
  complaint_date: "",

  description: "",

  risk_severity: "",
  risk_reason: "",

  suggested_next_action: "",

  possible_root_causes: [],

  corrective_action: "",
  preventive_action: "",
};


function App() {

  const [data, setData] = useState(initialData);

  const [copilotMessage, setCopilotMessage] =
    useState("");

  const [chatHistory, setChatHistory] =
    useState([]);

  const [selectedFile, setSelectedFile] =
    useState(null);

  const [loading, setLoading] =
    useState(false);

  const [message, setMessage] =
    useState("");

  const [completeness, setCompleteness] =
    useState({
      is_complete: false,
      missing_fields: [],
    });

  const [savedComplaintId, setSavedComplaintId] =
    useState(null);

  // ======================================================
// RESET / NEW COMPLAINT
// ======================================================

const resetForm = () => {

  setData(initialData);

  setCopilotMessage("");

  setChatHistory([]);

  setSelectedFile(null);

  setLoading(false);

  setMessage("");

  setCompleteness({
    is_complete: false,
    missing_fields: [],
  });

  setSavedComplaintId(null);

};
  // ======================================================
  // UPDATE FIELD
  // ======================================================

  const updateField = (field, value) => {

    setData((prev) => ({
      ...prev,
      [field]: value,
    }));

  };


  // ======================================================
  // FORMAT AI CONTENT
  // ======================================================

  const formatAIContent = (content) => {

    if (content === null || content === undefined) {
      return "";
    }

    if (typeof content === "string") {
      return content;
    }

    if (Array.isArray(content)) {

      return content
        .map((item) => {

          if (
            typeof item === "object" &&
            item !== null
          ) {
            return JSON.stringify(
              item,
              null,
              2
            );
          }

          return String(item);

        })
        .join("\n");

    }

    if (typeof content === "object") {

      return JSON.stringify(
        content,
        null,
        2
      );

    }

    return String(content);
  };


  // ======================================================
  // UPDATE FORM FROM AI
  // ======================================================

  const updateFromAI = (result) => {

    const aiData =
      result?.data || result || {};

    setData((prev) => ({

      ...prev,

      complaint_source:
        aiData.complaint_source ??
        prev.complaint_source,

      customer_name:
        aiData.customer_name ??
        prev.customer_name,

      product_name:
        aiData.product_name ??
        prev.product_name,

      product_strength:
        aiData.product_strength ??
        prev.product_strength,

      batch_number:
        aiData.batch_number ??
        prev.batch_number,

      manufacturing_date:
        aiData.manufacturing_date ??
        prev.manufacturing_date,

      expiry_date:
        aiData.expiry_date ??
        prev.expiry_date,

      quantity_affected:
        aiData.quantity_affected ??
        prev.quantity_affected,

      complaint_category:
        aiData.complaint_category ??
        prev.complaint_category,

      complaint_date:
        aiData.complaint_date ??
        prev.complaint_date,

      description:
        aiData.description ??
        prev.description,

      risk_severity:
        aiData.risk_severity ??
        aiData.severity_of_risk ??
        prev.risk_severity,

      risk_reason:
        aiData.risk_reason ??
        prev.risk_reason,

      suggested_next_action:
        aiData.suggested_next_action ??
        prev.suggested_next_action,

      possible_root_causes:
        aiData.possible_root_causes ??
        prev.possible_root_causes,

      corrective_action:
        aiData.corrective_action ??
        aiData.capa?.corrective_action ??
        prev.corrective_action,

      preventive_action:
        aiData.preventive_action ??
        aiData.capa?.preventive_action ??
        prev.preventive_action,

    }));

  };


  // ======================================================
  // SEND COPILOT MESSAGE
  // ======================================================

  const sendCopilotMessage = async () => {

    const text =
      copilotMessage.trim();

    if (!text && !selectedFile) {
      return;
    }

    setLoading(true);
    setMessage("");


    // ----------------------------------------------
    // SHOW USER MESSAGE
    // ----------------------------------------------

    setChatHistory((prev) => [

      ...prev,

      {
        role: "user",

        content:
          text ||
          `Uploaded file: ${
            selectedFile?.name || "file"
          }`,
      },

    ]);


    try {

      let response;


      // ==========================================
      // FILE
      // ==========================================

      if (selectedFile) {

        const formData =
          new FormData();

        formData.append(
          "file",
          selectedFile
        );

        formData.append(
          "message",
          text
        );

        formData.append(
          "current_data",
          JSON.stringify({
            ...data,

            quantity_affected:
              data.quantity_affected === ""
                ? null
                : Number(
                    data.quantity_affected
                  ),
          })
        );


        response = await fetch(
          "http://127.0.0.1:8000/ai/copilot/file",
          {
            method: "POST",
            body: formData,
          }
        );

      }


      // ==========================================
      // TEXT
      // ==========================================

      else {

        const payload = {

          message: text,

          current_data: {

            ...data,

            // IMPORTANT:
            // "" causes FastAPI 422.
            quantity_affected:
              data.quantity_affected === ""
                ? null
                : Number(
                    data.quantity_affected
                  ),

            // Empty strings should be null
            complaint_source:
              data.complaint_source || null,

            customer_name:
              data.customer_name || null,

            product_name:
              data.product_name || null,

            product_strength:
              data.product_strength || null,

            batch_number:
              data.batch_number || null,

            manufacturing_date:
              data.manufacturing_date || null,

            expiry_date:
              data.expiry_date || null,

            complaint_category:
              data.complaint_category || null,

            complaint_date:
              data.complaint_date || null,

            description:
              data.description || null,

            risk_severity:
              data.risk_severity || null,

            risk_reason:
              data.risk_reason || null,

            suggested_next_action:
              data.suggested_next_action || null,

            possible_root_causes:
              data.possible_root_causes || [],

            corrective_action:
              data.corrective_action || null,

            preventive_action:
              data.preventive_action || null,
          },
        };


        response = await fetch(
          "http://127.0.0.1:8000/ai/copilot",
          {

            method: "POST",

            headers: {
              "Content-Type":
                "application/json",
            },

            body:
              JSON.stringify(payload),

          }
        );

      }


      // ==========================================
      // RESPONSE
      // ==========================================

      const result =
        await response.json();


      if (!response.ok) {

        let errorMessage =
          "AI Copilot request failed.";

        if (
          typeof result.detail ===
          "string"
        ) {

          errorMessage =
            result.detail;

        } else if (
          Array.isArray(
            result.detail
          )
        ) {

          errorMessage =
            result.detail
              .map(
                (error) =>
                  error.msg ||
                  JSON.stringify(error)
              )
              .join("\n");

        } else if (
          result.detail
        ) {

          errorMessage =
            JSON.stringify(
              result.detail,
              null,
              2
            );

        }

        throw new Error(
          errorMessage
        );

      }


      // ==========================================
      // UPDATE FORM
      // ==========================================

      updateFromAI(result);


      // ==========================================
      // COMPLETENESS
      // ==========================================

      setCompleteness({

        is_complete:
          result.is_complete ??
          false,

        missing_fields:
          result.missing_fields ??
          [],

      });


      // ==========================================
      // AI MESSAGE
      // ==========================================

      const aiMessage =
        result.message ||
        "Information processed successfully.";


      setChatHistory((prev) => [

        ...prev,

        {

          role: "assistant",

          content:
            formatAIContent(
              aiMessage
            ),

        },

      ]);


      setCopilotMessage("");
      setSelectedFile(null);


    } catch (error) {

      console.error(error);


      setChatHistory((prev) => [

        ...prev,

        {

          role: "assistant",

          content:
            error.message ||
            "Unable to connect to AI Copilot.",

          error: true,

        },

      ]);


      setMessage(
        error.message ||
        "Failed to connect to backend."
      );


    } finally {

      setLoading(false);

    }

  };


  // ======================================================
  // FILE SELECT
  // ======================================================

  const handleFileChange = (event) => {

    const file =
      event.target.files?.[0];

    if (!file) {
      return;
    }

    setSelectedFile(file);


    setChatHistory((prev) => [

      ...prev,

      {

        role: "system",

        content:
          `Selected file: ${file.name}`,

      },

    ]);

  };


  // ======================================================
  // SAVE TO QMS
  // ======================================================

  const saveComplaint = async () => {

    if (!completeness.is_complete) {

      setMessage(
        "Please provide all required complaint information before saving."
      );

      return;
    }


    setLoading(true);
    setMessage("");


    try {

      const payload = {

        ...data,

        quantity_affected:
          data.quantity_affected === ""
            ? null
            : Number(
                data.quantity_affected
              ),

        possible_root_causes:
          Array.isArray(
            data.possible_root_causes
          )
            ? data.possible_root_causes
            : [],

        corrective_action:
          data.corrective_action || null,

        preventive_action:
          data.preventive_action || null,

      };


      const response =
        await fetch(
          "http://127.0.0.1:8000/ai/save",
          {

            method: "POST",

            headers: {
              "Content-Type":
                "application/json",
            },

            body:
              JSON.stringify(payload),

          }
        );


      const result =
        await response.json();


      if (!response.ok) {

        throw new Error(
          typeof result.detail ===
          "string"
            ? result.detail
            : JSON.stringify(
                result.detail,
                null,
                2
              )
        );

      }


      setSavedComplaintId(
        result.complaint_id ??
        result.id ??
        null
      );


      setMessage(
        result.message ||
        "Complaint successfully committed to QMS."
      );


    } catch (error) {

      console.error(error);

      setMessage(
        error.message ||
        "Failed to connect to QMS backend."
      );


    } finally {

      setLoading(false);

    }

  };


  // ======================================================
  // RENDER
  // ======================================================

  return (

    <div className="app">


      {/* ==================================================
          HEADER
      ================================================== */}

      <header className="app-header">

        <div>

          <h1>
            AI Complaint Management
          </h1>

          <p>
            AI-powered pharmaceutical complaint
            intake, assessment and QMS management
          </p>

        </div>

        <span className="status-badge">
          AI ENABLED
        </span>

      </header>


      {/* ==================================================
          MAIN
      ================================================== */}

      <div className="main-layout">


        {/* ==================================================
            LEFT - AI COPILOT
        ================================================== */}

        <section className="panel ai-panel">

          <div className="panel-header">

            <div>

              <h2>
                ✨ AI Complaint Copilot
              </h2>

              <p>
                Describe, upload or edit complaint
                information using one AI conversation.
              </p>

            </div>

            <span className="beta-badge">
              AI
            </span>

          </div>


          {/* CHAT */}

          <div className="chat-container">

            {chatHistory.length === 0 && (

              <div className="empty-chat">

                <div className="large-ai-icon">
                  ✦
                </div>

                <h3>
                  How can I help with this complaint?
                </h3>

              
              </div>

            )}


            {chatHistory.map(
              (chat, index) => (

                <div
                  key={index}
                  className={
                    `chat-message ${chat.role}`
                  }
                >

                  <div className="chat-role">

                    {chat.role === "user"
                      ? "You"
                      : chat.role === "assistant"
                      ? "AI Copilot"
                      : "System"}

                  </div>


                  <div
                    className={
                      `chat-bubble ${
                        chat.error
                          ? "chat-error"
                          : ""
                      }`
                    }
                  >

                    {formatAIContent(
                      chat.content
                    )}

                  </div>

                </div>

              )
            )}

          </div>


          {/* MISSING INFORMATION */}

          {!completeness.is_complete &&
            completeness.missing_fields.length > 0 && (

              <div className="missing-info-box">

                <strong>
                  ⚠ Missing Information
                </strong>

                <p>
                  Please provide:
                </p>

                <ul>

                  {completeness.missing_fields.map(
                    (field, index) => (

                      <li key={index}>
                        {field}
                      </li>

                    )
                  )}

                </ul>

              </div>

            )}


          {/* SELECTED FILE */}

          {selectedFile && (

            <div className="selected-file">

              <span>
                📎 {selectedFile.name}
              </span>

              <button
                type="button"
                onClick={() =>
                  setSelectedFile(null)
                }
              >
                ×
              </button>

            </div>

          )}


          {/* INPUT */}

          <div className="copilot-input-area">

            <textarea

              value={copilotMessage}

              onChange={(e) =>
                setCopilotMessage(
                  e.target.value
                )
              }

              onKeyDown={(e) => {

                if (
                  e.key === "Enter" &&
                  !e.shiftKey
                ) {

                  e.preventDefault();

                  if (!loading) {
                    sendCopilotMessage();
                  }

                }

              }}

              placeholder="Tell AI what you need..."

            />


            <div className="copilot-actions">

              <label className="upload-button">

                📎 Upload

                <input

                  type="file"

                  accept=".pdf"

                  onChange={
                    handleFileChange
                  }

                  hidden

                />

              </label>


              <button

                className="primary-button"

                onClick={
                  sendCopilotMessage
                }

                disabled={
                  loading ||
                  (
                    !copilotMessage.trim() &&
                    !selectedFile
                  )
                }

              >

                {loading
                  ? "Processing..."
                  : "Send ✦"}

              </button>

            </div>

          </div>


          {message && (

            <div className="message">
              {message}
            </div>

          )}

        </section>


        {/* ==================================================
            RIGHT - COMPLAINT
        ================================================== */}

        <section className="panel complaint-panel">

          <div className="panel-header">

            <div>

              <h2>
                Log Customer Complaint
              </h2>

              <p>
                Review AI-extracted information
                before committing to QMS.
              </p>

            </div>


            <span
              className={
                completeness.is_complete
                  ? "complete-badge"
                  : "pending-badge"
              }
            >

              {completeness.is_complete
                ? "Ready for QMS"
                : "Pending Information"}

            </span>

          </div>


          {/* ==================================================
              CUSTOMER
          ================================================== */}

          <div className="form-section">

            <h3>
              1. Origin & Customer Details
            </h3>

            <div className="form-grid">

              <label>

                Complaint Source

                <input

                  value={
                    data.complaint_source
                  }

                  onChange={(e) =>
                    updateField(
                      "complaint_source",
                      e.target.value
                    )
                  }

                />

              </label>


              <label>

                Customer Name

                <input

                  value={
                    data.customer_name
                  }

                  onChange={(e) =>
                    updateField(
                      "customer_name",
                      e.target.value
                    )
                  }

                />

              </label>

            </div>

          </div>


          {/* ==================================================
              PRODUCT
          ================================================== */}

          <div className="form-section">

            <h3>
              2. Product Details
            </h3>

            <div className="form-grid">

              <label>

                Product Name

                <input

                  value={
                    data.product_name
                  }

                  onChange={(e) =>
                    updateField(
                      "product_name",
                      e.target.value
                    )
                  }

                />

              </label>


              <label>

                Product Strength

                <input

                  value={
                    data.product_strength
                  }

                  onChange={(e) =>
                    updateField(
                      "product_strength",
                      e.target.value
                    )
                  }

                />

              </label>


              <label>

                Batch Number

                <input

                  value={
                    data.batch_number
                  }

                  onChange={(e) =>
                    updateField(
                      "batch_number",
                      e.target.value
                    )
                  }

                />

              </label>


              <label>

                Manufacturing Date

                <input

                  type="date"

                  value={
                    data.manufacturing_date
                  }

                  onChange={(e) =>
                    updateField(
                      "manufacturing_date",
                      e.target.value
                    )
                  }

                />

              </label>


              <label>

                Expiry Date

                <input

                  type="date"

                  value={
                    data.expiry_date
                  }

                  onChange={(e) =>
                    updateField(
                      "expiry_date",
                      e.target.value
                    )
                  }

                />

              </label>


              <label>

                Quantity Affected

                <input

                  type="number"

                  min="0"

                  value={
                    data.quantity_affected
                  }

                  onChange={(e) =>
                    updateField(
                      "quantity_affected",
                      e.target.value
                    )
                  }

                />

              </label>

            </div>

          </div>


          {/* ==================================================
              COMPLAINT
          ================================================== */}

          <div className="form-section">

            <h3>
              3. Complaint Details
            </h3>

            <div className="form-grid">

              <label>

                Complaint Category

                <input

                  value={
                    data.complaint_category
                  }

                  readOnly

                  placeholder="AI will determine category"

                />

              </label>


              <label>

                Complaint Date

                <input

                  type="date"

                  value={
                    data.complaint_date
                  }

                  onChange={(e) =>
                    updateField(
                      "complaint_date",
                      e.target.value
                    )
                  }

                />

              </label>

            </div>


            <label>

              Detailed Complaint Description

              <textarea

                value={
                  data.description
                }

                onChange={(e) =>
                  updateField(
                    "description",
                    e.target.value
                  )
                }

              />

            </label>

          </div>


          {/* ==================================================
              AI ASSESSMENT
          ================================================== */}

          <div className="form-section ai-assessment">

            <div className="assessment-title">

              <div>

                <h3>
                  🤖 AI Assessment
                </h3>

                <p>
                  AI-generated risk,
                  investigation and CAPA.
                </p>

              </div>

              <span className="ai-generated-badge">
                AI Generated
              </span>

            </div>


            <label>

              Complaint Category

              <input

                value={
                  data.complaint_category
                }

                readOnly

              />

            </label>


            <label>

              Severity of Risk

              <input

                value={
                  data.risk_severity
                }

                readOnly

              />

            </label>


            <label>

              Risk Reason

              <textarea

                value={
                  data.risk_reason
                }

                readOnly

              />

            </label>


            <label>

              Suggested Next Action

              <textarea

                value={
                  data.suggested_next_action
                }

                readOnly

              />

            </label>


            <label>

              Possible Root Causes

              <textarea

                value={
                  Array.isArray(
                    data.possible_root_causes
                  )
                    ? data.possible_root_causes
                        .map(
                          (cause) =>
                            `• ${cause}`
                        )
                        .join("\n")
                    : data.possible_root_causes
                }

                readOnly

              />

            </label>


            <label>

              Corrective Action

              <textarea

                value={
                  data.corrective_action
                }

                readOnly

              />

            </label>


            <label>

              Preventive Action

              <textarea

                value={
                  data.preventive_action
                }

                readOnly

              />

            </label>

          </div>


          {/* ==================================================
              SAVE
          ================================================== */}

          <div className="save-section">

              <button
                className="save-button"
                onClick={saveComplaint}
                disabled={
                  loading ||
                  !completeness.is_complete
                }
              >
                {loading
                  ? "Committing..."
                  : "💾 Commit to QMS"}
              </button>

              <button
                type="button"
                className="reload-button"
                onClick={resetForm}
                disabled={loading}
              >
                ↻ New Complaint
              </button>

            </div>


          {/* SUCCESS */}

          {savedComplaintId && (

            <div className="qms-success">

              <strong>
                ✓ Complaint committed to QMS
              </strong>

              <p>

                Complaint ID:{" "}

                <strong>
                  {savedComplaintId}
                </strong>

              </p>

            </div>

          )}

        </section>

      </div>

    </div>

  );
}


export default App;