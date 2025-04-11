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
        self.hider_ref = None
        self.last_seen_pos = None  
        # self.search_zones = self.create_search_zones()  
    
    def set_hider(self, hider):
        self.hider_ref = hider

    #def create_search_zones(self):
        # Create a grid of search zones with higher probability near the last known position of the Hider

    def think(self):
        hider_pos = self.hider_ref.position.to_grid_pos()
        seeker_pos = self.position.to_grid_pos()

        #Check if hider hasn't been set yet
        if not self.hider_ref:
            self.emit_thought("No hider to track.")
            return
        
        # End game if seeker reaches hider
        if self.position.to_grid_pos() == hider_pos:
            self.emit_thought("Seeker has caught the Hider! Game Over.")
            # end game

        if not self.grid.is_wall_between(seeker_pos, hider_pos):
        # if the Hider is in sight follow it 
            self.emit_thought(f"Hider seen at {hider_pos}!")
            self.last_seen_pos = hider_pos
            self.set_target(*hider_pos)

        else:
        # if there is no last seen position, wander randomly
            self.emit_thought("...")    
            while True:
                x = random.randint(0, self.grid.size - 1)
                y = random.randint(0, self.grid.size - 1)
                if self.set_target(x, y):
                    break

        # else:
        # # If the Hider is out of sight, but there is a last seen location
        #     self.emit_thought(f"Hider last seen at {self.last_seen_pos}!")
        #     self.search_nearby(self.last_seen_pos)

    # def search_nearby(self, last_seen_pos):
    #     best_prob = -1 
    #     best_pos = None
        
    #     # Search within a radius of 1 to 2 cells around the last known position
    #     for dx in [-1, 0, 1]:
    #         for dy in [-1, 0, 1]:
    #             x, y = last_seen_pos[0] + dx, last_seen_pos[1] + dy
    #             if 0 <= x < self.grid.size and 0 <= y < self.grid.size:
    #                 # Check if this position has the highest probability in the search zone grid
    #                 prob = self.search_zones[x][y]
    #                 if prob > best_prob:
    #                     best_prob = prob
    #                     best_pos = (x, y)

    #     if best_pos:
    #         self.emit_thought(f"Searching at {best_pos} with best probability!")
    #         self.set_target(*best_pos)

    def update(self, dt: float):
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
