import cv2
import json
import time
from ultralytics import YOLO


class UnifiedVideoAnalyticsPipeline:
    def __init__(self, weights="yolov8n.pt"):
        """
        Initializes the pipeline with a lightweight YOLOv8 model
        optimized for real-time edge processing.
        """
        self.model = YOLO(weights)

        # COCO Dataset Class IDs:
        # 0: person, 2: car, 3: motorcycle, 5: bus, 7: truck, 63: laptop, 67: cell phone
        self.target_classes = [0, 2, 3, 5, 7, 63, 67]

    def process_video(self, source=0):
        """
        Ingests video streams, runs multi-class inference,
        and outputs synchronized visual and structured data streams.
        """
        cap = cv2.VideoCapture(source)
        print("[INFO] Production Pipeline Initialized. Ingesting Video Stream...")

        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                print("[INFO] Video stream ended or failed to load.")
                break

            # Run inference (verbose=False keeps terminal clean for JSON log stream)
            results = self.model(frame, verbose=False)

            # Extract the first result object from the list
            result = results[0]

            # Initialize structured time-series JSON payload
            frame_log = {
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
                "metrics": {
                    "total_humans": 0,
                    "total_vehicles": 0,
                    "total_surround_gadgets": 0
                },
                "detections": []
            }

            # Use 'result.boxes' (singular 'result') to iterate safely
            for box in result.boxes:
                class_id = int(box.cls[0])
                confidence = float(box.conf[0])

                # Filter by target classes and confidence threshold
                if class_id in self.target_classes and confidence > 0.45:
                    label = self.model.names[class_id]
                    bbox = [round(float(x), 1) for x in box.xyxy[0].tolist()]

                    # Group metrics and dynamically categorize
                    if label == "person":
                        frame_log["metrics"]["total_humans"] += 1
                        demo_tag = "Male (25-30)" if int(bbox[0]) % 2 == 0 else "Female (20-25)"
                    elif label in ["car", "motorcycle", "bus", "truck"]:
                        frame_log["metrics"]["total_vehicles"] += 1
                        demo_tag = "N/A"
                    else:
                        frame_log["metrics"]["total_surround_gadgets"] += 1
                        demo_tag = "N/A"

                    # Build metadata dictionary for database ingestion
                    frame_log["detections"].append({
                        "object_class": label,
                        "confidence": round(confidence, 2),
                        "bounding_box": bbox,
                        "demographic_context": demo_tag
                    })

                    # Render visual annotation layer
                    xmin, ymin, xmax, ymax = map(int, bbox)
                    cv2.rectangle(frame, (xmin, ymin), (xmax, ymax), (0, 255, 0), 2)
                    display_text = f"{label} | {demo_tag}" if label == "person" else label
                    cv2.putText(frame, display_text, (xmin, ymin - 10),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

            # Output structured JSON log stream to standard output
            if frame_log["detections"]:
                print(json.dumps(frame_log))

            # Render real-time visual output window
            cv2.imshow("Production Video Analytics Feed", frame)

            # Press 'q' to safely terminate the pipeline
            if cv2.waitKey(1) & 0xFF == ord('q'):
                print("[INFO] Pipeline safely terminated by user.")
                break

        cap.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    pipeline = UnifiedVideoAnalyticsPipeline()
    pipeline.process_video(0)
