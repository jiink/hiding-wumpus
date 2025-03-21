import pygame
from constants import *
from core.npc import Npc
from core.pathfinder import Pathfinder
from models.grid import Grid
from models.vector import Vector2  

   
class Seeker(Npc):
    # This function runs periodically. This is where the algorithm should
    # figure out where to go. See the parent class to see what's available.

    THINK_INTERVAL = 1.0 # This npc will think every X seconds
    THOUGHT_DURATION = 0.5 # how long does thought-text appear for? (in sec)

    def __init__(self, grid: Grid, pathfinder: Pathfinder, color: pygame.Color, can_think: bool):
        self.grid = grid
        self.pathfinder = pathfinder
        # Position is in world coords. like cell coords, but float.
        self.position = Vector2(grid.size // 2, grid.size // 2)
        self.target = None
        self.path = [] # the list of positions this npc is travelling right now 
        self.current_path_index = 0 # current position it's going towards
        self.speed = 4.0
        self.color = color
        self.can_think = can_think
        self.think_timer = 0
        self.thought_text = None
        self.thought_timer = 0

    def set_speed(self, speed: float):
        self.speed = speed

    # If a node is at the given grid coordinates, the NPC will start pursuing
    # it.
    # Returns true if successful, false if the target could not be set.
    def set_target(self, x: int, y: int):
        if not self.grid.is_valid_position(x, y):
            return False
        node = self.grid.get_node(x, y)
        if node and not node.is_wall:
            self.target = Vector2(x, y)
            self.update_path()
            return True
        else:
            return False

    # NPCs come up with a target in this function.
    def think(self):
        raise NotImplementedError("Inherit this class and override this think() function!")

    # Assuming there's a valid target, finds a path to that target.
    # Returns true if it's working, false if it doesn't.
    def update_path(self):
        if not self.target:
            self.path = []
            self.current_path_index = 0
            return
        # round the pos to a cell coordinate
        start_pos = self.position.to_grid_pos()
        target_pos = self.target.to_tuple()
        path_nodes = self.pathfinder.find_path(start_pos, target_pos)
        # nodes to world coordinates (+0.5 offset gets you the center of the tile,
        # as each tile is 1 unit wide and tall).
        self.path = [Vector2(node.x + 0.5, node.y + 0.5) for node in path_nodes]
        if self.path:
            # Start walking from the beginning of the new path. 
            self.current_path_index = 0 
            return True
        else:
            return False

    # Every frame, this Seeker will move along its path smoothly from 
    # one point to the other.
    # `dt` means delta time, the amount of time passed since the last
    # frame. This is for framerate-independent motion.
    def update(self, dt: float):
        keys = pygame.key.get_pressed()
        # Check if any of the movement keys (WASD or Arrow keys) are pressed
        if keys[pygame.K_w] or keys[pygame.K_s] or keys[pygame.K_a] or keys[pygame.K_d] or \
            keys[pygame.K_UP] or keys[pygame.K_DOWN] or keys[pygame.K_LEFT] or keys[pygame.K_RIGHT]:
            self.manual_move(keys)
        if self.can_think:
            # "Think" periodically
            self.think_timer += dt
            if self.think_timer >= self.THINK_INTERVAL:
                self.think()
                self.think_timer = 0.0

        # Update thought timer
        if self.thought_text:
            self.thought_timer += dt
            if self.thought_timer >= self.THOUGHT_DURATION:
                self.thought_text = None
                self.thought_timer = 0

        # do nothing if there's no path to travel.
        if not self.path or self.current_path_index >= len(self.path):
            return
        target_pos = self.path[self.current_path_index]
        diff = target_pos - self.position
        dir = diff.normalized()
        dist = diff.length()
        # if roughly arrived at target_pos
        if dist < 0.1:
            self.current_path_index += 1
            if self.current_path_index >= len(self.path):
                return # I've arrived at the end of the path
            target_pos = self.path[self.current_path_index]
            # recalculate direction and distance and keep going
            diff = target_pos - self.position
            dir = diff.normalized()
            dist = diff.length()
        if dist > 0:
            # how far to move this frame
            move_dist = min(self.speed * dt, dist)
            self.position = self.position + dir * move_dist

    # instead of doing print statements, it's cool to call
    # this which causes the string to appear over the npc's head
    # for a bit then fade away
    def emit_thought(self, text: str):
        print(text)
        self.thought_text = text
        self.thought_timer = 0

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
        y = self.position.y  # 
        if x < GRID_SIZE - 1:  
            self.position = Vector2(x + 1, y)  

    def draw(self, screen):
        x = int(self.position.x)  
        y = int(self.position.y)
        center = self.grid.grid_to_screen(x, y)

        center_x = center[0] + self.grid.tile_size // 2
        center_y = center[1] + self.grid.tile_size // 2

        # Draw the circle at the center of the grid square
        seeker_color = SEEKER_COLOR
        pygame.draw.circle(screen, seeker_color, (center_x, center_y), self.grid.tile_size * 0.4)

