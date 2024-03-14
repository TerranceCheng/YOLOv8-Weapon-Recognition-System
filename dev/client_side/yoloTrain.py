from ultralytics import YOLO

# Create model
model = YOLO('yolov8n.pt')

# Train model
results = model.train(data='dev\client_side\config.yaml', epochs = 1)
model.export(format="onnx",opset=12)