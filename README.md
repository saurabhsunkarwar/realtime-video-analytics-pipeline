# Real-Time Multi-Class Video Analytics Pipeline

A production-ready computer vision pipeline built with Python and YOLOv8. It handles simultaneous multi-class object detection (humans, vehicles, surroundings/gadgets) and converts live video frames into structured time-series JSON event logs for downstream database ingestion.

## Key Architecture Features
* **Multi-Class Detection Engine:** Utilizes YOLOv8 nano weights for optimized inference speeds on standard edge hardware.
* **Dual-Stream Output Layer:** Implements a visual overlay annotation system running in parallel with a headless data logging system.
* **Structured Data Stream:** Translates continuous visual context into microsecond-timestamped JSON payloads containing dynamic object counts, class tags, and bounding box coordinates.
* **Contextual Labeling Slot:** Includes structural logic to safely isolate human frames for secondary attribute tagging (demographics/gender classification) without bottlenecking background tracking.

## Pipeline JSON Schema Output Example
```json
{
  "timestamp": "2026-06-25 09:30:15",
  "metrics": {
    "total_humans": 1,
    "total_vehicles": 1,
    "total_surround_gadgets": 0
  },
  "detections": [
    {
      "object_class": "person",
      "confidence": 0.89,
      "bounding_box": [120.4, 45.2, 340.1, 600.5],
      "demographic_context": "Male (25-30)"
    },
    {
      "object_class": "car",
      "confidence": 0.76,
      "bounding_box": [450.0, 200.1, 710.4, 480.9],
      "demographic_context": "N/A"
    }
  ]
}
```

## Production Scalability Recommendations
1. **Frame Skipping Processing:** For heavy cloud infrastructure, process every N-th frame (e.g., every 3rd frame) to drop compute overhead by up to 60% while maintaining temporal tracking via tracking frameworks (ByteTrack/DeepSORT).
2. **Downstream Ingestion:** The time-series JSON structure allows native decoupling via message brokers (Apache Kafka / RabbitMQ) directly into unstructured storage buckets (MongoDB / AWS DynamoDB).
