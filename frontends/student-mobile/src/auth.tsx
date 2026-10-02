import * as SecureStore from "expo-secure-store";
import React, {
  createContext,
  useContext,
  useEffect,
  useMemo,
  useState,
} from "react";
import * as A from "./api";

const TOKEN_KEY = "gm_student_token";
const META_KEY = "gm_student_meta";

type Meta = {
  student_number?: string;
  login_method?: string;
  must_change_password?: boolean;
  pin_created?: boolean;
};

type AuthValue = {
  hydrating: boolean;
  token: string;
  meta: Meta | null;
  student: any;
  fullAccess: boolean;
  needsOnboarding: boolean;
  needsPin: boolean;
  loginPassword: (studentNumber: string, password: string) => Promise<any>;
  loginPin: (studentNumber: string, pin: string) => Promise<any>;
  update: (token?: string, changes?: Partial<Meta>) => Promise<void>;
  refreshMe: () => Promise<void>;
  logout: () => Promise<void>;
};

const AuthContext = createContext<AuthValue | null>(null);

async function readMeta(): Promise<Meta | null> {
  const raw = await SecureStore.getItemAsync(META_KEY);
  if (!raw) return null;
  try {
    return JSON.parse(raw);
  } catch {
    return null;
  }
}

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [hydrating, setHydrating] = useState(true);
  const [token, setToken] = useState("");
  const [meta, setMeta] = useState<Meta | null>(null);
  const [student, setStudent] = useState<any>(null);

  useEffect(() => {
    let active = true;

    Promise.all([
      SecureStore.getItemAsync(TOKEN_KEY),
      readMeta(),
    ]).then(([storedToken, storedMeta]) => {
      if (!active) return;
      setToken(storedToken || "");
      setMeta(storedMeta);
      setHydrating(false);
    });

    return () => {
      active = false;
    };
  }, []);

  const needsOnboarding =
    !!token &&
    !!meta &&
    (!!meta.must_change_password || meta.pin_created === false);

  const needsPin =
    !!token &&
    !!meta &&
    !needsOnboarding &&
    meta.login_method === "password_pending_pin";

  const fullAccess =
    !!token &&
    !!meta &&
    !meta.must_change_password &&
    meta.pin_created === true &&
    meta.login_method === "password+pin";

  async function save(nextToken: string, nextMeta: Meta | null) {
    if (nextToken) {
      await SecureStore.setItemAsync(TOKEN_KEY, nextToken);
    } else {
      await SecureStore.deleteItemAsync(TOKEN_KEY);
    }

    if (nextMeta) {
      await SecureStore.setItemAsync(META_KEY, JSON.stringify(nextMeta));
    } else {
      await SecureStore.deleteItemAsync(META_KEY);
    }

    setToken(nextToken);
    setMeta(nextMeta);
  }

  async function logout() {
    await save("", null);
    setStudent(null);
  }

  async function refreshMe() {
    if (!token || !fullAccess) {
      setStudent(null);
      return;
    }

    try {
      const response = await A.me(token);
      setStudent(response?.student || null);
    } catch {
      await logout();
    }
  }

  useEffect(() => {
    if (!hydrating && fullAccess) {
      void refreshMe();
    }
  }, [hydrating, fullAccess, token]);

  async function loginPassword(studentNumber: string, password: string) {
    const response = await A.loginPassword({
      student_number: studentNumber,
      password,
    });

    const result = response?.result || response;

    const nextMeta: Meta = {
      student_number: result.student_number,
      login_method:
        result.login_method || "password_pending_pin",
      must_change_password: !!result.must_change_password,
      pin_created: !!result.pin_created,
    };

    await save(result.access_token, nextMeta);
    return result;
  }

  async function loginPin(studentNumber: string, pin: string) {
    if (!token) {
      throw new Error(
        "Password verification is required before PIN verification."
      );
    }

    const response = await A.loginPin(
      {
        student_number: studentNumber,
        pin,
      },
      token
    );

    const result = response?.result || response;

    await save(result.access_token, {
      student_number: result.student_number || studentNumber,
      login_method: result.login_method || "password+pin",
      must_change_password: false,
      pin_created: true,
    });

    return result;
  }

  async function update(
    nextToken = token,
    changes: Partial<Meta> = {}
  ) {
    await save(nextToken, {
      ...(meta || {}),
      ...changes,
    });
  }

  const value = useMemo<AuthValue>(
    () => ({
      hydrating,
      token,
      meta,
      student,
      fullAccess,
      needsOnboarding,
      needsPin,
      loginPassword,
      loginPin,
      update,
      refreshMe,
      logout,
    }),
    [
      hydrating,
      token,
      meta,
      student,
      fullAccess,
      needsOnboarding,
      needsPin,
    ]
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
    throw new Error("useAuth must be used inside AuthProvider");
  }
  return value;
}
