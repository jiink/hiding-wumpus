import random
import pygame
from constants import *
from core.npc import Npc
from core.pathfinder import Pathfinder
from models.grid import Grid
from models.vector import Vector2  

class Seeker(Npc):
    THINK_INTERVAL = 2.0 
    MOVEMENT_SPEED = 1
    def __init__(self, grid: Grid, pathfinder: Pathfinder, color: pygame.Color, can_think: bool):
        super().__init__(grid, pathfinder, color, can_think)
        
    def think(self):
        self.emit_thought("thinking...")
        # Random spot selection with a retry limit to avoid infinite loops
        retries = 5
        for _ in range(retries):
            x = random.randint(0, self.grid.size - 1)
            y = random.randint(0, self.grid.size - 1)
            if self.set_target(x, y):
                break

    def update(self, dt: float):
        keys = pygame.key.get_pressed()
        # Handle manual movement if any movement keys are pressed
        if any(keys[key] for key in [pygame.K_w, pygame.K_s, pygame.K_a, pygame.K_d, 
                                     pygame.K_UP, pygame.K_DOWN, pygame.K_LEFT, pygame.K_RIGHT]):
            self.last_key_time = 0.0 
            self.manual_move(keys)
        else:
            if self.target:
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
        x = self.position.x  
        y = self.position.y  
        if y > 0:  
            self.position = Vector2(x, y - 1)

    def move_down(self):
        x = self.position.x  
        y = self.position.y  
        if y < GRID_SIZE - 1:  
            self.position = Vector2(x, y + 1)

    def move_left(self):
        x = self.position.x  
        y = self.position.y  
        if x > 0:  
            self.position = Vector2(x - 1, y)

    def move_right(self):
        x = self.position.x  
        y = self.position.y
        if x < GRID_SIZE - 1:  
            self.position = Vector2(x + 1, y)