from enum import Enum, auto

import pygame
import pygame_gui

from pygame_gui.elements import UIButton, UITextEntryLine, UIDropDownMenu
from constants import *
from core.hider import Hider
from core.pathfinder import Pathfinder
from core.npc import Npc
from core.seeker import Seeker
from models.grid import Grid
from models.vector import Vector2
from level_manager import LevelManager

# This is just an enum.
# Used to know what happens when you click on the grid.
class ClickMode(Enum):
    TILE = auto()
    TARGET = auto()

# This App class is where alll those other classes come together.
class App:
    # Sets up the pygame stuff and instantiates our classes
    def __init__(self):
        pygame.init()
        # Get a pygame "Surface" we can draw graphics to
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("Hiding Wumpus")
        # This clock object lets us get how much time passed since it
        # was last "ticked". "Tick" it every frame so we can know how
        # much time passed since the last frame.
        self.clock = pygame.time.Clock() 
        self.running = True
        self.ui_manager = pygame_gui.UIManager((WINDOW_WIDTH, WINDOW_HEIGHT))
        # Initialize our non-pygame stuff
        self.grid: Grid = Grid(GRID_SIZE, GRID_DISPLAY_SIZE)
        self.pathfinder = Pathfinder(self.grid)
        self.seeker_npc = Seeker(self.grid, self.pathfinder, SEEKER_COLOR, can_think=True)
        self.hider_npcs = [
            {
                "name": "Hider A",
                "color": (255, 80, 10),
                "characteristics": {
                    # Preferences for where to hide
                    "distance to walls": 3,
                    "distance to shadows": 2,
                    "distance to hider": 1,
                    "size of blind spot": 1,
                    "stench": 1,
                    # Preferences for what path to take. Relative
                    # to the cost of moving 1 tile, which is 1.
                    "stench_cost": 10
                }
            },
            {
                "name": "Hider B",
                "color": (80, 255, 10),
                "characteristics": {
                    # Preferences for where to hide
                    "distance to walls": 0,
                    "distance to shadows": 50,
                    "distance to hider": 2,
                    "size of blind spot": 5,
                    "stench": 2,
                    # Preferences for what path to take.
                    "stench_cost": 0
                }
            }
        ]
        self.hider_index = 0
        self.hider_npc = Hider(
            self.grid, 
            self.pathfinder, 
            color=self.hider_npcs[self.hider_index]["color"], 
            can_think=True,
            characteristics=self.hider_npcs[self.hider_index]["characteristics"]
        )
        self.click_mode = ClickMode.TILE
        self.debug_mode = True
        self.cheats = False
        self.seeker_manual_mode = False # False = AI controlled, True = keyboard controlled
        self.mouse_down = False
        self.last_toggle_pos = None
        self.create_ui()
        
    def next_hider(self):
        self.hider_index = (self.hider_index + 1) % len(self.hider_npcs)
        self.hider_npc.color = self.hider_npcs[self.hider_index]["color"]
    
    # This defines all the buttons that show up and what they do.
    # See the `handle_events` function to find where an action is taken
    # based on which button/control was used.
    # Good pygame_gui knowledge here:
    # https://pygame-gui.readthedocs.io/en/latest/quick_start.html
    def create_ui(self):
        # todo: This is tedious, there's got to be an easier way to lay this out...
        btn_w = 100 # Width
        btn_h = 30 # Height
        btn_mn = 10 # Margin
        # The button that makes it so you change tiles when you click in the grid.
        self.tile_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(
                btn_mn, btn_mn,
                btn_w, btn_h),
            text="Tile",
            manager=self.ui_manager
        )
        # The button that makes it so you place the target when you click in the grid.
        self.target_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(btn_mn * 2 + btn_w, btn_mn, btn_w, btn_h),
            text="Target",
            manager=self.ui_manager
        )
        # Toggle debug mode (for helpful visuals)
        self.debug_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(btn_mn * 3 + btn_w * 2, btn_mn, btn_w, btn_h),
            text="Debug: ON",
            manager=self.ui_manager
        )
        # Controls how fast the agent(s) move
        slider_width = 200
        self.speed_label = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(btn_mn, btn_mn * 2 + btn_h, 100, btn_h),
            text="Speed:",
            manager=self.ui_manager
        )
        self.speed_slider = pygame_gui.elements.UIHorizontalSlider(
            relative_rect=pygame.Rect(110, btn_mn * 2 + btn_h, slider_width, btn_h),
            start_value=self.seeker_npc.speed,
            value_range=(1.0, 10.0),
            manager=self.ui_manager
        )

        # Toggle seeker mode (manual or AI)
        self.seeker_manual_mode_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(btn_mn * 4 + btn_w * 3, btn_mn * 4, btn_w, btn_h),
            text="Seeker: CPU",
        )

        # Scroll through hider AI agents
        self.hider_ai_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(btn_mn * 4 + btn_w * 3, btn_mn, btn_w * 1.5, btn_h),
            text=f"Hider AI: {self.hider_npcs[self.hider_index]['name']}",
            manager=self.ui_manager
        )

        right_x = WINDOW_WIDTH - 270  # Align to right edge
        # Text input for level name
        self.level_name_input = pygame_gui.elements.UITextEntryLine(
            relative_rect=pygame.Rect(right_x + btn_w + btn_mn, btn_mn, 150, btn_h),
            manager=self.ui_manager
        )
        self.level_name_input.set_text("NAME")  # Default name

        # Dropdown for saved levels
        saved_levels = LevelManager.list_saved_levels()
        if not saved_levels:  # Avoid empty dropdown
            saved_levels = ["No levels"]
            default_option = "No levels"
        else:
            default_option = saved_levels[0]
        self.level_dropdown = pygame_gui.elements.UIDropDownMenu(
            options_list=saved_levels,
            starting_option=default_option,
            relative_rect=pygame.Rect(right_x + btn_w + btn_mn, btn_mn + btn_h, 150, btn_h),
            manager=self.ui_manager
        )
        # Cheats button
        self.cheats_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(right_x + btn_w + btn_mn, btn_mn + btn_h * 2, btn_w, btn_h),
            text="Cheats",
            manager=self.ui_manager
        )

        # Clear the grid button
        self.clear_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(right_x - btn_w * 0.5 - btn_mn, btn_mn + btn_h, btn_w * 0.5, btn_h),
            text="Clear",
            manager=self.ui_manager
        )
        # Save button
        self.save_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(right_x, btn_mn, btn_w, btn_h),
            text="Save Level",
            manager=self.ui_manager
        )
        # Load button
        self.load_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(right_x, btn_mn + btn_h, btn_w, btn_h),
            text="Load Level",
            manager=self.ui_manager
        )

    def refresh_dropdown(self, select_level=None):
        """Updates the dropdown with current saved levels"""
        saved_levels = LevelManager.list_saved_levels()
        if not saved_levels:
            saved_levels = ["No levels"]
        
        # Get current selection if it exists
        current_selection = None
        if hasattr(self, 'level_dropdown'):
            current_selection = self.level_dropdown.selected_option
            self.level_dropdown.kill()
        

        # Create new dropdown
        self.level_dropdown = pygame_gui.elements.UIDropDownMenu(
            options_list=saved_levels,
            starting_option=select_level if select_level else saved_levels[0],
            relative_rect=pygame.Rect(WINDOW_WIDTH - 270 + 110, 40, 150, 30),
            manager=self.ui_manager
        )
        # Maintain the previous selection if it still exists
        if current_selection in saved_levels:
            self.level_dropdown.selected_option = current_selection
    
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False  # to exit the game loop in the run() func
            # When the user uses a pygame_gui button, it makes a pygame event
            # and we can take an action here.
            if event.type == pygame.USEREVENT:
                if event.user_type == pygame_gui.UI_BUTTON_PRESSED:
                    match event.ui_element:
                        case self.tile_button:
                            self.click_mode = ClickMode.TILE
                        case self.target_button:
                            self.click_mode = ClickMode.TARGET
                        case self.debug_button:
                            self.debug_mode = not self.debug_mode
                            self.debug_button.set_text(f"Debug: {'ON' if self.debug_mode else 'OFF'}")
                        case self.hider_ai_button:
                            self.next_hider()
                            self.hider_npc.characteristics = self.hider_npcs[self.hider_index]["characteristics"]
                            self.hider_ai_button.set_text(f"Hider AI: {self.hider_npcs[self.hider_index]['name']}")
                        case self.seeker_manual_mode_button:
                            self.seeker_manual_mode = not self.seeker_manual_mode
                            self.seeker_npc.auto_move = not self.seeker_manual_mode
                            self.seeker_manual_mode_button.set_text(f"Seeker: {'Human' if self.seeker_manual_mode else 'CPU'}")
                        case self.clear_button:
                            self.grid.clear()
                        case self.save_button:
                            level_name = self.level_name_input.get_text()
                            if level_name:
                                LevelManager.save_level(self.grid, self.seeker_npc, Vector2, level_name)
                                self.refresh_dropdown(select_level=level_name)
                                self.level_name_input.set_text(level_name)
                        case self.load_button:
                            selected_level = self.level_dropdown.selected_option
                            if isinstance(selected_level, tuple):  # Handle tuple case
                                selected_level = selected_level[0]
                            if selected_level != "No levels":
                                LevelManager.load_level(self.grid, self.seeker_npc, Vector2, selected_level)
                        case self.cheats_button:
                            self.cheats = not self.cheats
                            self.cheats_button.set_text(f"Cheats: {'ON' if self.cheats else 'OFF'}")
                elif event.user_type == pygame_gui.UI_HORIZONTAL_SLIDER_MOVED:
                    if event.ui_element == self.speed_slider:
                        self.seeker_npc.set_speed(event.value)

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                self.mouse_down = True
                self.last_toggle_pos = None
                self.handle_tile_click()
            # Handle mouse button up
            if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                self.mouse_down = False
            # Handle mouse motion while button is held down
            if event.type == pygame.MOUSEMOTION and self.mouse_down:
                self.handle_tile_click()

            self.ui_manager.process_events(event)  # pygame_gui requires this

    def update_visibility(self):
        # A gridnode is marked not visible if there is a wall tile between its
        # grid position and the npc
        for nrow in self.grid.nodes:
            for n in nrow:
                n_pos = n.get_position()
                n.seen_by_seeker = not self.grid.is_wall_between(n_pos, self.seeker_npc.position.to_grid_pos())
                n.seen_by_hider = not self.grid.is_wall_between(n_pos, self.hider_npc.position.to_grid_pos())
            

    def handle_tile_click(self):
        """Handle tile clicks based on current mode"""
        mouse_pos = pygame.mouse.get_pos()
        # For clicks within the grid, not the UI
        if mouse_pos[1] > UI_HEIGHT:
            grid_x, grid_y = self.grid.screen_to_grid(*mouse_pos)
            current_pos = (grid_x, grid_y)
            # Only proceed if we moved to a new tile
            if current_pos != self.last_toggle_pos:
                self.last_toggle_pos = current_pos
                if self.click_mode == ClickMode.TILE:
                    self.grid.toggle_wall(grid_x, grid_y)
                    self.seeker_npc.update_path()
                elif self.click_mode == ClickMode.TARGET:
                    self.seeker_npc.set_target(grid_x, grid_y)

    # dt is delta time, the time passed since the last update.
    def update(self, dt):
        self.ui_manager.update(dt) # pygame_gui requires this
        self.seeker_npc.update(dt)
        self.hider_npc.update(dt)
        self.update_visibility()

    
    def draw(self):
        self.screen.fill(BACKGROUND_COLOR)
        self.grid.draw(self.screen, self.seeker_manual_mode)
        if self.debug_mode:
            self.pathfinder.draw_debug(self.screen)
        self.seeker_npc.draw(self.screen, self.debug_mode)
        # If you're controlling the seeker, you shouldn't see the
        # hider if it's out of line of sight. Unless "cheats" is on of course
        if self.seeker_manual_mode:
            if self.cheats or not self.grid.is_wall_between(self.seeker_npc.position.to_grid_pos(), self.hider_npc.position.to_grid_pos()):
                self.hider_npc.draw(self.screen, self.debug_mode)
        else:
            self.hider_npc.draw(self.screen, self.debug_mode)
        self.ui_manager.draw_ui(self.screen)
        # Now show the frame
        pygame.display.flip()
    
    # The game loop
    def run(self):
        while self.running:
            dt = self.clock.tick(FPS) / 1000.0 # delta time
            self.handle_events()
            self.update(dt)
            self.draw()
        pygame.quit()
