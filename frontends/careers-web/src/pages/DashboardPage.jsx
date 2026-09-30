import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";

import {
  getMyApplications,
  getVacancies,
} from "../api/client";
import { useAuth } from "../auth/AuthContext";

function formatDate(value) {
  if (!value) return "—";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return String(value);

  return new Intl.DateTimeFormat("en-ZA", {
    day: "2-digit",
    month: "short",
    year: "numeric",
  }).format(date);
}

function statusClass(status) {
  return String(status || "Draft")
    .toLowerCase()
    .replace(/\s+/g, "-");
}

export default function DashboardPage() {
  const { token, account } = useAuth();

  const [applications, setApplications] = useState([]);
  const [vacancies, setVacancies] = useState([]);
  const [state, setState] = useState({
    loading: true,
    error: "",
  });

  async function load() {
    setState({ loading: true, error: "" });

    try {
      const [applicationResponse, vacancyResponse] = await Promise.all([
        getMyApplications(token),
        getVacancies(),
      ]);

      setApplications(applicationResponse?.applications || []);
      setVacancies(vacancyResponse?.vacancies || []);
      setState({ loading: false, error: "" });
    } catch (error) {
      setState({
        loading: false,
        error: error.message,
      });
    }
  }

  useEffect(() => {
    load();
  }, [token]);

  const counts = useMemo(() => {
    const submitted = applications.filter(
      (application) => application.status !== "Draft",
    ).length;

    const active = applications.filter(
      (application) =>
        !["Rejected", "Withdrawn", "Hired"].includes(
          application.status,
        ),
    ).length;

    return {
      all: applications.length,
      submitted,
      active,
    };
  }, [applications]);

  return (
    <section className="career-page">
      <div className="career-container">
        <div className="career-dashboard-heading">
          <div>
            <span className="career-eyebrow career-eyebrow-dark">
              Careers dashboard
            </span>
            <h1>
              Welcome, {account?.first_name || "Applicant"}.
            </h1>
            <p>
              Track your Glen Moniques job applications and recruitment
              activity.
            </p>
          </div>

          <Link className="career-button career-button-gold" to="/">
            Browse Vacancies
          </Link>
        </div>

        <div className="career-stats">
          <div>
            <strong>{counts.all}</strong>
            <span>Total applications</span>
          </div>
          <div>
            <strong>{counts.submitted}</strong>
            <span>Submitted</span>
          </div>
          <div>
            <strong>{counts.active}</strong>
            <span>Active processes</span>
          </div>
          <div>
            <strong>{vacancies.length}</strong>
            <span>Open vacancies</span>
          </div>
        </div>

        {state.error ? (
          <div className="career-alert career-alert-error">
            {state.error}
          </div>
        ) : null}

        <section className="career-dashboard-section">
          <div className="career-section-heading compact">
            <div>
              <span className="career-eyebrow career-eyebrow-dark">
                Recruitment activity
              </span>
              <h2>My Applications</h2>
            </div>
          </div>

          {state.loading ? (
            <div className="career-empty">
              <div className="career-spinner" />
              <h3>Loading applications...</h3>
            </div>
          ) : applications.length ? (
            <div className="career-applications-list">
              {applications.map((application) => (
                <Link
                  className="career-application-row"
                  key={application.id}
                  to={`/applications/${application.id}`}
                >
                  <div>
                    <span className="career-code">
                      {application.application_number}
                    </span>
                    <h3>{application.job_title}</h3>
                    <p>
                      {application.department || "Glen Moniques"} ·{" "}
                      {application.location || "Location TBC"}
                    </p>
                  </div>

                  <div className="career-application-row-right">
                    <span
                      className={`career-status career-status-${statusClass(
                        application.status,
                      )}`}
                    >
                      {application.status}
                    </span>
                    <small>
                      {application.submitted_at
                        ? `Submitted ${formatDate(application.submitted_at)}`
                        : `Draft created ${formatDate(application.created_at)}`}
                    </small>
                    {application.interview_date ? (
                      <small>
                        Interview: {formatDate(application.interview_date)}
                      </small>
                    ) : null}
                  </div>
                </Link>
              ))}
            </div>
          ) : (
            <div className="career-empty">
              <div className="career-empty-icon">📝</div>
              <h3>You have not started any job applications.</h3>
              <p>
                Browse the current vacancies and start an application when you
                find a suitable opportunity.
              </p>
              <Link className="career-button career-button-navy" to="/">
                Browse Vacancies
              </Link>
            </div>
          )}
        </section>
      </div>
    </section>
  );
}
