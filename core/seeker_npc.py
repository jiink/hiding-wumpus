import pygame
from core.pathfinder import Pathfinder
from models.grid import Grid
from models.vector import Vector2
from constants import *

# This NPC lives on a grid and pursues the target via its pathfinder.
class SeekerNPC:
    def __init__(self, grid: Grid, pathfinder: Pathfinder):
        self.grid = grid
        self.pathfinder = pathfinder
        # Position is in world coords. like cell coords, but float.
        self.position = Vector2(grid.size // 2, grid.size // 2)
        self.target = None
        self.path = [] # the list of positions this npc is travelling right now 
        self.current_path_index = 0 # current position it's going towards
        self.speed = 4.0
    
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
        # Find the best starting point in the path
        # TODO: a lot of this logic might not be necessary and 
        # current_path_index could just be 0? try that.
        if self.path:
            best_dist = 9999999
            best_index = 0
            for i, pos in enumerate(self.path):
                dist = self.position.distance_to(pos)
                if dist < best_dist:
                    best_dist = dist
                    best_index = i
            self.current_path_index = best_index
            return True
        else:
            return False
    
    # Every frame, this NPC will move along its path smoothly from 
    # one point to the other.
    # `dt` means delta time, the amount of time passed since the last
    # frame. This is for framerate-independent motion.
    def update(self, dt: float):
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
    
    def draw(self, surface: pygame.Surface):
        pygame.draw.circle(
            surface, SEEKER_COLOR,
            center = self.grid.grid_to_screen(self.position.x, self.position.y),
            radius = self.grid.tile_size * 0.4
        )
        # the target it's going towards
        if self.target:
            x, y = self.grid.grid_to_screen(self.target.x + 0.5, self.target.y + 0.5)
            size = self.grid.tile_size * 0.4
            # X shape
            pygame.draw.line(surface, TARGET_COLOR, 
                             (x - size, y - size), 
                             (x + size, y + size), 
                             width=3)
            pygame.draw.line(surface, TARGET_COLOR, 
                             (x + size, y - size), 
                             (x - size, y + size), 
                             width=3)
