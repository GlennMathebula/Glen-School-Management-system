import { useState } from "react";

import {
  publicRegistration,
  verifyPublicRegistration,
} from "../api/client";
import "./RegistrationWizard.css";


const STEPS = [
  "Verify",
  "Confirm Identity",
  "Registered",
];


function formatDate(value) {
  if (!value) return "—";

  const date = new Date(`${value}T00:00:00`);

  if (Number.isNaN(date.getTime())) {
    return String(value);
  }

  return new Intl.DateTimeFormat("en-ZA", {
    day: "2-digit",
    month: "short",
    year: "numeric",
  }).format(date);
}


function moduleTypeLabel(type) {
  return (
    {
      KM: "Knowledge Module",
      PM: "Practical Skills Module",
      WM: "Work Experience Module",
    }[type] ||
    type ||
    "Module"
  );
}


function Progress({ step }) {
  return (
    <div className="rw-progress">
      {STEPS.map((label, index) => {
        const number = index + 1;
        const complete = number < step;
        const active = number === step;

        return (
          <div className="rw-progress-part" key={label}>
            <div className="rw-step">
              <div
                className={[
                  "rw-dot",
                  complete ? "done" : "",
                  active ? "active" : "",
                ].join(" ")}
              >
                {complete ? "✓" : number}
              </div>
              <span className={active || complete ? "active" : ""}>
                {label}
              </span>
            </div>

            {number < STEPS.length ? (
              <div className={complete ? "rw-line done" : "rw-line"} />
            ) : null}
          </div>
        );
      })}
    </div>
  );
}


function InfoRow({ label, value }) {
  return (
    <div className="rw-info-row">
      <span>{label}</span>
      <strong>{value || "—"}</strong>
    </div>
  );
}


export default function RegisterPage() {
  const [step, setStep] = useState(1);

  const [verification, setVerification] = useState({
    student_number: "",
    id_or_passport: "",
  });

  const [preview, setPreview] = useState(null);

  const [identity, setIdentity] = useState({
    first_name: "",
    second_name: "",
    last_name: "",
    birth_date: "",
  });

  const [confirmAccuracy, setConfirmAccuracy] = useState(false);

  const [state, setState] = useState({
    loading: false,
    error: "",
  });

  const [result, setResult] = useState(null);


  function changeVerification(event) {
    const { name, value } = event.target;

    setVerification((current) => ({
      ...current,
      [name]:
        name === "student_number"
          ? value.replace(/\D/g, "")
          : value,
    }));

    setState({
      loading: false,
      error: "",
    });
  }


  function changeIdentity(event) {
    const { name, value } = event.target;

    setIdentity((current) => ({
      ...current,
      [name]: value,
    }));

    setState({
      loading: false,
      error: "",
    });
  }


  async function verify(event) {
    event.preventDefault();

    if (!/^\d{8}$/.test(verification.student_number)) {
      setState({
        loading: false,
        error: "Enter your 8-digit student number.",
      });
      return;
    }

    if (!verification.id_or_passport.trim()) {
      setState({
        loading: false,
        error: "Enter your SA ID or passport number.",
      });
      return;
    }

    setState({
      loading: true,
      error: "",
    });

    try {
      const response = await verifyPublicRegistration({
        student_number: verification.student_number,
        id_or_passport: verification.id_or_passport.trim(),
      });

      setPreview(response?.result || null);
      setStep(2);
      setState({
        loading: false,
        error: "",
      });

      window.scrollTo({
        top: 0,
        behavior: "smooth",
      });
    } catch (error) {
      setState({
        loading: false,
        error: error.message,
      });
    }
  }


  async function register(event) {
    event.preventDefault();

    const missing = [];

    if (!identity.first_name.trim()) {
      missing.push("first name");
    }

    if (!identity.last_name.trim()) {
      missing.push("last name");
    }

    if (!identity.birth_date) {
      missing.push("date of birth");
    }

    if (!confirmAccuracy) {
      missing.push("confirmation checkbox");
    }

    if (missing.length) {
      setState({
        loading: false,
        error: `Please complete: ${missing.join(", ")}.`,
      });
      return;
    }

    setState({
      loading: true,
      error: "",
    });

    try {
      const response = await publicRegistration({
        student_number: verification.student_number,
        id_or_passport: verification.id_or_passport.trim(),
        first_name: identity.first_name.trim(),
        second_name:
          identity.second_name.trim() || null,
        last_name: identity.last_name.trim(),
        birth_date: identity.birth_date,
      });

      setResult(response?.result || null);
      setStep(3);
      setState({
        loading: false,
        error: "",
      });

      window.scrollTo({
        top: 0,
        behavior: "smooth",
      });
    } catch (error) {
      setState({
        loading: false,
        error: error.message,
      });
    }
  }


  const pipeline = result?.registration || {};
  const account = pipeline?.student_account || {};
  const proof =
    pipeline?.documents?.proof_of_registration || {};
  const registrationEmail = pipeline?.email || {};


  return (
    <section className="rw-page">
      <div className="rw-shell">
        <div className="rw-heading">
          <span className="rw-kicker">Accepted applicants</span>
          <h1>Complete Registration</h1>
          <p>
            Registration is available only after your Glen Moniques application
            has been accepted. Verify your accepted application, review the
            programme and modules, then confirm your identity.
          </p>
        </div>

        <Progress step={step} />

        {state.error ? (
          <div className="rw-alert rw-error">
            {state.error}
          </div>
        ) : null}

        {step === 1 ? (
          <form className="rw-card" onSubmit={verify}>
            <div className="rw-card-head">
              <span>🔐</span>
              <h2>Verify Accepted Application</h2>
            </div>

            <div className="rw-card-body">
              <div className="rw-notice">
                <strong>Registration is not a new application.</strong>
                <p>
                  Use the student number issued during your application. Your
                  application must already be Accepted and the registration
                  window for the intake must be open.
                </p>
              </div>

              <div className="rw-grid">
                <label className="rw-field">
                  <span>Student Number <b>*</b></span>
                  <input
                    name="student_number"
                    value={verification.student_number}
                    onChange={changeVerification}
                    inputMode="numeric"
                    maxLength={8}
                    placeholder="e.g. 20260010"
                    required
                  />
                  <small>Your 8-digit Glen Moniques student number.</small>
                </label>

                <label className="rw-field">
                  <span>SA ID / Passport Number <b>*</b></span>
                  <input
                    name="id_or_passport"
                    value={verification.id_or_passport}
                    onChange={changeVerification}
                    maxLength={50}
                    placeholder="Identity number used on your application"
                    required
                  />
                  <small>Must match the accepted application.</small>
                </label>
              </div>

              <div className="rw-actions rw-actions-end">
                <button
                  type="submit"
                  className="rw-button rw-primary"
                  disabled={state.loading}
                >
                  {state.loading ? "Verifying..." : "Verify Application →"}
                </button>
              </div>
            </div>
          </form>
        ) : null}


        {step === 2 && preview ? (
          <>
            <section className="rw-verified">
              <div className="rw-verified-icon">✓</div>
              <div>
                <strong>Accepted application verified</strong>
                <p>Student Number: {preview.student_number}</p>
              </div>
            </section>

            <section className="rw-programme">
              <div>
                <span>Programme</span>
                <strong>
                  {preview.course?.course_name ||
                    preview.course?.course_code}
                </strong>
              </div>

              <div className="rw-programme-meta">
                <div>
                  <span>Qualification ID</span>
                  <strong>{preview.course?.course_code}</strong>
                </div>
                <div>
                  <span>NQF Level</span>
                  <strong>{preview.course?.nqf_level ?? "—"}</strong>
                </div>
                <div>
                  <span>Credits</span>
                  <strong>{preview.course?.credits ?? "—"}</strong>
                </div>
                <div>
                  <span>Intake</span>
                  <strong>
                    {preview.cycle?.cycle_name ||
                      preview.cycle?.cycle_code}
                  </strong>
                </div>
              </div>

              <div className="rw-dates">
                <InfoRow
                  label="Registration closes"
                  value={formatDate(
                    preview.cycle?.registration_end_date,
                  )}
                />
                <InfoRow
                  label="Programme starts"
                  value={formatDate(
                    preview.cycle?.program_start_date,
                  )}
                />
                <InfoRow
                  label="Expected completion"
                  value={formatDate(
                    preview.cycle?.expected_completion_date,
                  )}
                />
              </div>
            </section>

            <section className="rw-card">
              <div className="rw-card-head">
                <span>📚</span>
                <h2>Your Modules</h2>
              </div>

              <div className="rw-card-body">
                <div className="rw-module-summary">
                  <span>
                    Modules to be registered:{" "}
                    <strong>
                      {preview.module_count ??
                        preview.modules?.length ??
                        0}
                    </strong>
                  </span>
                  <span>
                    Total module credits:{" "}
                    <strong>{preview.module_credits ?? 0}</strong>
                  </span>
                </div>

                <div className="rw-module-list">
                  {(preview.modules || []).map((module) => (
                    <div
                      className="rw-module-item"
                      key={module.module_code}
                    >
                      <div className="rw-module-main">
                        <span className="rw-module-code">
                          {module.module_code}
                        </span>

                        <strong className="rw-module-name">
                          {module.module_name}
                        </strong>

                        <div className="rw-module-meta">
                          <span>
                            {moduleTypeLabel(module.module_type)}
                          </span>
                          <span>
                            NQF Level {module.nqf_level ?? "—"}
                          </span>
                        </div>
                      </div>

                      <div className="rw-module-credits">
                        <strong>{module.credits ?? 0}</strong>
                        <span>
                          {Number(module.credits) === 1
                            ? "credit"
                            : "credits"}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </section>

            <form className="rw-card" onSubmit={register}>
              <div className="rw-card-head">
                <span>👤</span>
                <h2>Confirm Your Identity</h2>
              </div>

              <div className="rw-card-body">
                <p className="rw-help">
                  Enter your first name, last name and date of birth exactly as
                  they appeared on your accepted application. A second or
                  middle name is optional.
                </p>

                <div className="rw-grid">
                  <label className="rw-field">
                    <span>First Name <b>*</b></span>
                    <input
                      name="first_name"
                      value={identity.first_name}
                      onChange={changeIdentity}
                      required
                    />
                  </label>

                  <label className="rw-field">
                    <span>Second / Middle Name</span>
                    <input
                      name="second_name"
                      value={identity.second_name}
                      onChange={changeIdentity}
                    />
                    <small>
                      Optional. Leave blank if you do not have one.
                    </small>
                  </label>

                  <label className="rw-field">
                    <span>Last Name <b>*</b></span>
                    <input
                      name="last_name"
                      value={identity.last_name}
                      onChange={changeIdentity}
                      required
                    />
                  </label>

                  <label className="rw-field">
                    <span>Date of Birth <b>*</b></span>
                    <input
                      name="birth_date"
                      value={identity.birth_date}
                      onChange={changeIdentity}
                      type="date"
                      required
                    />
                  </label>
                </div>

                <label className="rw-confirm">
                  <input
                    type="checkbox"
                    checked={confirmAccuracy}
                    onChange={(event) => {
                      setConfirmAccuracy(event.target.checked);
                      setState({
                        loading: false,
                        error: "",
                      });
                    }}
                  />
                  <span>
                    I confirm that the details above belong to me and match my
                    accepted Glen Moniques application.
                  </span>
                </label>

                {preview.email_masked ? (
                  <div className="rw-email-note">
                    Registration correspondence and the Proof of Registration
                    will be sent to the email saved on your application:{" "}
                    <strong>{preview.email_masked}</strong>
                  </div>
                ) : null}

                <div className="rw-actions">
                  <button
                    type="button"
                    className="rw-button rw-secondary"
                    onClick={() => {
                      setStep(1);
                      setPreview(null);
                      setState({
                        loading: false,
                        error: "",
                      });
                      window.scrollTo({
                        top: 0,
                        behavior: "smooth",
                      });
                    }}
                    disabled={state.loading}
                  >
                    ← Back
                  </button>

                  <button
                    type="submit"
                    className="rw-button rw-gold"
                    disabled={state.loading}
                  >
                    {state.loading
                      ? "Registering..."
                      : "Complete Registration ✓"}
                  </button>
                </div>
              </div>
            </form>
          </>
        ) : null}


        {step === 3 && result ? (
          <section className="rw-success-card">
            <div className="rw-success-icon">✓</div>
            <span className="rw-kicker">Registration complete</span>
            <h2>You are now registered.</h2>
            <p className="rw-success-copy">
              Your accepted application has been converted into an active Glen
              Moniques learner registration.
            </p>

            <div className="rw-student-number">
              {result.student_number}
            </div>

            <div className="rw-success-grid">
              <InfoRow
                label="Registration status"
                value={result.registration_status || "Registered"}
              />
              <InfoRow
                label="Intake"
                value={result.cycle_name || result.cycle}
              />
              <InfoRow
                label="Programme starts"
                value={formatDate(result.program_start_date)}
              />
              <InfoRow
                label="Expected completion"
                value={formatDate(result.expected_completion_date)}
              />
              <InfoRow
                label="Modules registered"
                value={
                  pipeline.modules_registered !== undefined
                    ? String(pipeline.modules_registered)
                    : "—"
                }
              />
              <InfoRow
                label="Student Portal account"
                value={account.created ? "Created" : "Not confirmed"}
              />
              <InfoRow
                label="Proof of Registration"
                value={proof.generated ? "Generated" : "Not confirmed"}
              />
              <InfoRow
                label="Registration email"
                value={registrationEmail.sent ? "Sent" : "Not confirmed"}
              />
            </div>

            {registrationEmail.sent ? (
              <div className="rw-success-note">
                Your registration email and Proof of Registration have been
                processed. Check the email address used on your application.
              </div>
            ) : (
              <div className="rw-warning-note">
                Your registration is complete, but email delivery was not
                confirmed. Keep your student number and contact Glen Moniques
                if you need your Proof of Registration resent.
              </div>
            )}
          </section>
        ) : null}
      </div>
    </section>
  );
}
