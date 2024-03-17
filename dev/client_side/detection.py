# from PyQt5.QtCore import QThread, Qt, pyqtSignal
# from PyQt5.QtGui import QImage
# from ultralytics import YOLO
# import cv2
# import cvzone
# import math
# import numpy as np

# class Detection(QThread):
#     def __init__(self):
#         super(Detection, self).__init__()

#     changePixmap = pyqtSignal(QImage)

#     def run(self):
#         self.running = True

#         # Reading the classes
#         with open('obj.names', 'r') as f:
#             classes = [line.strip() for line in f.readlines()] 

#         cap = cv2.VideoCapture(0)
#         model = YOLO('best.pt')

#         while True:
#             ret, frame = cap.read()
#             frame = cv2.resize(frame, (640, 480))
#             result = model(frame, stream=True)
            
#             # Getting bbox, confidence and class names informations to work with
#             for info in result:
#                 boxes = info.boxes

#                 for box in boxes:
#                     confidence = box.conf[0]
#                     confidence = math.ceil(confidence * 100)
#                     Class = int(box.cls[0])

#                     if confidence > 50:
#                         x1, y1, x2, y2 = box.xyxy[0]
#                         x1, y1, x2, y2 = int(x1), int(y1), int (x2), int(y2)
#                         cv2.rectangle(frame, (x1,y1), (x2,y2), (0,0,255), 5)
#                         cvzone.putTextRect(frame, f'{classes[Class]} {confidence}%', [x1 + 8, y1 + 100], scale=1.5, thickness=2)

#             cv2.imshow('frame', frame)

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from ultralytics import YOLO
import cvzone
import math
import sys
import cv2

class Detection(QWidget):
    def __init__(self):
        super(Detection, self).__init__()

        # changePixmap = pyqtSignal(QImage) // REMEMBER TO CHECK HOW TO LINK THIS

        self.VBL = QVBoxLayout()

        self.FeedLabel = QLabel()
        self.VBL.addWidget(self.FeedLabel)

        self.CancelBTN = QPushButton("Cancel")
        self.CancelBTN.clicked.connect(self.CancelFeed)
        self.VBL.addWidget(self.CancelBTN)

        self.Worker1 = Worker1()
        
        self.Worker1.start()
        self.Worker1.ImageUpdate.connect(self.ImageUpdateSlot)

        self.setLayout(self.VBL)

    def ImageUpdateSlot(self, Image):
        self.FeedLabel.setPixmap(QPixmap.fromImage(Image))

    def CancelFeed(self):
        self.Worker1.stop()


class Worker1(QThread):
    ImageUpdate = pyqtSignal(QImage)
    def run(self):
        self.ThreadActive = True

        with open('obj.names', 'r') as f:
            classes = [line.strip() for line in f.readlines()] 

        model = YOLO('best.pt')
        cap = cv2.VideoCapture(0)

        while self.ThreadActive:
            ret, frame = cap.read()
            if ret:
                Image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                FlippedImage = cv2.flip(Image, 1)
                ConvertToQtFormat = QImage(FlippedImage.data, FlippedImage.shape[1], FlippedImage.shape[0], QImage.Format_RGB888)
                Pic = ConvertToQtFormat.scaled(640, 480, Qt.KeepAspectRatio)
                self.ImageUpdate.emit(Pic)
        
            ret, frame = cap.read()
            frame = cv2.resize(frame, (640, 480))
            result = model(frame, stream=True)
            
            # Getting bbox, confidence and class names informations to work with
            for info in result:
                boxes = info.boxes

                for box in boxes:
                    confidence = box.conf[0]
                    confidence = math.ceil(confidence * 100)
                    Class = int(box.cls[0])

                    if confidence > 50:
                        x1, y1, x2, y2 = box.xyxy[0]
                        x1, y1, x2, y2 = int(x1), int(y1), int (x2), int(y2)
                        cv2.rectangle(frame, (x1,y1), (x2,y2), (0,0,255), 5)
                        cvzone.putTextRect(frame, f'{classes[Class]} {confidence}%', [x1 + 8, y1 + 100], scale=1.5, thickness=2)

    def stop(self):
        self.ThreadActive = False
        self.quit()

if __name__== "__main__":
    App = QApplication(sys.argv)
    Root = Detection()
    Root.show()
    sys.exit(App.exec())