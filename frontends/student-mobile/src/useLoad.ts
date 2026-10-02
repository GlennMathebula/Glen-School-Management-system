import { useEffect, useState } from "react";
import { useAuth } from "./auth";

export function useLoad(
  fn: (token: string) => Promise<any>
) {
  const auth = useAuth();
  const [data, setData] = useState<any>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  async function load() {
    if (!auth.token) return;
    setLoading(true);
    setError("");
    try {
      setData(await fn(auth.token));
    } catch (e: any) {
      setError(e?.message || "Could not load information.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void load();
  }, [auth.token]);

  return { data, error, loading, reload: load, setData };
}
