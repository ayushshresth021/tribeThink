"use client";

import { createClient } from "@/lib/supabase/client";
import { createJob } from "@/lib/api";
import { useRef, useState } from "react";

const ACCEPTED_FORMATS = ["video/mp4", "video/quicktime", "video/webm"];
const MAX_DURATION_S = 30;

interface Props {
  userId: string;
  onJobCreated: (jobId: string) => void;
}

export default function VideoUpload({ userId, onJobCreated }: Props) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [duration, setDuration] = useState<number | null>(null);
  const [file, setFile] = useState<File | null>(null);
  const [validationError, setValidationError] = useState<string | null>(null);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [uploading, setUploading] = useState(false);

  function reset() {
    setPreviewUrl(null);
    setDuration(null);
    setFile(null);
    setValidationError(null);
    setUploadError(null);
    if (inputRef.current) inputRef.current.value = "";
  }

  function handleFileChange(e: React.ChangeEvent<HTMLInputElement>) {
    const picked = e.target.files?.[0];
    if (!picked) return;
    setValidationError(null);
    setUploadError(null);

    if (!ACCEPTED_FORMATS.includes(picked.type)) {
      setValidationError("Unsupported format. Please upload an mp4, mov, or webm file.");
      return;
    }

    const url = URL.createObjectURL(picked);
    const video = document.createElement("video");
    video.preload = "metadata";
    video.onloadedmetadata = () => {
      URL.revokeObjectURL(video.src);
      if (video.duration > MAX_DURATION_S) {
        setValidationError(`Video is ${Math.round(video.duration)}s — maximum is 30 seconds.`);
        return;
      }
      setDuration(video.duration);
      setPreviewUrl(url);
      setFile(picked);
    };
    video.onerror = () => setValidationError("Could not read video metadata. Try a different file.");
    video.src = url;
  }

  async function handleSubmit() {
    if (!file || duration === null) return;
    setUploading(true);
    setUploadError(null);

    try {
      const supabase = createClient();
      const ext = file.name.split(".").pop() ?? "mp4";
      const path = `${userId}/${crypto.randomUUID()}.${ext}`;

      const { error: storageError } = await supabase.storage
        .from("videos")
        .upload(path, file, { contentType: file.type });

      if (storageError) throw new Error(storageError.message);

      const { job_id } = await createJob(path, duration);
      reset();
      onJobCreated(job_id);
    } catch (e) {
      setUploadError(e instanceof Error ? e.message : "Upload failed. Please try again.");
    } finally {
      setUploading(false);
    }
  }

  return (
    <div className="w-full max-w-xl mx-auto">
      {!previewUrl ? (
        <button
          onClick={() => inputRef.current?.click()}
          className="w-full border-2 border-dashed border-gray-300 rounded-2xl p-12 text-center hover:border-indigo-400 hover:bg-indigo-50 transition-colors cursor-pointer"
        >
          <p className="text-gray-500 text-sm font-medium">Click to upload a video</p>
          <p className="text-gray-400 text-xs mt-1">mp4, mov, webm · max 30 seconds</p>
        </button>
      ) : (
        <div className="rounded-2xl overflow-hidden border border-gray-200 bg-white shadow-sm">
          <video
            src={previewUrl}
            controls
            className="w-full max-h-64 object-contain bg-black"
          />
          <div className="p-4 flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-800 truncate max-w-xs">{file?.name}</p>
              <p className="text-xs text-gray-400 mt-0.5">{duration !== null ? `${Math.round(duration)}s` : ""}</p>
            </div>
            <div className="flex gap-2">
              <button
                onClick={reset}
                disabled={uploading}
                className="text-sm text-gray-500 hover:text-gray-700 px-3 py-1.5 rounded-lg border border-gray-200 transition-colors"
              >
                Remove
              </button>
              <button
                onClick={handleSubmit}
                disabled={uploading}
                className="text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 px-4 py-1.5 rounded-lg transition-colors"
              >
                {uploading ? "Uploading…" : "Analyze"}
              </button>
            </div>
          </div>
        </div>
      )}

      <input
        ref={inputRef}
        type="file"
        accept="video/mp4,video/quicktime,video/webm"
        className="hidden"
        onChange={handleFileChange}
      />

      {validationError && (
        <p className="mt-3 text-sm text-red-600 text-center">{validationError}</p>
      )}
      {uploadError && (
        <p className="mt-3 text-sm text-red-600 text-center">{uploadError}</p>
      )}
    </div>
  );
}
