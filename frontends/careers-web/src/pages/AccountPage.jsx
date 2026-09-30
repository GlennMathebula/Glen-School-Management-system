import { useState } from "react";

import { changeCareerPassword } from "../api/client";
import { useAuth } from "../auth/AuthContext";

function InfoRow({ label, value }) {
  return (
    <div className="career-info-row">
      <span>{label}</span>
      <strong>{value || "—"}</strong>
    </div>
  );
}

export default function AccountPage() {
  const { account, token } = useAuth();

  const [form, setForm] = useState({
    current_password: "",
    new_password: "",
    confirm_password: "",
  });

  const [state, setState] = useState({
    loading: false,
    error: "",
    message: "",
  });

  function change(event) {
    const { name, value } = event.target;
    setForm((current) => ({
      ...current,
      [name]: value,
    }));
    setState({
      loading: false,
      error: "",
      message: "",
    });
  }

  async function submit(event) {
    event.preventDefault();

    if (form.new_password.length < 8) {
      setState({
        loading: false,
        error: "New password must contain at least 8 characters.",
        message: "",
      });
      return;
    }

    if (form.new_password !== form.confirm_password) {
      setState({
        loading: false,
        error: "New passwords do not match.",
        message: "",
      });
      return;
    }

    setState({
      loading: true,
      error: "",
      message: "",
    });

    try {
      const response = await changeCareerPassword(
        {
          current_password: form.current_password,
          new_password: form.new_password,
        },
        token,
      );

      setForm({
        current_password: "",
        new_password: "",
        confirm_password: "",
      });

      setState({
        loading: false,
        error: "",
        message:
          response?.message || "Password changed successfully.",
      });
    } catch (error) {
      setState({
        loading: false,
        error: error.message,
        message: "",
      });
    }
  }

  return (
    <section className="career-page">
      <div className="career-container career-account-layout">
        <section className="career-panel">
          <div className="career-panel-head">
            <span>👤</span>
            <h2>Careers Account</h2>
          </div>
          <div className="career-panel-body">
            <InfoRow
              label="Applicant Number"
              value={account?.applicant_number}
            />
            <InfoRow
              label="Name"
              value={[account?.first_name, account?.last_name]
                .filter(Boolean)
                .join(" ")}
            />
            <InfoRow label="Email" value={account?.email} />
            <InfoRow label="Cell Number" value={account?.cell_number} />
            <InfoRow
              label="SA ID"
              value={account?.national_id || "Not supplied"}
            />
            <InfoRow
              label="Account Status"
              value={account?.account_status}
            />
          </div>
        </section>

        <section className="career-panel">
          <div className="career-panel-head">
            <span>🔐</span>
            <h2>Change Password</h2>
          </div>
          <div className="career-panel-body">
            <form onSubmit={submit}>
              <label className="career-field">
                <span>Current Password *</span>
                <input
                  name="current_password"
                  type="password"
                  value={form.current_password}
                  onChange={change}
                  required
                />
              </label>

              <label className="career-field">
                <span>New Password *</span>
                <input
                  name="new_password"
                  type="password"
                  value={form.new_password}
                  onChange={change}
                  minLength={8}
                  required
                />
              </label>

              <label className="career-field">
                <span>Confirm New Password *</span>
                <input
                  name="confirm_password"
                  type="password"
                  value={form.confirm_password}
                  onChange={change}
                  minLength={8}
                  required
                />
              </label>

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

              <button
                className="career-button career-button-navy"
                type="submit"
                disabled={state.loading}
              >
                {state.loading ? "Changing..." : "Change Password"}
              </button>
            </form>
          </div>
        </section>
      </div>
    </section>
  );
}
