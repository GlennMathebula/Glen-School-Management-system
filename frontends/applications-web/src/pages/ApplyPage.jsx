import { useEffect, useMemo, useState } from "react";

import {
  getApplicationCatalogue,
  submitApplication,
  uploadApplicationDocument,
} from "../api/client";
import { APP_CONFIG } from "../config/app";
import "./ApplicationWizard.css";


const STEPS = [
  "Course",
  "Personal",
  "Contact",
  "Demographics",
  "Academic Info",
  "Review",
  "Documents",
];

const SUBJECT_LEVELS = [
  "Level 7: 80 - 100% (Outstanding achievement)",
  "Level 6: 70 - 79% (Meritorious achievement)",
  "Level 5: 60 - 69% (Substantial achievement)",
  "Level 4: 50 - 59% (Moderate achievement)",
  "Level 3: 40 - 49% (Adequate achievement)",
  "Level 2: 30 - 39% (Elementary achievement)",
  "Level 1: 0 - 29% (Not achieved - Fail)",
];

const COMPULSORY_SUBJECTS = [
  "Home Language",
  "First Additional Language",
  "Mathematics / Mathematical Literacy",
  "Life Orientation / Life Skills",
];

const OPTIONS = {
  title: ["Mr", "Mrs", "Ms", "Miss", "Dr", "Prof"],
  gender: [
    ["M", "Male"],
    ["F", "Female"],
  ],
  citizen: [
    ["SA", "South African"],
    ["PR", "Permanent Resident"],
    ["D", "Dual (SA + Other)"],
    ["O", "Other"],
    ["U", "Unknown"],
  ],
  immigrant: [
    ["03", "South African Citizen"],
    ["01", "Immigrant"],
    ["02", "Refugee"],
  ],
  language: [
    ["Eng", "English"],
    ["Afr", "Afrikaans"],
    ["Nde", "isiNdebele"],
    ["Xho", "isiXhosa"],
    ["Zul", "isiZulu"],
    ["Sep", "sePedi / Northern Sotho"],
    ["Ses", "seSotho"],
    ["Set", "seTswana"],
    ["Swa", "siSwati"],
    ["Tsh", "tshiVenda"],
    ["Xit", "xiTsonga"],
    ["SASL", "South African Sign Language"],
    ["Oth", "Other"],
  ],
  nationality: [
    ["SA", "South Africa"],
    ["NAM", "Namibia"],
    ["BOT", "Botswana"],
    ["ZIM", "Zimbabwe"],
    ["ANG", "Angola"],
    ["MOZ", "Mozambique"],
    ["LES", "Lesotho"],
    ["SWA", "Eswatini / Swaziland"],
    ["MAL", "Malawi"],
    ["ZAM", "Zambia"],
    ["MAU", "Mauritius"],
    ["TAN", "Tanzania"],
    ["SEY", "Seychelles"],
    ["SDC", "Other SADC"],
    ["ROA", "Rest of Africa"],
    ["EUR", "European countries"],
    ["AIS", "Asian countries"],
    ["NOR", "North American countries"],
    ["SOU", "Central and South American countries"],
    ["AUS", "Australia / Oceania"],
    ["OOC", "Other / rest of Oceania"],
    ["U", "Unspecified"],
  ],
  equity: [
    ["BA", "Black African"],
    ["BC", "Coloured"],
    ["BI", "Indian / Asian"],
    ["Wh", "White"],
    ["Oth", "Other"],
    ["U", "Unknown"],
  ],
  socioeconomic: [
    ["01", "Employed"],
    ["02", "Unemployed, looking for work"],
    ["03", "Not working, not looking for work"],
    ["04", "Home-maker"],
    ["06", "Scholar / student"],
    ["07", "Pensioner / retired"],
    ["08", "Not working - disabled person"],
    ["09", "Not working - not wishing to work"],
    ["10", "Not working - other"],
    ["U", "Unspecified"],
  ],
  disability: [
    ["N", "None"],
    ["01", "Sight"],
    ["02", "Hearing"],
    ["03", "Communication"],
    ["04", "Physical"],
    ["05", "Intellectual / learning difficulty"],
    ["06", "Emotional / behavioural / psychological"],
    ["07", "Multiple"],
    ["09", "Disabled but unspecified"],
  ],
  rating: [
    ["01", "No difficulty"],
    ["02", "Some difficulty"],
    ["03", "A lot of difficulty"],
    ["04", "Cannot do at all"],
    ["06", "Cannot yet be determined"],
    ["60", "May be part of multiple difficulties"],
    ["70", "May have difficulty"],
    ["80", "Former difficulty - none now"],
  ],
  province: [
    ["1", "Western Cape"],
    ["2", "Eastern Cape"],
    ["3", "Northern Cape"],
    ["4", "Free State"],
    ["5", "KwaZulu-Natal"],
    ["6", "North West"],
    ["7", "Gauteng"],
    ["8", "Mpumalanga"],
    ["9", "Limpopo"],
    ["N", "SA National / province unspecified"],
    ["X", "Outside South Africa"],
  ],
  grade: [
    "Less than Grade 9",
    "Level 1 (Grade 9 or equivalent)",
    "Level 2 (Grade 10 / N1 / NCV L2 or equivalent)",
    "Level 3 (Grade 11 / N2 / NCV L3 or equivalent)",
    "Level 4 (NSC Matric / IEB / NCV L4 or equivalent)",
  ],
  relationship: [
    "Parent",
    "Guardian",
    "Spouse",
    "Sibling",
    "Child",
    "Relative",
    "Friend",
    "Other",
  ],
};

function blankSubjects() {
  return [
    ...COMPULSORY_SUBJECTS.map((category) => ({
      category,
      name: "",
      level: "",
      required: true,
    })),
    ...Array.from({ length: 3 }, () => ({
      category: "",
      name: "",
      level: "",
      required: false,
    })),
  ];
}

const INITIAL_FORM = {
  application_cycle: "",
  qualification_id: "",
  sdp_code: APP_CONFIG.sdpCode,

  title: "",
  first_name: "",
  middle_name: "",
  last_name: "",
  birth_date: "",
  national_id: "",
  gender_code: "",
  citizen_status: "",
  immigrant_status: "",

  email: "",
  cell_number: "",
  phone_number: "",

  home_addr_1: "",
  home_addr_2: "",
  home_addr_3: "",
  home_postal_code: "",
  postal_addr_1: "",
  postal_addr_2: "",
  postal_addr_3: "",
  postal_code: "",
  province_code: "",

  next_of_kin_surname: "",
  next_of_kin_full_name: "",
  next_of_kin_cell: "",
  next_of_kin_relationship: "",
  next_of_kin_email: "",

  home_language: "",
  nationality_code: "",
  equity_code: "",
  socioeconomic_code: "",
  disability_status: "N",
  disability_rating: "",

  highest_grade_passed: "",
  school_name: "",
  year_completed: "",
  popi_agree: false,
};

function Field({
  label,
  required = false,
  hint = "",
  children,
  full = false,
}) {
  return (
    <label className={`aw-field ${full ? "aw-full" : ""}`}>
      <span className="aw-label">
        {label}
        {required ? <span className="aw-req"> *</span> : null}
      </span>
      {children}
      {hint ? <span className="aw-hint">{hint}</span> : null}
    </label>
  );
}

function Input({
  name,
  value,
  onChange,
  type = "text",
  required = false,
  placeholder = "",
  maxLength,
  pattern,
  min,
  max,
}) {
  return (
    <input
      name={name}
      value={value ?? ""}
      onChange={onChange}
      type={type}
      required={required}
      placeholder={placeholder}
      maxLength={maxLength}
      pattern={pattern}
      min={min}
      max={max}
    />
  );
}

function Select({
  name,
  value,
  onChange,
  options,
  required = false,
  disabled = false,
  placeholder = "Select...",
}) {
  return (
    <select
      name={name}
      value={value ?? ""}
      onChange={onChange}
      required={required}
      disabled={disabled}
    >
      <option value="">{placeholder}</option>
      {options.map((item) => {
        const valueText = Array.isArray(item) ? item[0] : item;
        const labelText = Array.isArray(item) ? item[1] : item;

        return (
          <option key={valueText} value={valueText}>
            {labelText}
          </option>
        );
      })}
    </select>
  );
}

function StepProgress({ step }) {
  return (
    <div className="aw-progress" aria-label="Application progress">
      {STEPS.map((label, index) => {
        const number = index + 1;
        const state =
          number < step ? "done" : number === step ? "active" : "";

        return (
          <div className="aw-progress-fragment" key={label}>
            <div className="aw-step">
              <div className={`aw-dot ${state}`}>
                {number < step ? "✓" : number}
              </div>
              <div className={`aw-step-label ${state}`}>{label}</div>
            </div>
            {number < STEPS.length ? (
              <div className={`aw-line ${number < step ? "done" : ""}`} />
            ) : null}
          </div>
        );
      })}
    </div>
  );
}

function Section({ icon, title, children }) {
  return (
    <section className="aw-card">
      <div className="aw-card-head">
        <span aria-hidden="true">{icon}</span>
        <h2>{title}</h2>
      </div>
      <div className="aw-card-body">{children}</div>
    </section>
  );
}

function ReviewRow({ label, value }) {
  return (
    <div className="aw-review-row">
      <span>{label}</span>
      <strong>{value || "—"}</strong>
    </div>
  );
}

export default function ApplyPage() {
  const [step, setStep] = useState(1);
  const [form, setForm] = useState(INITIAL_FORM);
  const [subjects, setSubjects] = useState(blankSubjects);
  const [sameAddress, setSameAddress] = useState(false);

  const [catalogue, setCatalogue] = useState([]);
  const [catalogueState, setCatalogueState] = useState({
    loading: true,
    error: "",
  });

  const [error, setError] = useState("");
  const [documentChoice, setDocumentChoice] = useState("");
  const [files, setFiles] = useState({
    ID_COPY: null,
    SCHOOL_LEAVING_CERTIFICATE: null,
    CV: null,
    CIPC_CERTIFICATE: null,
    ADDITIONAL_DOCUMENT: null,
  });
  const [additionalLabel, setAdditionalLabel] = useState("");

  const [savedApplication, setSavedApplication] = useState(null);
  const [submitting, setSubmitting] = useState(false);
  const [uploadedTypes, setUploadedTypes] = useState([]);
  const [complete, setComplete] = useState(null);

  useEffect(() => {
    let active = true;

    getApplicationCatalogue()
      .then((response) => {
        if (!active) return;

        setCatalogue(response?.catalogue?.cycles || []);
        setCatalogueState({
          loading: false,
          error: "",
        });
      })
      .catch((requestError) => {
        if (!active) return;

        setCatalogueState({
          loading: false,
          error: requestError.message,
        });
      });

    return () => {
      active = false;
    };
  }, []);

  const selectedCycle = useMemo(
    () =>
      catalogue.find(
        (cycle) => cycle.cycle_code === form.application_cycle,
      ) || null,
    [catalogue, form.application_cycle],
  );

  const selectedCourse = useMemo(
    () =>
      selectedCycle?.courses?.find(
        (course) => course.course_code === form.qualification_id,
      ) || null,
    [selectedCycle, form.qualification_id],
  );

  function change(event) {
    const { name, value, type, checked } = event.target;

    setForm((current) => {
      const next = {
        ...current,
        [name]: type === "checkbox" ? checked : value,
      };

      if (name === "application_cycle") {
        next.qualification_id = "";
      }

      if (name === "disability_status" && value === "N") {
        next.disability_rating = "";
      }

      const addressMap = {
        home_addr_1: "postal_addr_1",
        home_addr_2: "postal_addr_2",
        home_addr_3: "postal_addr_3",
        home_postal_code: "postal_code",
      };

      if (sameAddress && addressMap[name]) {
        next[addressMap[name]] = value;
      }

      return next;
    });

    setError("");
  }

  function toggleSameAddress(event) {
    const checked = event.target.checked;
    setSameAddress(checked);

    if (checked) {
      setForm((current) => ({
        ...current,
        postal_addr_1: current.home_addr_1,
        postal_addr_2: current.home_addr_2,
        postal_addr_3: current.home_addr_3,
        postal_code: current.home_postal_code,
      }));
    }
  }

  function updateSubject(index, key, value) {
    setSubjects((current) =>
      current.map((subject, subjectIndex) =>
        subjectIndex === index
          ? { ...subject, [key]: value }
          : subject,
      ),
    );
    setError("");
  }

  function addSubject() {
    if (subjects.length >= 10) return;

    setSubjects((current) => [
      ...current,
      {
        category: "",
        name: "",
        level: "",
        required: false,
      },
    ]);
  }

  function removeSubject(index) {
    setSubjects((current) =>
      current.filter((_, subjectIndex) => subjectIndex !== index),
    );
  }

  function validEmail(value) {
    return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value || "");
  }

  function validateStep(number) {
    const missing = [];

    if (number === 1) {
      if (!form.application_cycle) missing.push("application intake");
      if (!form.qualification_id) missing.push("programme");
    }

    if (number === 2) {
      [
        ["title", "title"],
        ["first_name", "first name"],
        ["last_name", "last name"],
        ["birth_date", "date of birth"],
        ["national_id", "SA ID number"],
        ["gender_code", "gender"],
        ["citizen_status", "citizen / resident status"],
        ["immigrant_status", "immigrant status"],
      ].forEach(([key, label]) => {
        if (!String(form[key] || "").trim()) missing.push(label);
      });

      if (form.national_id && !/^\d{13}$/.test(form.national_id)) {
        setError("South African ID number must contain exactly 13 digits.");
        return false;
      }
    }

    if (number === 3) {
      [
        ["email", "email address"],
        ["home_addr_1", "home address line 1"],
        ["home_addr_2", "home address line 2"],
        ["home_postal_code", "home postal code"],
        ["postal_addr_1", "postal address line 1"],
        ["postal_addr_2", "postal address line 2"],
        ["postal_code", "postal code"],
        ["province_code", "province"],
      ].forEach(([key, label]) => {
        if (!String(form[key] || "").trim()) missing.push(label);
      });

      if (form.email && !validEmail(form.email)) {
        setError("Enter a valid email address.");
        return false;
      }

      if (
        form.home_postal_code &&
        !/^\d{4}$/.test(form.home_postal_code)
      ) {
        setError("Home postal code must contain exactly 4 digits.");
        return false;
      }

      if (form.postal_code && !/^\d{4}$/.test(form.postal_code)) {
        setError("Postal code must contain exactly 4 digits.");
        return false;
      }

      if (form.next_of_kin_email && !validEmail(form.next_of_kin_email)) {
        setError("Enter a valid next-of-kin email address.");
        return false;
      }
    }

    if (number === 4) {
      [
        ["home_language", "home language"],
        ["nationality_code", "nationality"],
        ["equity_code", "equity"],
        ["socioeconomic_code", "socioeconomic status"],
      ].forEach(([key, label]) => {
        if (!String(form[key] || "").trim()) missing.push(label);
      });

      if (
        form.disability_status !== "N" &&
        !form.disability_rating
      ) {
        missing.push("disability rating");
      }

      if (!form.popi_agree) {
        missing.push("POPIA consent");
      }
    }

    if (number === 5) {
      if (!form.highest_grade_passed) missing.push("highest grade passed");
      if (!form.year_completed) missing.push("year completed");
      if (!form.school_name.trim()) missing.push("school name");

      const incompleteRequired = subjects
        .filter((subject) => subject.required)
        .some(
          (subject) =>
            !subject.name.trim() || !subject.level,
        );

      if (incompleteRequired) {
        setError(
          "Complete all four compulsory subject rows, including the subject name and achievement level.",
        );
        return false;
      }
    }

    if (number === 6 && !documentChoice) {
      missing.push("document upload choice");
    }

    if (missing.length) {
      setError(
        `Please complete: ${missing.join(", ")}.`,
      );
      return false;
    }

    setError("");
    return true;
  }

  function next(number) {
    if (!validateStep(number)) return;

    window.scrollTo({ top: 0, behavior: "smooth" });
    setStep(number + 1);
  }

  function back(number) {
    setError("");
    window.scrollTo({ top: 0, behavior: "smooth" });
    setStep(number - 1);
  }

  function applicationPayload() {
    const activeSubjects = subjects
      .filter((subject) => subject.name.trim())
      .map(({ category, name, level }) => ({
        category: category || "Additional",
        subject: name.trim(),
        achievement_level: level,
      }));

    const payload = {
      ...form,
      sdp_code: selectedCourse?.sdp_code || APP_CONFIG.sdpCode || "PUBLIC",
      qualification_id: selectedCourse?.course_code || form.qualification_id,
      application_cycle: selectedCycle?.cycle_code || form.application_cycle,
      academic_subjects: JSON.stringify(activeSubjects),
      year_completed: form.year_completed
        ? Number(form.year_completed)
        : null,
      disability_rating:
        form.disability_status === "N"
          ? null
          : form.disability_rating || null,
    };

    Object.keys(payload).forEach((key) => {
      if (payload[key] === "") payload[key] = null;
    });

    return payload;
  }

  async function saveApplication() {
    if (savedApplication) return savedApplication;

    const response = await submitApplication(applicationPayload());
    const application = response?.application || {};

    if (!application.student_number) {
      throw new Error(
        "The application was saved but no student number was returned.",
      );
    }

    const saved = {
      ...application,
      email_sent:
        application.email_sent === true
          ? true
          : application.email_sent === false
            ? false
            : null,
    };

    setSavedApplication(saved);
    return saved;
  }

  async function continueFromReview() {
    if (!validateStep(6)) return;

    setSubmitting(true);
    setError("");

    try {
      const saved = await saveApplication();

      if (documentChoice === "no") {
        setComplete({
          studentNumber: saved.student_number,
          status: saved.app_status || "Pending",
          acknowledgementStatus:
            saved.email_sent === true
              ? "Sent"
              : saved.email_sent === false
                ? "Not confirmed"
                : "Processed",
          documentsUploaded: 0,
        });
        return;
      }

      setStep(7);
      window.scrollTo({ top: 0, behavior: "smooth" });
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setSubmitting(false);
    }
  }

  function fileChange(type, file) {
    setFiles((current) => ({
      ...current,
      [type]: file || null,
    }));
    setError("");
  }

  function validateFiles() {
    const requiredTypes = [
      ["ID_COPY", "ID Copy"],
      ["SCHOOL_LEAVING_CERTIFICATE", "School Leaving Certificate"],
      ["CV", "Curriculum Vitae"],
    ];

    if (selectedCycle?.cipc_required) {
      requiredTypes.push(["CIPC_CERTIFICATE", "CIPC Certificate"]);
    }

    for (const [type, label] of requiredTypes) {
      if (!files[type] && !uploadedTypes.includes(type)) {
        setError(`${label} is required.`);
        return false;
      }
    }

    for (const file of Object.values(files)) {
      if (!file) continue;

      if (file.size > 10 * 1024 * 1024) {
        setError(`${file.name} exceeds the 10 MB upload limit.`);
        return false;
      }

      if (
        ![
          "application/pdf",
          "image/jpeg",
          "image/png",
        ].includes(file.type)
      ) {
        setError(
          `${file.name} must be a PDF, JPG, JPEG or PNG file.`,
        );
        return false;
      }
    }

    if (files.ADDITIONAL_DOCUMENT && !additionalLabel.trim()) {
      setError("Enter a label for the additional document.");
      return false;
    }

    return true;
  }

  async function finishWithDocuments() {
    if (!savedApplication) {
      setError("Application details have not been saved yet.");
      return;
    }

    if (!validateFiles()) return;

    setSubmitting(true);
    setError("");

    const queue = [
      ["ID_COPY", "ID Copy"],
      ["SCHOOL_LEAVING_CERTIFICATE", "School Leaving Certificate"],
      ["CV", "Curriculum Vitae"],
      ["CIPC_CERTIFICATE", "CIPC Certificate"],
      ["ADDITIONAL_DOCUMENT", additionalLabel.trim()],
    ];

    try {
      let uploaded = [...uploadedTypes];

      for (const [type, label] of queue) {
        const file = files[type];

        if (!file || uploaded.includes(type)) continue;

        await uploadApplicationDocument({
          studentNumber: savedApplication.student_number,
          nationalId: form.national_id,
          documentType: type,
          documentLabel:
            type === "ADDITIONAL_DOCUMENT" ? label : "",
          file,
        });

        uploaded = [...uploaded, type];
        setUploadedTypes(uploaded);
      }

      setComplete({
        studentNumber: savedApplication.student_number,
        status: savedApplication.app_status || "Pending",
        acknowledgementStatus:
          savedApplication.email_sent === true
            ? "Sent"
            : savedApplication.email_sent === false
              ? "Not confirmed"
              : "Processed",
        documentsUploaded: uploaded.length,
      });
    } catch (requestError) {
      setError(
        `${requestError.message} Any documents already uploaded were kept. You can retry to continue with the remaining files.`,
      );
    } finally {
      setSubmitting(false);
    }
  }

  function startAnother() {
    setStep(1);
    setForm(INITIAL_FORM);
    setSubjects(blankSubjects());
    setSameAddress(false);
    setError("");
    setDocumentChoice("");
    setFiles({
      ID_COPY: null,
      SCHOOL_LEAVING_CERTIFICATE: null,
      CV: null,
      CIPC_CERTIFICATE: null,
      ADDITIONAL_DOCUMENT: null,
    });
    setAdditionalLabel("");
    setSavedApplication(null);
    setUploadedTypes([]);
    setComplete(null);
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  const years = Array.from(
    { length: 31 },
    (_, index) => new Date().getFullYear() - index,
  );

  if (complete) {
    return (
      <div className="aw-page">
        <div className="aw-shell aw-shell-success">
          <div className="aw-success">
            <div className="aw-success-icon">✓</div>
            <span className="aw-kicker">Application received</span>
            <h1>Thank you for applying.</h1>
            <p>
              Your application has been saved successfully. Keep your student
              number safe for all future correspondence.
            </p>

            <div className="aw-student-number">
              {complete.studentNumber}
            </div>

            <div className="aw-success-details">
              <ReviewRow label="Application status" value={complete.status} />
              <ReviewRow
                label="Acknowledgement email"
                value={complete.acknowledgementStatus}
              />
              <ReviewRow
                label="Documents uploaded now"
                value={String(complete.documentsUploaded)}
              />
            </div>

            <button
              type="button"
              className="aw-btn aw-btn-primary"
              onClick={startAnother}
            >
              Start another application
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="aw-page">
      <div className="aw-shell">
        <div className="aw-intro">
          <span className="aw-kicker">Learner Application</span>
          <h1>Apply to Glen Moniques</h1>
          <p>
            Complete each step carefully. Your information is used for
            admissions, learner administration and required statutory records.
          </p>
        </div>

        <StepProgress step={step} />

        {error ? <div className="aw-alert aw-alert-error">{error}</div> : null}

        {step === 1 ? (
          <>
            <Section icon="📚" title="Select Course & Programme">
              {catalogueState.loading ? (
                <div className="aw-loading">Loading open application intakes...</div>
              ) : catalogueState.error ? (
                <div className="aw-alert aw-alert-error">
                  {catalogueState.error}
                </div>
              ) : catalogue.length === 0 ? (
                <div className="aw-empty">
                  There are currently no open application intakes.
                </div>
              ) : (
                <div className="aw-grid">
                  <Field label="Application Intake" required>
                    <Select
                      name="application_cycle"
                      value={form.application_cycle}
                      onChange={change}
                      required
                      options={catalogue.map((cycle) => [
                        cycle.cycle_code,
                        cycle.cycle_name || cycle.cycle_code,
                      ])}
                    />
                  </Field>

                  <Field label="Course / Programme" required>
                    <Select
                      name="qualification_id"
                      value={form.qualification_id}
                      onChange={change}
                      required
                      disabled={!selectedCycle}
                      options={(selectedCycle?.courses || []).map((course) => [
                        course.course_code,
                        course.course_name,
                      ])}
                      placeholder={
                        selectedCycle
                          ? "Select programme..."
                          : "Select intake first..."
                      }
                    />
                  </Field>
                </div>
              )}

              {selectedCourse ? (
                <div className="aw-course-card">
                  <div className="aw-course-title">{selectedCourse.course_name}</div>
                  <div className="aw-course-meta">
                    <div>
                      <span>Qualification ID</span>
                      <strong>{selectedCourse.course_code}</strong>
                    </div>
                    <div>
                      <span>NQF Level</span>
                      <strong>{selectedCourse.nqf_level}</strong>
                    </div>
                    <div>
                      <span>Credits</span>
                      <strong>{selectedCourse.credits}</strong>
                    </div>
                    <div>
                      <span>Duration</span>
                      <strong>
                        {selectedCourse.completion_months
                          ? `${selectedCourse.completion_months} month(s)`
                          : "—"}
                      </strong>
                    </div>
                  </div>
                  {selectedCourse.entry_requirements ? (
                    <p>
                      <strong>Entry requirement:</strong>{" "}
                      {selectedCourse.entry_requirements}
                    </p>
                  ) : null}
                </div>
              ) : null}
            </Section>

            <div className="aw-nav">
              <button
                type="button"
                className="aw-btn aw-btn-primary aw-next"
                onClick={() => next(1)}
                disabled={catalogueState.loading || catalogue.length === 0}
              >
                Next: Personal Details →
              </button>
            </div>
          </>
        ) : null}

        {step === 2 ? (
          <>
            <Section icon="👤" title="Personal Information">
              <div className="aw-grid aw-grid-three">
                <Field label="Title" required>
                  <Select
                    name="title"
                    value={form.title}
                    onChange={change}
                    required
                    options={OPTIONS.title}
                  />
                </Field>

                <Field label="First Name" required>
                  <Input
                    name="first_name"
                    value={form.first_name}
                    onChange={change}
                    required
                  />
                </Field>

                <Field label="Middle Name" hint="Optional">
                  <Input
                    name="middle_name"
                    value={form.middle_name}
                    onChange={change}
                  />
                </Field>
              </div>

              <div className="aw-grid">
                <Field label="Last Name" required>
                  <Input
                    name="last_name"
                    value={form.last_name}
                    onChange={change}
                    required
                  />
                </Field>

                <Field
                  label="Date of Birth"
                  required
                  hint="The backend stores the date in the required learner record."
                >
                  <Input
                    name="birth_date"
                    value={form.birth_date}
                    onChange={change}
                    type="date"
                    required
                  />
                </Field>

                <Field
                  label="South African ID Number"
                  required
                  hint="13 digits. The backend validates the SA ID structure and checksum."
                >
                  <Input
                    name="national_id"
                    value={form.national_id}
                    onChange={change}
                    required
                    maxLength={13}
                    pattern="[0-9]{13}"
                    placeholder="13-digit SA ID"
                  />
                </Field>

                <Field label="Gender" required>
                  <Select
                    name="gender_code"
                    value={form.gender_code}
                    onChange={change}
                    required
                    options={OPTIONS.gender}
                  />
                </Field>

                <Field label="Citizen / Resident Status" required>
                  <Select
                    name="citizen_status"
                    value={form.citizen_status}
                    onChange={change}
                    required
                    options={OPTIONS.citizen}
                  />
                </Field>

                <Field label="Immigrant Status" required>
                  <Select
                    name="immigrant_status"
                    value={form.immigrant_status}
                    onChange={change}
                    required
                    options={OPTIONS.immigrant}
                  />
                </Field>
              </div>
            </Section>

            <div className="aw-nav">
              <button type="button" className="aw-btn aw-btn-secondary" onClick={() => back(2)}>
                ← Back
              </button>
              <button type="button" className="aw-btn aw-btn-primary" onClick={() => next(2)}>
                Next: Contact →
              </button>
            </div>
          </>
        ) : null}

        {step === 3 ? (
          <>
            <Section icon="📬" title="Contact Information">
              <div className="aw-grid">
                <Field
                  label="Email Address"
                  required
                  hint="Required by Glen Moniques for application correspondence."
                >
                  <Input
                    name="email"
                    value={form.email}
                    onChange={change}
                    type="email"
                    required
                    placeholder="name@example.com"
                  />
                </Field>

                <Field label="Cell Phone" hint="Optional in the QCTO learner data specification.">
                  <Input
                    name="cell_number"
                    value={form.cell_number}
                    onChange={change}
                    placeholder="e.g. 0821234567"
                  />
                </Field>

                <Field label="Alternative Phone" hint="Optional">
                  <Input
                    name="phone_number"
                    value={form.phone_number}
                    onChange={change}
                  />
                </Field>
              </div>
            </Section>

            <Section icon="🏠" title="Home Address">
              <div className="aw-grid">
                <Field label="Address Line 1" required>
                  <Input
                    name="home_addr_1"
                    value={form.home_addr_1}
                    onChange={change}
                    required
                    placeholder="Street / stand number and street or location"
                  />
                </Field>

                <Field label="Address Line 2" required>
                  <Input
                    name="home_addr_2"
                    value={form.home_addr_2}
                    onChange={change}
                    required
                    placeholder="Suburb, village or locality"
                  />
                </Field>

                <Field label="Address Line 3" hint="Conditional / optional">
                  <Input
                    name="home_addr_3"
                    value={form.home_addr_3}
                    onChange={change}
                    placeholder="City / town"
                  />
                </Field>

                <Field label="Home Postal Code" required>
                  <Input
                    name="home_postal_code"
                    value={form.home_postal_code}
                    onChange={change}
                    required
                    maxLength={4}
                    pattern="[0-9]{4}"
                    placeholder="4 digits"
                  />
                </Field>

                <Field label="Province" required>
                  <Select
                    name="province_code"
                    value={form.province_code}
                    onChange={change}
                    required
                    options={OPTIONS.province}
                  />
                </Field>
              </div>
            </Section>

            <Section icon="📮" title="Postal Address">
              <label className="aw-check-row">
                <input
                  type="checkbox"
                  checked={sameAddress}
                  onChange={toggleSameAddress}
                />
                <span>My postal address is the same as my home address.</span>
              </label>

              <div className="aw-grid">
                <Field label="Postal Address Line 1" required>
                  <Input
                    name="postal_addr_1"
                    value={form.postal_addr_1}
                    onChange={change}
                    required
                  />
                </Field>

                <Field label="Postal Address Line 2" required>
                  <Input
                    name="postal_addr_2"
                    value={form.postal_addr_2}
                    onChange={change}
                    required
                  />
                </Field>

                <Field label="Postal Address Line 3" hint="Conditional / optional">
                  <Input
                    name="postal_addr_3"
                    value={form.postal_addr_3}
                    onChange={change}
                  />
                </Field>

                <Field label="Postal Code" required>
                  <Input
                    name="postal_code"
                    value={form.postal_code}
                    onChange={change}
                    required
                    maxLength={4}
                    pattern="[0-9]{4}"
                    placeholder="4 digits"
                  />
                </Field>
              </div>
            </Section>

            <Section icon="👪" title="Next of Kin">
              <p className="aw-section-note">
                These details are useful to Glen Moniques but are not marked as
                required QCTO learner-load fields in the supplied specification.
              </p>

              <div className="aw-grid">
                <Field label="Surname">
                  <Input
                    name="next_of_kin_surname"
                    value={form.next_of_kin_surname}
                    onChange={change}
                  />
                </Field>

                <Field label="Full Name">
                  <Input
                    name="next_of_kin_full_name"
                    value={form.next_of_kin_full_name}
                    onChange={change}
                  />
                </Field>

                <Field label="Cell Phone">
                  <Input
                    name="next_of_kin_cell"
                    value={form.next_of_kin_cell}
                    onChange={change}
                  />
                </Field>

                <Field label="Relationship">
                  <Select
                    name="next_of_kin_relationship"
                    value={form.next_of_kin_relationship}
                    onChange={change}
                    options={OPTIONS.relationship}
                  />
                </Field>

                <Field label="Email Address">
                  <Input
                    name="next_of_kin_email"
                    value={form.next_of_kin_email}
                    onChange={change}
                    type="email"
                  />
                </Field>
              </div>
            </Section>

            <div className="aw-nav">
              <button type="button" className="aw-btn aw-btn-secondary" onClick={() => back(3)}>
                ← Back
              </button>
              <button type="button" className="aw-btn aw-btn-primary" onClick={() => next(3)}>
                Next: Demographics →
              </button>
            </div>
          </>
        ) : null}

        {step === 4 ? (
          <>
            <Section icon="📊" title="Demographics">
              <div className="aw-grid">
                <Field label="Home Language" required>
                  <Select
                    name="home_language"
                    value={form.home_language}
                    onChange={change}
                    required
                    options={OPTIONS.language}
                  />
                </Field>

                <Field label="Nationality" required>
                  <Select
                    name="nationality_code"
                    value={form.nationality_code}
                    onChange={change}
                    required
                    options={OPTIONS.nationality}
                  />
                </Field>

                <Field label="Equity" required>
                  <Select
                    name="equity_code"
                    value={form.equity_code}
                    onChange={change}
                    required
                    options={OPTIONS.equity}
                  />
                </Field>

                <Field label="Socioeconomic Status" required>
                  <Select
                    name="socioeconomic_code"
                    value={form.socioeconomic_code}
                    onChange={change}
                    required
                    options={OPTIONS.socioeconomic}
                  />
                </Field>

                <Field label="Disability Status" required>
                  <Select
                    name="disability_status"
                    value={form.disability_status}
                    onChange={change}
                    required
                    options={OPTIONS.disability}
                  />
                </Field>

                <Field
                  label="Disability Rating"
                  required={form.disability_status !== "N"}
                  hint={
                    form.disability_status === "N"
                      ? "Not required when disability status is None."
                      : "Required when a disability is selected."
                  }
                >
                  <Select
                    name="disability_rating"
                    value={form.disability_rating}
                    onChange={change}
                    required={form.disability_status !== "N"}
                    disabled={form.disability_status === "N"}
                    options={OPTIONS.rating}
                  />
                </Field>
              </div>
            </Section>

            <Section icon="🔒" title="POPIA Consent">
              <div className="aw-popi">
                <p>
                  I consent to Glen Moniques processing the information supplied
                  in this application for admissions, learner administration,
                  statutory reporting and related educational purposes.
                </p>
                <label className="aw-check-row">
                  <input
                    type="checkbox"
                    name="popi_agree"
                    checked={form.popi_agree}
                    onChange={change}
                  />
                  <span>I agree and consent to the processing of my information.</span>
                </label>
              </div>
            </Section>

            <div className="aw-nav">
              <button type="button" className="aw-btn aw-btn-secondary" onClick={() => back(4)}>
                ← Back
              </button>
              <button type="button" className="aw-btn aw-btn-primary" onClick={() => next(4)}>
                Next: Academic Info →
              </button>
            </div>
          </>
        ) : null}

        {step === 5 ? (
          <>
            <Section icon="🎓" title="Academic Information">
              <div className="aw-grid">
                <Field label="Highest Grade Passed" required>
                  <Select
                    name="highest_grade_passed"
                    value={form.highest_grade_passed}
                    onChange={change}
                    required
                    options={OPTIONS.grade}
                  />
                </Field>

                <Field label="Year Completed" required>
                  <Select
                    name="year_completed"
                    value={form.year_completed}
                    onChange={change}
                    required
                    options={years.map((year) => String(year))}
                  />
                </Field>

                <Field label="Name of School" required full>
                  <Input
                    name="school_name"
                    value={form.school_name}
                    onChange={change}
                    required
                    placeholder="Name of school or institution"
                  />
                </Field>
              </div>
            </Section>

            <Section icon="📚" title="Subjects">
              <p className="aw-section-note">
                Complete the first four compulsory subject categories. You can
                add additional subjects up to a maximum of 10.
              </p>

              <div className="aw-subjects">
                {subjects.map((subject, index) => (
                  <div className="aw-subject-row" key={`${subject.category}-${index}`}>
                    <div className="aw-subject-category">
                      {subject.category || "Additional Subject"}
                      {subject.required ? <span className="aw-req"> *</span> : null}
                    </div>

                    <input
                      value={subject.name}
                      onChange={(event) =>
                        updateSubject(index, "name", event.target.value)
                      }
                      placeholder={
                        subject.category
                          ? `Enter ${subject.category}`
                          : "Subject name"
                      }
                    />

                    <select
                      value={subject.level}
                      onChange={(event) =>
                        updateSubject(index, "level", event.target.value)
                      }
                    >
                      <option value="">Achievement level...</option>
                      {SUBJECT_LEVELS.map((level) => (
                        <option key={level} value={level}>
                          {level}
                        </option>
                      ))}
                    </select>

                    {!subject.required ? (
                      <button
                        type="button"
                        className="aw-remove-subject"
                        onClick={() => removeSubject(index)}
                        aria-label="Remove subject"
                      >
                        ×
                      </button>
                    ) : null}
                  </div>
                ))}
              </div>

              <button
                type="button"
                className="aw-btn aw-btn-light"
                onClick={addSubject}
                disabled={subjects.length >= 10}
              >
                + Add Subject
              </button>
            </Section>

            <div className="aw-nav">
              <button type="button" className="aw-btn aw-btn-secondary" onClick={() => back(5)}>
                ← Back
              </button>
              <button type="button" className="aw-btn aw-btn-primary" onClick={() => next(5)}>
                Next: Review →
              </button>
            </div>
          </>
        ) : null}

        {step === 6 ? (
          <>
            <Section icon="📋" title="Review Your Application">
              <div className="aw-review-group">
                <h3>Programme</h3>
                <ReviewRow label="Intake" value={selectedCycle?.cycle_name || selectedCycle?.cycle_code} />
                <ReviewRow label="Programme" value={selectedCourse?.course_name} />
                <ReviewRow label="Qualification ID" value={selectedCourse?.course_code} />
              </div>

              <div className="aw-review-group">
                <h3>Personal Details</h3>
                <ReviewRow label="Name" value={[form.title, form.first_name, form.middle_name, form.last_name].filter(Boolean).join(" ")} />
                <ReviewRow label="Date of Birth" value={form.birth_date} />
                <ReviewRow label="SA ID" value={form.national_id} />
                <ReviewRow label="Email" value={form.email} />
                <ReviewRow label="Cell" value={form.cell_number} />
              </div>

              <div className="aw-review-group">
                <h3>Address & Demographics</h3>
                <ReviewRow
                  label="Home Address"
                  value={[form.home_addr_1, form.home_addr_2, form.home_addr_3, form.home_postal_code].filter(Boolean).join(", ")}
                />
                <ReviewRow label="Home Language" value={form.home_language} />
                <ReviewRow label="Nationality" value={form.nationality_code} />
                <ReviewRow label="Equity" value={form.equity_code} />
                <ReviewRow label="Socioeconomic Status" value={form.socioeconomic_code} />
              </div>

              <div className="aw-review-group">
                <h3>Academic Information</h3>
                <ReviewRow label="Highest Grade" value={form.highest_grade_passed} />
                <ReviewRow label="Year Completed" value={form.year_completed} />
                <ReviewRow label="School" value={form.school_name} />
                <ReviewRow
                  label="Subjects Captured"
                  value={String(subjects.filter((subject) => subject.name.trim()).length)}
                />
              </div>
            </Section>

            <Section icon="📎" title="Supporting Documents">
              <p className="aw-section-note">
                Do you have electronic copies of your supporting documents ready
                to upload with this application?
              </p>

              <div className="aw-radio-stack">
                <label className={documentChoice === "yes" ? "selected" : ""}>
                  <input
                    type="radio"
                    name="documentChoice"
                    value="yes"
                    checked={documentChoice === "yes"}
                    onChange={(event) => {
                      setDocumentChoice(event.target.value);
                      setError("");
                    }}
                  />
                  <span>
                    <strong>Yes, upload them now</strong>
                    <small>
                      Your application details will be saved first so your
                      documents can be linked to your new student number.
                    </small>
                  </span>
                </label>

                <label className={documentChoice === "no" ? "selected" : ""}>
                  <input
                    type="radio"
                    name="documentChoice"
                    value="no"
                    checked={documentChoice === "no"}
                    onChange={(event) => {
                      setDocumentChoice(event.target.value);
                      setError("");
                    }}
                  />
                  <span>
                    <strong>No, I do not have them ready now</strong>
                    <small>
                      Submit the application now. Admissions may request the
                      required documents later.
                    </small>
                  </span>
                </label>
              </div>
            </Section>

            <div className="aw-nav">
              <button type="button" className="aw-btn aw-btn-secondary" onClick={() => back(6)} disabled={submitting}>
                ← Back & Edit
              </button>
              <button
                type="button"
                className="aw-btn aw-btn-primary"
                onClick={continueFromReview}
                disabled={submitting}
              >
                {submitting
                  ? "Saving application..."
                  : documentChoice === "yes"
                    ? "Save & Continue to Documents →"
                    : "Submit Application ✓"}
              </button>
            </div>
          </>
        ) : null}

        {step === 7 ? (
          <>
            <div className="aw-saved-banner">
              <div>
                <strong>Application saved.</strong>
                <span>
                  {" "}
                  {savedApplication?.email_sent === true
                    ? "Acknowledgement email sent."
                    : savedApplication?.email_sent === false
                      ? "Acknowledgement email delivery was not confirmed."
                      : "Acknowledgement email processed."}
                </span>
              </div>
              <span>
                Student Number: {savedApplication?.student_number}
              </span>
            </div>

            <Section icon="📎" title="Supporting Documents">
              <div className="aw-info">
                Accepted formats: PDF, JPG, JPEG and PNG. Maximum 10 MB per
                document. Documents uploaded successfully are kept even if a
                later upload needs to be retried.
              </div>

              <div className="aw-file-grid">
                <Field label="ID Copy" required>
                  <input
                    type="file"
                    accept=".pdf,.jpg,.jpeg,.png"
                    onChange={(event) =>
                      fileChange("ID_COPY", event.target.files?.[0])
                    }
                    disabled={uploadedTypes.includes("ID_COPY")}
                  />
                  {uploadedTypes.includes("ID_COPY") ? (
                    <span className="aw-uploaded">✓ Uploaded</span>
                  ) : null}
                </Field>

                <Field label="School Leaving Certificate" required>
                  <input
                    type="file"
                    accept=".pdf,.jpg,.jpeg,.png"
                    onChange={(event) =>
                      fileChange(
                        "SCHOOL_LEAVING_CERTIFICATE",
                        event.target.files?.[0],
                      )
                    }
                    disabled={uploadedTypes.includes("SCHOOL_LEAVING_CERTIFICATE")}
                  />
                  {uploadedTypes.includes("SCHOOL_LEAVING_CERTIFICATE") ? (
                    <span className="aw-uploaded">✓ Uploaded</span>
                  ) : null}
                </Field>

                <Field label="Curriculum Vitae" required>
                  <input
                    type="file"
                    accept=".pdf,.jpg,.jpeg,.png"
                    onChange={(event) =>
                      fileChange("CV", event.target.files?.[0])
                    }
                    disabled={uploadedTypes.includes("CV")}
                  />
                  {uploadedTypes.includes("CV") ? (
                    <span className="aw-uploaded">✓ Uploaded</span>
                  ) : null}
                </Field>

                <Field
                  label="CIPC Certificate"
                  required={Boolean(selectedCycle?.cipc_required)}
                  hint={
                    selectedCycle?.cipc_required
                      ? "Required for this application intake."
                      : "Optional for this intake."
                  }
                >
                  <input
                    type="file"
                    accept=".pdf,.jpg,.jpeg,.png"
                    onChange={(event) =>
                      fileChange("CIPC_CERTIFICATE", event.target.files?.[0])
                    }
                    disabled={uploadedTypes.includes("CIPC_CERTIFICATE")}
                  />
                  {uploadedTypes.includes("CIPC_CERTIFICATE") ? (
                    <span className="aw-uploaded">✓ Uploaded</span>
                  ) : null}
                </Field>

                <Field label="Additional Document" hint="Optional">
                  <Input
                    name="additional_document_label"
                    value={additionalLabel}
                    onChange={(event) => setAdditionalLabel(event.target.value)}
                    placeholder="e.g. Reference Letter"
                  />
                  <input
                    type="file"
                    accept=".pdf,.jpg,.jpeg,.png"
                    onChange={(event) =>
                      fileChange("ADDITIONAL_DOCUMENT", event.target.files?.[0])
                    }
                    disabled={uploadedTypes.includes("ADDITIONAL_DOCUMENT")}
                  />
                  {uploadedTypes.includes("ADDITIONAL_DOCUMENT") ? (
                    <span className="aw-uploaded">✓ Uploaded</span>
                  ) : null}
                </Field>
              </div>
            </Section>

            <div className="aw-nav aw-nav-lock">
              <div className="aw-lock-note">
                Your application and acknowledgement have already been processed.
                Finish the supporting document uploads to complete this step.
              </div>
              <button
                type="button"
                className="aw-btn aw-btn-submit"
                onClick={finishWithDocuments}
                disabled={submitting}
              >
                {submitting ? "Uploading documents..." : "Finish Application ✓"}
              </button>
            </div>
          </>
        ) : null}
      </div>
    </div>
  );
}
