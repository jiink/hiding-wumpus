import random
import pygame
from constants import *
from core.npc import Npc
from core.pathfinder import Pathfinder
from models.grid import Grid
from models.vector import Vector2  

class Seeker(Npc):
    def __init__(self, grid: Grid, pathfinder: Pathfinder, color: pygame.Color, can_think: bool):
        super().__init__(grid, pathfinder, color, can_think)
        self.auto_move = True
        
    def think(self):
        self.emit_thought("thinking...")
        # Random spot selection with a retry limit to avoid infinite loops
        while True:
            x = random.randint(0, self.grid.size - 1)
            y = random.randint(0, self.grid.size - 1)
            if self.set_target(x, y):
                break

    def update(self, dt: float):
        keys = pygame.key.get_pressed()
        # Handle manual movement if any movement keys are pressed
        if any(keys[key] for key in [pygame.K_w, pygame.K_s, pygame.K_a, pygame.K_d, 
                                     pygame.K_UP, pygame.K_DOWN, pygame.K_LEFT, pygame.K_RIGHT]):
            self.auto_move = False
            self.last_key_time = 0.0 
            self.manual_move(keys)
        else:
            if self.target and self.auto_move:
                super().update(dt)  

        # Think periodically
        self.think_timer += dt
        if self.think_timer >= self.THINK_INTERVAL:
            self.think()
            self.think_timer = 0.0

    def manual_move(self, keys):
        # manual movement using WASD or Arrow keys.
        if keys[pygame.K_w]:
            self.move_up()
        if keys[pygame.K_s]:
            self.move_down()
        if keys[pygame.K_a]:
            self.move_left()
        if keys[pygame.K_d]:
            self.move_right()

    def move_up(self):
        x, y = self.position.x, self.position.y
        if y > 0:
            node = self.grid.get_node(int(x), int(y - 1)) 
            if node and not node.is_wall: 
                self.position = Vector2(x, y - 1)

    def move_down(self):
        x, y = self.position.x, self.position.y
        if y < self.grid.size - 1:
            node = self.grid.get_node(int(x), int(y + 1)) 
            if node and not node.is_wall: 
                self.position = Vector2(x, y + 1)

    def move_left(self):
        x, y = self.position.x, self.position.y
        if x > 0:
            node = self.grid.get_node(int(x - 1), int(y)) 
            if node and not node.is_wall: 
                self.position = Vector2(x - 1, y)

    def move_right(self):
        x, y = self.position.x, self.position.y
        if x < self.grid.size - 1:
            node = self.grid.get_node(int(x + 1), int(y)) 
            if node and not node.is_wall: 
                self.position = Vector2(x + 1, y)