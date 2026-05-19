import { createClient } from "@/lib/supabase/client";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

async function authHeaders(): Promise<Record<string, string>> {
  const supabase = createClient();
  const { data } = await supabase.auth.getSession();
  const token = data.session?.access_token;
  if (!token) throw new Error("Not authenticated");
  return { Authorization: `Bearer ${token}`, "Content-Type": "application/json" };
}

export async function createJob(
  videoStoragePath: string,
  durationSeconds: number
): Promise<{ job_id: string }> {
  const headers = await authHeaders();
  const res = await fetch(`${API_URL}/jobs`, {
    method: "POST",
    headers,
    body: JSON.stringify({ video_storage_path: videoStoragePath, duration_seconds: durationSeconds }),
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail ?? `Failed to create job (${res.status})`);
  }
  return res.json();
}

export async function getJob(jobId: string): Promise<Job> {
  const headers = await authHeaders();
  const res = await fetch(`${API_URL}/jobs/${jobId}`, { headers });
  if (!res.ok) throw new Error(`Failed to fetch job (${res.status})`);
  return res.json();
}

export interface Job {
  id: string;
  status: "pending" | "running" | "complete" | "failed";
  video_storage_path: string;
  created_at: string;
  completed_at: string | null;
  error_message: string | null;
}
