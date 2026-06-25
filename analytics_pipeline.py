import cv2
import json
import time
import os
import pyodbc
from ultralytics import YOLO


class UnifiedVideoAnalyticsPipeline:
    def __init__(self, weights="yolov8n.pt", log_file="analytics_logs.json"):
        """
        Initializes YOLOv8, local JSON logging, and active SQL Server connectivity.
        """
        self.model = YOLO(weights)
        self.log_file = log_file
        self.target_classes = [0, 2, 3, 5, 7, 63, 67]

        # Initialize local JSON file
        with open(self.log_file, "w") as f:
            f.write("[]\n")

        # SQL Server Connection Configuration
        self.server = r'MSI\SQLEXPRESS'
        self.database = 'SecurityAnalytics'
        self.conn_str = f"DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={self.server};DATABASE={self.database};Trusted_Connection=yes;"

        print("[INFO] Testing SQL Server Connection...")
        try:
            conn = pyodbc.connect(self.conn_str)
            conn.close()
            print("[SUCCESS] Connected to SQL Server Table: VideoAnalyticsLogs")
        except Exception as e:
            print(f"[WARNING] SQL Connection failed: {e}. Ensure SQL Server is running.")

    def save_to_local_json(self, frame_log):
        """Appends the live frame log directly into a local JSON array file."""
        try:
            with open(self.log_file, "r+") as f:
                f.seek(0, os.SEEK_END)
                pos = f.tell() - 2
                if pos > 0:
                    f.seek(pos)
                    f.write(",\n" + json.dumps(frame_log) + "]")
                else:
                    f.seek(0)
                    f.write("[" + json.dumps(frame_log) + "]")
        except Exception as e:
            print(f"[ERROR] JSON file write failed: {e}")

    def insert_into_sql_server(self, timestamp, humans, vehicles, gadgets):
        """Inserts aggregated frame traffic counts straight into SSMS."""
        try:
            conn = pyodbc.connect(self.conn_str)
            cursor = conn.cursor()
            query = """
                    INSERT INTO VideoAnalyticsLogs (LogTimestamp, TotalHumans, TotalVehicles, TotalGadgets)
                    VALUES (?, ?, ?, ?)
                    """
            cursor.execute(query, (timestamp, humans, vehicles, gadgets))
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"[DATABASE ERROR] Failed inserting to SQL Server: {e}")

    def process_video(self, source=0):
        cap = cv2.VideoCapture(source)
        print(f"[INFO] Ingestion Pipeline Active. Streaming to Local JSON and SSMS...")

        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            results = self.model(frame, verbose=False)
            result = results[0]

            timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
            frame_log = {
                "timestamp": timestamp,
                "metrics": {"total_humans": 0, "total_vehicles": 0, "total_surround_gadgets": 0},
                "detections": []
            }

            for box in result.boxes:
                class_id = int(box.cls)
                confidence = float(box.conf)

                if class_id in self.target_classes and confidence > 0.45:
                    label = self.model.names[class_id]
                    # Flatten the multi-dimensional tensor list by extracting the first element [0]
                    bbox_flat = box.xyxy.tolist()[0]
                    bbox = [round(float(x), 1) for x in bbox_flat]

                    if label == "person":
                        frame_log["metrics"]["total_humans"] += 1
                    elif label in ["car", "motorcycle", "bus", "truck"]:
                        frame_log["metrics"]["total_vehicles"] += 1
                    else:
                        frame_log["metrics"]["total_surround_gadgets"] += 1

                    frame_log["detections"].append({
                        "object_class": label,
                        "confidence": round(confidence, 2),
                        "bounding_box": bbox
                    })

                    # Convert to integers for drawing bounding boxes safely
                    xmin, ymin, xmax, ymax = map(int, bbox)
                    cv2.rectangle(frame, (xmin, ymin), (xmax, ymax), (0, 255, 0), 2)
                    display_text = label
                    cv2.putText(frame, display_text, (xmin, ymin - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

            if frame_log["detections"]:
                print(json.dumps(frame_log))
                self.save_to_local_json(frame_log)

                # Write direct metrics stream to local SSMS database
                self.insert_into_sql_server(
                    timestamp,
                    frame_log["metrics"]["total_humans"],
                    frame_log["metrics"]["total_vehicles"],
                    frame_log["metrics"]["total_surround_gadgets"]
                )

            cv2.imshow("Production Video Analytics Feed", frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                print("[INFO] Pipeline safely terminated by user.")
                break

        cap.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    pipeline = UnifiedVideoAnalyticsPipeline()
    pipeline.process_video(0)
