# Real-Time Video Analytics Pipeline Using YOLOv8, OpenCV and SQL Server
A real-time computer vision pipeline that performs object detection on live video streams, generates structured analytics metadata, and simultaneously stores results in JSON and Microsoft SQL Server for downstream analysis.
## 1. Problem Statement
Manual security monitoring and video surveillance are highly inefficient, error-prone, and scale poorly. Organizations capture thousands of hours of video footage but fail to convert this visual data into structured, actionable business intelligence. 

### Key Challenges
* **Data Silos:** Raw video streams lack metadata, making search, automated alerting, and historical auditing impossible.
* **Latency:** Sending raw video to centralized cloud environments for processing consumes massive bandwidth and introduces network lag.
* **Lack of Concurrency:** Security teams cannot cross-reference real-time physical foot traffic or vehicle queues with structured operational data.

---

## 2. Technical Approach
This project implements an **edge-computing ingestion pipeline** that processes live video feeds locally, extracts structural metadata, and simultaneously streams it to both a high-speed local cache and an enterprise relational database.

### Data Flow Architecture
1. **Live Camera Stream** (Captured via OpenCV)
2. **YOLOv8 Engine Inference** (Object Detection & Class Filtering)
3. **Dual Ingestion Targets:**
   * **Local JSON Cache** (Stores detailed bounding box structures)
   * **SQL Server DB** (Stores aggregated metrics stream)

### Architectural Pillars
1. **Edge Inference Engine (`OpenCV` + `Ultralytics YOLOv8`):** Captures high-frame-rate video streams at the edge. The system filters objects down to targeted structural classes (Humans, Vehicles, Gadgets) using a confidence threshold of >0.45.
2. **Semi-Structured Local Cache (`JSON`):** Serializes object class labels, confidence scores, bounding box coordinates, and frame-level metadata into a local JSON file. This provides a detailed event log alongside the structured SQL analytics records.
3. **Relational Ingestion Pipeline (`PyODBC`):** Flattens the deep JSON array into a metrics stream and issues `INSERT` transactions to a local Microsoft SQL Server (`SSMS`) instance for operational dashboards.

---

## 3. Implementation & Results
The pipeline delivers a real-time, low-latency display feed overlaying dynamic bounding boxes onto the video canvas while consistently populating storage.

### Prerequisites & Dependencies
To install the necessary components on your machine, create a `requirements.txt` file and run:
```bash
pip install -r requirements.txt
```
*Note: Ensure the **Microsoft ODBC Driver 17 for SQL Server** is installed natively on your OS.*

### Database Schema Setup
Execute this schema inside your SQL Server Management Studio (`SSMS`) to initialize the database and logs table prior to running the ingestion script:

```sql
CREATE DATABASE SecurityAnalytics;
GO

USE SecurityAnalytics;
GO

CREATE TABLE VideoAnalyticsLogs (
    LogID INT IDENTITY(1,1) PRIMARY KEY,
    LogTimestamp DATETIME NOT NULL,
    TotalHumans INT DEFAULT 0,
    TotalVehicles INT DEFAULT 0,
    TotalGadgets INT DEFAULT 0
);
GO
```

### Analytical Queries (Business Intelligence)
Once your pipeline has run for a few minutes, you can execute the following production queries to analyze your data trends directly from your structured database:

#### Query 1: Live Stream Telemetry Audit
*Retrieves all raw frames sorted chronologically to review the most recent detections streaming into the database.*
```sql
USE SecurityAnalytics;
GO

SELECT * FROM VideoAnalyticsLogs 
ORDER BY LogTimestamp DESC;
```

#### Query 2: Pipeline Performance Summary Metrics
*Calculates the overall system load, counting cumulative detections across all classes and extracting the pipeline's last known active heartbeat.*
```sql
USE SecurityAnalytics;
GO

SELECT 
    COUNT(*) as TotalFramesLogged,
    SUM(TotalHumans) as CumulativeHumanDetections,
    SUM(TotalVehicles) as CumulativeVehicleDetections,
    SUM(TotalGadgets) as CumulativeGadgetDetections,
    MAX(LogTimestamp) as LastActiveTimestamp
FROM VideoAnalyticsLogs;
```
### 4. Edge Performance Benchmark & Field Notes
During a **20-second local webcam benchmark**, the pipeline's ingestion speed and detection behavior were evaluated on CPU-based edge hardware:

* **Total Processed Volume:** ~572 frames.
* **Ingestion Frame Rate:** ~28.6 Frames Per Sec (FPS) live capture.
* **Cumulative Metric Drift:** Total logged human detections reached **586 counts** over the raw frame span.

#### Technical Analysis of Metric Drift (Ghost Detections)
The slight inflation in cumulative metrics (~2.4% variance relative to actual background counts) is a documented behavior of running a lightweight edge model (`yolov8n.pt`) without an overlapping temporal tracking layer:
1. **Bounding Box Jitter:** Minor lighting fluctuations at the edge can cause the model to split or duplicate a single human target across sequential high-frequency frames.
2. **Ghost Detections:** Transient background noise can trigger a brief, isolated high-confidence threshold flag (>0.45) that resolves itself natively in under 3 frames.

#### Engineering Mitigations (Future Roadmap)
To stabilize metric aggregation for enterprise deployments, the next development iteration will transition from raw spatial detections to stateful trajectory tracking by integrating **ByteTRACK** or **BoT-SORT** (`model.track(source, persist=True)`). This will tie detections to persistent unique IDs, neutralizing individual frame-level count spikes.

## Current Limitations

The current implementation performs frame-level object detection only.

Because detections are counted independently for each frame:

- The same object may be counted multiple times across consecutive frames.
- Temporary duplicate detections may occur.
- Persistent object identities are not maintained.

As a result, cumulative object counts should be interpreted as detection events rather than unique individuals or vehicles.

Future versions will integrate ByteTrack or BoT-SORT to assign persistent object IDs and improve aggregation accuracy.
### 5. Sample JSON Event Stream Output
Below is an architectural snapshot of the semi-structured JSON payload structured by the pipeline per active frame:

```json
[
  {
    "timestamp": "2026-06-25 10:34:17",
    "metrics": {
      "total_humans": 1,
      "total_vehicles": 0,
      "total_surround_gadgets": 0
    },
    "detections": [
      {
        "object_class": "person",
        "confidence": 0.89,
        "bounding_box": [120.4, 45.1, 340.8, 620.0] 
      }
    ]
  }
]
```
## Future Enhancements

Planned improvements include:

- ByteTrack / BoT-SORT object tracking
- Unique footfall counting
- Multi-camera stream support
- GPU-accelerated inference
- Asynchronous database ingestion
- Secondary age and gender classification models
- REST API for analytics retrieval