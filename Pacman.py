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
        # self.mapa = mapa
        
        # Posición inicial
        self.x = 71
        self.y = 0
        self.size = 16
        self.angle = 0
        self.rotation_axis_x = 0
        self.rotation_axis_y = 0
        self.rotation_axis_z = 0
        self.dir_id = 4
        self.future_dir_id = 4
        self.speed = 1

        self.x_delta = 0
        self.y_delta = 0
        
        self.directions = {
        0: (0, 1),   # abajo
        1: (1, 0),   # derecha
        2: (0, -1),  # arriba
        3: (-1, 0),  # izquierda
        4: (0, 0)    # stop
        }

        self.corners = {
            0: (1, 3),
            1: (0, 2),
            10: (0, 1),
            21: (0, 1, 3),
            11: (0, 3),
            12: (1, 2),
            13: (2, 3),
            22: (0, 2, 3),
            23: (1, 2, 3),
            24: (0, 1, 2),
            25: (0, 1, 2, 3),
            26: (1,),
            27: (3,)
        }

        self.angles = [(0, 0, 1, 90), (0, 0, 1, 0), (0, 0, 1, -90), (0, 1, 0, 180)]

    def loadTextures(self, texturas, id):
        self.texturas = texturas
        self.Id = id

    def update_dir(self, key):
        if (key == pygame.K_DOWN or key == pygame.K_s):
            self.future_dir_id = 0
        elif (key == pygame.K_RIGHT or key == pygame.K_d):
            self.future_dir_id = 1
        elif (key == pygame.K_UP or key == pygame.K_w):
            self.future_dir_id = 2
        elif (key == pygame.K_LEFT or key == pygame.K_a):
            self.future_dir_id = 3

    def validate_dir(self):
        idx_1 = self.XPxToMC[int(self.x)]
        idx_2 = self.YPxToMC[int(self.y)]
        corner = self.MC[idx_2][idx_1]
        # print(corner)
        
        if corner < 0:
            if (self.dir_id == 0 and self.future_dir_id == 2) or (self.dir_id == 2 and self.future_dir_id == 0):
                self.dir_id = self.future_dir_id
            elif (self.dir_id == 1 and self.future_dir_id == 3) or (self.dir_id == 3 and self.future_dir_id == 1):
                self.dir_id = self.future_dir_id
        
        else:
            if self.future_dir_id in self.corners[corner]:
                self.dir_id = self.future_dir_id
            elif not (self.dir_id in self.corners[corner]):
                self.dir_id = 4
                self.future_dir_id = 4
        

    def update_delta(self):
        dx, dy = self.directions[self.dir_id]

        self.x_delta = self.speed * dx
        self.y_delta = self.speed * dy

    def update_angle(self):
        if self.dir_id != 4:
            self.rotation_axis_x, self.rotation_axis_y, self.rotation_axis_z, self.angle = self.angles[self.dir_id]
        self.cx = self.x + self.size/2
        self.cy = self.y + self.size/2

    def update_move(self):
        self.x += self.x_delta
        self.y += self.y_delta

    def update(self):
        self.validate_dir()
        self.update_delta()
        self.update_angle()
        self.update_move()

    def draw(self):
        glEnable(GL_TEXTURE_2D)
        glBindTexture(GL_TEXTURE_2D, self.texturas[self.Id])

        glPushMatrix()

        glTranslatef(14, 11, 0)

        glTranslatef(self.cx, self.cy, 0)   # 1. Move to rotation center
        glRotatef(self.angle, self.rotation_axis_x, self.rotation_axis_y, self.rotation_axis_z) # 2. Rotate (Z axis for 2D)
        glTranslatef(-self.cx, -self.cy, 0) # 3. Move back

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

        glPopMatrix()

        glDisable(GL_TEXTURE_2D)