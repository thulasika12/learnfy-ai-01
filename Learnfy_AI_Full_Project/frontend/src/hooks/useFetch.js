import { useState, useEffect, useCallback } from "react";

/**
 * Generic hook for calling an async fetcher function and tracking
 * loading / error / data state. Pass a memoized fetcher or include
 * dependencies so it re-runs when needed.
 *
 * Usage:
 *   const { data, loading, error, refetch } = useFetch(() => getNotes({ subject }), [subject]);
 */
export function useFetch(fetcher, deps = []) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetcher();
      setData(res.data);
    } catch (err) {
      setError(err.response?.data?.detail || err.message || "Something went wrong");
    } finally {
      setLoading(false);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps);

  useEffect(() => {
    load();
  }, [load]);

  return { data, loading, error, refetch: load, setData };
}

export default useFetch;
