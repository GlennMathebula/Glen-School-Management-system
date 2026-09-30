import { useState } from "react";
import { Link } from "react-router-dom";

import {
  getApplicationStatus,
  resendAcknowledgement,
} from "../api/client";
import "./ApplicationStatus.css";


function formatDate(value) {
  if (!value) return "—";

  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return String(value);
  }

  return new Intl.DateTimeFormat("en-ZA", {
    day: "2-digit",
    month: "short",
    year: "numeric",
  }).format(date);
}

function statusCopy(status) {
  switch (status) {
    case "Accepted":
      return {
        title: "Your application has been accepted.",
        text:
          "You can continue to the registration step when the registration window is open.",
      };

    case "Rejected":
      return {
        title: "Your application has been reviewed.",
        text:
          "The recorded application outcome is Rejected. Contact Admissions if you need clarification about the outcome.",
      };

    case "Outstanding Documents":
      return {
        title: "Admissions needs additional documents.",
        text:
          "Review the outstanding-document list below and follow the instructions sent by Admissions.",
      };

    default:
      return {
        title: "Your application is under review.",
        text:
          "Glen Moniques has received your application. Admissions will update the status after review.",
      };
  }
}

function InfoRow({ label, value }) {
  return (
    <div className="as-info-row">
      <span>{label}</span>
      <strong>{value || "—"}</strong>
    </div>
  );
}

export default function StatusPage() {
  const [studentNumber, setStudentNumber] = useState("");
  const [nationalId, setNationalId] = useState("");

  const [lookupState, setLookupState] = useState({
    loading: false,
    error: "",
    application: null,
  });

  const [resendState, setResendState] = useState({
    loading: false,
    error: "",
    message: "",
  });

  async function lookup(event) {
    event.preventDefault();

    setLookupState({
      loading: true,
      error: "",
      application: null,
    });

    setResendState({
      loading: false,
      error: "",
      message: "",
    });

    if (!/^\d{8}$/.test(studentNumber.trim())) {
      setLookupState({
        loading: false,
        error: "Enter your 8-digit student number.",
        application: null,
      });
      return;
    }

    if (!/^\d{13}$/.test(nationalId.trim())) {
      setLookupState({
        loading: false,
        error: "Enter your 13-digit South African ID number.",
        application: null,
      });
      return;
    }

    try {
      const response = await getApplicationStatus({
        studentNumber,
        nationalId,
      });

      setLookupState({
        loading: false,
        error: "",
        application: response?.application || null,
      });
    } catch (error) {
      setLookupState({
        loading: false,
        error: error.message,
        application: null,
      });
    }
  }

  async function resend() {
    setResendState({
      loading: true,
      error: "",
      message: "",
    });

    try {
      const response = await resendAcknowledgement(
        studentNumber,
        nationalId,
      );

      setResendState({
        loading: false,
        error: "",
        message:
          response?.message ||
          "Application acknowledgement was resent successfully.",
      });
    } catch (error) {
      setResendState({
        loading: false,
        error: error.message,
        message: "",
      });
    }
  }

  function reset() {
    setStudentNumber("");
    setNationalId("");
    setLookupState({
      loading: false,
      error: "",
      application: null,
    });
    setResendState({
      loading: false,
      error: "",
      message: "",
    });
  }

  const application = lookupState.application;
  const copy = application
    ? statusCopy(application.app_status)
    : null;

  return (
    <section className="as-page">
      <div className="as-shell">
        <div className="as-heading">
          <span className="as-kicker">Application services</span>
          <h1>Check Application Status</h1>
          <p>
            Verify your identity with the student number issued when you
            applied and your South African ID number.
          </p>
        </div>

        {!application ? (
          <form className="as-lookup-card" onSubmit={lookup}>
            <div className="as-security-note">
              <span>🔒</span>
              <div>
                <strong>Secure applicant lookup</strong>
                <p>
                  Both details must match the application record before any
                  status information is displayed.
                </p>
              </div>
            </div>

            <label className="as-field">
              <span>
                Student Number <b>*</b>
              </span>
              <input
                value={studentNumber}
                onChange={(event) => {
                  setStudentNumber(event.target.value.replace(/\D/g, ""));
                  setLookupState((current) => ({
                    ...current,
                    error: "",
                  }));
                }}
                inputMode="numeric"
                maxLength={8}
                placeholder="e.g. 20260010"
                required
              />
              <small>Your 8-digit application student number.</small>
            </label>

            <label className="as-field">
              <span>
                South African ID Number <b>*</b>
              </span>
              <input
                value={nationalId}
                onChange={(event) => {
                  setNationalId(event.target.value.replace(/\D/g, ""));
                  setLookupState((current) => ({
                    ...current,
                    error: "",
                  }));
                }}
                inputMode="numeric"
                maxLength={13}
                placeholder="13-digit SA ID"
                required
              />
              <small>
                Used only to verify that you are viewing your own application.
              </small>
            </label>

            {lookupState.error ? (
              <div className="as-alert as-error">{lookupState.error}</div>
            ) : null}

            <button
              className="as-button as-button-primary"
              type="submit"
              disabled={lookupState.loading}
            >
              {lookupState.loading ? "Checking..." : "Check status →"}
            </button>
          </form>
        ) : (
          <div className="as-results">
            <div className={`as-status-hero as-status-${application.app_status.toLowerCase().replace(/\s+/g, "-")}`}>
              <div className="as-status-top">
                <span className="as-status-label">Current application status</span>
                <span className="as-status-pill">{application.app_status}</span>
              </div>

              <h2>{copy.title}</h2>
              <p>{copy.text}</p>

              {application.app_status === "Accepted" ? (
                <Link className="as-button as-button-gold" to="/register">
                  Complete Registration →
                </Link>
              ) : null}
            </div>

            <div className="as-grid">
              <section className="as-card">
                <div className="as-card-head">
                  <span>📄</span>
                  <h3>Application Details</h3>
                </div>
                <div className="as-card-body">
                  <InfoRow
                    label="Student Number"
                    value={application.student_number}
                  />
                  <InfoRow
                    label="Applicant"
                    value={[application.first_name, application.last_name]
                      .filter(Boolean)
                      .join(" ")}
                  />
                  <InfoRow
                    label="Programme"
                    value={application.course_name || application.course_code}
                  />
                  <InfoRow
                    label="Intake"
                    value={application.cycle_name || application.cycle_code}
                  />
                  <InfoRow
                    label="Application submitted"
                    value={formatDate(application.created_at)}
                  />
                  <InfoRow
                    label="Last updated"
                    value={formatDate(application.updated_at)}
                  />
                </div>
              </section>

              <section className="as-card">
                <div className="as-card-head">
                  <span>📎</span>
                  <h3>Supporting Documents</h3>
                </div>
                <div className="as-card-body">
                  <div className="as-document-stats">
                    <div>
                      <strong>{application.documents_uploaded ?? 0}</strong>
                      <span>Uploaded</span>
                    </div>
                    <div>
                      <strong>{application.documents_pending_review ?? 0}</strong>
                      <span>Pending review</span>
                    </div>
                    <div>
                      <strong>{application.documents_approved ?? 0}</strong>
                      <span>Approved</span>
                    </div>
                  </div>

                  {application.documents?.length ? (
                    <div className="as-document-list">
                      {application.documents.map((document) => (
                        <div
                          className="as-document"
                          key={`${document.document_type}-${document.uploaded_at}`}
                        >
                          <div>
                            <strong>{document.document_label}</strong>
                            <small>{document.original_filename}</small>
                          </div>
                          <span className={`as-review as-review-${document.review_status.toLowerCase().replace(/\s+/g, "-")}`}>
                            {document.review_status}
                          </span>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="as-muted">
                      No supporting documents are currently recorded against
                      this application.
                    </p>
                  )}
                </div>
              </section>
            </div>

            {application.outstanding_documents?.length ? (
              <section className="as-outstanding">
                <div className="as-card-head">
                  <span>⚠️</span>
                  <h3>Outstanding Documents</h3>
                </div>
                <div className="as-card-body">
                  <p>
                    Admissions has requested the following:
                  </p>
                  <ul>
                    {application.outstanding_documents.map((item) => (
                      <li key={String(item)}>{String(item)}</li>
                    ))}
                  </ul>
                </div>
              </section>
            ) : null}

            <section className="as-card as-correspondence">
              <div className="as-card-head">
                <span>✉️</span>
                <h3>Application Acknowledgement</h3>
              </div>
              <div className="as-card-body">
                <p>
                  Need another copy of your acknowledgement? We will resend it
                  to the email address saved with this application
                  {application.email_masked
                    ? ` (${application.email_masked})`
                    : ""}.
                </p>

                {resendState.error ? (
                  <div className="as-alert as-error">{resendState.error}</div>
                ) : null}

                {resendState.message ? (
                  <div className="as-alert as-success">
                    {resendState.message}
                  </div>
                ) : null}

                <button
                  className="as-button as-button-secondary"
                  type="button"
                  onClick={resend}
                  disabled={resendState.loading}
                >
                  {resendState.loading
                    ? "Sending..."
                    : "Resend acknowledgement"}
                </button>
              </div>
            </section>

            <button
              className="as-reset"
              type="button"
              onClick={reset}
            >
              ← Check another application
            </button>
          </div>
        )}
      </div>
    </section>
  );
}
