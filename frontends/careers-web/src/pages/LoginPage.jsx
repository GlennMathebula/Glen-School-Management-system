import { useState } from "react";
import {
  Link,
  Navigate,
  useLocation,
  useNavigate,
} from "react-router-dom";

import { useAuth } from "../auth/AuthContext";

export default function LoginPage() {
  const { isAuthenticated, login } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();

  const [form, setForm] = useState({
    email: "",
    password: "",
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
      [name]: value,
    }));
    setState({ loading: false, error: "" });
  }

  async function submit(event) {
    event.preventDefault();

    setState({ loading: true, error: "" });

    try {
      await login(form.email.trim(), form.password);

      navigate(
        location.state?.from || "/dashboard",
        { replace: true },
      );
    } catch (error) {
      setState({
        loading: false,
        error: error.message,
      });
    }
  }

  return (
    <section className="career-auth-page">
      <div className="career-auth-card">
        <span className="career-eyebrow career-eyebrow-dark">
          Careers account
        </span>
        <h1>Sign In</h1>
        <p>
          Access your job applications, documents, interview information and
          recruitment status.
        </p>

        <form onSubmit={submit}>
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
            <span>Password *</span>
            <input
              name="password"
              type="password"
              value={form.password}
              onChange={change}
              required
            />
          </label>

          {state.error ? (
            <div className="career-alert career-alert-error">
              {state.error}
            </div>
          ) : null}

          <button
            className="career-button career-button-navy career-button-full"
            type="submit"
            disabled={state.loading}
          >
            {state.loading ? "Signing in..." : "Sign In →"}
          </button>
        </form>

        <div className="career-auth-foot">
          Don't have a Careers account?{" "}
          <Link to="/create-account">Create one</Link>
        </div>
      </div>
    </section>
  );
}
