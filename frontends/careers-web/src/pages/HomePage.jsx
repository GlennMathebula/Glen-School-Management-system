import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";

import { getVacancies } from "../api/client";

function formatDate(value) {
  if (!value) return "—";
  const date = new Date(`${value}T00:00:00`);
  if (Number.isNaN(date.getTime())) return value;

  return new Intl.DateTimeFormat("en-ZA", {
    day: "2-digit",
    month: "short",
    year: "numeric",
  }).format(date);
}

export default function HomePage() {
  const [vacancies, setVacancies] = useState([]);
  const [query, setQuery] = useState("");
  const [state, setState] = useState({
    loading: true,
    error: "",
  });

  useEffect(() => {
    let active = true;

    getVacancies()
      .then((response) => {
        if (!active) return;
        setVacancies(response?.vacancies || []);
        setState({ loading: false, error: "" });
      })
      .catch((error) => {
        if (!active) return;
        setState({
          loading: false,
          error: error.message,
        });
      });

    return () => {
      active = false;
    };
  }, []);

  const filtered = useMemo(() => {
    const needle = query.trim().toLowerCase();

    if (!needle) return vacancies;

    return vacancies.filter((vacancy) =>
      [
        vacancy.job_title,
        vacancy.department,
        vacancy.location,
        vacancy.employment_type,
        vacancy.vacancy_code,
      ]
        .filter(Boolean)
        .some((value) =>
          String(value).toLowerCase().includes(needle),
        ),
    );
  }, [vacancies, query]);

  return (
    <>
      <section className="career-hero">
        <div className="career-container career-hero-grid">
          <div>
            <span className="career-eyebrow">
              Glen Moniques Careers
            </span>
            <h1>Build your career with us.</h1>
            <p>
              Browse current opportunities, apply online, upload your
              supporting documents and track your application from one secure
              Careers account.
            </p>

            <div className="career-hero-actions">
              <a className="career-button career-button-gold" href="#vacancies">
                View Vacancies
              </a>
              <Link
                className="career-button career-button-outline-light"
                to="/create-account"
              >
                Create Careers Account
              </Link>
            </div>
          </div>

          <div className="career-process">
            <span className="career-process-label">How it works</span>
            <div>
              <b>01</b>
              <p>
                <strong>Create an account</strong>
                <span>Keep your recruitment activity in one secure place.</span>
              </p>
            </div>
            <div>
              <b>02</b>
              <p>
                <strong>Apply online</strong>
                <span>Complete your application and upload required documents.</span>
              </p>
            </div>
            <div>
              <b>03</b>
              <p>
                <strong>Track progress</strong>
                <span>Follow review, interview and offer updates online.</span>
              </p>
            </div>
          </div>
        </div>
      </section>

      <section className="career-vacancies-section" id="vacancies">
        <div className="career-container">
          <div className="career-section-heading">
            <div>
              <span className="career-eyebrow career-eyebrow-dark">
                Current opportunities
              </span>
              <h2>Open Vacancies</h2>
            </div>

            <div className="career-search">
              <span>⌕</span>
              <input
                value={query}
                onChange={(event) => setQuery(event.target.value)}
                placeholder="Search title, department or location"
              />
            </div>
          </div>

          {state.error ? (
            <div className="career-alert career-alert-error">
              {state.error}
            </div>
          ) : null}

          {state.loading ? (
            <div className="career-empty">
              <div className="career-spinner" />
              <h3>Loading vacancies...</h3>
            </div>
          ) : filtered.length ? (
            <div className="career-vacancy-grid">
              {filtered.map((vacancy) => (
                <article
                  className="career-vacancy-card"
                  key={vacancy.vacancy_code}
                >
                  <div className="career-vacancy-card-top">
                    <span className="career-code">
                      {vacancy.vacancy_code}
                    </span>
                    <span className="career-type">
                      {vacancy.employment_type}
                    </span>
                  </div>

                  <h3>{vacancy.job_title}</h3>

                  <div className="career-vacancy-meta">
                    <span>🏢 {vacancy.department || "Glen Moniques"}</span>
                    <span>📍 {vacancy.location || "To be confirmed"}</span>
                    <span>
                      👥 {vacancy.positions_available || 1} position
                      {Number(vacancy.positions_available || 1) === 1
                        ? ""
                        : "s"}
                    </span>
                  </div>

                  <p className="career-vacancy-description">
                    {vacancy.description}
                  </p>

                  <div className="career-vacancy-footer">
                    <div>
                      <small>Closing date</small>
                      <strong>{formatDate(vacancy.closing_date)}</strong>
                    </div>
                    <Link
                      className="career-text-link"
                      to={`/vacancies/${vacancy.vacancy_code}`}
                    >
                      View vacancy →
                    </Link>
                  </div>
                </article>
              ))}
            </div>
          ) : (
            <div className="career-empty">
              <div className="career-empty-icon">💼</div>
              <h3>
                {vacancies.length
                  ? "No vacancies match your search."
                  : "No vacancies currently open."}
              </h3>
              <p>
                {vacancies.length
                  ? "Try a different title, department or location."
                  : "New Glen Moniques opportunities will appear here once HR publishes them."}
              </p>
            </div>
          )}
        </div>
      </section>
    </>
  );
}
