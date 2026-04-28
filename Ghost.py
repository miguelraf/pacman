import pygame
from pygame.locals import *
from enum import Enum

# Cargamos las bibliotecas de OpenGL
from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *

import math
import os
import numpy as np
import pandas as pd
import random
import heapq
import copy

class Ghost:
    MAX_COOP_PENALTY = 4

    class Node:
        def __init__(self, ix, iy, cr, parent):
            self.idx_x = ix
            self.idx_y = iy
            self.corner = cr
            self.g = 0
            self.h = 0
            self.f = 0
            self.p = 0
            self.parent = parent

        def info(self, n):
            str = ""
            if n == 0:
                str = f"{(int(self.idx_x), int(self.idx_y), self.corner)}"
            elif n == 1:
                str = f"{(int(self.idx_x), int(self.idx_y), self.corner, self.g, self.h, self.f)}"
            elif n == 2:
                str = f"{(int(self.idx_x), int(self.idx_y), self.corner, self.g, self.h, self.f, self.pc_proximity, self.pc_prox_offset)}"

            return str

        def __eq__(self, other):
            if not isinstance(other, Ghost.Node):
                return NotImplemented
            return self.idx_x == other.idx_x and self.idx_y == other.idx_y
        
        def __hash__(self):
            return hash((self.idx_x, self.idx_y))
        
        def __lt__(self, other):
            if not isinstance(other, Ghost.Node):
                return NotImplemented
            return self.f < other.f
        
        def __le__(self, other):
            if not isinstance(other, Ghost.Node):
                return NotImplemented
            return self.f <= other.f
        
        def __gt__(self, other):
            if not isinstance(other, Ghost.Node):
                return NotImplemented
            return self.f > other.f
        
        def __ge__(self, other):
            if not isinstance(other, Ghost.Node):
                return NotImplemented
            return self.f >= other.f
        
    def __init__(self, mapa, mc, x_mc, y_mc, xmc, ymc, xini, yini, tipo): #xini y yini deben de ser coordenadas de un elemento >= 0 del MC

        #Mapeo de tipo de corner a direcciones permitidas
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

        #Mapeo de direcciones permitidas a valores de control para el delta
        self.directions = {
        0: (0, 1),   # abajo
        1: (1, 0),   # derecha
        2: (0, -1),  # arriba
        3: (-1, 0),  # izquierda
        4: (0, 0)    # stop
        }

        self.dir_ids = {v: k for k, v in self.directions.items()}

        #Matriz de control que almacena los IDs de las intersecciones
        self.MC = mc
        #Vectores que almacenan las coordenadas 
        self.XPxToMC = x_mc
        self.YPxToMC = y_mc

        #Listas de coordenadas clave
        self.xMC = xmc
        self.yMC = ymc
        #se resplanda el mapa en terminos de pixeles
        self.mapa = mapa

        #Variables de control
        self.x = xini
        self.y = yini
        self.size = 16
        self.mode = self.Mode.RANDOM
        self.roll = self.Roll.HELPER
        self.mode_counter = -5
        self.dir_id = random.choice(self.corners[self.MC[self.YPxToMC[int(self.y)]][self.XPxToMC[int(self.x)]]])
        self.speed = 1
        self.x_delta = 0
        self.y_delta = 0
        self.range = 10
        self.path = []
        # print(f"{tipo} {self.mode} {self.roll}")
    
    class Mode(Enum):
        RANDOM = 0
        CHASE = 1

    class Roll(Enum):
        LEADER = 0
        HELPER = 1
        
    def loadTextures(self, texturas, id):
        self.texturas = texturas
        self.Id = id

    def dynamic_mode(self, corner):
        # print(f"[][][] MODE COUNTER >>>>>> {self.mode_counter}")
        if self.mode_counter > 0:
            self.mode_counter -= 1
            if self.mode_counter == 0:
                self.mode = self.Mode.RANDOM
                self.mode_counter = random.randint(-8, -4)
        elif self.mode_counter < 0:
            self.mode_counter += 1
            if self.mode_counter == 0:
                self.mode = self.Mode.CHASE
                self.mode_counter = random.randint(10, 25)
    
    def dynamic_mode_coop(self, corner, partner):
        self.dynamic_mode(corner)
        partner.mode = self.mode

    def update_dir_random(self, corner):
        options = list(self.corners[corner])

        if self.dir_id < 2:
            reverse = self.dir_id + 2
        else:
            reverse = self.dir_id - 2

        if corner != 26 and corner != 27 and reverse in options:
            options.remove(reverse)
                
        self.dir_id = random.choice(options)

    def update_dir_seeker(self, pacmanXY, idx_1, idx_2, corner):
        if self.dir_id < 2:
            reverse = self.dir_id + 2
        else:
            reverse = self.dir_id - 2

        xo, yo = self.directions[reverse]
        # print("----- A Star Tree -----")
        next = self.astar(pacmanXY, 3, Ghost.Node(idx_1, idx_2, corner, Ghost.Node(idx_1 + xo, idx_2 + yo, self.MC[idx_2 + yo][idx_1 + xo], None)))
        dv = (next.idx_x - idx_1, next.idx_y - idx_2)
        self.dir_id = self.dir_ids[dv]

        # print(f"Next node: {next.info(0)}")

        # print("----- Tree end -----")

    def update_dir_coop_seeker(self, pacmanXY, idx_1, idx_2, corner, partner, safe_distance):
        if self.dir_id < 2:
            reverse = self.dir_id + 2
        else:
            reverse = self.dir_id - 2

        xo, yo = self.directions[reverse]
        # print("----- A Star Tree (COOP) -----")
        next = self.astar_coop(pacmanXY, 3, Ghost.Node(idx_1, idx_2, corner, Ghost.Node(idx_1 + xo, idx_2 + yo, self.MC[idx_2 + yo][idx_1 + xo], None)), partner, safe_distance)
        dv = (next.idx_x - idx_1, next.idx_y - idx_2)
        self.dir_id = self.dir_ids[dv]

        # print(f"Next node: {next.info(0)}")

        # print("----- Tree end (COOP) -----")

    def update_delta(self):
        dx, dy = self.directions[self.dir_id]

        self.x_delta = self.speed * dx
        self.y_delta = self.speed * dy
    
    def update_move(self):
        self.x += self.x_delta
        self.y += self.y_delta

    def get_neighbors(self, node):
        dirs = self.corners[node.corner]
        neighbors = []
        for d in dirs:
            xo, yo = self.directions[d]
            pn = Ghost.Node(node.idx_x + xo, node.idx_y + yo, self.MC[node.idx_y + yo][node.idx_x + xo], node)
            if node.corner != 27 and node.corner != 26 and pn == node.parent:
                continue
            neighbors.append(pn)
        return neighbors
    
    def ponder_neighbors(self, parent, neighbors, pcx, pcy):
        for neighbor in neighbors:
            parent_coord_x = self.xMC[parent.idx_x]
            parent_coord_y = self.yMC[parent.idx_y]
            neighbor_coord_x = self.xMC[neighbor.idx_x]
            neighbor_coord_y = self.yMC[neighbor.idx_y]
            neighbor.g = parent.g + abs(neighbor_coord_x - parent_coord_x) + abs(neighbor_coord_y - parent_coord_y)
            neighbor.h = abs(neighbor_coord_x - pcx) + abs(neighbor_coord_y - pcy)
            neighbor.f = neighbor.g + neighbor.h

    @staticmethod
    def inverse_linear_mapping(value, max_penalty, max_safe_distance):
        if max_safe_distance <= 0:
            return 0

        normalized_value = min(max(value / max_safe_distance, 0), 1)
        return max_penalty * (1 - normalized_value)

    def ponder_neighbors_coop( self, parent, neighbors, pcx, pcy, partner, step: int, safe_distance):
        for neighbor in neighbors:
            parent_coord_x = self.xMC[parent.idx_x]
            parent_coord_y = self.yMC[parent.idx_y]
            neighbor_coord_x = self.xMC[neighbor.idx_x]
            neighbor_coord_y = self.yMC[neighbor.idx_y]

            if 2 + step <= len(partner.path):
                partner_x_at_step = self.xMC[partner.path[len(partner.path) - (2 + step)].idx_x]
                partner_y_at_step = self.yMC[partner.path[len(partner.path) - (2 + step)].idx_y]
            else:
                partner_x_at_step = 1000
                partner_y_at_step = 1000

            distance_to_partner = math.sqrt(math.pow((neighbor_coord_x - partner_x_at_step), 2) + math.pow((neighbor_coord_y - partner_y_at_step), 2))
            penalty = self.inverse_linear_mapping(distance_to_partner, self.MAX_COOP_PENALTY, safe_distance)

            neighbor.g = parent.g + abs(neighbor_coord_x - parent_coord_x) + abs(neighbor_coord_y - parent_coord_y)
            neighbor.h = abs(neighbor_coord_x - pcx) + abs(neighbor_coord_y - pcy)
            neighbor.p = (safe_distance - distance_to_partner) * penalty
            neighbor.f = neighbor.g + neighbor.p + neighbor.h


    def evaluate_node(self, pcx, pcy, open_heap: list, closed: list):
        current = heapq.heappop(open_heap)
        neighbors = self.get_neighbors(current)

        self.ponder_neighbors(current, neighbors, pcx, pcy)
        for n in neighbors:
            heapq.heappush(open_heap, n)

        dist = 1000
        if open_heap:
            p = open_heap[0]
            best_coord_x = self.xMC[p.idx_x]
            best_coord_y = self.yMC[p.idx_y]

            dist = math.sqrt(math.pow((pcx - best_coord_x), 2) + math.pow((pcy - best_coord_y), 2))

        closed.append(current)

        finished = False

        if dist < self.range:
            finished = True

        # print("Node: " + current.info(0))
        str = "Childs: "

        for n in neighbors:
            str = str + " | " + n.info(0)

        str2 = "Open: "
        for n in open_heap:
            str2 = str2 + " | " + n.info(0)
        
        str3 = "Closed: "
        for n in closed:
            str3 = str3 + " | " + n.info(0)

        # print(str)
        # print(str2)
        # print(str3)

        return finished
    
    def evaluate_node_coop(self, pcx, pcy, open_heap: list, closed: list, partner, step, safe_distance):
        current = heapq.heappop(open_heap)
        neighbors = self.get_neighbors(current)

        self.ponder_neighbors_coop(current, neighbors, pcx, pcy, partner, step, safe_distance)
        for n in neighbors:
            heapq.heappush(open_heap, n)

        dist = 1000
        if open_heap:
            p = open_heap[0]
            best_coord_x = self.xMC[p.idx_x]
            best_coord_y = self.yMC[p.idx_y]

            dist = math.sqrt(math.pow((pcx - best_coord_x), 2) + math.pow((pcy - best_coord_y), 2))

        closed.append(current)

        finished = False

        if dist < self.range:
            finished = True

        # print("Node: " + current.info(0))
        str = "Childs: "

        for n in neighbors:
            str = str + " | " + n.info(0)

        str2 = "Open: "
        for n in open_heap:
            str2 = str2 + " | " + n.info(0)
        
        str3 = "Closed: "
        for n in closed:
            str3 = str3 + " | " + n.info(0)

        # print(str)
        # print(str2)
        # print(str3)

        return finished

    
    def get_next(self, node, n0):
        self.path = []
        recall = node
        str = f"Reconstrtuction from {node.info(0)} to {n0.info(0)}: {node.info(0)}"
        self.path.append(node)
        while recall.parent != n0:
            recall = recall.parent
            self.path.append(recall)
            str = str + " -> " + recall.info(0)

        self.path.append(n0)

        # str2 = "Resulting Path: "
        # for n in self.path:
        #     str2 = str2 + " -> " + n.info(0)
        
        # print(str)
        # print(str2)
        return self.path[len(self.path) - 2]

    def astar(self, pacmanXY, depth, n0):
        pcx, pcy = pacmanXY
        open_heap = [n0]
        closed = []

        # print(f"Initial Node: {n0.info(0)}")

        while depth > 0 and open_heap:
            if self.evaluate_node(pcx, pcy, open_heap, closed):
                break
            depth -= 1

        return self.get_next(heapq.heappop(open_heap), n0)
    
    def astar_coop(self, pacmanXY, depth, n0, partner, safe_distance):
        pcx, pcy = pacmanXY
        open_heap = [n0]
        closed = []

        # print(f"Initial Node: {n0.info(0)}")
        step = 0
        while depth > 0 and open_heap:
            if self.evaluate_node_coop(pcx, pcy, open_heap, closed, partner, step, safe_distance):
                break
            step += 1
            depth -= 1

        return self.get_next(heapq.heappop(open_heap), n0)
    
    def change_roll(self, corner, partner, pacmanXY):
        pcx, pcy = pacmanXY
        if corner >= 0:
            dist_self = math.sqrt(math.pow((pcx - self.x), 2) + math.pow((pcy - self.y), 2))
            dist_partner = math.sqrt(math.pow((pcx - partner.x), 2) + math.pow((pcy - partner.y), 2))
            if dist_self < dist_partner:
                self.roll = self.Roll.LEADER
                partner.roll = self.Roll.HELPER
            else:
                self.roll = self.Roll.HELPER
                partner.roll = self.Roll.LEADER
    
    def test_astar(self, pacmanXY):
        idx_1 = self.XPxToMC[int(self.x)]
        idx_2 = self.YPxToMC[int(self.y)]
        corner = self.MC[idx_2][idx_1]

        if corner >= 0:
            if self.dir_id < 2:
                reverse = self.dir_id + 2
            else:
                reverse = self.dir_id - 2

            xo, yo = self.directions[reverse]
            next = self.astar(pacmanXY, 3, Ghost.Node(idx_1, idx_2, corner, Ghost.Node(idx_1 + xo, idx_2 + yo, self.MC[idx_2 + yo][idx_1 + xo], None)))

    def update(self):
        idx_1 = self.XPxToMC[int(self.x)]
        idx_2 = self.YPxToMC[int(self.y)]
        corner = self.MC[idx_2][idx_1]

        if corner >= 0:
            self.update_dir_random(corner)
            self.update_delta()
        
        self.update_move()

    def update2(self, pacmanXY):
        idx_1 = self.XPxToMC[int(self.x)]
        idx_2 = self.YPxToMC[int(self.y)]
        corner = self.MC[idx_2][idx_1]

        if corner >= 0:

            self.dynamic_mode(corner)

            if self.mode == self.Mode.CHASE:
                self.update_dir_seeker(pacmanXY, idx_1, idx_2, corner)
            elif self.mode == self.Mode.RANDOM:
                self.update_dir_random(corner)

            self.update_delta()

        self.update_move()

    def update3(self, pacmanXY, partner, master: bool, safe_distance): # master should be True for the Ghost that will handle the control variables and False for the other Ghost
        idx_1 = self.XPxToMC[int(self.x)]
        idx_2 = self.YPxToMC[int(self.y)]
        corner = self.MC[idx_2][idx_1]

        if corner >= 0:
            if master:
                self.dynamic_mode_coop(corner, partner)
                self.change_roll(corner, partner, pacmanXY)

            if self.mode == self.Mode.CHASE:
                if self.roll == self.Roll.LEADER:
                    self.update_dir_seeker(pacmanXY, idx_1, idx_2, corner)
                elif self.roll == self.Roll.HELPER:
                    self.update_dir_coop_seeker(pacmanXY, idx_1, idx_2, corner, partner, safe_distance)
            elif self.mode == self.Mode.RANDOM:
                self.update_dir_random(corner)

            
            # print(f"Master?: {master} || Mode: {"RANDOM" if self.mode == self.Mode.RANDOM else "CHASE"} || ROL: {"LEADER" if self.roll == self.Roll.LEADER else "HELPER"}")


        self.update_delta()
        self.update_move()

        
    def draw(self):
        glEnable(GL_TEXTURE_2D)
        glBindTexture(GL_TEXTURE_2D, self.texturas[self.Id])

        glPushMatrix()

        glTranslatef(14, 11, 0)

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
 
