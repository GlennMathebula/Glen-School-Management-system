import {
  useEffect,
  useMemo,
  useState,
} from "react";

import {
  NavLink,
  Navigate,
  Route,
  Routes,
  useNavigate,
} from "react-router-dom";

import * as API from "./api";
import { useAuth } from "./auth";
import * as V3 from "./AdminV3";
import * as V5 from "./V5Operations";

// ============================================================
// COMMON UI
// ============================================================

function Alert({
  error,
  success,
}) {
  if (!error && !success) {
    return null;
  }

  return (
    <div
      className={
        error
          ? "alert error"
          : "alert success"
      }
    >
      {error || success}
    </div>
  );
}

function Badge({
  value,
}) {
  return (
    <span className="badge">
      {value ?? "—"}
    </span>
  );
}

function PageTitle({
  eyebrow,
  title,
  text,
  actions,
}) {
  return (
    <div className="page-title">
      <div>
        <span className="eyebrow">
          {eyebrow}
        </span>
        <h1>{title}</h1>
        {text ? <p>{text}</p> : null}
      </div>

      {actions ? (
        <div className="page-actions">
          {actions}
        </div>
      ) : null}
    </div>
  );
}

function Empty({
  title = "No records",
  text = "No records are currently available.",
}) {
  return (
    <div className="empty">
      <div>—</div>
      <strong>{title}</strong>
      <span>{text}</span>
    </div>
  );
}

function humanize(key) {
  return String(key || "")
    .replace(/_/g, " ")
    .replace(
      /\b\w/g,
      (letter) =>
        letter.toUpperCase(),
    );
}

function displayValue(value) {
  if (
    value === null ||
    value === undefined ||
    value === ""
  ) {
    return "—";
  }

  if (
    typeof value === "boolean"
  ) {
    return value
      ? "Yes"
      : "No";
  }

  if (
    typeof value === "object"
  ) {
    if (Array.isArray(value)) {
      return `${value.length} item(s)`;
    }

    return Object.entries(value)
      .slice(0, 3)
      .map(
        ([key, nested]) =>
          `${humanize(key)}: ${
            typeof nested ===
            "object"
              ? "…"
              : String(nested)
          }`,
      )
      .join(" Â· ");
  }

  return String(value);
}

const ARRAY_KEYS = [
  "applications",
  "students",
  "registrations",
  "cycles",
  "courses",
  "classes",
  "learners",
  "vacancies",
  "employees",
  "reports",
  "records",
  "items",
  "results",
  "threads",
  "messages",
  "announcements",
  "tickets",
  "notifications",
  "staff",
  "staff_accounts",
  "roles",
  "sponsors",
  "payments",
  "invoices",
  "receipts",
  "payment_plans",
  "queue",
];

function findRows(data) {
  if (Array.isArray(data)) {
    return data;
  }

  if (
    !data ||
    typeof data !== "object"
  ) {
    return null;
  }

  for (
    const key of ARRAY_KEYS
  ) {
    if (
      Array.isArray(data[key])
    ) {
      return data[key];
    }
  }

  if (
    data.data &&
    data.data !== data
  ) {
    return findRows(data.data);
  }

  for (
    const value of Object.values(
      data,
    )
  ) {
    if (
      Array.isArray(value) &&
      value.length
    ) {
      return value;
    }
  }

  return null;
}

function preferredColumns(row) {
  const preferred = [
    "student_number",
    "application_number",
    "staff_code",
    "employee_number",
    "course_code",
    "cycle_code",
    "class_code",
    "vacancy_code",
    "title",
    "subject",
    "first_name",
    "last_name",
    "full_name",
    "course_name",
    "class_name",
    "status",
    "app_status",
    "registration_status",
    "role_code",
    "role_name",
    "department",
    "amount",
    "mark",
    "result",
    "created_at",
    "updated_at",
  ];

  const keys =
    Object.keys(row || {});

  const selected = [
    ...preferred.filter(
      (key) =>
        keys.includes(key),
    ),
    ...keys.filter(
      (key) =>
        !preferred.includes(key) &&
        typeof row[key] !== "object",
    ),
  ];

  return [
    ...new Set(selected),
  ].slice(0, 7);
}

function DataTable({
  rows,
}) {
  const [query, setQuery] =
    useState("");

  const filtered = useMemo(
    () =>
      (rows || []).filter(
        (row) =>
          JSON.stringify(row)
            .toLowerCase()
            .includes(
              query.toLowerCase(),
            ),
      ),
    [rows, query],
  );

  if (!rows?.length) {
    return <Empty />;
  }

  const columns =
    preferredColumns(
      rows[0],
    );

  return (
    <>
      <div className="table-tools">
        <input
          value={query}
          onChange={(event) =>
            setQuery(
              event.target.value,
            )
          }
          placeholder="Filter these records..."
        />

        <span>
          {filtered.length} of{" "}
          {rows.length}
        </span>
      </div>

      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              {columns.map(
                (key) => (
                  <th key={key}>
                    {humanize(key)}
                  </th>
                ),
              )}
            </tr>
          </thead>

          <tbody>
            {filtered.map(
              (row, index) => (
                <tr
                  key={
                    row.id ||
                    row.student_number ||
                    row.application_number ||
                    row.staff_code ||
                    index
                  }
                >
                  {columns.map(
                    (key) => (
                      <td key={key}>
                        {key.includes(
                          "status",
                        ) ||
                        key ===
                          "result" ? (
                          <Badge
                            value={
                              row[key]
                            }
                          />
                        ) : (
                          displayValue(
                            row[key],
                          )
                        )}
                      </td>
                    ),
                  )}
                </tr>
              ),
            )}
          </tbody>
        </table>
      </div>
    </>
  );
}

function ObjectView({
  data,
}) {
  if (
    !data ||
    typeof data !== "object"
  ) {
    return (
      <Empty
        text="No data was returned."
      />
    );
  }

  const rows = findRows(data);

  if (rows) {
    return (
      <DataTable rows={rows} />
    );
  }

  const source =
    data.data &&
    typeof data.data ===
      "object"
      ? data.data
      : data;

  return (
    <div className="object-grid">
      {Object.entries(source)
        .filter(
          ([key]) =>
            ![
              "success",
            ].includes(key),
        )
        .map(
          ([key, value]) => (
            <div
              className="object-item"
              key={key}
            >
              <span>
                {humanize(key)}
              </span>

              <strong>
                {displayValue(
                  value,
                )}
              </strong>
            </div>
          ),
        )}
    </div>
  );
}

// ============================================================
// STAFF AUTHENTICATION UI
// ============================================================

function LoginFlow() {
  const auth = useAuth();

  const [login, setLogin] =
    useState({
      staff_code: "",
      password: "",
      pin: "",
    });

  const [credentials, setCredentials] =
    useState({
      new_password: "",
      confirm_password: "",
      new_pin: "",
      confirm_pin: "",
    });

  const [otp, setOtp] =
    useState("");

  const [state, setState] =
    useState({
      busy: false,
      error: "",
      success: "",
      apiOnline: null,
    });

  useEffect(() => {
    let active = true;

    API.health()
      .then(() => {
        if (active) {
          setState(
            (current) => ({
              ...current,
              apiOnline: true,
            }),
          );
        }
      })
      .catch(() => {
        if (active) {
          setState(
            (current) => ({
              ...current,
              apiOnline: false,
            }),
          );
        }
      });

    return () => {
      active = false;
    };
  }, []);

  async function submitLogin(
    event,
  ) {
    event.preventDefault();

    if (
      !/^\d{5}$/.test(
        login.pin,
      )
    ) {
      setState({
        ...state,
        error:
          "Staff PIN must contain exactly 5 digits.",
      });
      return;
    }

    setState({
      ...state,
      busy: true,
      error: "",
      success: "",
    });

    try {
      await auth.login(
        login.staff_code,
        login.password,
        login.pin,
      );

      setState(
        (current) => ({
          ...current,
          busy: false,
          error: "",
        }),
      );
    } catch (error) {
      setState(
        (current) => ({
          ...current,
          busy: false,
          error: error.message,
        }),
      );
    }
  }

  async function submitCredentials(
    event,
  ) {
    event.preventDefault();

    setState({
      ...state,
      busy: true,
      error: "",
      success: "",
    });

    try {
      await auth.changeCredentials(
        credentials,
      );

      setState(
        (current) => ({
          ...current,
          busy: false,
          success:
            "Credentials changed. A 6-digit OTP has been sent to your email.",
        }),
      );
    } catch (error) {
      setState(
        (current) => ({
          ...current,
          busy: false,
          error: error.message,
        }),
      );
    }
  }

  async function submitOtp(
    event,
  ) {
    event.preventDefault();

    if (!/^\d{6}$/.test(otp)) {
      setState({
        ...state,
        error:
          "Enter the 6-digit OTP.",
      });
      return;
    }

    setState({
      ...state,
      busy: true,
      error: "",
      success: "",
    });

    try {
      await auth.submitOtp(
        otp,
      );
    } catch (error) {
      setState(
        (current) => ({
          ...current,
          busy: false,
          error: error.message,
        }),
      );
    }
  }

  async function resendOtp() {
    setState({
      ...state,
      busy: true,
      error: "",
      success: "",
    });

    try {
      const result =
        await auth.resend();

      setState(
        (current) => ({
          ...current,
          busy: false,
          success:
            `A new OTP was sent to ${
              result.otp_sent_to ||
              "your email"
            }.`,
        }),
      );
    } catch (error) {
      setState(
        (current) => ({
          ...current,
          busy: false,
          error: error.message,
        }),
      );
    }
  }

  return (
    <div className="login-page">
      <section className="login-brand">
        <img
          src="./glen-moniques-logo.png"
          alt="Glen Moniques"
        />

        <span>
          GLEN MONIQUES (PTY) LTD
        </span>

        <h1>
          Staff Portal
        </h1>

        <p>
          Secure role-based access to
          admissions, academics,
          assessments, finance, HR,
          reporting and administration.
        </p>

        <div className="backend-indicator">
          <i
            className={
              state.apiOnline
                ? "online"
                : "offline"
            }
          />

          {state.apiOnline === null
            ? "Checking API..."
            : state.apiOnline
              ? "SMS API connected"
              : "SMS API is offline"}
        </div>
      </section>

      <section className="login-panel">
        <div className="login-card">
          {auth.stage === "login" ? (
            <>
              <span className="eyebrow">
                Staff authentication
              </span>

              <h2>
                Sign in to Staff Portal
              </h2>

              <p>
                Enter your Staff Code,
                password and 5-digit PIN.
                Successful credentials are
                followed by email OTP
                verification.
              </p>

              <Alert
                error={state.error}
              />

              <form
                onSubmit={
                  submitLogin
                }
              >
                <label>
                  <span>
                    Staff Code *
                  </span>

                  <input
                    value={
                      login.staff_code
                    }
                    onChange={(
                      event,
                    ) =>
                      setLogin({
                        ...login,
                        staff_code:
                          event.target.value
                            .toUpperCase(),
                      })
                    }
                    required
                    autoFocus
                  />
                </label>

                <label>
                  <span>
                    Password *
                  </span>

                  <input
                    type="password"
                    value={
                      login.password
                    }
                    onChange={(
                      event,
                    ) =>
                      setLogin({
                        ...login,
                        password:
                          event.target.value,
                      })
                    }
                    required
                  />
                </label>

                <label>
                  <span>
                    5-Digit PIN *
                  </span>

                  <input
                    type="password"
                    inputMode="numeric"
                    maxLength={5}
                    value={
                      login.pin
                    }
                    onChange={(
                      event,
                    ) =>
                      setLogin({
                        ...login,
                        pin:
                          event.target.value
                            .replace(
                              /\D/g,
                              "",
                            ),
                      })
                    }
                    required
                  />
                </label>

                <button
                  className="button gold full"
                  disabled={
                    state.busy
                  }
                >
                  {state.busy
                    ? "Verifying..."
                    : "Continue Securely →"}
                </button>
              </form>
            </>
          ) : null}

          {auth.stage ===
          "credentials" ? (
            <>
              <span className="eyebrow">
                First-time security
              </span>

              <h2>
                Change temporary credentials
              </h2>

              <p>
                Staff Code:{" "}
                <strong>
                  {
                    auth.challengeInfo
                      ?.staff_code
                  }
                </strong>
              </p>

              <Alert
                error={state.error}
                success={
                  state.success
                }
              />

              <form
                onSubmit={
                  submitCredentials
                }
              >
                <div className="form-grid">
                  <label>
                    <span>
                      New Password *
                    </span>
                    <input
                      type="password"
                      value={
                        credentials
                          .new_password
                      }
                      onChange={(
                        event,
                      ) =>
                        setCredentials({
                          ...credentials,
                          new_password:
                            event.target
                              .value,
                        })
                      }
                      required
                    />
                  </label>

                  <label>
                    <span>
                      Confirm Password *
                    </span>
                    <input
                      type="password"
                      value={
                        credentials
                          .confirm_password
                      }
                      onChange={(
                        event,
                      ) =>
                        setCredentials({
                          ...credentials,
                          confirm_password:
                            event.target
                              .value,
                        })
                      }
                      required
                    />
                  </label>

                  <label>
                    <span>
                      New 5-Digit PIN *
                    </span>
                    <input
                      type="password"
                      inputMode="numeric"
                      maxLength={5}
                      value={
                        credentials
                          .new_pin
                      }
                      onChange={(
                        event,
                      ) =>
                        setCredentials({
                          ...credentials,
                          new_pin:
                            event.target
                              .value
                              .replace(
                                /\D/g,
                                "",
                              ),
                        })
                      }
                      required
                    />
                  </label>

                  <label>
                    <span>
                      Confirm PIN *
                    </span>
                    <input
                      type="password"
                      inputMode="numeric"
                      maxLength={5}
                      value={
                        credentials
                          .confirm_pin
                      }
                      onChange={(
                        event,
                      ) =>
                        setCredentials({
                          ...credentials,
                          confirm_pin:
                            event.target
                              .value
                              .replace(
                                /\D/g,
                                "",
                              ),
                        })
                      }
                      required
                    />
                  </label>
                </div>

                <button
                  className="button gold full"
                  disabled={
                    state.busy
                  }
                >
                  Change Credentials →
                </button>
              </form>
            </>
          ) : null}

          {auth.stage === "otp" ? (
            <>
              <span className="eyebrow">
                Final security step
              </span>

              <h2>
                Verify email OTP
              </h2>

              <p>
                A 6-digit OTP was sent to{" "}
                <strong>
                  {auth.challengeInfo
                    ?.otp_sent_to ||
                    "your registered email"}
                </strong>
                .
              </p>

              <Alert
                error={state.error}
                success={
                  state.success
                }
              />

              <form
                onSubmit={
                  submitOtp
                }
              >
                <label>
                  <span>
                    6-Digit OTP *
                  </span>

                  <input
                    className="otp-input"
                    value={otp}
                    onChange={(
                      event,
                    ) =>
                      setOtp(
                        event.target.value
                          .replace(
                            /\D/g,
                            "",
                          )
                          .slice(0, 6),
                      )
                    }
                    maxLength={6}
                    inputMode="numeric"
                    required
                    autoFocus
                  />
                </label>

                <button
                  className="button gold full"
                  disabled={
                    state.busy
                  }
                >
                  Verify & Open Desktop →
                </button>
              </form>

              <button
                className="text-button"
                type="button"
                onClick={
                  resendOtp
                }
                disabled={
                  state.busy
                }
              >
                Resend OTP
              </button>
            </>
          ) : null}
        </div>
      </section>
    </div>
  );
}

// ============================================================
// AUTHENTICATED DATA
// ============================================================

function useEndpoint(
  path,
  token,
  enabled = true,
) {
  const [state, setState] =
    useState({
      data: null,
      error: "",
      loading: enabled,
      tick: 0,
    });

  useEffect(() => {
    let active = true;

    if (
      !enabled ||
      !path
    ) {
      setState(
        (current) => ({
          ...current,
          loading: false,
        }),
      );

      return undefined;
    }

    setState(
      (current) => ({
        ...current,
        loading: true,
        error: "",
      }),
    );

    API.request(
      path,
      {},
      token,
    )
      .then((data) => {
        if (!active) return;

        setState(
          (current) => ({
            ...current,
            data,
            loading: false,
            error: "",
          }),
        );
      })
      .catch((error) => {
        if (!active) return;

        setState(
          (current) => ({
            ...current,
            loading: false,
            error:
              error.message,
          }),
        );
      });

    return () => {
      active = false;
    };
  }, [
    path,
    token,
    enabled,
    state.tick,
  ]);

  return {
    ...state,
    refresh: () =>
      setState(
        (current) => ({
          ...current,
          tick:
            current.tick + 1,
        }),
      ),
  };
}

function ResourceSection({
  title,
  description,
  path,
  token,
}) {
  const state =
    useEndpoint(
      path,
      token,
    );

  return (
    <section className="panel">
      <div className="panel-head">
        <div>
          <h2>{title}</h2>
          {description ? (
            <p>
              {description}
            </p>
          ) : null}
        </div>

        <button
          className="button light"
          onClick={
            state.refresh
          }
          disabled={
            state.loading
          }
        >
          Refresh
        </button>
      </div>

      <div className="panel-body">
        {state.loading ? (
          <div className="loading-row">
            Loading...
          </div>
        ) : null}

        <Alert
          error={
            state.error
          }
        />

        {!state.loading &&
        !state.error ? (
          <ObjectView
            data={state.data}
          />
        ) : null}
      </div>
    </section>
  );
}

function WorkspacePage({
  eyebrow,
  title,
  text,
  sections,
  token,
}) {
  return (
    <>
      <PageTitle
        eyebrow={eyebrow}
        title={title}
        text={text}
      />

      {sections.map(
        (section) => (
          <ResourceSection
            key={
              section.path
            }
            {...section}
            token={token}
          />
        ),
      )}
    </>
  );
}

// ============================================================
// DASHBOARD
// ============================================================

function DashboardPage({
  dashboard,
  refresh,
}) {
  const staff =
    dashboard?.staff || {};

  const counts =
    dashboard?.counts || {};

  const workload =
    dashboard?.workload || {};

  return (
    <>
      <PageTitle
        eyebrow="Staff dashboard"
        title={`Welcome, ${
          staff.first_name ||
          staff.full_name ||
          "Staff Member"
        }.`}
        text="Your role, live workload and staff services."
        actions={
          <button
            className="button light"
            onClick={refresh}
          >
            Refresh
          </button>
        }
      />

      <section className="role-banner">
        <div>
          <span>
            Current Role
          </span>
          <h2>
            {staff.role_name ||
              staff.role_code}
          </h2>
          <p>
            {staff.job_title ||
              "Staff"}{" "}
            Â·{" "}
            {staff.department ||
              "Glen Moniques"}
          </p>
        </div>

        <Badge
          value={
            staff.staff_code
          }
        />
      </section>

      <div className="stat-grid">
        <div className="stat-card">
          <span>
            Notifications
          </span>
          <strong>
            {counts.unread_notifications ??
              0}
          </strong>
          <small>
            unread
          </small>
        </div>

        <div className="stat-card">
          <span>
            Staff Messages
          </span>
          <strong>
            {counts.unread_staff_messages ??
              0}
          </strong>
          <small>
            unread
          </small>
        </div>

        <div className="stat-card">
          <span>
            Support Tickets
          </span>
          <strong>
            {counts.open_support_tickets ??
              0}
          </strong>
          <small>
            open
          </small>
        </div>

        <div className="stat-card">
          <span>
            Permissions
          </span>
          <strong>
            {dashboard
              ?.access
              ?.permission_count ??
              0}
          </strong>
          <small>
            active
          </small>
        </div>
      </div>

      <div className="dashboard-grid">
        <section className="panel">
          <div className="panel-head">
            <h2>
              Workload
            </h2>
          </div>

          <div className="panel-body">
            {Object.keys(
              workload,
            ).length ? (
              <ObjectView
                data={workload}
              />
            ) : (
              <Empty
                title="No role workload counters"
                text="This role does not currently expose additional workload counters."
              />
            )}
          </div>
        </section>

        <section className="panel">
          <div className="panel-head">
            <h2>
              Recent Notifications
            </h2>
          </div>

          <div className="panel-body">
            <ObjectView
              data={{
                notifications:
                  dashboard
                    ?.recent_notifications ||
                  [],
              }}
            />
          </div>
        </section>
      </div>
    </>
  );
}

function StudentRecordsPage({token}) {
  const [search, setSearch] = useState("");
  const [rows, setRows] = useState([]);
  const [studentNumber, setStudentNumber] = useState("");
  const [student, setStudent] = useState(null);
  const [form, setForm] = useState({});
  const [state, setState] = useState({busy:false,error:"",success:""});

  async function loadList() {
    setState({busy:true,error:"",success:""});
    try {
      const data = await API.request(
        `/api/staff/admin/students?search=${encodeURIComponent(search)}&limit=100`,
        {},
        token,
      );
      setRows(data.students || []);
      setState({busy:false,error:"",success:""});
    } catch (error) {
      setState({busy:false,error:error.message,success:""});
    }
  }

  async function openStudent(value = studentNumber) {
    const number = String(value || "").trim();

    if (!number) {
      setState({busy:false,error:"Enter a student number.",success:""});
      return;
    }

    setStudentNumber(number);
    setState({busy:true,error:"",success:""});

    try {
      const data = await API.request(
        `/api/staff/admin/students/${encodeURIComponent(number)}`,
        {},
        token,
      );

      const item = data.student || {};

      setStudent(item);
      setForm({
        first_name:item.first_name||"",
        middle_name:item.middle_name||"",
        last_name:item.last_name||"",
        national_id:item.national_id||"",
        alternate_id:item.alternate_id||"",
        birth_date:item.birth_date||"",
        email:item.email||"",
        cell_number:item.cell_number||"",
        phone_number:item.phone_number||"",
        home_addr_1:item.home_addr_1||"",
        home_addr_2:item.home_addr_2||"",
        home_addr_3:item.home_addr_3||"",
        home_postal_code:item.home_postal_code||"",
        province_code:item.province_code||"",
        municipality:item.municipality||"",
        ward:item.ward||"",
        next_of_kin_full_name:item.next_of_kin_full_name||"",
        next_of_kin_surname:item.next_of_kin_surname||"",
        next_of_kin_cell:item.next_of_kin_cell||"",
        next_of_kin_relationship:item.next_of_kin_relationship||"",
        next_of_kin_email:item.next_of_kin_email||"",
        registration_status:item.registration_status||"Registered",
      });

      setState({busy:false,error:"",success:""});
    } catch (error) {
      setState({busy:false,error:error.message,success:""});
    }
  }

  function setField(key, value) {
    setForm((current) => ({
      ...current,
      [key]: value,
    }));
  }

  async function save(event) {
    event.preventDefault();
    setState({busy:true,error:"",success:""});

    try {
      const data = await API.request(
        `/api/staff/admin/students/${encodeURIComponent(studentNumber)}`,
        {
          method:"PATCH",
          body:JSON.stringify(Object.fromEntries(Object.entries(form).filter(([k,v])=>String(v??"")!==String(student?.[k]??"")))),
        },
        token,
      );

      setStudent(data.student || student);
      setState({
        busy:false,
        error:"",
        success:"Student record updated successfully.",
      });

      await loadList();
    } catch (error) {
      setState({busy:false,error:error.message,success:""});
    }
  }

  useEffect(() => {
    void loadList();
  }, []);

  const fields = [
    ["first_name","First Name"],
    ["middle_name","Middle Name"],
    ["last_name","Last Name"],
    ["national_id","National ID"],
    ["alternate_id","Alternate ID"],
    ["birth_date","Birth Date"],
    ["email","Email"],
    ["cell_number","Cell Number"],
    ["phone_number","Phone Number"],
    ["home_addr_1","Home Address 1"],
    ["home_addr_2","Home Address 2"],
    ["home_addr_3","Home Address 3"],
    ["home_postal_code","Home Postal Code"],
    ["province_code","Province"],
    ["next_of_kin_full_name","Next of Kin Full Name"],
    ["next_of_kin_surname","Next of Kin Surname"],
    ["next_of_kin_cell","Next of Kin Cell"],
    ["next_of_kin_relationship","Relationship"],
    ["next_of_kin_email","Next of Kin Email"],
  ];

  return (
    <>
      <PageTitle
        eyebrow="Administration"
        title="Student Records"
        text="Search, open and edit learner records. Generated PDFs are under Documents & Letters."
        actions={
          <button className="button light" onClick={loadList}>
            Refresh List
          </button>
        }
      />

      <Alert error={state.error} success={state.success} />

      <section className="panel">
        <div className="panel-head">
          <div>
            <h2>Find Student</h2>
            <p>Search by student number, name, email or ID.</p>
          </div>
        </div>

        <div className="panel-body">
          <div className="record-search">
            <input
              value={search}
              onChange={(event) => setSearch(event.target.value)}
              placeholder="Search students..."
            />
            <button className="button gold" onClick={loadList}>
              Search
            </button>
            <input
              value={studentNumber}
              onChange={(event) => setStudentNumber(event.target.value)}
              placeholder="Student number"
            />
            <button className="button light" onClick={() => openStudent()}>
              Open Student
            </button>
          </div>

          <div className="student-list">
            {rows.slice(0, 30).map((item) => (
              <button
                key={item.student_number}
                type="button"
                onClick={() => openStudent(item.student_number)}
              >
                <strong>{item.student_number}</strong>
                <span>
                  {[item.first_name,item.middle_name,item.last_name]
                    .filter(Boolean)
                    .join(" ")}
                </span>
                <small>
                  {item.course_name || item.course_code || "No registration"}
                  {" Â· "}
                  {item.registration_status || item.app_status || "—"}
                </small>
              </button>
            ))}
          </div>
        </div>
      </section>

      {student ? (
        <form onSubmit={save}>
          <section className="panel">
            <div className="panel-head">
              <div>
                <h2>Edit {student.student_number}</h2>
                <p>Personal, contact, address, next-of-kin and registration status.</p>
              </div>
              <button className="button gold" disabled={state.busy}>
                {state.busy ? "Saving..." : "Save Changes"}
              </button>
            </div>

            <div className="panel-body">
              <div className="edit-grid">
                {fields.map(([key,label]) => (
                  <label key={key}>
                    <span>{label}</span>
                    <input
                      type={key === "birth_date" ? "date" : "text"}
                      value={form[key] ?? ""}
                      onChange={(event) => setField(key,event.target.value)}
                    />
                  </label>
                ))}

                <label>
                  <span>Registration Status</span>
                  <select
                    value={form.registration_status || "Registered"}
                    onChange={(event) => setField("registration_status",event.target.value)}
                  >
                    {["Registered","In Progress","Suspended","Withdrawn","Cancelled","Completed"]
                      .map((value) => <option key={value}>{value}</option>)}
                  </select>
                </label>
              </div>
            </div>
          </section>
        </form>
      ) : null}
    </>
  );
}


function DocumentsLettersPage({token}) {
  const [studentNumber, setStudentNumber] = useState("");
  const [overview, setOverview] = useState(null);
  const [state, setState] = useState({busy:false,error:"",success:""});
  const [bulkCycles, setBulkCycles] = useState([]);
  const [bulkClasses, setBulkClasses] = useState([]);
  const [bulkStudents, setBulkStudents] = useState([]);
  const [bulkCycle, setBulkCycle] = useState("");
  const [bulkClass, setBulkClass] = useState("");
  const [bulkStudent, setBulkStudent] = useState("");

  function number() {
    return studentNumber.trim();
  }

  useEffect(() => {
    let cancelled = false;

    async function loadBulkOptions() {
      try {
        const [cycleData, classData, studentData] = await Promise.all([
          API.request("/api/staff/academic-management/cycles",{},token),
          API.request("/api/staff/academic-management/classes",{},token),
          API.request("/api/staff/admin/students?limit=200",{},token),
        ]);

        if (cancelled) return;
        setBulkCycles(cycleData.cycles || []);
        setBulkClasses(classData.classes || []);
        setBulkStudents((studentData.students || []).filter((row) => row.registration_id));
      } catch (error) {
        if (!cancelled) {
          setState({busy:false,error:error.message,success:""});
        }
      }
    }

    loadBulkOptions();
    return () => { cancelled = true; };
  }, [token]);

  async function load() {
    if (!number()) {
      setState({busy:false,error:"Enter a student number.",success:""});
      return;
    }

    setState({busy:true,error:"",success:""});
    try {
      const data = await API.request(
        `/api/staff/admin/documents/${encodeURIComponent(number())}/overview`,
        {},
        token,
      );
      setOverview(data);
      setState({busy:false,error:"",success:""});
    } catch (error) {
      setState({busy:false,error:error.message,success:""});
    }
  }

  async function post(path, success) {
    setState({busy:true,error:"",success:""});
    try {
      await API.request(path,{method:"POST"},token);
      setState({busy:false,error:"",success});
      await load();
    } catch (error) {
      setState({busy:false,error:error.message,success:""});
    }
  }

  async function download(path, filename) {
    setState({busy:true,error:"",success:""});
    try {
      await API.downloadFile(path,token,filename);
      setState({busy:false,error:"",success:"Document generated/downloaded."});
    } catch (error) {
      setState({busy:false,error:error.message,success:""});
    }
  }

  function selectCycle(value) {
    setBulkCycle(value);
    if (value) { setBulkClass(""); setBulkStudent(""); }
  }

  function selectClass(value) {
    setBulkClass(value);
    if (value) { setBulkCycle(""); setBulkStudent(""); }
  }

  function selectBulkStudent(value) {
    setBulkStudent(value);
    if (value) { setBulkCycle(""); setBulkClass(""); }
  }

  function bulkScope() {
    if (bulkCycle) return {type:"cycle",value:bulkCycle,label:`Cycle ${bulkCycle}`};
    if (bulkClass) return {type:"class",value:bulkClass,label:`Class ${bulkClass}`};
    if (bulkStudent) return {type:"student",value:bulkStudent,label:`Student ${bulkStudent}`};
    return null;
  }

  async function bulkDownload(documentType, label) {
    const scope = bulkScope();
    if (!scope) {
      setState({busy:false,error:"Select one Cycle, Class or Student first.",success:""});
      return;
    }

    setState({busy:true,error:"",success:""});
    const query = new URLSearchParams({
      document_type:documentType,
      scope_type:scope.type,
      scope_value:scope.value,
    });
    const filename = `${label}_${scope.type}_${scope.value}.zip`.replace(/[^A-Za-z0-9._-]+/g,"_");

    try {
      await API.downloadFile(
        `/api/staff/admin/bulk-documents/zip?${query.toString()}`,
        token,
        filename,
      );
      setState({
        busy:false,
        error:"",
        success:`Bulk ${label} ZIP generated for ${scope.label}. The ZIP includes generation_report.csv showing generated and skipped learners.`,
      });
    } catch (error) {
      setState({busy:false,error:error.message,success:""});
    }
  }

  return (
    <>
      <PageTitle
        eyebrow="Administration"
        title="Documents & Letters"
        text="Generate learner documents individually or in bulk by Cycle, Class or Student."
      />

      <Alert error={state.error} success={state.success} />

      <section className="panel">
        <div className="panel-head"><div><h2>Bulk Document Generator</h2><p>Choose exactly one scope. Selecting a Cycle, Class or Student automatically clears the other two.</p></div></div>
        <div className="panel-body">
          <div className="edit-grid">
            <label><span>Cycle</span><select value={bulkCycle} onChange={(event)=>selectCycle(event.target.value)}><option value="">Select cycle</option>{bulkCycles.map((row)=><option key={row.cycle_code} value={row.cycle_code}>{row.cycle_code} — {row.cycle_name || row.status}</option>)}</select></label>
            <label><span>Class</span><select value={bulkClass} onChange={(event)=>selectClass(event.target.value)}><option value="">Select class</option>{bulkClasses.map((row)=><option key={row.class_code} value={row.class_code}>{row.class_code} — {row.class_name || row.course_code}</option>)}</select></label>
            <label><span>Student</span><select value={bulkStudent} onChange={(event)=>selectBulkStudent(event.target.value)}><option value="">Select student</option>{bulkStudents.map((row)=><option key={row.student_number} value={row.student_number}>{row.student_number} — {[row.first_name,row.middle_name,row.last_name].filter(Boolean).join(" ")}</option>)}</select></label>
          </div>

          <div className="where-grid" style={{marginTop:"16px"}}>
            <div><strong>Registration Pack</strong><span>Generate one ZIP for the selected scope.</span><div className="button-row"><button className="button gold" onClick={()=>bulkDownload("enrolment_form","Enrolment_Forms")}>Enrolment Forms ZIP</button><button className="button light" onClick={()=>bulkDownload("proof_of_registration","Proof_of_Registration")}>Proof of Registration ZIP</button></div></div>
            <div><strong>Completion Pack</strong><span>Ineligible learners are skipped and listed in the ZIP report.</span><div className="button-row"><button className="button gold" onClick={()=>bulkDownload("letter_of_completion","Letters_of_Completion")}>Completion Letters ZIP</button><button className="button light" onClick={()=>bulkDownload("graduation_letter","Graduation_Letters")}>Graduation Letters ZIP</button></div></div>
            <div><strong>Statement of Results — FISA Only</strong><span>Uses the existing FISA-only SoR generator and release rules.</span><button className="button gold" onClick={()=>bulkDownload("sor_fisa_only","SOR_FISA_ONLY")}>FISA Only SoR ZIP</button></div>
            <div><strong>Statement of Results — FISA + EISA</strong><span>Uses the existing FISA + EISA SoR generator and release rules.</span><button className="button gold" onClick={()=>bulkDownload("sor_fisa_plus_eisa","SOR_FISA_PLUS_EISA")}>FISA + EISA SoR ZIP</button></div>
          </div>
        </div>
      </section>

      <section className="panel">
        <div className="panel-head"><div><h2>Individual Student Documents</h2><p>Enter the learner's 8-digit student number.</p></div></div>
        <div className="panel-body"><div className="document-search"><input value={studentNumber} onChange={(event)=>setStudentNumber(event.target.value.replace(/\D/g,"").slice(0,8))} placeholder="e.g. 20260010"/><button className="button gold" onClick={load}>Load Document Status</button></div></div>
      </section>

      <div className="document-grid">
        <section className="doc-card"><span>REGISTRATION</span><h3>Enrolment Form</h3><p>Generate the administrative enrolment PDF for physical learner signature.</p><button className="button gold" onClick={()=>post(`/api/staff/admin/students/${number()}/enrolment-form/generate`,"Enrolment Form generated.")}>Generate</button><button className="button light" onClick={()=>download(`/api/staff/admin/students/${number()}/enrolment-form/download`,`${number()}_Enrolment_Form.pdf`)}>Download Latest</button></section>
        <section className="doc-card"><span>REGISTRATION</span><h3>Proof of Registration</h3><p>Regenerate the Proof of Registration and email it to the learner.</p><button className="button gold" onClick={()=>post(`/api/staff/admin/documents/${number()}/proof-of-registration/resend`,"Proof of Registration regenerated and processed.")}>Regenerate & Email</button></section>
        <section className="doc-card"><span>COMPLETION</span><h3>Letter of Completion</h3><p>Available for eligible FISA-only learners once completion conditions are met.</p><button className="button gold" onClick={()=>download(`/api/staff/admin/documents/${number()}/letter-of-completion`,`${number()}_Letter_of_Completion.pdf`)}>Generate / Download</button></section>
        <section className="doc-card"><span>COMPLETION</span><h3>Graduation Letter</h3><p>Available for eligible FISA + EISA learners after the official competent EISA outcome.</p><button className="button gold" onClick={()=>download(`/api/staff/admin/documents/${number()}/graduation-letter`,`${number()}_Graduation_Letter.pdf`)}>Generate / Download</button></section>
      </div>

      {overview ? <section className="panel"><div className="panel-head"><h2>Document Status — {number()}</h2></div><div className="panel-body"><ObjectView data={overview} /></div></section> : null}

      <section className="panel"><div className="panel-head"><h2>Where do I generate each document?</h2></div><div className="panel-body"><div className="where-grid"><div><strong>Admissions</strong><span>Acceptance Letter, Rejection Letter and Outstanding Documents requests.</span></div><div><strong>Documents & Letters</strong><span>Individual and bulk Enrolment Forms, Proofs of Registration, completion/graduation letters and Statements of Results.</span></div><div><strong>Finance</strong><span>Invoices, Receipts, Statements and Payment Plan PDFs.</span></div><div><strong>Assessment / EISA Administration</strong><span>FISA admission, seating, attendance and assessment-related administrative documents.</span></div></div></div></section>
    </>
  );
}



// ============================================================
// DESKTOP SHELL / RBAC
// ============================================================

const SUPPORTED_ROLES =
  new Set([
    "ADMIN",
    "PRINCIPAL",
    "HR",
    "CFO",
    "FINANCIAL_OFFICER",
    "FACILITATOR",
    "ASSESSOR",
    "MODERATOR",
  ]);

function DesktopShell() {
  const auth = useAuth();

  const dashboardState =
    useEndpoint(
      "/api/staff/dashboard",
      auth.token,
    );

  const dashboard =
    dashboardState
      .data?.data || null;

  const access =
    dashboard?.access || {};

  const permissions =
    new Set(
      access.permissions ||
      [],
    );

  const role =
    String(
      dashboard
        ?.staff
        ?.role_code ||
      auth.staff
        ?.role_code ||
      "",
    ).toUpperCase();

  const can = (
    permission,
  ) =>
    permissions.has(
      permission,
    );

  const any = (
    list,
  ) =>
    list.some(
      (permission) =>
        can(permission),
    );

  const nav = [
    {
      label: "Dashboard",
      path: "/dashboard",
      icon: "⌂",
      show: true,
    },
    {
      label: "Admissions",
      path: "/admissions",
      icon: "A",
      show: any([
        "VIEW_APPLICATIONS",
        "MANAGE_APPLICATIONS",
      ]),
    },
    {
      label: "Student Records",
      path: "/students",
      icon: "S",
      show:
        can(
          "MANAGE_STUDENT_RECORDS",
        ),
    },
    {
      label: "Documents & Letters",
      path: "/documents",
      icon: "D",
      show: any([
        "MANAGE_STUDENT_RECORDS",
        "MANAGE_COMPLETION",
        "MANAGE_CERTIFICATION",
      ]),
    },
    {
      label: "Academic Management",
      path: "/academics",
      icon: "C",
      show:
        can(
          "MANAGE_ACADEMIC_STRUCTURE",
        ),
    },
    {
      label: "Timetable",
      path: "/timetable",
      icon: "T",
      show:
        can(
          "MANAGE_TIMETABLE",
        ),
    },
    {
      label: "Attendance Registers",
      path: "/attendance-registers",
      icon: "R",
      show:
        can(
          "MANAGE_TIMETABLE",
        ),
    },
    {
      label: "Completion & Certification",
      path: "/completion",
      icon: "✓",
      show: any([
        "MANAGE_COMPLETION",
        "MANAGE_CERTIFICATION",
      ]),
    },
    {
      label: "EISA Administration",
      path: "/eisa",
      icon: "E",
      show: any([
        "MANAGE_EISA_SITTINGS",
        "CAPTURE_EISA",
        "PUBLISH_EISA",
      ]),
    },
    {
      label: "Academic Delivery",
      path: "/delivery",
      icon: "D",
      show: any([
        "VIEW_ASSIGNED_CLASSES",
        "MANAGE_ATTENDANCE",
      ]),
    },
    {
      label: "Assessments",
      path: "/assessments",
      icon: "✓",
      show: any([
        "ASSESS_RESULT",
        "MODERATE_RESULT",
      ]),
    },
    {
      label: "Finance",
      path: "/finance",
      icon: "R",
      show:
        can(
          "VIEW_FINANCE",
        ),
    },
    {
      label: "HR & Recruitment",
      path: "/hr",
      icon: "H",
      show: any([
        "VIEW_RECRUITMENT",
        "VIEW_EMPLOYEES",
      ]),
    },
    {
      label: "Workplace & QA",
      path: "/compliance",
      icon: "W",
      show: any([
        "MANAGE_WORK_EXPERIENCE",
        "MANAGE_ASSESSMENT_APPEALS",
        "MANAGE_QA_ACTIONS",
      ]),
    },
    {
      label: "Academic Calendar",
      path: "/academic-calendar",
      icon: "Y",
      show:
        can(
          "MANAGE_ACADEMIC_CALENDAR",
        ),
    },
    {
      label: "Finance Setup",
      path: "/finance-setup",
      icon: "F",
      show: any([
        "MANAGE_INVOICES",
        "VIEW_FINANCE",
      ]),
    },
    {
      label: "Assessment Admin",
      path: "/assessment-admin",
      icon: "X",
      show: any([
        "MANAGE_EISA_SITTINGS",
        "CAPTURE_EISA",
        "PUBLISH_EISA",
      ]),
    },
    {
      label: "Learning Resources",
      path: "/learning-resources",
      icon: "B",
      show:
        can(
          "MANAGE_LEARNING_RESOURCES",
        ),
    },
    {
      label: "Student Cards",
      path: "/student-cards",
      icon: "I",
      show:
        can(
          "MANAGE_STUDENT_RECORDS",
        ),
    },
    {
      label: "Reports",
      path: "/reports",
      icon: "P",
      show:
        can(
          "VIEW_REPORTS",
        ),
    },
    {
      label: "Communications",
      path: "/communications",
      icon: "✉",
      show: any([
        "USE_STAFF_MESSAGES",
        "VIEW_STUDENT_MESSAGES",
        "VIEW_ANNOUNCEMENTS",
      ]),
    },
    {
      label: "Student Support",
      path: "/student-support",
      icon: "?",
      show:
        can(
          "VIEW_STUDENT_SUPPORT",
        ),
    },
    {
      label: "Principal Oversight",
      path: "/principal",
      icon: "O",
      show:
        can(
          "SYSTEM_OVERSIGHT",
        ),
    },
    {
      label: "Audit",
      path: "/audit",
      icon: "L",
      show:
        can(
          "VIEW_AUDIT_LOG",
        ),
    },
    {
      label: "System Management",
      path: "/system",
      icon: "âš™",
      show: any([
        "MANAGE_SYSTEM_SETTINGS",
        "MANAGE_STAFF_ACCOUNTS",
        "MANAGE_ROLES_PERMISSIONS",
      ]),
    },
    {
      label: "Notifications",
      path: "/notifications",
      icon: "N",
      show:
        can(
          "VIEW_NOTIFICATIONS",
        ),
    },
    {
      label: "Google Calendar",
      path: "/calendar",
      icon: "G",
      show: true,
    },
    {
      label: "My Profile",
      path: "/profile",
      icon: "M",
      show: true,
    },
  ].filter(
    (item) =>
      item.show,
  );

  if (
    dashboardState.loading
  ) {
    return (
      <div className="splash">
        Loading Staff Desktop...
      </div>
    );
  }

  if (
    dashboardState.error
  ) {
    return (
      <div className="fatal">
        <h1>
          Staff Desktop could not load
        </h1>

        <p>
          {
            dashboardState.error
          }
        </p>

        <button
          className="button gold"
          onClick={
            dashboardState.refresh
          }
        >
          Retry
        </button>

        <button
          className="button light"
          onClick={
            auth.logout
          }
        >
          Sign Out
        </button>
      </div>
    );
  }

  if (
    role &&
    !SUPPORTED_ROLES.has(
      role,
    )
  ) {
    return (
      <div className="fatal">
        <h1>
          Unsupported staff role
        </h1>

        <p>
          Role{" "}
          <strong>
            {role}
          </strong>{" "}
          is not enabled in the Glen
          Moniques Staff portal.
        </p>

        <button
          className="button light"
          onClick={
            auth.logout
          }
        >
          Sign Out
        </button>
      </div>
    );
  }

  const admissionsSections = [
    {
      title:
        "Applications",
      description:
        "Applications awaiting admissions processing.",
      path:
        "/api/staff/admissions/applications",
    },
  ];

  const studentSections = [
    {
      title:
        "Student Records",
      description:
        "Registered learners and administrative student records.",
      path:
        "/api/staff/admin/students",
    },
  ];

  const academicSections = [
    {
      title:
        "Academic Cycles",
      path:
        "/api/staff/academic-management/cycles",
    },
    {
      title:
        "Courses",
      path:
        "/api/staff/academic-management/courses",
    },
    {
      title:
        "Classes",
      path:
        "/api/staff/academic-management/classes",
    },
  ];

  const deliverySections = [
    {
      title:
        "Assigned Classes",
      path:
        "/api/staff/facilitator/classes",
    },
    {
      title:
        "My Timetable",
      path:
        "/api/staff/facilitator/timetable",
    },
    {
      title:
        "Attendance History",
      path:
        "/api/staff/facilitator/attendance",
    },
  ];

  const assessmentSections = [
    ...(can(
      "ASSESS_RESULT",
    )
      ? [
          {
            title:
              "Module Assessment Queue",
            path:
              "/api/staff/assessment/assessor/module-queue",
          },
          {
            title:
              "FISA / EISA Queue",
            path:
              "/api/staff/assessment/assessor/summative-queue",
          },
        ]
      : []),
    ...(can(
      "MODERATE_RESULT",
    )
      ? [
          {
            title:
              "Module Moderation Queue",
            path:
              "/api/staff/assessment/moderator/module-queue",
          },
          {
            title:
              "Summative Moderation Queue",
            path:
              "/api/staff/assessment/moderator/summative-queue",
          },
        ]
      : []),
  ];

  const financeSections = [
    {
      title:
        "Finance Dashboard",
      path:
        "/api/staff/finance/dashboard",
    },
    {
      title:
        "Student Accounts",
      path:
        "/api/staff/finance/students",
    },
    ...(can(
      "MANAGE_SPONSORS",
    ) ||
    can(
      "ASSIGN_SPONSORS",
    )
      ? [
          {
            title:
              "Sponsors",
            path:
              "/api/staff/finance/sponsors",
          },
        ]
      : []),
  ];

  const hrSections = [
    ...(can(
      "VIEW_RECRUITMENT",
    )
      ? [
          {
            title:
              "HR Dashboard",
            path:
              "/api/staff/hr/dashboard",
          },
          {
            title:
              "Vacancies",
            path:
              "/api/staff/hr/vacancies",
          },
          {
            title:
              "Job Applications",
            path:
              "/api/staff/hr/applications",
          },
        ]
      : []),
    ...(can(
      "VIEW_EMPLOYEES",
    )
      ? [
          {
            title:
              "Employees",
            path:
              "/api/staff/hr/employees",
          },
        ]
      : []),
  ];

  const communicationSections = [
    ...(can(
      "USE_STAFF_MESSAGES",
    )
      ? [
          {
            title:
              "Staff Messages",
            path:
              "/api/staff/communications/staff-messages",
          },
        ]
      : []),
    ...(can(
      "VIEW_STUDENT_MESSAGES",
    )
      ? [
          {
            title:
              "Student Messages",
            path:
              "/api/staff/communications/student-messages",
          },
        ]
      : []),
    ...(can(
      "VIEW_ANNOUNCEMENTS",
    )
      ? [
          {
            title:
              "Announcements",
            path:
              "/api/staff/communications/announcements",
          },
        ]
      : []),
  ];

  const systemSections = [
    ...(can(
      "MANAGE_SYSTEM_SETTINGS",
    )
      ? [
          {
            title:
              "System Settings",
            path:
              "/api/staff/admin/system-management/settings",
          },
        ]
      : []),
    ...(can(
      "MANAGE_STAFF_ACCOUNTS",
    )
      ? [
          {
            title:
              "Staff Accounts",
            path:
              "/api/staff/admin/system-management/staff-accounts",
          },
        ]
      : []),
    ...(can(
      "MANAGE_ROLES_PERMISSIONS",
    )
      ? [
          {
            title:
              "Roles & Permissions",
            path:
              "/api/staff/admin/system-management/roles",
          },
        ]
      : []),
  ];

  return (
    <div className="desktop">
      <aside className="sidebar">
        <div className="brand">
          <img
            src="./glen-moniques-logo.png"
            alt="Glen Moniques"
          />

          <div>
            <strong>
              Glen Moniques
            </strong>
            <span>
              Staff Portal
            </span>
          </div>
        </div>

        <div className="role-chip">
          <span>
            Signed in as
          </span>
          <strong>
            {dashboard
              ?.staff
              ?.full_name ||
              auth.staff
                ?.full_name ||
              "Staff Member"}
          </strong>
          <small>
            {role}
          </small>
        </div>

        <nav>
          {nav.map(
            (item) => (
              <NavLink
                key={
                  item.path
                }
                to={
                  item.path
                }
              >
                <b>
                  {
                    item.icon
                  }
                </b>

                <span>
                  {
                    item.label
                  }
                </span>
              </NavLink>
            ),
          )}
        </nav>

        <div className="sidebar-foot">
          <span>
            {
              dashboard
                ?.staff
                ?.staff_code ||
              auth.staff
                ?.staff_code
            }
          </span>

          <button
            onClick={
              auth.logout
            }
          >
            Sign Out
          </button>
        </div>
      </aside>

      <main className="main">
        <header className="topbar">
          <div>
            <span>
              GLEN MONIQUES
            </span>
            <strong>
              Staff Management System
            </strong>
          </div>

          <div className="topbar-right">
            <Badge
              value={role}
            />
          </div>
        </header>

        <div className="content">
          <Routes>
            <Route
              path="/dashboard"
              element={
                <DashboardPage
                  dashboard={
                    dashboard
                  }
                  refresh={
                    dashboardState.refresh
                  }
                />
              }
            />

            <Route
              path="/admissions"
              element={
                <V3.Admissions
                  token={auth.token}
                />
              }
            />

            <Route
              path="/students"
              element={
                <StudentRecordsPage
                  token={auth.token}
                />
              }
            />

            <Route
              path="/documents"
              element={
                <DocumentsLettersPage
                  token={auth.token}
                />
              }
            />

            <Route
              path="/academics"
              element={
                <V3.Academics
                  token={auth.token}
                />
              }
            />

            <Route
              path="/delivery"
              element={
                <V5.Delivery
                  token={auth.token}
                />
              }
            />

            <Route
              path="/assessments"
              element={
                <V5.Assessments
                  token={auth.token}
                />
              }
            />

            <Route
              path="/timetable"
              element={
                <V3.Timetable
                  token={auth.token}
                />
              }
            />

            <Route
              path="/attendance-registers"
              element={
                <V3.AttendanceRegisters
                  token={auth.token}
                />
              }
            />

            <Route
              path="/completion"
              element={
                <V3.Completion
                  token={auth.token}
                />
              }
            />

            <Route
              path="/eisa"
              element={
                <V3.Eisa
                  token={auth.token}
                />
              }
            />

            <Route
              path="/finance"
              element={
                <V5.FinanceOperations
                  token={auth.token}
                />
              }
            />

            <Route
              path="/hr"
              element={
                <V5.HR
                  token={auth.token}
                />
              }
            />

            <Route
              path="/compliance"
              element={
                <V5.Compliance
                  token={auth.token}
                />
              }
            />

            <Route
              path="/academic-calendar"
              element={
                <V5.AcademicCalendar
                  token={auth.token}
                />
              }
            />

            <Route
              path="/finance-setup"
              element={
                <V5.FinanceSetup
                  token={auth.token}
                />
              }
            />

            <Route
              path="/assessment-admin"
              element={
                <V5.AssessmentAdminV54
                  token={auth.token}
                />
              }
            />

            <Route
              path="/learning-resources"
              element={
                <V5.LearningResources
                  token={auth.token}
                />
              }
            />

            <Route
              path="/student-cards"
              element={
                <V5.StudentCards
                  token={auth.token}
                />
              }
            />

            <Route
              path="/reports"
              element={
                <V3.Reports
                  token={auth.token}
                />
              }
            />

            <Route
              path="/communications"
              element={
                <V3.Communications
                  token={auth.token}
                />
              }
            />

            <Route
              path="/student-support"
              element={
                <V3.Support
                  token={auth.token}
                />
              }
            />

            <Route
              path="/principal"
              element={
                <V5.Principal
                  token={auth.token}
                />
              }
            />

            <Route
              path="/audit"
              element={
                <V3.Audit
                  token={auth.token}
                />
              }
            />

            <Route
              path="/system"
              element={
                <V3.System
                  token={auth.token}
                />
              }
            />

            <Route
              path="/notifications"
              element={
                <V3.Notifications
                  token={auth.token}
                />
              }
            />

            <Route
              path="/calendar"
              element={
                <V3.Calendar
                  token={auth.token}
                />
              }
            />

            <Route
              path="/profile"
              element={
                <V3.Profile
                  token={auth.token}
                />
              }
            />

            <Route
              path="/"
              element={
                <Navigate
                  to="/dashboard"
                  replace
                />
              }
            />

            <Route
              path="*"
              element={
                <Navigate
                  to="/dashboard"
                  replace
                />
              }
            />
          </Routes>
        </div>
      </main>
    </div>
  );
}

// ============================================================
// APP
// ============================================================

export default function App() {
  const auth = useAuth();

  if (auth.loading) {
    return (
      <div className="splash">
        <img
          src="./glen-moniques-logo.png"
          alt="Glen Moniques"
        />
        <strong>
          Loading Staff Desktop...
        </strong>
      </div>
    );
  }

  if (
    !auth.isAuthenticated
  ) {
    return <LoginFlow />;
  }

  return <DesktopShell />;
}

