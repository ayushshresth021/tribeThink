"use client";

import { useJobPoller } from "@/hooks/useJobPoller";

interface Props {
  jobId: string;
  onDismiss: () => void;
}

const STATUS_COPY: Record<string, { label: string; sublabel: string }> = {
  pending: {
    label: "Queued",
    sublabel: "Your video is waiting for a GPU worker to pick it up. Est. wait: 1–3 min.",
  },
  running: {
    label: "Analyzing",
    sublabel: "TribeV2 is predicting brain responses to your video. Hang tight.",
  },
  complete: {
    label: "Done",
    sublabel: "Analysis complete! Opening results…",
  },
  failed: {
    label: "Failed",
    sublabel: "Something went wrong during analysis.",
  },
};

export default function JobStatusCard({ jobId, onDismiss }: Props) {
  const { job, error } = useJobPoller(jobId);

  const status = job?.status ?? "pending";
  const copy = STATUS_COPY[status];
  const isTerminal = status === "complete" || status === "failed";

  return (
    <div className="w-full max-w-xl mx-auto mt-6 p-5 bg-white border border-gray-200 rounded-2xl shadow-sm">
      <div className="flex items-start justify-between gap-4">
        <div className="flex items-center gap-3">
          {!isTerminal && (
            <span className="inline-block w-3 h-3 rounded-full bg-indigo-500 animate-pulse shrink-0 mt-0.5" />
          )}
          {status === "complete" && (
            <span className="inline-block w-3 h-3 rounded-full bg-green-500 shrink-0 mt-0.5" />
          )}
          {status === "failed" && (
            <span className="inline-block w-3 h-3 rounded-full bg-red-500 shrink-0 mt-0.5" />
          )}
          <div>
            <p className="text-sm font-semibold text-gray-900">{copy.label}</p>
            <p className="text-xs text-gray-500 mt-0.5">{copy.sublabel}</p>
            {status === "failed" && job?.error_message && (
              <p className="text-xs text-red-600 mt-1">{job.error_message}</p>
            )}
            {error && <p className="text-xs text-red-600 mt-1">{error}</p>}
          </div>
        </div>
        {isTerminal && (
          <button
            onClick={onDismiss}
            className="text-xs text-gray-400 hover:text-gray-600 shrink-0"
          >
            Dismiss
          </button>
        )}
      </div>
    </div>
  );
}
