import random
import pygame
from constants import *
from core.npc import Npc
from core.pathfinder import Pathfinder
from models.grid import Grid
from models.vector import Vector2

class Seeker(Npc):
    # How many seconds to stay frozen when freeze() is called.
    # This is how much time the hider has to run away at the start
    # of a new round.
    FREEZE_TIME = 5.0
    STINK_INTERVAL = 0.5 # every X seconds
    def __init__(self, grid: Grid, pathfinder: Pathfinder, color: pygame.Color, can_think: bool):
        super().__init__(grid, pathfinder, color, can_think)
        self.auto_move = True
        self.hider_ref = None
        self.last_seen_time = 0  # Last time the Hider was seen
        self.tile_memory = {
            (x, y): 0
            for x in range(self.grid.size)
            for y in range(self.grid.size)
            if not self.grid.get_node(x, y).is_wall # when user draws tiles, tile_memory can end up having wall nodes in it, which is bad. need a tile_memory_refresh function to recalculate this.
        }
        self.start_position = self.position
        self.stink_timer = 0
        self.freeze_timer = self.FREEZE_TIME

    def freeze(self):
        self.freeze_timer = self.FREEZE_TIME

    def is_frozen(self):
        return self.freeze_timer > 0

    def set_hider(self, hider):
        self.hider_ref = hider

    def refresh_tile_memory(self):
        """Refresh the tile memory to exclude wall nodes."""
        self.tile_memory = {
            (x, y): 0
            for x in range(self.grid.size)
            for y in range(self.grid.size)
            if not self.grid.get_node(x, y).is_wall
        }

    def think(self):
        if self.is_frozen():
            self.emit_thought(f"Frozen ({round(self.freeze_timer, 1)}s)")
            return
        if not self.hider_ref:
            self.emit_thought("No hider to track.")
            return

        # Refresh tile memory if tiles have changed
        if self.grid.tiles_changed:  # Assuming `tiles_changed` is a flag set when tiles are modified
            self.refresh_tile_memory()
            self.grid.tiles_changed = False

        hider_pos = self.hider_ref.position.to_grid_pos()
        seeker_pos = self.position.to_grid_pos()

        if not self.grid.is_wall_between(seeker_pos, hider_pos):
            # If the Hider is in sight, follow it
            self.emit_thought(f"Hider seen at {hider_pos}!")
            self.last_seen_time = pygame.time.get_ticks() / 1000
            self.set_target(*hider_pos)
            return
            
        current_time = pygame.time.get_ticks() / 1000  # Get current time in seconds
        time_since_seen = current_time - self.last_seen_time

        if time_since_seen < 3 and self.grid.is_wall_between(seeker_pos, hider_pos):
            # If the Seeker loses sight, predict the Hider's next position based on direction
            predicted_pos = self.predict_hider_position(hider_pos)
            self.emit_thought(f"Hider escaped sight, he might be here!")
            self.set_target(*predicted_pos)
            return

        else:
            # Update tile memory
            visible_tiles = self.grid.get_visible_tiles(seeker_pos)
            for pos in self.tile_memory:
                if pos in visible_tiles:
                    self.tile_memory[pos] = 0
                else:
                    self.tile_memory[pos] += 1

            # Check if Seeker can find a target tile (unexplored or unexplored recently)
            target = self.find_best_target()

            if target:
                self.emit_thought(f"Exploring unexplored area: {target}")
                target_node = self.grid.get_node(*target)
                #print(f"Target node at {target} is a wall: {target_node.is_wall}")
                self.set_target(*target)
            else:
                # Log the issue if no target was found
                self.emit_thought("No target found, wandering randomly.")
                # Fallback to random wandering if no target is found
                for _ in range(50):  # Try up to 50 times to find a walkable random tile
                    x = random.randint(0, self.grid.size - 1)
                    y = random.randint(0, self.grid.size - 1)
                    if self.set_target(x, y):
                        break

    def find_best_target(self):
        unexplored_tiles = [(x, y) for (x, y), time in self.tile_memory.items() if time > 5] 
        if unexplored_tiles:
            self.emit_thought(f"Unexplored tiles: {unexplored_tiles}")
            return max(unexplored_tiles, key=lambda pos: self.tile_memory[pos])
        self.emit_thought("No unexplored tiles found!")
        return None


    def predict_hider_position(self, last_pos):
        # Search around the last seen position 
        radius = 5 
        random.shuffle(DIRECTIONS := [(dx, dy) for dx in range(-radius, radius + 1)
                                                for dy in range(-radius, radius + 1)
                                                if (dx != 0 or dy != 0)])
        for dx, dy in DIRECTIONS:
            x = last_pos[0] + dx
            y = last_pos[1] + dy
            if 0 <= x < self.grid.size and 0 <= y < self.grid.size:
                node = self.grid.get_node(x, y)
                if node and not node.is_wall:
                    return (x, y)
        return last_pos

    def update(self, dt: float):
        self.stink_timer += dt
        self.freeze_timer -= dt
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
                # Stop at the Hider's position if Seeker reaches it
                if (int(new_x), int(new_y)) == self.target:
                    self.position = Vector2(int(new_x), int(new_y))
                    self.emit_thought("Reached target!")
                    self.check_game_over()  # Check if Seeker has caught the Hider
                else:
                    # Otherwise, keep moving
                    self.position = Vector2(new_x, new_y)