# ArkAI API — FE Developer Guide

> **This is a demo server.** It returns realistic mock data so you can build the frontend without waiting for production ML models. All endpoints, request shapes, and response schemas match the real API exactly — when the real server is ready, change the base URL and you're done.

---

## Quick Start

### Option 1 — Docker (recommended, no Python needed)

```bash
git clone <repo-url>
cd Demo-Livestox-API
docker compose up --build
```

### Option 2 — Bare Python

```bash
cd Demo-Livestox-API
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -r requirements.txt
uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
```

API running at: **http://localhost:8000**

| URL | Purpose |
|-----|---------|
| http://localhost:8000/docs | Interactive Swagger UI — try every endpoint in the browser |
| http://localhost:8000/redoc | ReDoc — clean reference docs |
| http://localhost:8000/health | Health check |

---

## API Overview

| Router Group | Base Path | Purpose |
|---|---|---|
| Camera Management | `/api/v1/cameras` | Register cameras, set RTSP URLs, take snapshots |
| ROI Management | `/api/v1/roi` | Define polygon zones and counting lines |
| Tracking | `/api/v1/tracking` | Per-frame chicken tracking (Bot-SORT) |
| Counting | `/api/v1/counting` | Zone counts, line crossings, event history |
| Weight Estimation | `/api/v1/weight` | GBDT weight estimation per chicken |
| Processing | `/api/v1` | Batch image/video jobs and live stream management |

---

## Mock Behaviour — What to Expect

| Behaviour | Detail |
|-----------|--------|
| Chickens detected | 8–20 per call (random) |
| Weight (GBDT/predicted) | 900–1500 g |
| Weight (YOLO/class-name) | GBDT ± 30 g |
| Age | 21–35 days |
| Detection confidence | 0.72–0.96 |
| Counts | Increment slightly on every call — simulates live data |
| Cameras | Persist in memory for the session |
| ROI zones & lines | Persist in memory per camera |
| Processing jobs | Created as `processing`, auto-complete to `completed` in ~3 s |
| State reset | Clears on server restart — intentional for a demo |

---

## Typical FE Workflow

```
1. Register a camera
2. Upload a sample image → get base64 for ROI drawing UI
3. Post zone polygon coords and counting line coords
4. Start a live stream or submit a batch job
5. Poll /counting/counts and /stream/results in a loop
6. Display weights from /weight/analyze/*
```

---

## Endpoint Reference

### Health Check

```
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "uptime_seconds": 42.3,
  "model_loaded": true
}
```

**JavaScript (React fetch):**
```js
const checkHealth = async () => {
  const res = await fetch('http://localhost:8000/health');
  const data = await res.json();
  setServerOnline(data.status === 'healthy');
};
```

**C# (.NET HttpClient):**
```csharp
using var client = new HttpClient();
var response = await client.GetAsync("http://localhost:8000/health");
var json = await response.Content.ReadAsStringAsync();
// Deserialize with System.Text.Json or Newtonsoft
var data = JsonSerializer.Deserialize<HealthResponse>(json);
Console.WriteLine(data.Status); // "healthy"
```

---

### Register a Camera

```
POST /api/v1/cameras/?camera_id=cam1
```

**Response:**
```json
{
  "message": "Camera 'cam1' added",
  "camera": {
    "camera_id": "cam1",
    "rtsp_url": null,
    "status": "inactive",
    "added_at": 1712694000.0,
    "frame_count": 0
  }
}
```

**JavaScript (React):**
```js
const addCamera = async (cameraId) => {
  const res = await fetch(
    `http://localhost:8000/api/v1/cameras/?camera_id=${cameraId}`,
    { method: 'POST' }
  );
  if (!res.ok) throw new Error((await res.json()).detail);
  const data = await res.json();
  setCameras(prev => [...prev, data.camera]);
};
```

**C# (.NET):**
```csharp
var response = await client.PostAsync(
  $"http://localhost:8000/api/v1/cameras/?camera_id=cam1",
  null
);
response.EnsureSuccessStatusCode();
var json = await response.Content.ReadAsStringAsync();
```

---

### Set RTSP URL

```
PUT /api/v1/cameras/{camera_id}
Content-Type: application/json

{ "rtsp_url": "rtsp://192.168.1.100/stream" }
```

**JavaScript (React):**
```js
const setRtsp = async (cameraId, rtspUrl) => {
  await fetch(`http://localhost:8000/api/v1/cameras/${cameraId}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ rtsp_url: rtspUrl }),
  });
};
```

**C# (.NET):**
```csharp
var body = JsonSerializer.Serialize(new { rtsp_url = "rtsp://192.168.1.100/stream" });
var content = new StringContent(body, Encoding.UTF8, "application/json");
await client.PutAsync($"http://localhost:8000/api/v1/cameras/{cameraId}", content);
```

---

### Upload Sample Image for ROI Drawing

```
POST /api/v1/roi/sample_image
Content-Type: multipart/form-data
```

**Response:**
```json
{
  "width": 1920,
  "height": 1080,
  "standard_width": 1280,
  "standard_height": 720,
  "image_base64": "<base64 JPEG string>"
}
```

Render `image_base64` in an `<img>` tag. Let users click polygon vertices on it.
All zone/line coordinates must be in **1280×720** pixel space.

**JavaScript (React):**
```js
const uploadSampleImage = async (file) => {
  const form = new FormData();
  form.append('file', file);
  const res = await fetch('http://localhost:8000/api/v1/roi/sample_image', {
    method: 'POST',
    body: form,
  });
  const data = await res.json();
  setSampleImage(`data:image/jpeg;base64,${data.image_base64}`);
};
```

**C# (.NET):**
```csharp
using var form = new MultipartFormDataContent();
using var stream = File.OpenRead("sample.jpg");
form.Add(new StreamContent(stream), "file", "sample.jpg");
var response = await client.PostAsync(
  "http://localhost:8000/api/v1/roi/sample_image", form
);
var json = await response.Content.ReadAsStringAsync();
```

---

### Create an ROI Zone

```
POST /api/v1/roi/{camera_id}/zone
Content-Type: application/json

{
  "zone_name": "feeding_area",
  "points": [[10,10],[400,10],[400,300],[10,300]],
  "description": "Main feeding zone"
}
```

Points are `[x, y]` pairs in 1280×720 pixels. Minimum 3 points.

**JavaScript (React):**
```js
const createZone = async (cameraId, zoneName, points) => {
  const res = await fetch(`http://localhost:8000/api/v1/roi/${cameraId}/zone`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ zone_name: zoneName, points }),
  });
  return res.json();
};
```

**C# (.NET):**
```csharp
var zone = new {
  zone_name = "feeding_area",
  points = new[] {
    new[] { 10, 10 }, new[] { 400, 10 },
    new[] { 400, 300 }, new[] { 10, 300 }
  }
};
var content = new StringContent(
  JsonSerializer.Serialize(zone), Encoding.UTF8, "application/json"
);
await client.PostAsync($"http://localhost:8000/api/v1/roi/{cameraId}/zone", content);
```

---

### Create a Counting Line

```
POST /api/v1/roi/{camera_id}/line
Content-Type: application/json

{
  "line_name": "entry_line",
  "points": [[0, 360], [1280, 360]]
}
```

Exactly 2 points required.

**JavaScript (React):**
```js
const createLine = async (cameraId, lineName, p1, p2) => {
  await fetch(`http://localhost:8000/api/v1/roi/${cameraId}/line`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ line_name: lineName, points: [p1, p2] }),
  });
};
```

**C# (.NET):**
```csharp
var line = new { line_name = "entry_line", points = new[] { new[] {0,360}, new[] {1280,360} } };
var content = new StringContent(JsonSerializer.Serialize(line), Encoding.UTF8, "application/json");
await client.PostAsync($"http://localhost:8000/api/v1/roi/{cameraId}/line", content);
```

---

### Get Live Counts — Poll This

```
GET /api/v1/counting/counts?camera_id=cam1
```

**Response:**
```json
{
  "camera_id": "cam1",
  "zone_counts": [
    { "roi_name": "feeding_area", "count": 12 },
    { "roi_name": "resting_area", "count": 5 }
  ],
  "line_counts": [
    { "line_name": "entry_line", "count_in": 34, "count_out": 28 }
  ],
  "total_unique_objects": 47
}
```

**JavaScript (React) — polling with interval:**
```js
useEffect(() => {
  const interval = setInterval(async () => {
    const res = await fetch(
      `http://localhost:8000/api/v1/counting/counts?camera_id=${cameraId}`
    );
    const data = await res.json();
    setCounts(data);
  }, 2000); // poll every 2 seconds
  return () => clearInterval(interval);
}, [cameraId]);
```

**C# (.NET) — polling loop:**
```csharp
using var cts = new CancellationTokenSource();
while (!cts.Token.IsCancellationRequested)
{
  var response = await client.GetAsync(
    $"http://localhost:8000/api/v1/counting/counts?camera_id={cameraId}",
    cts.Token
  );
  var json = await response.Content.ReadAsStringAsync(cts.Token);
  var counts = JsonSerializer.Deserialize<CountingResponse>(json);
  UpdateUI(counts);
  await Task.Delay(2000, cts.Token);
}
```

---

### Analyse an Image for Weight (Segmentation)

```
POST /api/v1/weight/analyze/image/segmentation?model_type=yolov8
Content-Type: multipart/form-data
```

**Response:**
```json
{
  "source": "frame.jpg",
  "source_type": "image",
  "statistics": {
    "total_chickens": 15,
    "avg_weight_predicted": 1243.3,
    "avg_weight_yolo": 1285.7,
    "avg_weight_combined": 1261.4,
    "total_weight_predicted": 18649.5,
    "total_weight_yolo": 19285.5,
    "total_weight_combined": 18920.25
  },
  "per_chicken_detections": [
    {
      "chicken_id": 1,
      "track_id": null,
      "observations": 1,
      "age_days": 28.0,
      "yolo_weight_grams": 1286.0,
      "predicted_weight_grams": 1241.7,
      "combined_weight_grams": 1263.85,
      "confidence": 0.87,
      "class_name": "1286_28",
      "bbox": [100.0, 200.0, 250.0, 350.0]
    }
  ],
  "unique_tracked_chickens": null,
  "total_observations": null,
  "annotated_output": "output/annotated_frame.jpg",
  "message": "Analysis completed: 15 chickens detected with avg weight 1243.3g"
}
```

**JavaScript (React):**
```js
const analyseImage = async (file) => {
  const form = new FormData();
  form.append('file', file);
  const res = await fetch(
    'http://localhost:8000/api/v1/weight/analyze/image/segmentation?model_type=yolov8',
    { method: 'POST', body: form }
  );
  const data = await res.json();
  setAnalysisResult(data);
  // data.statistics.avg_weight_predicted = average weight in grams
  // data.per_chicken_detections = array of per-chicken results
};
```

**C# (.NET):**
```csharp
using var form = new MultipartFormDataContent();
using var stream = File.OpenRead("frame.jpg");
form.Add(new StreamContent(stream), "file", "frame.jpg");
var response = await client.PostAsync(
  "http://localhost:8000/api/v1/weight/analyze/image/segmentation?model_type=yolov8",
  form
);
var json = await response.Content.ReadAsStringAsync();
var result = JsonSerializer.Deserialize<WeightAnalysisResponse>(json);
Console.WriteLine($"Avg weight: {result.Statistics.AvgWeightPredicted}g");
```

---

### Analyse a Video for Weight

```
POST /api/v1/weight/analyze/video/segmentation?model_type=yolov8
Content-Type: multipart/form-data
```

Same response shape as image analysis but:
- `source_type` = `"video"`
- `unique_tracked_chickens` = number of unique chickens tracked (non-null)
- `total_observations` = total detections across all frames
- Each detection has `track_id` and `observations` count

**JavaScript (React):**
```js
const analyseVideo = async (file) => {
  const form = new FormData();
  form.append('file', file);
  // Note: videos take longer — show a loading state
  const res = await fetch(
    'http://localhost:8000/api/v1/weight/analyze/video/segmentation?model_type=yolov8',
    { method: 'POST', body: form }
  );
  const data = await res.json();
  // data.unique_tracked_chickens = total unique chickens seen
  setVideoResult(data);
};
```

---

### Camera Snapshot (JPEG image)

```
GET /api/v1/cameras/{camera_id}/snapshot.jpg
```

Returns a raw JPEG. In the demo this is a solid-colour placeholder; in production it's a real camera frame.

**JavaScript (React) — use directly as img src:**
```jsx
// Refresh every second for live preview
const [snapUrl, setSnapUrl] = useState('');

useEffect(() => {
  const update = () => {
    // Cache-bust so the browser re-fetches
    setSnapUrl(`http://localhost:8000/api/v1/cameras/${cameraId}/snapshot.jpg?t=${Date.now()}`);
  };
  update();
  const id = setInterval(update, 1000);
  return () => clearInterval(id);
}, [cameraId]);

return <img src={snapUrl} alt="camera snapshot" style={{ width: '100%' }} />;
```

**C# (.NET):**
```csharp
var bytes = await client.GetByteArrayAsync(
  $"http://localhost:8000/api/v1/cameras/{cameraId}/snapshot.jpg"
);
await File.WriteAllBytesAsync("snapshot.jpg", bytes);
```

---

### Submit a Batch Processing Job

```
POST /api/v1/process/images?directory_path=/data/images&camera_id=cam1
```

**Response:**
```json
{ "job_id": "f47ac10b-...", "status": "processing", "camera_id": "cam1" }
```

Poll for completion:

```
GET /api/v1/jobs/{job_id}
```

**Response when completed:**
```json
{
  "job_id": "f47ac10b-...",
  "status": "completed",
  "progress_percent": 100.0,
  "frames_processed": 150,
  "frames_total": 150,
  "camera_id": "cam1",
  "result": {
    "summary": {
      "unique_count": 14,
      "average_weight": 1231.5,
      "total_weight": 17241.0,
      "min_weight": 923.4,
      "max_weight": 1487.2,
      "processing_time": 3.0,
      "frames_processed": 150
    },
    "detections": [ ... ]
  }
}
```

**JavaScript (React) — submit and poll:**
```js
const submitJob = async (directoryPath, cameraId) => {
  const res = await fetch(
    `http://localhost:8000/api/v1/process/images?directory_path=${encodeURIComponent(directoryPath)}&camera_id=${cameraId}`,
    { method: 'POST' }
  );
  const { job_id } = await res.json();
  setJobId(job_id);
  setJobStatus('processing');

  const poll = setInterval(async () => {
    const statusRes = await fetch(`http://localhost:8000/api/v1/jobs/${job_id}`);
    const job = await statusRes.json();
    setJobStatus(job.status);
    setProgress(job.progress_percent);
    if (job.status === 'completed') {
      clearInterval(poll);
      setResult(job.result);
    }
  }, 1000);
};
```

**C# (.NET):**
```csharp
// Submit
var createRes = await client.PostAsync(
  $"http://localhost:8000/api/v1/process/images?directory_path=/data&camera_id={cameraId}",
  null
);
var jobJson = await createRes.Content.ReadAsStringAsync();
var job = JsonSerializer.Deserialize<JobResponse>(jobJson);

// Poll until done
while (true)
{
  await Task.Delay(1000);
  var pollRes = await client.GetAsync($"http://localhost:8000/api/v1/jobs/{job.JobId}");
  var status = JsonSerializer.Deserialize<JobStatus>(
    await pollRes.Content.ReadAsStringAsync()
  );
  Console.WriteLine($"Status: {status.Status} ({status.ProgressPercent}%)");
  if (status.Status == "completed") break;
}
```

---

### Live Stream Lifecycle

```
POST /api/v1/stream/start?stream_url=rtsp://...&camera_id=cam1
  → { "stream_id": "...", "status": "running" }

GET  /api/v1/stream/results?stream_id=...
  → { "detections": [...], "statistics": {...} }

POST /api/v1/stream/stop?stream_id=...
  → { "status": "stopped" }
```

**JavaScript (React):**
```js
const startStream = async (rtspUrl, cameraId) => {
  const res = await fetch(
    `http://localhost:8000/api/v1/stream/start?stream_url=${encodeURIComponent(rtspUrl)}&camera_id=${cameraId}`,
    { method: 'POST' }
  );
  const { stream_id } = await res.json();
  setStreamId(stream_id);

  // Poll results every 2 seconds
  const poll = setInterval(async () => {
    const r = await fetch(
      `http://localhost:8000/api/v1/stream/results?stream_id=${stream_id}`
    );
    const data = await r.json();
    setStreamData(data);
  }, 2000);

  return () => {
    clearInterval(poll);
    fetch(`http://localhost:8000/api/v1/stream/stop?stream_id=${stream_id}`, { method: 'POST' });
  };
};
```

**C# (.NET):**
```csharp
// Start
var startRes = await client.PostAsync(
  $"http://localhost:8000/api/v1/stream/start?stream_url=rtsp://cam&camera_id={cameraId}",
  null
);
var streamId = JsonSerializer.Deserialize<StreamResponse>(
  await startRes.Content.ReadAsStringAsync()
).StreamId;

// Poll results
using var cts = new CancellationTokenSource();
while (!cts.Token.IsCancellationRequested)
{
  var r = await client.GetAsync(
    $"http://localhost:8000/api/v1/stream/results?stream_id={streamId}",
    cts.Token
  );
  var results = JsonSerializer.Deserialize<StreamResults>(
    await r.Content.ReadAsStringAsync()
  );
  UpdateDashboard(results);
  await Task.Delay(2000, cts.Token);
}

// Stop
await client.PostAsync(
  $"http://localhost:8000/api/v1/stream/stop?stream_id={streamId}", null
);
```

---

## Error Reference

All errors use FastAPI's standard envelope:

```json
{ "detail": "Human-readable error message" }
```

| HTTP Code | Trigger |
|-----------|---------|
| `400` | Invalid file type, duplicate camera ID, SAM2 without `detector_model_path` |
| `404` | Camera not found, track/zone/line/job/stream not found |
| `422` | Missing required query param or invalid request body field |
| `500` | Unexpected server error (should not occur in demo) |

**JavaScript — centralised error handler:**
```js
const apiFetch = async (url, options = {}) => {
  const res = await fetch(url, options);
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: `HTTP ${res.status}` }));
    throw new Error(err.detail);
  }
  return res.json();
};
```

**C# — extension method:**
```csharp
public static async Task<T> ReadOrThrowAsync<T>(this HttpResponseMessage response)
{
  var json = await response.Content.ReadAsStringAsync();
  if (!response.IsSuccessStatusCode)
  {
    var err = JsonSerializer.Deserialize<ErrorResponse>(json);
    throw new HttpRequestException($"API error {(int)response.StatusCode}: {err?.Detail}");
  }
  return JsonSerializer.Deserialize<T>(json)!;
}
```

---

## Recommended Polling Intervals

| Data | Interval |
|------|----------|
| Live counts (`/counting/counts`) | 2 s |
| Stream results (`/stream/results`) | 1–2 s |
| Job status (`/jobs/{id}`) | 1 s |
| Camera snapshot JPEG | 500 ms–1 s |

---

## Full Workflow Sequence

```
POST /api/v1/cameras/?camera_id=cam1          # 1. Register camera
PUT  /api/v1/cameras/cam1                      # 2. Set RTSP URL
POST /api/v1/roi/sample_image                  # 3. Get base64 image for drawing UI
POST /api/v1/roi/cam1/zone                     # 4. Define polygon zones
POST /api/v1/roi/cam1/line                     # 5. Define counting lines
POST /api/v1/cameras/cam1/stream/start         # 6. Start live stream
GET  /api/v1/counting/counts?camera_id=cam1    # 7. Poll zone counts (every 2s)
GET  /api/v1/stream/results?stream_id=...      # 8. Poll weight results (every 2s)
POST /api/v1/cameras/cam1/stream/stop          # 9. Stop stream
```

---

## Switching to the Real API

When the production server is ready, **only the base URL changes**:

```js
// Demo
const BASE = 'http://localhost:8000';

// Production (exact URL TBD)
const BASE = 'https://api.arkai.io';
```

All endpoint paths, query parameters, request bodies, and response shapes are identical. No other code changes are needed.

> **Note:** The real API expects genuine image/video files. The demo accepts any file content as long as the extension is correct (`.jpg`, `.png`, `.mp4`, etc.). Your existing upload code will work unchanged.
