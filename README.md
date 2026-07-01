# CheatingDetector API

This project now has a package-based structure plus a FastAPI app that can be deployed to Render or Vercel.

## Structure

- `cheating_detector/core`: feature extraction, scoring, MediaPipe face mesh, HUD, and data collection.
- `cheating_detector/services`: reusable orchestration and in-memory session handling.
- `cheating_detector/api`: FastAPI app and request/response schemas.
- `api/index.py`: Vercel entrypoint.
- `render.yaml`: Render Blueprint service configuration.

## Local API Run

```bash
uvicorn cheating_detector.api.app:app --reload
```

Open:

- `/docs` for Swagger UI
- `/health` for a health check

## Local Webcam Run (Real-Time)

```bash
python faceDetector.py
```

This opens an OpenCV camera window named `FYPGuard` so you can test behavior live.
Press `Q` to quit.

Data-collection mode:

```bash
python faceDetector.py --collect
```

## Run Tests

```bash
python -m unittest discover -s tests -v
```

If you want a clean environment for both runtime and testing:

```bash
pip install -r requirements-dev.txt
```

## Postman Testing

Import these files into Postman:

- `postman/CheatingDetector.postman_collection.json`
- `postman/CheatingDetector.local.postman_environment.json`

Recommended order inside the collection:

1. `Root`
2. `Health`
3. `Create Session`
4. `Reset Session`
5. `Score Features`
6. `Analyze Landmarks`
7. `Analyze Image`
8. `Analyze Video`
9. `Analyze Video Summary`
10. `List Datasets`
11. `Download Dataset`
12. `Delete Session`

Notes:

- Run your API first with `uvicorn cheating_detector.api.app:app --reload`
- `Create Session` automatically stores `sessionId`
- `List Datasets` automatically stores the first CSV filename in `datasetFilename`
- For `Analyze Image`, you must manually choose a real image file in the Postman form-data body before sending
- For `Analyze Video`, you must manually choose a video file in the Postman form-data body before sending
- `Analyze Video` supports `include_landmarks=true|false` (default is `false`) so responses stay fast by default
- `Analyze Video` supports `inference_max_width` (default `640`) so you can control speed/accuracy tradeoff
- `Analyze Video` supports `include_frame_results=true|false` (default `false`) so you can keep payloads minimal
- `Analyze Video` supports `max_alerts` (default `5`) to limit how many incident messages come back per request
- If you deploy to Vercel later, just change `baseUrl` in the Postman environment to your deployed URL

## Main Endpoints

- `POST /api/v1/sessions`
- `DELETE /api/v1/sessions/{session_id}`
- `POST /api/v1/sessions/{session_id}/reset`
- `POST /api/v1/analyze/image`
- `POST /api/v1/analyze/video`
- `POST /api/v1/analyze/video/summary`
- `POST /api/v1/analyze/landmarks`
- `POST /api/v1/score`
- `GET /api/v1/datasets`
- `GET /api/v1/datasets/{filename}`

## Example Requests

Create a session:

```bash
curl -X POST http://127.0.0.1:8000/api/v1/sessions
```

Analyze an uploaded image:

```bash
curl -X POST http://127.0.0.1:8000/api/v1/analyze/image \
  -F "image=@frame.jpg" \
  -F "session_id=YOUR_SESSION_ID"
```

Analyze an uploaded video:

```bash
curl -X POST http://127.0.0.1:8000/api/v1/analyze/video \
  -F "video=@sample.mp4" \
  -F "session_id=YOUR_SESSION_ID" \
  -F "sample_every_n_frames=3" \
  -F "max_frames=20" \
  -F "include_landmarks=false" \
  -F "inference_max_width=640" \
  -F "include_frame_results=false" \
  -F "max_alerts=5"
```

Analyze a video summary:

```bash
curl -X POST http://127.0.0.1:8000/api/v1/analyze/video/summary \
  -F "video=@sample.mp4" \
  -F "session_id=YOUR_SESSION_ID" \
  -F "sample_every_n_frames=3" \
  -F "max_frames=20" \
  -F "inference_max_width=640" \
  -F "max_alerts=5" \
  -F "max_key_frames=5"
```

Video response highlights:

- `frame_results`: one entry per sampled frame
- `frame_results[].observations`: human-readable notes tied to the specific signals detected in each frame
- `frame_results[].signals`: machine-readable detections (head pose, gaze, speaking, no-face, low-light, etc.) for frontend rendering/logging
- `frame_results[].sample_window_seconds`: estimated duration represented by that sampled frame
- `frame_results[].timestamp_source`: `video_fps` or `estimated_30fps` when source FPS metadata is missing
- `frame_results[].landmarks`: the detected landmark points for that sampled frame when `include_landmarks=true`
- `events`: grouped suspicious intervals across the video
- `events[].reason`: the main reason the interval was flagged
- `events[].start_timestamp_seconds`, `events[].end_timestamp_seconds`, and `events[].duration_seconds`: when and for how long that interval happened
- `alerts`: compact incident list (best for mobile/real-time feeds) with start/end/duration + reason
- `events[].signal_code`: machine-readable primary reason code

Video summary response highlights:

- `events`: grouped suspicious intervals only
- `alerts`: compact incident list only (few messages per chunk)
- `key_frames`: the most important sampled frames ranked by score
- no `frame_results` payload, so it is lighter for Postman and frontend consumption

Image and landmark response highlights:

- `observations`: human-readable notes generated from the detected signals
- `signals`: machine-readable detections that can be rendered directly in your mobile UI

Score already-extracted features:

```bash
curl -X POST http://127.0.0.1:8000/api/v1/score \
  -H "Content-Type: application/json" \
  -d "{\"face_count\":1,\"features\":{\"gaze_x\":0.1,\"gaze_y\":0.0,\"blink_rate\":12.0,\"head_yaw\":3.0,\"head_pitch\":1.0,\"head_roll\":0.5,\"ear\":0.24}}"
```

## Vercel Deployment

1. Import the project into Vercel.
2. Vercel will use `api/index.py` as the Python function entrypoint.
3. The rewrite in `vercel.json` sends all routes to the FastAPI app.
4. `requirements.txt` contains the runtime dependencies needed for deployment.
5. Set `ALLOWED_ORIGINS` in Vercel if you want to lock CORS down to specific frontend domains.

## Render Deployment

This repo includes a `render.yaml` Blueprint config for a Python web service.

1. In Render, create a new Blueprint and point it to this repository.
2. Render will read `render.yaml` and use:
   - build command: `pip install -r requirements.txt`
   - start command: `uvicorn cheating_detector.api.app:app --host 0.0.0.0 --port $PORT`
   - health check path: `/health`
3. Set `ALLOWED_ORIGINS` in Render to your frontend domain(s) when moving to production.
4. The repo includes `.python-version` pinned to `3.11.9` so dependency builds stay compatible with `numpy==1.26.4` and `mediapipe==0.10.21`.

Manual service setup in Render uses the same build/start commands if you prefer not to use Blueprint.
If you already created a manual Render web service before this file existed, set `PYTHON_VERSION=3.11.9` in that service's Environment settings and redeploy.

## Notes

- `session_id` is optional but recommended when you send multiple frames from the same client, because blink rate and rolling suspicion score are temporal features.
- For repeated short video chunks (for example every 2-5 seconds), always reuse the same `session_id` so calibration and temporal features remain stable and false positives drop.
- Sessions are stored in-memory; restarting or re-scaling the service resets active sessions.
- Dataset download endpoints are read-only. Writing persistent training data is better handled with external storage on Vercel because the function filesystem is ephemeral.
- Render filesystem is also ephemeral unless you attach persistent disk/storage.
- Video uploads are supported, but shorter clips are best, especially on Vercel where serverless execution time is limited.
- The existing webcam runner still works through `faceDetector.py`.
