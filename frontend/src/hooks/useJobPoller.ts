import { useEffect, useRef, useState } from "react";
import { getJob, type Job } from "@/lib/api";

const POLL_INTERVAL_MS = 3000;
const TERMINAL_STATUSES = new Set(["complete", "failed"]);

export function useJobPoller(jobId: string | null) {
  const [job, setJob] = useState<Job | null>(null);
  const [error, setError] = useState<string | null>(null);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    if (!jobId) return;

    async function poll() {
      try {
        const data = await getJob(jobId!);
        setJob(data);
        if (TERMINAL_STATUSES.has(data.status)) {
          clearInterval(intervalRef.current!);
        }
      } catch (e) {
        setError(e instanceof Error ? e.message : "Polling error");
        clearInterval(intervalRef.current!);
      }
    }

    poll();
    intervalRef.current = setInterval(poll, POLL_INTERVAL_MS);
    return () => clearInterval(intervalRef.current!);
  }, [jobId]);

  return { job, error };
}
