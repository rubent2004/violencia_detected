import tensorflow as tf
print("Num GPUs Available: ", len(tf.config.list_physical_devices('GPU')))
import torch
print("CUDA Available: ", torch.cuda.is_available())
