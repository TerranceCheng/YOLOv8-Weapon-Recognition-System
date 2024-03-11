from ultralytics import YOLO

# Create model
model = YOLO('yolov8n.yaml')

# Train model
results = model.train(data='dev\client_side\config.yaml', epochs = 1)
