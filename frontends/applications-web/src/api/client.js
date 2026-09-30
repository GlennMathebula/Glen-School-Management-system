const API_BASE = (import.meta.env.VITE_API_BASE_URL || "").replace(/\/$/, "");

async function parseResponse(response) {
  let body = null;

  try {
    body = await response.json();
  } catch {
    body = null;
  }

  if (!response.ok) {
    const detail =
      body?.detail ||
      body?.message ||
      `Request failed with HTTP ${response.status}.`;

    throw new Error(
      typeof detail === "string" ? detail : JSON.stringify(detail),
    );
  }

  return body;
}

export async function apiRequest(path, options = {}) {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {}),
    },
    ...options,
  });

  return parseResponse(response);
}

export function healthCheck() {
  return apiRequest("/health");
}

export function submitApplication(payload) {
  return apiRequest("/api/applications", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function getApplicationStatus({
  studentNumber,
  nationalId,
}) {
  return apiRequest("/api/applications/status", {
    method: "POST",
    body: JSON.stringify({
      student_number: studentNumber.trim(),
      national_id: nationalId.trim(),
    }),
  });
}

export function resendAcknowledgement(
  studentNumber,
  nationalId,
) {
  const safeNumber = encodeURIComponent(
    studentNumber.trim(),
  );

  return apiRequest(
    `/api/applications/${safeNumber}/acknowledgement/resend`,
    {
      method: "POST",
      body: JSON.stringify({
        student_number: studentNumber.trim(),
        national_id: nationalId.trim(),
      }),
    },
  );
}

export function publicRegistration(payload) {
  return apiRequest("/api/public/registration", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function getApplicationCatalogue() {
  return apiRequest("/api/applications/catalogue");
}

export async function uploadApplicationDocument({
  studentNumber,
  nationalId,
  documentType,
  documentLabel = "",
  file,
}) {
  const form = new FormData();

  form.append("national_id", nationalId);
  form.append("document_type", documentType);

  if (documentLabel) {
    form.append("document_label", documentLabel);
  }

  form.append("file", file);

  const response = await fetch(
    `${API_BASE}/api/applications/${encodeURIComponent(
      studentNumber,
    )}/documents`,
    {
      method: "POST",
      body: form,
    },
  );

  return parseResponse(response);
}


export function verifyPublicRegistration(payload) {
  return apiRequest("/api/public/registration/verify", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}
