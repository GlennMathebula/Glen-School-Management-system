import {
  createContext,
  useContext,
  useEffect,
  useMemo,
  useState,
} from "react";

import {
  getCareerMe,
  loginCareerAccount,
} from "../api/client";

const TOKEN_KEY = "glen_moniques_careers_token";
const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [token, setToken] = useState(
    () => localStorage.getItem(TOKEN_KEY) || "",
  );
  const [account, setAccount] = useState(null);
  const [loading, setLoading] = useState(Boolean(token));

  useEffect(() => {
    let active = true;

    if (!token) {
      setAccount(null);
      setLoading(false);
      return undefined;
    }

    setLoading(true);

    getCareerMe(token)
      .then((response) => {
        if (!active) return;
        setAccount(response?.account || null);
        setLoading(false);
      })
      .catch(() => {
        if (!active) return;
        localStorage.removeItem(TOKEN_KEY);
        setToken("");
        setAccount(null);
        setLoading(false);
      });

    return () => {
      active = false;
    };
  }, [token]);

  async function login(email, password) {
    const response = await loginCareerAccount({
      email,
      password,
    });

    const nextToken = response?.access_token;
    const nextAccount = response?.account;

    if (!nextToken) {
      throw new Error("Careers login did not return an access token.");
    }

    localStorage.setItem(TOKEN_KEY, nextToken);
    setToken(nextToken);
    setAccount(nextAccount || null);

    return response;
  }

  function logout() {
    localStorage.removeItem(TOKEN_KEY);
    setToken("");
    setAccount(null);
  }

  const value = useMemo(
    () => ({
      token,
      account,
      loading,
      isAuthenticated: Boolean(token && account),
      login,
      logout,
      setAccount,
    }),
    [token, account, loading],
  );

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const value = useContext(AuthContext);

  if (!value) {
    throw new Error("useAuth must be used inside AuthProvider.");
  }

  return value;
}
