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

export async function apiRequest(path, options = {}, token = null) {
  const headers = {
    ...(options.body instanceof FormData
      ? {}
      : { "Content-Type": "application/json" }),
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...(options.headers || {}),
  };

  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers,
  });

  return parseResponse(response);
}

export function getVacancies() {
  return apiRequest("/api/careers/vacancies");
}

export function getVacancy(vacancyCode) {
  return apiRequest(
    `/api/careers/vacancies/${encodeURIComponent(vacancyCode)}`,
  );
}

export function registerCareerAccount(payload) {
  return apiRequest("/api/careers/auth/register", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function loginCareerAccount(payload) {
  return apiRequest("/api/careers/auth/login", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function getCareerMe(token) {
  return apiRequest("/api/careers/auth/me", {}, token);
}

export function changeCareerPassword(payload, token) {
  return apiRequest(
    "/api/careers/auth/change-password",
    {
      method: "POST",
      body: JSON.stringify(payload),
    },
    token,
  );
}

export function createCareerApplication(
  vacancyCode,
  coverLetter,
  token,
) {
  return apiRequest(
    `/api/careers/vacancies/${encodeURIComponent(
      vacancyCode,
    )}/applications`,
    {
      method: "POST",
      body: JSON.stringify({
        cover_letter: coverLetter.trim() || null,
      }),
    },
    token,
  );
}

export function getMyApplications(token) {
  return apiRequest("/api/careers/applications", {}, token);
}

export function getMyApplication(applicationId, token) {
  return apiRequest(
    `/api/careers/applications/${encodeURIComponent(applicationId)}`,
    {},
    token,
  );
}

export async function uploadCareerDocument({
  applicationId,
  documentType,
  file,
  token,
}) {
  const form = new FormData();
  form.append("document_type", documentType);
  form.append("upload", file);

  return apiRequest(
    `/api/careers/applications/${encodeURIComponent(
      applicationId,
    )}/documents`,
    {
      method: "POST",
      body: form,
    },
    token,
  );
}

export function submitCareerApplication(applicationId, token) {
  return apiRequest(
    `/api/careers/applications/${encodeURIComponent(
      applicationId,
    )}/submit`,
    { method: "POST" },
    token,
  );
}

export function withdrawCareerApplication(applicationId, token) {
  return apiRequest(
    `/api/careers/applications/${encodeURIComponent(
      applicationId,
    )}/withdraw`,
    { method: "POST" },
    token,
  );
}

export async function downloadCareerDocument({
  applicationId,
  documentId,
  filename,
  token,
}) {
  const response = await fetch(
    `${API_BASE}/api/careers/applications/${encodeURIComponent(
      applicationId,
    )}/documents/${encodeURIComponent(documentId)}/download`,
    {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    },
  );

  if (!response.ok) {
    return parseResponse(response);
  }

  const blob = await response.blob();
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");

  anchor.href = url;
  anchor.download = filename || "document";
  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();

  URL.revokeObjectURL(url);
}
