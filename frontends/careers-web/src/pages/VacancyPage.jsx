import { useEffect, useState } from "react";
import {
  Link,
  useNavigate,
  useParams,
} from "react-router-dom";

import {
  createCareerApplication,
  getVacancy,
} from "../api/client";
import { useAuth } from "../auth/AuthContext";

function formatDate(value) {
  if (!value) return "—";
  const date = new Date(`${value}T00:00:00`);
  if (Number.isNaN(date.getTime())) return value;
  return new Intl.DateTimeFormat("en-ZA", {
    day: "2-digit",
    month: "long",
    year: "numeric",
  }).format(date);
}

function TextBlock({ title, value }) {
  if (!value) return null;

  return (
    <section className="career-detail-section">
      <h2>{title}</h2>
      <div className="career-rich-text">{value}</div>
    </section>
  );
}

export default function VacancyPage() {
  const { vacancyCode } = useParams();
  const navigate = useNavigate();
  const { token, isAuthenticated } = useAuth();

  const [vacancy, setVacancy] = useState(null);
  const [coverLetter, setCoverLetter] = useState("");
  const [state, setState] = useState({
    loading: true,
    applying: false,
    error: "",
  });

  useEffect(() => {
    let active = true;

    getVacancy(vacancyCode)
      .then((response) => {
        if (!active) return;
        setVacancy(response?.vacancy || null);
        setState({
          loading: false,
          applying: false,
          error: "",
        });
      })
      .catch((error) => {
        if (!active) return;
        setState({
          loading: false,
          applying: false,
          error: error.message,
        });
      });

    return () => {
      active = false;
    };
  }, [vacancyCode]);

  async function startApplication(event) {
    event.preventDefault();

    setState((current) => ({
      ...current,
      applying: true,
      error: "",
    }));

    try {
      const response = await createCareerApplication(
        vacancy.vacancy_code,
        coverLetter,
        token,
      );

      const application = response?.application;

      if (!application?.id) {
        throw new Error("Application draft was created without an ID.");
      }

      navigate(`/applications/${application.id}`);
    } catch (error) {
      setState((current) => ({
        ...current,
        applying: false,
        error: error.message,
      }));
    }
  }

  if (state.loading) {
    return (
      <div className="career-loading-page">
        <div className="career-spinner" />
        <p>Loading vacancy...</p>
      </div>
    );
  }

  if (!vacancy) {
    return (
      <section className="career-page">
        <div className="career-container career-narrow">
          <div className="career-alert career-alert-error">
            {state.error || "Vacancy not found."}
          </div>
          <Link className="career-text-link" to="/">
            ← Back to vacancies
          </Link>
        </div>
      </section>
    );
  }

  const requiredDocuments = Array.isArray(vacancy.required_documents)
    ? vacancy.required_documents
    : [];

  return (
    <section className="career-page">
      <div className="career-container career-detail-layout">
        <div>
          <Link className="career-back-link" to="/">
            ← Back to vacancies
          </Link>

          <div className="career-vacancy-header">
            <div className="career-vacancy-card-top">
              <span className="career-code">{vacancy.vacancy_code}</span>
              <span className="career-type">{vacancy.employment_type}</span>
            </div>
            <h1>{vacancy.job_title}</h1>
            <div className="career-vacancy-meta">
              <span>🏢 {vacancy.department || "Glen Moniques"}</span>
              <span>📍 {vacancy.location || "To be confirmed"}</span>
              <span>
                👥 {vacancy.positions_available || 1} position
                {Number(vacancy.positions_available || 1) === 1 ? "" : "s"}
              </span>
            </div>
          </div>

          <TextBlock title="About the role" value={vacancy.description} />
          <TextBlock
            title="Responsibilities"
            value={vacancy.responsibilities}
          />
          <TextBlock
            title="Minimum requirements"
            value={vacancy.minimum_requirements}
          />
          <TextBlock
            title="Preferred requirements"
            value={vacancy.preferred_requirements}
          />

          {requiredDocuments.length ? (
            <section className="career-detail-section">
              <h2>Required documents</h2>
              <ul className="career-document-requirements">
                {requiredDocuments.map((document) => (
                  <li key={document}>✓ {document}</li>
                ))}
              </ul>
            </section>
          ) : null}
        </div>

        <aside className="career-apply-panel">
          <span className="career-eyebrow career-eyebrow-dark">
            Application
          </span>
          <h2>Interested in this role?</h2>

          <div className="career-apply-facts">
            <div>
              <span>Opening date</span>
              <strong>{formatDate(vacancy.opening_date)}</strong>
            </div>
            <div>
              <span>Closing date</span>
              <strong>{formatDate(vacancy.closing_date)}</strong>
            </div>
          </div>

          {isAuthenticated ? (
            <form onSubmit={startApplication}>
              <label className="career-field">
                <span>Cover Letter</span>
                <textarea
                  value={coverLetter}
                  onChange={(event) => setCoverLetter(event.target.value)}
                  maxLength={10000}
                  rows={8}
                  placeholder="Tell us why you are interested in this opportunity. Optional."
                />
                <small>Optional. Maximum 10,000 characters.</small>
              </label>

              {state.error ? (
                <div className="career-alert career-alert-error">
                  {state.error}
                </div>
              ) : null}

              <button
                className="career-button career-button-gold career-button-full"
                type="submit"
                disabled={state.applying}
              >
                {state.applying ? "Starting application..." : "Start Application →"}
              </button>
            </form>
          ) : (
            <div className="career-signin-prompt">
              <p>
                Sign in to your Careers account before starting an application.
              </p>
              <Link
                className="career-button career-button-navy career-button-full"
                to="/login"
                state={{
                  from: `/vacancies/${vacancy.vacancy_code}`,
                }}
              >
                Sign In to Apply
              </Link>
              <Link
                className="career-button career-button-light career-button-full"
                to="/create-account"
              >
                Create Careers Account
              </Link>
            </div>
          )}
        </aside>
      </div>
    </section>
  );
}
