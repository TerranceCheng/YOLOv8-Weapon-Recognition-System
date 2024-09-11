# import socket
# import cv2
# import numpy as np
# import math
# from PyQt5.QtCore import QThread, pyqtSignal
# from PyQt5.QtWidgets import QApplication
# from ultralytics import YOLO
# from PyQt5.QtGui import QImage, QPixmap


# class Worker1(QThread):
#     ImageUpdate = pyqtSignal(QImage)

#     def run(self):
#         self.ThreadActive = True

#         # Load class names for object detection
#         with open('C:/Users/yongt/Desktop/FYP Project/YOLOv8 Weapon Recognition System/obj.names', 'r') as f:
#             classes = [line.strip() for line in f.readlines()]

#         # Initialize YOLO model
#         model = YOLO('C:/Users/yongt/Desktop/FYP Project/YOLOv8 Weapon Recognition System/weaponRecognition_firstModel.pt')
#         cap = cv2.VideoCapture(0)

#         # Setup socket
#         try:
#             server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#             server_socket.bind(('0.0.0.0', 8000))
#             server_socket.listen(0)
#             print("Server is listening on port 8000")
#             conn, addr = server_socket.accept()
#             print(f"Connection accepted from {addr}")

#         except socket.error as e:
#             print(f"Socket error: {e}")
#             return

#         while self.ThreadActive:
#             ret, frame = cap.read()
#             if ret:
#                 Image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
#                 FlippedImage = cv2.flip(Image, 1)

#                 # Object detection and drawing boxes
#                 image_with_boxes = self.draw_boxes(FlippedImage, model, classes)

#                 # Encode frame as JPEG
#                 _, buffer = cv2.imencode('.jpg', image_with_boxes)
#                 frame_bytes = buffer.tobytes()
#                 frame_size = len(frame_bytes)
#                 print(f"Sending frame size: {frame_size}")

#                 # Send frame size first
#                 conn.sendall(frame_size.to_bytes(4, byteorder='big'))
#                 # Then send the frame itself
#                 conn.sendall(frame_bytes)

#     def draw_boxes(self, image, model, classes):
#         result = model(image, stream=True)
#         for info in result:
#             for box in info.boxes:
#                 confidence = box.conf[0]
#                 confidence = math.ceil(confidence * 100)
#                 Class = int(box.cls[0])

#                 if confidence > 70:
#                     x1, y1, x2, y2 = box.xyxy[0]
#                     x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
#                     cv2.rectangle(image, (x1, y1), (x2, y2), (0, 255, 0), 2)
#                     cv2.putText(image, f'{classes[Class]} {confidence}%', (x1 + 8, y1 + 25), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 3)

#         return image

#     def stop(self):
#         self.ThreadActive = False
#         self.quit()

# if __name__ == "__main__":
#     app = QApplication([])
#     worker = Worker1()
#     worker.start()
#     app.exec_()

import socket
import cv2
import numpy as np
import math
from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtWidgets import QApplication
from ultralytics import YOLO
from PyQt5.QtGui import QImage, QPixmap


class Worker1(QThread):
    ImageUpdate = pyqtSignal(QImage)

    def run(self):
        self.ThreadActive = True

        # Load class names for object detection
        with open('C:/Users/yongt/Desktop/FYP Project/YOLOv8 Weapon Recognition System/obj.names', 'r') as f:
            classes = [line.strip() for line in f.readlines()]

        # Initialize YOLO model
        model = YOLO('C:/Users/yongt/Desktop/FYP Project/YOLOv8 Weapon Recognition System/weaponRecognition_firstModel.pt')
        cap = cv2.VideoCapture(0)

        # Setup socket
        try:
            server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server_socket.bind(('0.0.0.0', 8000))
            server_socket.listen(0)
            print("Server is listening on port 8000")
            conn, addr = server_socket.accept()
            print(f"Connection accepted from {addr}")

        except socket.error as e:
            print(f"Socket error: {e}")
            return

        while self.ThreadActive:
            ret, frame = cap.read()
            if ret:
                Image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                FlippedImage = cv2.flip(Image, 1)

                # Object detection and drawing boxes
                image_with_boxes = self.draw_boxes(FlippedImage, model, classes)

                # Encode frame as JPEG
                _, buffer = cv2.imencode('.jpg', image_with_boxes)
                frame_bytes = buffer.tobytes()
                frame_size = len(frame_bytes)
                print(f"Sending frame size: {frame_size}")

                # Send frame size first
                conn.sendall(frame_size.to_bytes(4, byteorder='big'))
                # Then send the frame itself
                conn.sendall(frame_bytes)
                print(f"Sent frame of size {frame_size}")

    def draw_boxes(self, image, model, classes):
        result = model(image, stream=True)
        for info in result:
            for box in info.boxes:
                confidence = box.conf[0]
                confidence = math.ceil(confidence * 100)
                Class = int(box.cls[0])

                if confidence > 70:
                    x1, y1, x2, y2 = box.xyxy[0]
                    x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
                    cv2.rectangle(image, (x1, y1), (x2, y2), (0, 255, 0), 2)
                    cv2.putText(image, f'{classes[Class]} {confidence}%', (x1 + 8, y1 + 25), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 3)

        return image

    def stop(self):
        self.ThreadActive = False
        self.quit()

if __name__ == "__main__":
    app = QApplication([])
    worker = Worker1()
    worker.start()
    app.exec_()
