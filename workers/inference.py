import os
import modal

TRIBEV2_COMMIT = "34f52344e5ba651db83ce9d2f9b99e26b5d86e4a"

app = modal.App("tribethink")

image = (
    modal.Image.debian_slim(python_version="3.11")
    .apt_install("ffmpeg")
    .pip_install(
        "numpy",
        "supabase==2.7.4",
        f"git+https://github.com/facebookresearch/tribev2.git@{TRIBEV2_COMMIT}",
    )
)


@app.function(
    gpu="T4",
    image=image,
    timeout=600,
    secrets=[
        modal.Secret.from_name("tribethink-supabase"),
    ],
)
def run_inference(job_id: str, video_storage_path: str) -> None:
    import io
    import tempfile
    from datetime import datetime, timezone

    import numpy as np
    from supabase import create_client
    from tribev2 import TribeModel

    from workers.predictions import serialize

    supabase = create_client(
        os.environ["SUPABASE_URL"],
        os.environ["SUPABASE_SERVICE_ROLE_KEY"],
    )

    def _update_job(fields: dict) -> None:
        supabase.table("jobs").update(fields).eq("id", job_id).execute()

    _update_job({"status": "running"})

    try:
        video_bytes = supabase.storage.from_("videos").download(video_storage_path)
        ext = video_storage_path.rsplit(".", 1)[-1]
        with tempfile.NamedTemporaryFile(suffix=f".{ext}", delete=False) as f:
            f.write(video_bytes)
            video_path = f.name

        model = TribeModel.from_pretrained("facebook/tribev2", cache_folder="/cache/tribev2")
        df = model.get_events_dataframe(video_path=video_path)
        preds, _segments = model.predict(events=df)

        predictions_bytes = serialize(preds.astype(np.float32))
        predictions_path = f"predictions/{job_id}.npz"
        supabase.storage.from_("predictions").upload(
            predictions_path,
            predictions_bytes,
            {"content-type": "application/octet-stream"},
        )

        _update_job({
            "status": "complete",
            "completed_at": datetime.now(timezone.utc).isoformat(),
        })

    except Exception as exc:
        _update_job({
            "status": "failed",
            "error_message": str(exc)[:500],
            "completed_at": datetime.now(timezone.utc).isoformat(),
        })
        raise
