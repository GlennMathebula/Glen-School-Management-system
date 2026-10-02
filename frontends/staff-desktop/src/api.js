const BASE = (
  import.meta.env.DEV
    ? ""
    : "http://127.0.0.1:8000"
);

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
      `HTTP ${response.status}`;

    throw new Error(
      typeof detail === "string"
        ? detail
        : JSON.stringify(detail),
    );
  }

  return body;
}

export async function request(
  path,
  options = {},
  token = null,
) {
  const headers = {
    ...(options.body instanceof FormData
      ? {}
      : {
          "Content-Type": "application/json",
        }),
    ...(token
      ? {
          Authorization: `Bearer ${token}`,
        }
      : {}),
    ...(options.headers || {}),
  };

  return parseResponse(
    await fetch(
      `${BASE}${path}`,
      {
        ...options,
        headers,
      },
    ),
  );
}

export function health() {
  return request("/health");
}

export function staffLogin(payload) {
  return request(
    "/api/staff-auth/login",
    {
      method: "POST",
      body: JSON.stringify(payload),
    },
  );
}

export function changeTemporaryCredentials(
  payload,
) {
  return request(
    "/api/staff-auth/change-temporary-credentials",
    {
      method: "POST",
      body: JSON.stringify(payload),
    },
  );
}

export function verifyOtp(payload) {
  return request(
    "/api/staff-auth/verify-otp",
    {
      method: "POST",
      body: JSON.stringify(payload),
    },
  );
}

export function resendOtp(challengeToken) {
  return request(
    "/api/staff-auth/resend-otp",
    {
      method: "POST",
      body: JSON.stringify({
        challenge_token: challengeToken,
      }),
    },
  );
}

export function currentStaff(token) {
  return request(
    "/api/staff-auth/me",
    {},
    token,
  );
}

export function staffDashboard(token) {
  return request(
    "/api/staff/dashboard",
    {},
    token,
  );
}

export async function downloadFile(
  path,
  token,
  filename,
) {
  const response = await fetch(
    `${BASE}${path}`,
    {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    },
  );

  if (!response.ok) {
    await parseResponse(response);
    return;
  }

  const blob = await response.blob();
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");

  anchor.href = url;
  anchor.download = filename;
  anchor.click();

  URL.revokeObjectURL(url);
}


export async function fetchBlob(
  path,
  token,
) {
  const response = await fetch(
    `${BASE}${path}`,
    {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    },
  );

  if (!response.ok) {
    let detail = `HTTP ${response.status}`;

    try {
      const body = await response.json();

      detail =
        body?.detail ||
        body?.message ||
        detail;

      if (
        typeof detail !== "string"
      ) {
        detail = JSON.stringify(detail);
      }
    } catch {
      // Keep HTTP fallback.
    }

    throw new Error(detail);
  }

  return {
    blob: await response.blob(),
    contentType:
      response.headers.get(
        "content-type"
      ) || "",
    disposition:
      response.headers.get(
        "content-disposition"
      ) || "",
  };
}


export async function uploadForm(
  path,
  token,
  formData,
  method = "POST",
) {
  const response = await fetch(
    `${BASE}${path}`,
    {
      method,
      headers: token
        ? {
            Authorization:
              `Bearer ${token}`,
          }
        : {},
      body: formData,
    },
  );

  const contentType =
    response.headers.get(
      "content-type",
    ) || "";

  let body = null;

  if (
    contentType.includes(
      "application/json",
    )
  ) {
    body = await response.json();
  } else {
    body = await response.text();
  }

  if (!response.ok) {
    let detail =
      body?.detail ||
      body?.message ||
      body ||
      `HTTP ${response.status}`;

    if (
      typeof detail !== "string"
    ) {
      detail = JSON.stringify(
        detail,
      );
    }

    throw new Error(
      detail,
    );
  }

  return body;
}
