from enum import Enum, auto

import pygame
import pygame_gui

from constants import *
from core.hider_a import HiderA
from core.pathfinder import Pathfinder
from core.npc import Npc
from core.seeker import Seeker
from models.grid import Grid

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
        self.grid = Grid(GRID_SIZE, GRID_DISPLAY_SIZE)
        self.pathfinder = Pathfinder(self.grid)
        self.seeker_npc = Seeker(self.grid, self.pathfinder, SEEKER_COLOR, can_think=True)
        # TODO: some way to change the hider algorithms during runtime
        self.hider_npc = HiderA(self.grid, self.pathfinder, HIDER_COLOR, can_think=True)
        self.click_mode = ClickMode.TILE
        self.debug_mode = True
        self.seeker_manual_mode = False # False = AI controlled, True = keyboard controlled
        self.create_ui()
    
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
            relative_rect=pygame.Rect(btn_mn * 4 + btn_w * 3, btn_mn, btn_w, btn_h),
            text="Seeker: CPU",
            manager=self.ui_manager
        )
    
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False # to exit the game loop in the run() func
            # When the user uses a pygame_gui button, it makes a pygame event
            # and we can take an action here.
            if event.type == pygame.USEREVENT:
                if event.user_type == pygame_gui.UI_BUTTON_PRESSED:
                    # There's probably a better way to do this too.
                    if event.ui_element == self.tile_button:
                        self.click_mode = ClickMode.TILE
                    elif event.ui_element == self.target_button:
                        self.click_mode = ClickMode.TARGET
                    elif event.ui_element == self.debug_button:
                        self.debug_mode = not self.debug_mode
                        self.debug_button.set_text(f"Debug: {'ON' if self.debug_mode else 'OFF'}")
                    elif event.ui_element == self.seeker_manual_mode_button:
                        self.seeker_manual_mode = not self.seeker_manual_mode
                        self.seeker_npc.auto_move = not self.seeker_manual_mode
                        self.seeker_manual_mode_button.set_text(f"Seeker: {'Human' if self.seeker_manual_mode else 'CPU'}")
                elif event.user_type == pygame_gui.UI_HORIZONTAL_SLIDER_MOVED:
                    if event.ui_element == self.speed_slider:
                        self.seeker_npc.set_speed(event.value)
            
            # Non pygame_gui stuff, just mouse clicks
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mouse_pos = pygame.mouse.get_pos()
                # For clicks within the grid, not the UI
                if mouse_pos[1] > UI_HEIGHT:
                    # the asterisk notation unpacks mouse_pos into
                    # 2 separate arguments
                    grid_x, grid_y = self.grid.screen_to_grid(*mouse_pos)
                    if self.click_mode == ClickMode.TILE:
                        self.grid.toggle_wall(grid_x, grid_y)
                        # Path needs to be updated since the envrionment changed.
                        self.seeker_npc.update_path()
                    if self.click_mode == ClickMode.TARGET:
                        self.seeker_npc.set_target(grid_x, grid_y)
            # Process pygame_gui events
            self.ui_manager.process_events(event)

    def update_visibility(self):
        # A gridnode is marked not visible if there is a wall tile between its
        # grid position and the npc
        for nrow in self.grid.nodes:
            for n in nrow:
                n_pos = n.get_position()
                n.seen_by_seeker = not self.grid.is_wall_between(n_pos, self.seeker_npc.position.to_grid_pos())
                n.seen_by_hider = not self.grid.is_wall_between(n_pos, self.hider_npc.position.to_grid_pos())
         
    
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
        self.seeker_npc.draw(self.screen)
        # If you're controlling the seeker, you shouldn't see the
        # hider if it's out of line of sight
        if self.seeker_manual_mode:
            if not self.grid.is_wall_between(self.seeker_npc.position.to_grid_pos(), self.hider_npc.position.to_grid_pos()):
                self.hider_npc.draw(self.screen)
        else:
            self.hider_npc.draw(self.screen)
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
