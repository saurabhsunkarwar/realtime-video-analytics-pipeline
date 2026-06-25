# Real-Time Video Analytics Pipeline: Edge-to-Database Ingestion

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
2. **Semi-Structured Local Cache (`JSON`):** Serializes raw pixel coordinates, granular tracking IDs, bounding boxes, and metadata into a local JSON flat-file. This ensures zero data loss if connection to the database drops.
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
