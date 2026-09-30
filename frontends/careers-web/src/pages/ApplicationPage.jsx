import { useEffect, useMemo, useState } from "react";
import {
  Link,
  useNavigate,
  useParams,
} from "react-router-dom";

import {
  downloadCareerDocument,
  getMyApplication,
  submitCareerApplication,
  uploadCareerDocument,
  withdrawCareerApplication,
} from "../api/client";
import { useAuth } from "../auth/AuthContext";

function formatDate(value, withTime = false) {
  if (!value) return "—";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return String(value);

  return new Intl.DateTimeFormat("en-ZA", {
    day: "2-digit",
    month: "short",
    year: "numeric",
    ...(withTime
      ? {
          hour: "2-digit",
          minute: "2-digit",
        }
      : {}),
  }).format(date);
}

function statusClass(status) {
  return String(status || "")
    .toLowerCase()
    .replace(/\s+/g, "-");
}

function InfoRow({ label, value }) {
  return (
    <div className="career-info-row">
      <span>{label}</span>
      <strong>{value || "—"}</strong>
    </div>
  );
}

export default function ApplicationPage() {
  const { applicationId } = useParams();
  const navigate = useNavigate();
  const { token } = useAuth();

  const [data, setData] = useState(null);
  const [files, setFiles] = useState({});
  const [extraType, setExtraType] = useState("");
  const [extraFile, setExtraFile] = useState(null);

  const [state, setState] = useState({
    loading: true,
    busy: false,
    error: "",
    message: "",
  });

  async function load() {
    setState((current) => ({
      ...current,
      loading: true,
      error: "",
    }));

    try {
      const response = await getMyApplication(applicationId, token);
      setData(response?.data || null);
      setState({
        loading: false,
        busy: false,
        error: "",
        message: "",
      });
    } catch (error) {
      setState({
        loading: false,
        busy: false,
        error: error.message,
        message: "",
      });
    }
  }

  useEffect(() => {
    load();
  }, [applicationId, token]);

  const application = data?.application;
  const documents = data?.documents || [];
  const interview = data?.interview;
  const offer = data?.offer;

  const requiredDocuments = useMemo(
    () =>
      Array.isArray(application?.required_documents)
        ? application.required_documents
        : [],
    [application],
  );

  const uploadedTypes = useMemo(
    () => new Set(documents.map((document) => document.document_type)),
    [documents],
  );

  const missingDocuments = requiredDocuments.filter(
    (documentType) => !uploadedTypes.has(documentType),
  );

  async function uploadRequired(documentType) {
    const file = files[documentType];

    if (!file) {
      setState((current) => ({
        ...current,
        error: `Choose a file for ${documentType}.`,
        message: "",
      }));
      return;
    }

    setState((current) => ({
      ...current,
      busy: true,
      error: "",
      message: "",
    }));

    try {
      await uploadCareerDocument({
        applicationId,
        documentType,
        file,
        token,
      });

      setFiles((current) => ({
        ...current,
        [documentType]: null,
      }));

      await load();
      setState((current) => ({
        ...current,
        message: `${documentType} uploaded successfully.`,
      }));
    } catch (error) {
      setState((current) => ({
        ...current,
        busy: false,
        error: error.message,
      }));
    }
  }

  async function uploadExtra() {
    if (!extraType.trim() || !extraFile) {
      setState((current) => ({
        ...current,
        error: "Enter a document type and choose a file.",
        message: "",
      }));
      return;
    }

    setState((current) => ({
      ...current,
      busy: true,
      error: "",
      message: "",
    }));

    try {
      await uploadCareerDocument({
        applicationId,
        documentType: extraType.trim(),
        file: extraFile,
        token,
      });

      setExtraType("");
      setExtraFile(null);
      await load();

      setState((current) => ({
        ...current,
        message: "Additional document uploaded successfully.",
      }));
    } catch (error) {
      setState((current) => ({
        ...current,
        busy: false,
        error: error.message,
      }));
    }
  }

  async function submitApplication() {
    if (missingDocuments.length) {
      setState((current) => ({
        ...current,
        error: `Required documents still missing: ${missingDocuments.join(
          ", ",
        )}`,
        message: "",
      }));
      return;
    }

    setState((current) => ({
      ...current,
      busy: true,
      error: "",
      message: "",
    }));

    try {
      await submitCareerApplication(applicationId, token);
      await load();

      setState((current) => ({
        ...current,
        message: "Job application submitted successfully.",
      }));
    } catch (error) {
      setState((current) => ({
        ...current,
        busy: false,
        error: error.message,
      }));
    }
  }

  async function withdraw() {
    if (
      !window.confirm(
        "Withdraw this job application? This cannot be undone from the applicant portal.",
      )
    ) {
      return;
    }

    setState((current) => ({
      ...current,
      busy: true,
      error: "",
      message: "",
    }));

    try {
      await withdrawCareerApplication(applicationId, token);
      await load();

      setState((current) => ({
        ...current,
        message: "Application withdrawn.",
      }));
    } catch (error) {
      setState((current) => ({
        ...current,
        busy: false,
        error: error.message,
      }));
    }
  }

  if (state.loading) {
    return (
      <div className="career-loading-page">
        <div className="career-spinner" />
        <p>Loading application...</p>
      </div>
    );
  }

  if (!application) {
    return (
      <section className="career-page">
        <div className="career-container career-narrow">
          <div className="career-alert career-alert-error">
            {state.error || "Application not found."}
          </div>
          <button
            className="career-text-link career-link-button"
            type="button"
            onClick={() => navigate("/dashboard")}
          >
            ← Back to My Applications
          </button>
        </div>
      </section>
    );
  }

  const isDraft = application.status === "Draft";
  const canWithdraw = ![
    "Rejected",
    "Hired",
    "Withdrawn",
  ].includes(application.status);

  return (
    <section className="career-page">
      <div className="career-container">
        <Link className="career-back-link" to="/dashboard">
          ← Back to My Applications
        </Link>

        <div className="career-application-hero">
          <div>
            <span className="career-code">
              {application.application_number}
            </span>
            <h1>{application.job_title}</h1>
            <p>
              {application.department || "Glen Moniques"} ·{" "}
              {application.location || "Location TBC"}
            </p>
          </div>

          <span
            className={`career-status career-status-${statusClass(
              application.status,
            )}`}
          >
            {application.status}
          </span>
        </div>

        {state.error ? (
          <div className="career-alert career-alert-error">
            {state.error}
          </div>
        ) : null}

        {state.message ? (
          <div className="career-alert career-alert-success">
            {state.message}
          </div>
        ) : null}

        <div className="career-application-layout">
          <div>
            {isDraft ? (
              <>
                <section className="career-panel">
                  <div className="career-panel-head">
                    <span>📎</span>
                    <h2>Required Documents</h2>
                  </div>

                  <div className="career-panel-body">
                    {requiredDocuments.length ? (
                      <div className="career-upload-list">
                        {requiredDocuments.map((documentType) => {
                          const existing = documents.filter(
                            (document) =>
                              document.document_type === documentType,
                          );

                          return (
                            <div
                              className="career-upload-row"
                              key={documentType}
                            >
                              <div>
                                <strong>{documentType}</strong>
                                <small>
                                  {existing.length
                                    ? `${existing.length} file(s) uploaded`
                                    : "Required before submission"}
                                </small>
                              </div>

                              {existing.length ? (
                                <span className="career-check">
                                  ✓ Uploaded
                                </span>
                              ) : (
                                <div className="career-upload-controls">
                                  <input
                                    type="file"
                                    accept=".pdf,.doc,.docx,.jpg,.jpeg,.png"
                                    onChange={(event) =>
                                      setFiles((current) => ({
                                        ...current,
                                        [documentType]:
                                          event.target.files?.[0] || null,
                                      }))
                                    }
                                  />
                                  <button
                                    className="career-button career-button-light"
                                    type="button"
                                    disabled={
                                      state.busy || !files[documentType]
                                    }
                                    onClick={() =>
                                      uploadRequired(documentType)
                                    }
                                  >
                                    Upload
                                  </button>
                                </div>
                              )}
                            </div>
                          );
                        })}
                      </div>
                    ) : (
                      <p className="career-muted">
                        HR has not configured any mandatory documents for this
                        vacancy.
                      </p>
                    )}

                    <div className="career-file-note">
                      Allowed formats: PDF, DOC, DOCX, JPG, JPEG and PNG.
                      Maximum 10 MB per file.
                    </div>
                  </div>
                </section>

                <section className="career-panel">
                  <div className="career-panel-head">
                    <span>➕</span>
                    <h2>Additional Document</h2>
                  </div>
                  <div className="career-panel-body">
                    <div className="career-extra-upload">
                      <label className="career-field">
                        <span>Document Type</span>
                        <input
                          value={extraType}
                          onChange={(event) =>
                            setExtraType(event.target.value)
                          }
                          placeholder="e.g. Reference Letter"
                        />
                      </label>

                      <label className="career-field">
                        <span>File</span>
                        <input
                          type="file"
                          accept=".pdf,.doc,.docx,.jpg,.jpeg,.png"
                          onChange={(event) =>
                            setExtraFile(
                              event.target.files?.[0] || null,
                            )
                          }
                        />
                      </label>

                      <button
                        className="career-button career-button-light"
                        type="button"
                        disabled={
                          state.busy ||
                          !extraType.trim() ||
                          !extraFile
                        }
                        onClick={uploadExtra}
                      >
                        Upload Additional Document
                      </button>
                    </div>
                  </div>
                </section>
              </>
            ) : null}

            <section className="career-panel">
              <div className="career-panel-head">
                <span>📁</span>
                <h2>Uploaded Documents</h2>
              </div>

              <div className="career-panel-body">
                {documents.length ? (
                  <div className="career-documents-list">
                    {documents.map((document) => (
                      <div
                        className="career-document-row"
                        key={document.id}
                      >
                        <div>
                          <strong>{document.document_type}</strong>
                          <small>{document.original_filename}</small>
                        </div>
                        <span
                          className={`career-status career-status-${statusClass(
                            document.review_status,
                          )}`}
                        >
                          {document.review_status}
                        </span>
                        <button
                          className="career-text-link career-link-button"
                          type="button"
                          onClick={() =>
                            downloadCareerDocument({
                              applicationId,
                              documentId: document.id,
                              filename: document.original_filename,
                              token,
                            })
                          }
                        >
                          Download
                        </button>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="career-muted">
                    No documents uploaded yet.
                  </p>
                )}
              </div>
            </section>

            {interview ? (
              <section className="career-panel career-panel-highlight">
                <div className="career-panel-head">
                  <span>📅</span>
                  <h2>Interview</h2>
                </div>
                <div className="career-panel-body">
                  <InfoRow
                    label="Date & Time"
                    value={formatDate(interview.scheduled_at, true)}
                  />
                  <InfoRow label="Mode" value={interview.mode} />
                  <InfoRow
                    label="Venue"
                    value={interview.venue || "To be confirmed"}
                  />
                  <InfoRow label="Outcome" value={interview.outcome} />
                </div>
              </section>
            ) : null}

            {offer ? (
              <section className="career-panel career-panel-offer">
                <div className="career-panel-head">
                  <span>🤝</span>
                  <h2>Employment Offer</h2>
                </div>
                <div className="career-panel-body">
                  <InfoRow
                    label="Offer Status"
                    value={offer.status}
                  />
                  <InfoRow
                    label="Start Date"
                    value={formatDate(offer.start_date)}
                  />
                  <InfoRow
                    label="Employment Type"
                    value={offer.employment_type}
                  />
                  <div className="career-offer-summary">
                    {offer.offer_summary}
                  </div>
                </div>
              </section>
            ) : null}
          </div>

          <aside className="career-application-sidebar">
            <section className="career-panel">
              <div className="career-panel-head">
                <span>📋</span>
                <h2>Application Summary</h2>
              </div>
              <div className="career-panel-body">
                <InfoRow
                  label="Application Number"
                  value={application.application_number}
                />
                <InfoRow
                  label="Vacancy Code"
                  value={application.vacancy_code}
                />
                <InfoRow
                  label="Employment Type"
                  value={application.employment_type}
                />
                <InfoRow
                  label="Closing Date"
                  value={formatDate(application.closing_date)}
                />
                <InfoRow
                  label="Submitted"
                  value={formatDate(application.submitted_at)}
                />
              </div>
            </section>

            {application.cover_letter ? (
              <section className="career-panel">
                <div className="career-panel-head">
                  <span>✉️</span>
                  <h2>Cover Letter</h2>
                </div>
                <div className="career-panel-body">
                  <div className="career-rich-text">
                    {application.cover_letter}
                  </div>
                </div>
              </section>
            ) : null}

            {application.status_reason ? (
              <section className="career-panel">
                <div className="career-panel-head">
                  <span>ℹ️</span>
                  <h2>HR Update</h2>
                </div>
                <div className="career-panel-body">
                  <p className="career-muted">
                    {application.status_reason}
                  </p>
                </div>
              </section>
            ) : null}

            {isDraft ? (
              <button
                className="career-button career-button-gold career-button-full"
                type="button"
                disabled={state.busy}
                onClick={submitApplication}
              >
                {state.busy
                  ? "Please wait..."
                  : missingDocuments.length
                    ? `${missingDocuments.length} required document(s) missing`
                    : "Submit Application ✓"}
              </button>
            ) : null}

            {canWithdraw ? (
              <button
                className="career-button career-button-danger-outline career-button-full"
                type="button"
                disabled={state.busy}
                onClick={withdraw}
              >
                Withdraw Application
              </button>
            ) : null}
          </aside>
        </div>
      </div>
    </section>
  );
}
