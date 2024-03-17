# !!!!!!!!!!! CPU !!!!!!!!!!!

from ultralytics import YOLO

# Create model
model = YOLO('best.pt')

# Train model
results = model.train(data='dev\client_side\config.yaml', pretrained=('best.pt'), epochs=35, save_period=-1)
model.export(format="onnx",opset=12)

# !!!!!!!!!!! TORCH CUDA, GPU !!!!!!!!!!!

# from ultralytics import YOLO
# import torch

# device = '0' if torch.cuda.is_available() else "cpu"
# if device == '0':
#     torch.cuda.set_device(0)

# # Load a model
# # model = YOLO('best.pt')  # build a new model from scratch
# # results=model('a.jpeg')
# # model.to(device)
# # model.train(data="dev\client_side\config.yaml", epochs=5)
# print ('Device:', device)

# model = YOLO('best.pt')

# model.to(device='cuda')
# print ('Before:', model.device.type)
# results=model('a.jpeg')
# print("After:", model.device.type)