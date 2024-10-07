from ultralytics import YOLO

def train_model():
    # Create model
    model = YOLO(r'C:\Users\yongt\Desktop\FYP Project\YOLOv8 Weapon Recognition System\runs\detect\train2\weights\best.pt')
    # model = YOLO('best.pt')

    # Train model
    # results = model.train(data='dev\client_side\config.yaml', epochs=50, save_period=-1, resume=True)

    # results = model.train(data=r'C:\Users\yongt\Downloads\weapon_yolov8\data.yaml', epochs=50, save_period=-1, resume=True)
    # results = model.train(data=r'C:\Users\yongt\Downloads\weapon_yolov8\data.yaml', epochs=50, save_period=-1, device=0, resume=True)
    results = model.train(data=r'C:\Users\yongt\Downloads\yolov8\data.yaml', epochs=50, save_period=-1, device=0)

if __name__ == '__main__':
    train_model()


# model.info(detailed=True)
# model.export(format="onnx",opset=12)

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