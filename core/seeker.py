import random
import pygame
from constants import *
from core.npc import Npc
from core.pathfinder import Pathfinder
from models.grid import Grid
from models.vector import Vector2  

class Seeker(Npc):
    STINK_INTERVAL = 0.5 # every X seconds
    def __init__(self, grid: Grid, pathfinder: Pathfinder, color: pygame.Color, can_think: bool):
        super().__init__(grid, pathfinder, color, can_think)
        self.auto_move = True
        self.stink_timer = 0
        
    def think(self):
        self.emit_thought("thinking...")
        # Random spot selection with a retry limit to avoid infinite loops
        while True:
            x = random.randint(0, self.grid.size - 1)
            y = random.randint(0, self.grid.size - 1)
            if self.set_target(x, y):
                break

    def update(self, dt: float):
        self.stink_timer += dt
        if self.stink_timer >= self.STINK_INTERVAL:
            self.stink_timer = 0.0
            self.grid.stink_it(*self.position.to_grid_pos(), radius=8)
        if self.auto_move:
            super().update(dt) 
        else:
            keys = pygame.key.get_pressed()
            # Handle manual movement if any movement keys are pressed
            if not self.auto_move and any(keys[key] for key in [pygame.K_w, pygame.K_s, pygame.K_a, pygame.K_d, 
                                        pygame.K_UP, pygame.K_DOWN, pygame.K_LEFT, pygame.K_RIGHT]):
                self.last_key_time = 0.0 
                self.manual_move(keys, dt)
                

    def manual_move(self, keys, dt):
        # Manual movement using WASD or Arrow keys.
        directions = {
            pygame.K_w: (0, -1),
            pygame.K_s: (0, 1),
            pygame.K_a: (-1, 0),
            pygame.K_d: (1, 0)
        }
        for key, (dx, dy) in directions.items():
            if keys[key]:
                self.move(dx, dy, dt)

    def move(self, dx, dy, dt):
        # Normalize it so going diagonal isn't faster
        magnitude = (dx**2 + dy**2)**0.5
        if magnitude > 0:
            dx /= magnitude
            dy /= magnitude
        dx *= self.speed * dt
        dy *= self.speed * dt
        new_x = self.position.x + dx
        new_y = self.position.y + dy
        # Check boundaries and obstacles
        if 0 <= new_x < self.grid.size and 0 <= new_y < self.grid.size:
            node = self.grid.get_node(int(new_x), int(new_y))
            if node and not node.is_wall:
                self.position = Vector2(new_x, new_y)
