// GM_STAFF_DISPLAY_POLISH_V1
/* React JSX is compiled automatically by Vite. */

/** Presentation-only helpers. Never change the API payload or the stored data. */
const EMPTY = "—";
const MAX_DEPTH = 4;
const SENSITIVE_KEY = /(^|_)(password|passwd|password_hash|pin|pin_hash|access_token|refresh_token|id_token|client_secret|api_key|private_key|authorization|credentials|secret|secret_key|service_role_key)(_|$)/i;
const LABELS = {
  id: "ID", national_id: "National ID", staff_account_id: "Staff account ID",
  google_email: "Google account email", google_calendar_id: "Google Calendar ID",
  google_connection: "Google connection", is_active: "Active status",
  token_expiry: "Token expiry", scopes: "Permissions granted",
  academic_subjects: "Academic subjects", achievement_level: "Achievement level",
  created_at: "Created", updated_at: "Last updated", last_synced_at: "Last synced",
  first_name: "First name", last_name: "Last name", app_status: "Application status",
  po_e: "POE", qcto: "QCTO", fisa: "FISA", eisa: "EISA",
};

export function formatField(key) {
  const raw = String(key ?? "");
  if (LABELS[raw.toLowerCase()]) return LABELS[raw.toLowerCase()];
  return raw.replace(/([a-z\d])([A-Z])/g, "$1 $2")
    .replace(/[_-]+/g, " ")
    .replace(/\b\w/g, character => character.toUpperCase())
    .replace(/\b(Id|Api|Sms|Lms|Url|Pdf|PoE|Qcto|Fisa|Eisa|Sdp|Nqf)\b/g,
      word => ({Id:"ID",Api:"API",Sms:"SMS",Lms:"LMS",Url:"URL",Pdf:"PDF",PoE:"POE",Qcto:"QCTO",Fisa:"FISA",Eisa:"EISA",Sdp:"SDP",Nqf:"NQF"}[word] || word));
}

export function parseDisplayData(value) {
  if (typeof value !== "string") return value;
  const string = value.trim();
  if (string.length < 2 || string.length > 100000) return value;
  if (!((string[0] === "[" && string.at(-1) === "]") ||
        (string[0] === "{" && string.at(-1) === "}"))) return value;
  try {
    const parsed = JSON.parse(string);
    return parsed && typeof parsed === "object" ? parsed : value;
  } catch { return value; }
}

function sensitive(key) { return SENSITIVE_KEY.test(String(key || "").toLowerCase()); }
function blank(value) { return value == null || value === ""; }

function localDate(value) {
  if (typeof value !== "string") return null;
  if (/^\d{4}-\d{2}-\d{2}$/.test(value)) {
    const match = value.match(/^(\d{4})-(\d{2})-(\d{2})$/);
    return match ? `${match[3]}/${match[2]}/${match[1]}` : null;
  }
  if (!/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}/.test(value)) return null;
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return null;
  return new Intl.DateTimeFormat("en-ZA", {
    timeZone: "Africa/Johannesburg", year: "numeric", month: "short", day: "2-digit",
    hour: "2-digit", minute: "2-digit", hour12: false,
  }).format(date);
}

function friendlyScope(value) {
  const text = String(value ?? "");
  if (text === "openid") return "Basic account sign-in";
  if (text.includes("googleapis.com/auth/userinfo.email")) return "View Google account email";
  if (text.includes("googleapis.com/auth/userinfo.profile")) return "View Google account profile";
  if (text.includes("googleapis.com/auth/calendar.events")) return "Manage Calendar events";
  if (text.includes("googleapis.com/auth/calendar.readonly")) return "View Calendar";
  if (text.startsWith("https://www.googleapis.com/auth/")) {
    return text.slice(text.lastIndexOf("/") + 1).replace(/[._-]/g, " ");
  }
  return text;
}

export function formatBrief(value, fieldName = "") {
  if (sensitive(fieldName)) return "Hidden for security";
  const data = parseDisplayData(value);
  if (blank(data)) return EMPTY;
  if (typeof data === "boolean") return data ? "Yes" : "No";
  if (Array.isArray(data)) return `${data.length} ${data.length === 1 ? "item" : "items"}`;
  if (typeof data === "object") {
    const count = Object.keys(data).length;
    return `${count} ${count === 1 ? "field" : "fields"}`;
  }
  const date = localDate(data);
  if (date) return date;
  const result = String(data);
  return result.length > 120 ? `${result.slice(0, 117)}…` : result;
}

function ScalarValue({value, fieldName}) {
  if (sensitive(fieldName)) return <span className="pretty-redacted">Hidden for security</span>;
  if (blank(value)) return <span className="pretty-empty">Not provided</span>;
  if (typeof value === "boolean") {
    const active = fieldName === "is_active" || fieldName === "connected";
    return <span className={`pretty-status ${value ? "pretty-status-on" : "pretty-status-off"}`}>
      {active ? (value ? "Active" : "Inactive") : (value ? "Yes" : "No")}
    </span>;
  }
  const formatted = localDate(value);
  if (formatted) return <span className="pretty-date">{formatted}</span>;
  const text = String(value);
  if (fieldName === "scopes") return <span>{friendlyScope(text)}</span>;
  return <span className={text.length > 90 ? "pretty-long-text" : undefined}>{text}</span>;
}

function SubjectTable({rows}) {
  return <div className="pretty-table-wrap"><table className="pretty-table">
    <thead><tr><th>Subject</th><th>Category</th><th>Achievement level</th></tr></thead>
    <tbody>{rows.map((row, index) => <tr key={`${index}-${row.subject || "subject"}`}>
      <td className="pretty-subject-name">{row.subject || EMPTY}</td>
      <td>{row.category || EMPTY}</td>
      <td>{row.achievement_level || EMPTY}</td>
    </tr>)}</tbody>
  </table></div>;
}

function RecordTable({rows, depth}) {
  const keys = Array.from(new Set(rows.slice(0, 30).flatMap(row => Object.keys(row || {})))).slice(0, 7);
  return <div className="pretty-table-wrap"><table className="pretty-table">
    <thead><tr>{keys.map(key => <th key={key}>{formatField(key)}</th>)}</tr></thead>
    <tbody>{rows.map((row, i) => <tr key={row?.id || row?.student_number || i}>
      {keys.map(key => <td key={key}><ReadableValue value={row?.[key]} fieldName={key} depth={depth + 1} /></td>)}
    </tr>)}</tbody>
  </table></div>;
}

export function ReadableValue({value, fieldName = "", depth = 0}) {
  if (sensitive(fieldName)) return <ScalarValue fieldName={fieldName} value={value} />;
  const data = parseDisplayData(value);
  if (data === null || typeof data !== "object") return <ScalarValue value={data} fieldName={fieldName} />;
  if (depth >= MAX_DEPTH) return <span className="pretty-muted">{formatBrief(data)}</span>;
  if (Array.isArray(data)) {
    if (!data.length) return <span className="pretty-empty">No entries recorded</span>;
    const subjects = data.every(item => item && typeof item === "object" && !Array.isArray(item) && ("subject" in item || "achievement_level" in item));
    if (subjects) return <SubjectTable rows={data} />;
    const records = data.every(item => item && typeof item === "object" && !Array.isArray(item));
    if (records) return <RecordTable rows={data} depth={depth} />;
    return <div className="pretty-tags">{data.map((item, index) => <span className="pretty-tag" key={index}>
      {typeof item === "object" ? formatBrief(item) : (fieldName === "scopes" ? friendlyScope(item) : formatBrief(item))}
    </span>)}</div>;
  }
  const entries = Object.entries(data).filter(([key]) => key !== "success");
  if (!entries.length) return <span className="pretty-empty">No details available</span>;
  return <div className="pretty-nested-grid">{entries.map(([key, nested]) => <div className="pretty-nested-item" key={key}>
    <span className="pretty-nested-label">{formatField(key)}</span>
    <div className="pretty-value"><ReadableValue value={nested} fieldName={key} depth={depth + 1} /></div>
  </div>)}</div>;
}

export function DetailGrid({data}) {
  if (!data || typeof data !== "object") return <div className="empty">No details available.</div>;
  const items = Object.entries(data).filter(([key]) => key !== "success");
  if (!items.length) return <div className="empty">No details available.</div>;
  return <div className="object-grid pretty-grid">{items.map(([key, value]) => {
    const parsed = parseDisplayData(value);
    const wide = (parsed && typeof parsed === "object" && !sensitive(key)) || (typeof value === "string" && value.length > 150);
    return <article className={`object-item pretty-item ${wide ? "pretty-wide" : ""}`} key={key}>
      <span className="pretty-label">{formatField(key)}</span>
      <div className="pretty-value"><ReadableValue value={value} fieldName={key} /></div>
    </article>;
  })}</div>;
}

export function SmartCell({value, fieldName = ""}) {
  const parsed = parseDisplayData(value);
  const isComplex = parsed !== null && typeof parsed === "object" && !sensitive(fieldName);
  if (!isComplex) return <ScalarValue value={parsed} fieldName={fieldName} />;
  return <details className="pretty-cell-details">
    <summary>{formatBrief(parsed)}</summary>
    <div className="pretty-cell-expanded"><ReadableValue value={parsed} fieldName={fieldName} /></div>
  </details>;
}
