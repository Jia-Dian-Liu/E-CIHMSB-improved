
# 建立 image_encoding.py → Z碼圖編碼模組

import numpy as np
import math

from PIL import Image
from binary_operations import int_to_binary, binary_to_int

def z_to_image(z_bits):
  """
  功能:
    將 Z 碼位元列表編碼成灰階圖片
  """
  num_bits = len(z_bits)
  num_pixels = math.ceil(num_bits / 8)

  if num_bits % 8 != 0:
    padding = 8 - (num_bits % 8)
    z_bits = z_bits + [0] * padding
  
  pixels = []
  for i in range(0, len(z_bits), 8):
    byte = z_bits[i:i+8]
    pixel_value = binary_to_int(byte)
    pixels.append(pixel_value)
  
  width = int(math.sqrt(num_pixels))
  height = math.ceil(num_pixels / width)
  
  while len(pixels) < width * height:
    pixels.append(0)
  
  pixel_array = np.array(pixels, dtype=np.uint8)
  pixel_array = pixel_array[:width * height].reshape(height, width)
  
  image = Image.fromarray(pixel_array, mode='L')
  
  return image

def image_to_z(image, original_bit_length=None):
  """
  功能:
    從灰階圖片解碼 Z 碼位元列表
  """
  pixel_array = np.array(image)
  pixels = pixel_array.flatten()
  
  z_bits = []
  for pixel in pixels:
    binary = int_to_binary(pixel, 8)
    z_bits.extend(binary)
  
  if original_bit_length is not None:
    z_bits = z_bits[:original_bit_length]
  
  return z_bits

def embed_data_multi_msb(image, data, msb_indices=[6, 7]):
    """
    將 data 嵌入 image 的指定 MSB 位元中。
    msb_indices: list of bit positions to use for embedding
    """
    # 轉換資料為位元序列
    bit_stream = convert_data_to_bits(data)
    
    # 遍歷像素並嵌入資料
    for pixel in image:
        for channel in pixel:  # R, G, B
            for msb in msb_indices:
                # 清除指定位元
                channel &= ~(1 << msb)
                # 嵌入資料位元
                channel |= (bit_stream.pop(0) << msb)
    return image
