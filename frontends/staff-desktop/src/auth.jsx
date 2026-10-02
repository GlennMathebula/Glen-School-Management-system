import {
  createContext,
  useContext,
  useEffect,
  useMemo,
  useState,
} from "react";

import {
  changeTemporaryCredentials,
  currentStaff,
  resendOtp,
  staffLogin,
  verifyOtp,
} from "./api";

const TOKEN_KEY = "gm_staff_access_token";
const STAFF_KEY = "gm_staff_profile";

const AuthContext = createContext(null);

function readStaff() {
  try {
    return JSON.parse(
      localStorage.getItem(STAFF_KEY) ||
      "null",
    );
  } catch {
    return null;
  }
}

export function AuthProvider({
  children,
}) {
  const [token, setToken] = useState(
    () =>
      localStorage.getItem(TOKEN_KEY) ||
      "",
  );

  const [staff, setStaff] = useState(
    readStaff,
  );

  const [stage, setStage] = useState(
    token
      ? "authenticated"
      : "login",
  );

  const [
    challengeToken,
    setChallengeToken,
  ] = useState("");

  const [challengeInfo, setChallengeInfo] =
    useState(null);

  const [loading, setLoading] = useState(
    Boolean(token),
  );

  function saveAuthenticated(
    nextToken,
    nextStaff,
  ) {
    localStorage.setItem(
      TOKEN_KEY,
      nextToken,
    );

    localStorage.setItem(
      STAFF_KEY,
      JSON.stringify(nextStaff || {}),
    );

    setToken(nextToken);
    setStaff(nextStaff || {});
    setStage("authenticated");
    setChallengeToken("");
    setChallengeInfo(null);
  }

  function logout() {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(STAFF_KEY);

    setToken("");
    setStaff(null);
    setStage("login");
    setChallengeToken("");
    setChallengeInfo(null);
    setLoading(false);
  }

  useEffect(() => {
    let active = true;

    if (!token) {
      setLoading(false);
      return undefined;
    }

    setLoading(true);

    currentStaff(token)
      .then((profile) => {
        if (!active) return;

        setStaff(profile);

        localStorage.setItem(
          STAFF_KEY,
          JSON.stringify(profile),
        );

        setStage("authenticated");
        setLoading(false);
      })
      .catch(() => {
        if (!active) return;
        logout();
      });

    return () => {
      active = false;
    };
  }, [token]);

  async function login(
    staffCode,
    password,
    pin,
  ) {
    const response = await staffLogin({
      staff_code: staffCode,
      password,
      pin,
    });

    setChallengeToken(
      response.challenge_token || "",
    );

    setChallengeInfo(response);

    if (
      response.status ===
      "CREDENTIAL_CHANGE_REQUIRED"
    ) {
      setStage("credentials");
      return response;
    }

    if (
      response.status === "OTP_REQUIRED"
    ) {
      setStage("otp");
      return response;
    }

    throw new Error(
      "Unexpected staff authentication response.",
    );
  }

  async function changeCredentials(
    values,
  ) {
    const response =
      await changeTemporaryCredentials({
        challenge_token:
          challengeToken,
        new_password:
          values.new_password,
        confirm_password:
          values.confirm_password,
        new_pin:
          values.new_pin,
        confirm_pin:
          values.confirm_pin,
      });

    setChallengeToken(
      response.challenge_token || "",
    );

    setChallengeInfo(response);

    if (
      response.status !== "OTP_REQUIRED"
    ) {
      throw new Error(
        "OTP verification was not started.",
      );
    }

    setStage("otp");

    return response;
  }

  async function submitOtp(otp) {
    const response = await verifyOtp({
      challenge_token:
        challengeToken,
      otp,
    });

    if (
      !response.access_token ||
      !response.authenticated
    ) {
      throw new Error(
        "Staff authentication was not completed.",
      );
    }

    saveAuthenticated(
      response.access_token,
      response.staff,
    );

    return response;
  }

  async function resend() {
    const response =
      await resendOtp(
        challengeToken,
      );

    setChallengeToken(
      response.challenge_token ||
      challengeToken,
    );

    setChallengeInfo(response);

    return response;
  }

  const value = useMemo(
    () => ({
      token,
      staff,
      stage,
      challengeInfo,
      loading,
      isAuthenticated:
        Boolean(token) &&
        stage === "authenticated",
      login,
      changeCredentials,
      submitOtp,
      resend,
      logout,
    }),
    [
      token,
      staff,
      stage,
      challengeInfo,
      loading,
    ],
  );

  return (
    <AuthContext.Provider
      value={value}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const value =
    useContext(AuthContext);

  if (!value) {
    throw new Error(
      "useAuth must be used within AuthProvider.",
    );
  }

  return value;
}
