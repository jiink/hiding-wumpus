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
        if self.auto_move:
            super().update(dt) 
        else:
            keys = pygame.key.get_pressed()
            # Handle manual movement if any movement keys are pressed
            if not self.auto_move and any(keys[key] for key in [pygame.K_w, pygame.K_s, pygame.K_a, pygame.K_d, 
                                        pygame.K_UP, pygame.K_DOWN, pygame.K_LEFT, pygame.K_RIGHT]):
                self.last_key_time = 0.0 
                self.manual_move(keys)
                

    def manual_move(self, keys):
        # Manual movement using WASD or Arrow keys.
        directions = {
            pygame.K_w: (0, -1),
            pygame.K_s: (0, 1),
            pygame.K_a: (-1, 0),
            pygame.K_d: (1, 0)
        }
        for key, (dx, dy) in directions.items():
            if keys[key]:
                self.move(dx, dy)

    def move(self, dx, dy):
        x, y = self.position.x, self.position.y
        new_x, new_y = x + dx, y + dy
        if 0 <= new_x < self.grid.size and 0 <= new_y < self.grid.size:
            node = self.grid.get_node(int(new_x), int(new_y))
            if node and not node.is_wall:
                self.position = Vector2(new_x, new_y)
