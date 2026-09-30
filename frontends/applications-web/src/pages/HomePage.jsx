import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { healthCheck } from "../api/client";

export default function HomePage() {
  const [backendState, setBackendState] = useState("checking");

  useEffect(() => {
    let active = true;

    healthCheck()
      .then(() => {
        if (active) setBackendState("online");
      })
      .catch(() => {
        if (active) setBackendState("offline");
      });

    return () => {
      active = false;
    };
  }, []);

  return (
    <>
      <section className="hero">
        <div className="container hero-grid">
          <div className="hero-copy">
            <span className="eyebrow">Applications & Registration</span>
            <h1>Start your learning journey with Glen Moniques.</h1>
            <p>
              Apply online, keep your student number safe, and complete
              registration once your application has been accepted.
            </p>

            <div className="hero-actions">
              <Link className="button button-gold" to="/apply">
                Start an application
              </Link>
              <Link className="button button-outline-light" to="/register">
                Complete registration
              </Link>
            </div>

            <div className={`api-chip api-${backendState}`}>
              <span className="api-dot" />
              {backendState === "checking" && "Checking backend connection"}
              {backendState === "online" && "FastAPI backend connected"}
              {backendState === "offline" && "Backend is not running locally"}
            </div>
          </div>

          <div className="hero-panel">
            <p className="panel-kicker">How it works</p>
            <ol className="steps">
              <li>
                <span>01</span>
                <div>
                  <strong>Apply</strong>
                  <p>Submit your personal and academic information.</p>
                </div>
              </li>
              <li>
                <span>02</span>
                <div>
                  <strong>Admissions review</strong>
                  <p>Keep your 8-digit student number for all follow-up.</p>
                </div>
              </li>
              <li>
                <span>03</span>
                <div>
                  <strong>Register</strong>
                  <p>
                    Accepted applicants verify their identity and register
                    during the active intake window.
                  </p>
                </div>
              </li>
            </ol>
          </div>
        </div>
      </section>

      <section className="container feature-section">
        <div className="section-heading">
          <span className="eyebrow eyebrow-dark">Self-service</span>
          <h2>What would you like to do?</h2>
        </div>

        <div className="card-grid">
          <Link className="action-card" to="/apply">
            <span className="card-number">01</span>
            <h3>New Application</h3>
            <p>
              Apply for admission and receive your student number by email.
            </p>
            <span className="card-link">Apply now →</span>
          </Link>

          <Link className="action-card" to="/status">
            <span className="card-number">02</span>
            <h3>Application Follow-up</h3>
            <p>
              Resend your acknowledgement while secure status lookup is being
              added.
            </p>
            <span className="card-link">Application services →</span>
          </Link>

          <Link className="action-card" to="/register">
            <span className="card-number">03</span>
            <h3>Accepted Applicant Registration</h3>
            <p>
              Verify your accepted application and create your student portal
              account.
            </p>
            <span className="card-link">Register →</span>
          </Link>
        </div>
      </section>
    </>
  );
}
