const RAW_BASE = process.env.EXPO_PUBLIC_API_BASE_URL || "";
export const API_BASE = RAW_BASE.replace(/\/$/, "");

if (!API_BASE) {
  console.warn("EXPO_PUBLIC_API_BASE_URL is not configured.");
}

async function parseResponse(response: Response) {
  const contentType = response.headers.get("content-type") || "";
  let body: any = null;

  try {
    body = contentType.includes("application/json")
      ? await response.json()
      : await response.text();
  } catch {
    body = null;
  }

  if (!response.ok) {
    const detail =
      typeof body === "object" && body
        ? body.detail || body.message
        : body;

    throw new Error(detail || `HTTP ${response.status}`);
  }

  return body;
}

export async function req(
  path: string,
  options: RequestInit = {},
  token?: string | null
) {
  const isForm = options.body instanceof FormData;
  const headers: Record<string, string> = {
    ...(isForm ? {} : { "Content-Type": "application/json" }),
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...((options.headers || {}) as Record<string, string>),
  };

  return parseResponse(
    await fetch(`${API_BASE}${path}`, {
      ...options,
      headers,
    })
  );
}

export const loginPassword = (payload: any) =>
  req("/api/student-auth/login/password", {
    method: "POST",
    body: JSON.stringify(payload),
  });

export const loginPin = (payload: any, token: string) =>
  req(
    "/api/student-auth/login/pin",
    {
      method: "POST",
      body: JSON.stringify(payload),
    },
    token
  );

export const changePassword = (payload: any) =>
  req("/api/student-auth/change-password", {
    method: "POST",
    body: JSON.stringify(payload),
  });

export const setupPin = (payload: any) =>
  req("/api/student-auth/setup-pin", {
    method: "POST",
    body: JSON.stringify(payload),
  });

export const me = (token: string) =>
  req("/api/student-auth/me", {}, token);

export const profile = (token: string) =>
  req("/api/student/profile", {}, token);

export const registration = (token: string) =>
  req("/api/student/registration", {}, token);

export const modules = (token: string) =>
  req("/api/student/modules", {}, token);

export const results = (token: string) =>
  req("/api/student/results", {}, token);

export const assessment = (token: string) =>
  req("/api/student/assessment-status", {}, token);

export const attendance = (token: string) =>
  req("/api/student/attendance", {}, token);

export const timetable = (token: string) =>
  req("/api/student/timetable", {}, token);

export const resources = (token: string) =>
  req("/api/student/learning-resources", {}, token);

export const resource = (resourceId: string, token: string) =>
  req(
    `/api/student/learning-resources/${encodeURIComponent(resourceId)}`,
    {},
    token
  );

export const documents = (token: string) =>
  req("/api/student/documents", {}, token);

export const finance = (token: string) =>
  req("/api/student/finance", {}, token);

export const card = (token: string) =>
  req("/api/student/card", {}, token);

export const completion = (token: string) =>
  req("/api/student/completion-documents", {}, token);

export const announcements = (token: string) =>
  req("/api/student/announcements", {}, token);

export const messages = (token: string) =>
  req("/api/student/messages", {}, token);

export const support = (token: string) =>
  req("/api/student/support", {}, token);

export const settings = (token: string) =>
  req("/api/student/settings", {}, token);

export const newMessage = (payload: any, token: string) =>
  req(
    "/api/student/messages",
    {
      method: "POST",
      body: JSON.stringify(payload),
    },
    token
  );

export const newSupport = (payload: any, token: string) =>
  req(
    "/api/student/support",
    {
      method: "POST",
      body: JSON.stringify(payload),
    },
    token
  );

export const saveContact = (payload: any, token: string) =>
  req(
    "/api/student/settings/contact",
    {
      method: "PATCH",
      body: JSON.stringify(payload),
    },
    token
  );

export const savePrefs = (payload: any, token: string) =>
  req(
    "/api/student/settings/preferences",
    {
      method: "PATCH",
      body: JSON.stringify(payload),
    },
    token
  );

export const requestAvatarReplacement = (
  reason: string,
  token: string
) =>
  req(
    "/api/student/card/avatar/replacement-request",
    {
      method: "POST",
      body: JSON.stringify({ reason }),
    },
    token
  );

export const startPayfast = (payload: any, token: string) =>
  req(
    "/api/student/finance/payfast/start",
    {
      method: "POST",
      body: JSON.stringify(payload),
    },
    token
  );

export async function uploadDocument(
  requestId: string,
  asset: { uri: string; name?: string | null; mimeType?: string | null },
  token: string
) {
  const form = new FormData();
  form.append("request_id", requestId);
  form.append(
    "file",
    {
      uri: asset.uri,
      name: asset.name || "student-document.pdf",
      type: asset.mimeType || "application/octet-stream",
    } as any
  );

  return req(
    "/api/student/documents/upload",
    {
      method: "POST",
      body: form,
    },
    token
  );
}

export async function uploadAvatar(
  asset: { uri: string; fileName?: string | null; mimeType?: string | null },
  token: string
) {
  const form = new FormData();
  form.append(
    "avatar",
    {
      uri: asset.uri,
      name: asset.fileName || "student-avatar.jpg",
      type: asset.mimeType || "image/jpeg",
    } as any
  );

  return req(
    "/api/student/card/avatar",
    {
      method: "POST",
      body: form,
    },
    token
  );
}
