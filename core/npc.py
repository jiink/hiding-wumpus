import pygame
from core.pathfinder import Pathfinder
from models.grid import Grid
from models.vector import Vector2
from constants import *
import random

# This NPC lives on a grid and pursues the target via its pathfinder.
class Npc:
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
        self.auto_move = False

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

    # Every frame, this NPC will move along its path smoothly from 
    # one point to the other.
    # `dt` means delta time, the amount of time passed since the last
    # frame. This is for framerate-independent motion.
    def update(self, dt: float):
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
        self.thought_text = text
        self.thought_timer = 0

    def draw(self, surface: pygame.Surface):
        pygame.draw.circle(
            surface, self.color,
            center = self.grid.grid_to_screen(self.position.x, self.position.y),
            radius = self.grid.tile_size * 0.4
        )
        if self.auto_move:
            # the target it's going towards
            if self.target:
                x, y = self.grid.grid_to_screen(self.target.x + 0.5, self.target.y + 0.5)
                size = self.grid.tile_size * 0.4
                # X shape
                pygame.draw.line(surface, self.color, 
                                (x - size, y - size), 
                                (x + size, y + size), 
                                width=3)
                pygame.draw.line(surface, self.color, 
                                (x + size, y - size), 
                                (x - size, y + size), 
                                width=3)    
            # Only draw the path if auto_move is enabled
            if len(self.path) > 1:
                points = [
                    self.grid.grid_to_screen(node.x, node.y)
                    for node in self.path
                ]
                pygame.draw.lines(surface, self.color, False, points, width=3)
            if self.thought_text:
                font = pygame.font.Font(None, 24)
                text_surface = font.render(self.thought_text, True, self.color)
                text_rect = text_surface.get_rect(center=(self.grid.grid_to_screen(self.position.x, self.position.y - 1)))
                text_surface.set_alpha(max(0, 255 * (1 - self.thought_timer / self.THOUGHT_DURATION)))
                surface.blit(text_surface, text_rect)
