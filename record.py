import pygame
import sys
import pygame.camera
from pygame.locals import *
import tensorflow as tf
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing import image
import cv2
import numpy as np
# Load the model
model = load_model('model.h5')


pygame.init()
pygame.camera.init()

screen = pygame.display.set_mode((640, 480))

cam = pygame.camera.Camera("/dev/video0", (640, 480))
cam.start()

while True:
    image = cam.get_image()
    screen.blit(image, (0, 0))
    pygame.display.update()
    
    # Convert the image to a numpy array
    frame = pygame.surfarray.array3d(image)
    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    frame = cv2.rotate(frame, cv2.ROTATE_90_COUNTERCLOCKWISE)
    frame = cv2.resize(frame, (64, 64))
    frame = np.expand_dims(frame, axis=0)
    frame = frame/255.0
    # Predict the sign
    result = model.predict(frame)
 
    # Get the sign
    indx = np.argmax(result[0])
    chars = "ABCDEFGHIKLMNOPQRSTUVWXYZ"
    print(indx)
    print(chars[indx])
    

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            # save as video output
            sys.exit()
