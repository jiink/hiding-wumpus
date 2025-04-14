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
        # dictionary that keeps track of the "memory" of each tile on the grid. 
        self.tile_memory = {
            (x, y): 0
            for x in range(self.grid.size)
            for y in range(self.grid.size)
            if not self.grid.get_node(x, y).is_wall
        }
        self.game_over = False 
        self.start_position = self.position
        self.is_game_started = False 

    def set_hider(self, hider):
        self.hider_ref = hider

    def end_game(self):
        self.game_over = True 
        self.emit_thought("Game Over! Seeker has caught the Hider!")

    def think(self):
        if not self.hider_ref:
            self.emit_thought("No hider to track.")
            return

        hider_pos = self.hider_ref.position.to_grid_pos()
        seeker_pos = self.position.to_grid_pos()

        # Skip the game over check during the first frame
        if not self.is_game_started:
            self.is_game_started = True 
            return
        
        # Check if Seeker has caught the Hider
        if seeker_pos == hider_pos:
            self.end_game()  # End the game when the Seeker catches the Hider
            self.emit_thought("Seeker has caught the Hider!")
            return

        if not self.grid.is_wall_between(seeker_pos, hider_pos):
            # If the Hider is in sight, follow it
            self.emit_thought(f"Hider seen at {hider_pos}!")
            self.last_seen_pos = hider_pos
            self.set_target(*hider_pos)

        else:
            # Update tile memory
            visible_tiles = self.grid.get_visible_tiles(seeker_pos)
            for pos in self.tile_memory:
                if pos in visible_tiles:
                    self.tile_memory[pos] = 0
                else:
                    self.tile_memory[pos] += 1

            # Filter reachable tiles
            reachable = [pos for pos in self.tile_memory if self.set_target(*pos)]
            
            if reachable:
                # Find the tile that has gone unseen for the longest
                target = max(reachable, key=lambda pos: self.tile_memory[pos])
                self.emit_thought(f"Wandering to {target}, unseen for {self.tile_memory[target]} frames.")
                self.set_target(*target)
            else:
                # Fallback to random wandering
                self.emit_thought("Fallback: Wandering randomly.")
                for _ in range(50):  # try up to 50 times to find a walkable random tile
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
                # Stop at the Hider's position if Seeker reaches it
                if (int(new_x), int(new_y)) == self.target:
                    self.position = Vector2(int(new_x), int(new_y))
                    self.emit_thought("Reached target!")
                    self.check_game_over()  # Check if Seeker has caught the Hider
                else:
                    # Otherwise, keep moving
                    self.position = Vector2(new_x, new_y)


    def check_game_over(self):
        # Check if the Seeker has caught the Hider (game over condition)
        if self.position == self.hider_ref.position:
            self.end_game()  # End the game when the Seeker catches the Hider
            self.emit_thought("Seeker has caught the Hider!")
