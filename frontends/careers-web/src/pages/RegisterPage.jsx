import { useState } from "react";
import {
  Link,
  Navigate,
  useNavigate,
} from "react-router-dom";

import { registerCareerAccount } from "../api/client";
import { useAuth } from "../auth/AuthContext";

export default function RegisterPage() {
  const navigate = useNavigate();
  const { isAuthenticated, login } = useAuth();

  const [form, setForm] = useState({
    first_name: "",
    last_name: "",
    email: "",
    cell_number: "",
    national_id: "",
    password: "",
    confirm_password: "",
  });

  const [state, setState] = useState({
    loading: false,
    error: "",
  });

  if (isAuthenticated) {
    return <Navigate to="/dashboard" replace />;
  }

  function change(event) {
    const { name, value } = event.target;

    setForm((current) => ({
      ...current,
      [name]:
        name === "national_id"
          ? value.replace(/\D/g, "")
          : value,
    }));

    setState({ loading: false, error: "" });
  }

  async function submit(event) {
    event.preventDefault();

    if (form.password.length < 8) {
      setState({
        loading: false,
        error: "Password must contain at least 8 characters.",
      });
      return;
    }

    if (form.password !== form.confirm_password) {
      setState({
        loading: false,
        error: "Passwords do not match.",
      });
      return;
    }

    setState({ loading: true, error: "" });

    try {
      await registerCareerAccount({
        first_name: form.first_name.trim(),
        last_name: form.last_name.trim(),
        email: form.email.trim(),
        cell_number: form.cell_number.trim(),
        national_id: form.national_id.trim() || null,
        password: form.password,
      });

      await login(form.email.trim(), form.password);
      navigate("/dashboard", { replace: true });
    } catch (error) {
      setState({
        loading: false,
        error: error.message,
      });
    }
  }

  return (
    <section className="career-auth-page">
      <div className="career-auth-card career-auth-wide">
        <span className="career-eyebrow career-eyebrow-dark">
          Careers account
        </span>
        <h1>Create Account</h1>
        <p>
          Create one account to apply for Glen Moniques vacancies and track
          recruitment progress.
        </p>

        <form onSubmit={submit}>
          <div className="career-form-grid">
            <label className="career-field">
              <span>First Name *</span>
              <input
                name="first_name"
                value={form.first_name}
                onChange={change}
                required
              />
            </label>

            <label className="career-field">
              <span>Last Name *</span>
              <input
                name="last_name"
                value={form.last_name}
                onChange={change}
                required
              />
            </label>

            <label className="career-field">
              <span>Email Address *</span>
              <input
                name="email"
                type="email"
                value={form.email}
                onChange={change}
                required
              />
            </label>

            <label className="career-field">
              <span>Cell Number *</span>
              <input
                name="cell_number"
                value={form.cell_number}
                onChange={change}
                required
              />
            </label>

            <label className="career-field">
              <span>South African ID Number</span>
              <input
                name="national_id"
                value={form.national_id}
                onChange={change}
                maxLength={13}
                inputMode="numeric"
                placeholder="Optional"
              />
            </label>

            <div />

            <label className="career-field">
              <span>Password *</span>
              <input
                name="password"
                type="password"
                value={form.password}
                onChange={change}
                minLength={8}
                required
              />
              <small>Minimum 8 characters.</small>
            </label>

            <label className="career-field">
              <span>Confirm Password *</span>
              <input
                name="confirm_password"
                type="password"
                value={form.confirm_password}
                onChange={change}
                minLength={8}
                required
              />
            </label>
          </div>

          {state.error ? (
            <div className="career-alert career-alert-error">
              {state.error}
            </div>
          ) : null}

          <button
            className="career-button career-button-gold"
            type="submit"
            disabled={state.loading}
          >
            {state.loading ? "Creating account..." : "Create Careers Account →"}
          </button>
        </form>

        <div className="career-auth-foot">
          Already registered? <Link to="/login">Sign in</Link>
        </div>
      </div>
    </section>
  );
}
