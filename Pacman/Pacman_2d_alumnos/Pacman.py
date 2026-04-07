import pygame
from pygame.locals import *

# Cargamos las bibliotecas de OpenGL
from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *

import math
import os
import numpy as np
import pandas as pd

class Pacman:
    def __init__(self, mapa, mc, x_mc, y_mc):
        self.MC = mc
        self.XPxToMC = x_mc
        self.YPxToMC = y_mc
        self.mapa = mapa
        
        # Posición inicial
        self.x = 15
        self.y = 15
        self.size = 15
        self.dir_id = 1 
        self.speed = 1
        
        self.directions = {
        0: (0, 1),   # abajo
        1: (1, 0),   # derecha
        2: (0, -1),  # arriba
        3: (-1, 0)   # izquierda
        }

    def loadTextures(self, texturas, id):
        self.texturas = texturas
        self.Id = id

    def update(self, keys):

        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            self.dir_id = 0
        elif (keys[pygame.K_RIGHT] or keys[pygame.K_d]):
            self.dir_id = 1
        elif keys[pygame.K_UP] or keys[pygame.K_w]:
            self.dir_id = 2
        elif keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.dir_id = 3

        self.move()
        
    def move(self):
        dx, dy = self.directions[self.dir_id]

        self.x += dx * self.speed
        self.y += dy * self.speed

    def draw(self):
        glEnable(GL_TEXTURE_2D)
        glBindTexture(GL_TEXTURE_2D, self.texturas[self.Id])

        glBegin(GL_QUADS)
        glTexCoord2f(0, 0)
        glVertex2f(self.x, self.y)

        glTexCoord2f(1, 0)
        glVertex2f(self.x + self.size, self.y)

        glTexCoord2f(1, 1)
        glVertex2f(self.x + self.size, self.y + self.size)

        glTexCoord2f(0, 1)
        glVertex2f(self.x, self.y + self.size)
        glEnd()

        glDisable(GL_TEXTURE_2D)