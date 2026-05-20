def spawn_inference_job(job_id: str, video_storage_path: str) -> None:
    from workers.inference import run_inference
    run_inference.spawn(job_id=job_id, video_storage_path=video_storage_path)
