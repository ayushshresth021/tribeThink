# PRD: TribeThink — Neural Emotion Analysis for Video Content

## Problem Statement

Content creators invest significant time and resources producing videos — ads, reels, trailers, YouTube intros — without reliable insight into what emotional responses their content actually triggers in viewers. Traditional analytics tell creators what people clicked or watched, but not how the content made them *feel* at a neurological level. This leaves creators guessing whether their emotional intent (create excitement, build trust, evoke nostalgia) matched the actual emotional impact.

## Solution

TribeThink is a web application where content creators upload a short video (≤30 seconds) and receive a detailed emotional analysis powered by TribeV2 — a Facebook Research multimodal brain encoding model that predicts fMRI cortical responses to naturalistic stimuli. The raw neural predictions are mapped to named brain regions via the HCP-MMP atlas and interpreted by Claude Sonnet 4.6 into a human-readable timeline and summary card. Creators see exactly which moments in their video trigger which emotional responses, grounded in predicted population-level neural activity.

## User Stories

1. As a content creator, I want to upload a video clip so that I can analyze its emotional impact without technical neuroscience knowledge.
2. As a content creator, I want to see a timeline of emotional responses overlaid on my video so that I can identify which specific moments are working or failing.
3. As a content creator, I want each 3-second segment of my video labeled with its dominant emotional response so that I can pinpoint where to make edits.
4. As a content creator, I want a plain-language summary card describing my video's overall emotional arc so that I can quickly understand the big picture.
5. As a content creator, I want to know which brain regions were most activated by my video so that I can understand the neuroscientific basis of the analysis.
6. As a content creator, I want real-time job status updates while my video is being analyzed so that I am not left wondering if the analysis is still running.
7. As a content creator, I want to see an estimated wait time when I submit a video so that I can set my expectations appropriately.
8. As a content creator, I want to create an account so that my analyses are saved and I can revisit them later.
9. As a content creator, I want to browse my analysis history so that I can compare results across multiple videos over time.
10. As a content creator, I want to re-open a past analysis without re-running inference so that I do not waste time or compute credits.
11. As a content creator, I want to see the video play alongside its emotion timeline so that I can experience the analysis in sync with the content.
12. As a content creator, I want the emotion timeline to show the moment in the video that *caused* the response (not when the brain registered it) so that the labels feel intuitive and actionable.
13. As a content creator, I want a clear error message if my video exceeds 30 seconds so that I understand why the upload was rejected.
14. As a content creator, I want a clear error message if my video format is unsupported so that I know how to fix the issue.
15. As a content creator, I want to understand that the analysis reflects average predicted neural responses (not my specific audience's brains) so that I have the right expectations about what the data represents.
16. As a content creator, I want the summary card to include actionable language (e.g., "your opening triggers anxiety rather than excitement") so that I know what to change.
17. As a content creator, I want to log out and have my session securely terminated so that my analyses are not accessible to others on shared devices.
18. As a content creator, I want to delete a past analysis from my history so that I can manage my stored data.
19. As a content creator, I want the upload interface to show a video preview before I submit so that I can confirm I uploaded the right file.
20. As a content creator, I want the analysis to complete within a reasonable time (target: under 5 minutes for a 30s clip) so that the tool fits into my workflow.

## Implementation Decisions

### Modules

**1. TribeV2 Inference Worker**
- Deployed as a Modal serverless GPU function
- Accepts a Supabase Storage video URL as input
- Downloads the video, runs `TribeModel.from_pretrained("facebook/tribev2")`, calls `model.get_events_dataframe(video_path=...)` then `model.predict(events=df)`
- Returns raw predictions array of shape `(n_timesteps, n_vertices)` serialized as a numpy array or JSON
- Stateless and idempotent — same video URL always produces the same output
- Interface: `run_inference(video_url: str) -> np.ndarray`

**2. Atlas Mapper**
- Pure Python module, no GPU required
- Loads the HCP-MMP 1.0 parcellation on the fsaverage5 surface (~180 named parcels)
- Maps the 20k fsaverage5 vertices to their corresponding HCP-MMP parcel labels
- For each 3-second temporal chunk, computes mean activation per parcel
- Applies the 5-second hemodynamic lag correction: shifts all labels 5 seconds earlier to align with the video moment that *caused* the response
- Returns a structured list of chunks: `[{ start_s, end_s, top_regions: [{ name, activation_z }] }]`
- Interface: `map_to_atlas(predictions: np.ndarray) -> list[ChunkActivation]`

**3. Emotion Interpreter**
- Calls Claude Sonnet 4.6 (via Anthropic SDK with prompt caching)
- Input: structured list of `ChunkActivation` objects from the Atlas Mapper
- Prompt instructs Claude to act as a neuroscience-informed content analyst writing for a creator audience
- Per-chunk output: a short emotion label (2–4 words, e.g., "high arousal / tension") and a one-sentence explanation
- Overall output: a 3–5 sentence summary card describing the video's full emotional arc, written in actionable creator language
- Includes a standard disclaimer note that results reflect population-average predicted neural responses
- Interface: `interpret_emotions(chunks: list[ChunkActivation]) -> EmotionReport`

**4. Job Orchestrator (FastAPI)**
- Runs on Railway, Python 3.11+
- Endpoints:
  - `POST /jobs` — accepts a Supabase Storage URL, creates a job record, enqueues Modal inference call, returns `job_id`
  - `GET /jobs/{job_id}` — returns job status (`pending | running | complete | failed`) and result payload when complete
  - `GET /jobs` — returns paginated list of job summaries for the authenticated user
  - `DELETE /jobs/{job_id}` — soft-deletes a job record and its associated results
- All endpoints require Supabase JWT authentication (validated via Supabase Auth middleware)
- Job pipeline: upload confirmed → Modal inference → Atlas Mapper → Emotion Interpreter → store `EmotionReport` in Supabase → mark job complete

**5. Video Upload Handler**
- Client-side Next.js module
- Validates video duration ≤30 seconds before upload (using browser MediaInfo API)
- Validates supported formats (mp4, mov, webm)
- Uploads directly to Supabase Storage (bypassing the FastAPI backend for large binary payloads)
- On upload success, calls `POST /jobs` with the storage URL to trigger the pipeline

**6. Results Store (Supabase)**
- Schema:
  - `users` — managed by Supabase Auth
  - `jobs` — `id`, `user_id`, `video_storage_path`, `status`, `created_at`, `completed_at`, `error_message`
  - `emotion_reports` — `id`, `job_id`, `chunks` (JSONB), `summary` (text), `disclaimer` (text), `created_at`
- Row-level security ensures users can only read/write their own rows
- Videos stored in a `videos` Supabase Storage bucket with per-user path prefixes

**7. Timeline Renderer (Next.js)**
- React component displaying the uploaded video with an emotion overlay track below the scrubber
- Each 3-second chunk renders as a colored segment (color-coded by arousal/valence dimension derived from the emotion label)
- Clicking a segment highlights it and shows the full explanation text in a tooltip/panel
- Video playback position syncs with the highlighted chunk in real time
- Displays a subtle "5s offset corrected" indicator so curious users understand the alignment

**8. Summary Card (Next.js)**
- React component rendered below the timeline
- Displays the 3–5 sentence overall emotional arc narrative from the Emotion Interpreter
- Includes a collapsible "Brain Regions" section listing the top activated HCP-MMP parcels across the full video
- Displays the population-average disclaimer

### Architecture
- Frontend: Next.js (App Router) deployed on Vercel
- Backend: FastAPI on Railway (always-on, no cold starts)
- Inference: Modal serverless GPU (pay-per-inference, scales to zero)
- Storage + Auth + DB: Supabase (free tier)
- LLM: Claude Sonnet 4.6 via Anthropic SDK

### Key Technical Constraints
- TribeV2 requires Python 3.11+ and a GPU for practical inference speed
- Hemodynamic lag correction: all timeline labels shifted 5 seconds earlier relative to raw model output
- 3-second chunking: temporal predictions grouped into non-overlapping 3s windows, dominant activations computed per window
- Video limit enforced client-side (UX) and server-side (FastAPI validates storage object metadata before enqueuing)

## Testing Decisions

A good test verifies externally observable behavior — what the module returns given a specific input — not how it achieves that result internally. Tests should not mock the Atlas Mapper's internal parcel lookup logic; they should assert that a known synthetic predictions array produces the correct chunk structure.

**Modules to test:**

- **Atlas Mapper** — highest priority. Given a synthetic `(n_timesteps, n_vertices)` predictions array with known values in specific vertex ranges, assert that the output chunks contain the expected parcel names and activation values, and that the 5-second hemodynamic offset is correctly applied to `start_s`/`end_s`.

- **Emotion Interpreter** — test with a mocked Claude response. Given a fixed `list[ChunkActivation]`, assert that the returned `EmotionReport` has the correct number of chunk labels, non-empty summary text, and includes the disclaimer. Do not test Claude's actual output — test the parsing and structuring logic.

- **Job Orchestrator (FastAPI)** — integration tests using FastAPI's `TestClient`. Test that `POST /jobs` returns a valid `job_id`, that `GET /jobs/{job_id}` returns `pending` immediately after creation, and that unauthenticated requests return 401. Mock the Modal inference call.

- **Video Upload Handler** — unit tests for the client-side validation logic: assert that a 35-second video is rejected before upload, that an unsupported format is rejected, and that a valid 28-second mp4 passes through to the Supabase upload call.

## Out of Scope

- Audio-only and text input modalities (v2)
- Videos longer than 30 seconds
- Personalized brain models (TribeV2 predicts for an average subject only)
- Real-time/live video analysis
- Mobile native apps (iOS/Android)
- Comparing two videos side-by-side
- Exporting results as PDF or CSV reports
- Team/workspace accounts — single user only
- Any clinical, diagnostic, or therapeutic use case
- Fine-tuning or retraining TribeV2

## Further Notes

- TribeV2's predictions represent an *average subject* — the analysis reflects population-level predicted neural responses, not any individual viewer's actual brain activity. This should be clearly communicated in the UI at every point where results are shown.
- The HCP-MMP 1.0 atlas parcellation file for fsaverage5 is available from the Human Connectome Project and must be bundled with the Atlas Mapper module (it is a static 20k-vertex label array).
- Modal's cold start on GPU instances can add 30–90 seconds to the first inference after a period of inactivity. Consider keeping the Modal function warm during expected usage windows, or communicating cold-start wait times transparently in the UI.
- The Emotion Interpreter prompt should explicitly instruct Claude to avoid overclaiming (e.g., "this video makes people feel X" rather than "this proves your audience feels X") to maintain scientific integrity and user trust.
- TribeV2 is a research model from Facebook Research, not a production API. Pin the dependency to a specific commit hash to avoid breaking changes.
