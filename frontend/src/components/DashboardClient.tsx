"use client";

import { useState } from "react";
import VideoUpload from "@/components/VideoUpload";
import JobStatusCard from "@/components/JobStatusCard";

interface Props {
  userId: string;
}

export default function DashboardClient({ userId }: Props) {
  const [activeJobId, setActiveJobId] = useState<string | null>(null);

  return (
    <div>
      <div className="mb-8 text-center">
        <h2 className="text-xl font-semibold text-gray-900">Analyze a video</h2>
        <p className="text-sm text-gray-500 mt-1">
          Upload a clip (≤30s) to see what emotions it fires in the brain.
        </p>
      </div>

      <VideoUpload
        userId={userId}
        onJobCreated={(jobId) => setActiveJobId(jobId)}
      />

      {activeJobId && (
        <JobStatusCard
          jobId={activeJobId}
          onDismiss={() => setActiveJobId(null)}
        />
      )}

      {!activeJobId && (
        <div className="mt-16 text-center text-gray-400">
          <p className="text-sm">No analyses yet</p>
        </div>
      )}
    </div>
  );
}
