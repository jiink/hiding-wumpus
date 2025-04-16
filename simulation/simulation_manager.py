import time
import csv
import os
import random
from typing import Dict, List
from constants import FPS
from models.grid import Grid
from models.vector import Vector2
from core.pathfinder import Pathfinder
from core.seeker import Seeker
from core.hider import Hider

class SimulationManager:
    def __init__(self, grid: Grid, pathfinder: Pathfinder, seeker: Seeker, hider: Hider):
        self.grid = grid
        self.pathfinder = pathfinder
        self.seeker = seeker
        self.hider = hider
        self.results = []
    
    def reset_game(self) -> None:
        self.hider.reset()
        self.seeker.reset()
        # Tell the seeker to freeze for a moment to give the hider a chance to run away.
        self.seeker.freeze()

    def run_simulation(self, iterations: int):
        #Run multiple simulation rounds and collect data
        self.results = []
        
        for round_num in range(iterations):
            self.reset_game()
            # Run the simulation
            print(f"Round {round_num} begin!")
            start_time = time.time()
            result = self._run_single_round()
            result['sim_time'] = time.time() - start_time
            self.results.append(result)

        self.generate_report()
    
    def _is_caught(self) -> bool:
        if self.seeker.is_frozen():
            return False
        # Check if hider is caught.
        seeker_pos = self.seeker.position.to_grid_pos()
        hider_pos = self.hider.position.to_grid_pos()
        return (abs(seeker_pos[0] - hider_pos[0]) == 0 and 
                abs(seeker_pos[1] - hider_pos[1]) == 0)
    
    def _run_single_round(self) -> Dict:
        # Run a single simulation round and return metrics
        # If the hider can stay away for this many in-game seconds
        # (not real seconds), it wins.
        max_game_time_s = 5 * 60
        steps = 0
        path_length = 0
        last_position = None
        timestep = FPS / 1000 # in in-game seconds
        max_steps = max_game_time_s / timestep
        
        while steps < max_steps:
            steps += 1
            
            # Update NPCs
            self.seeker.update(timestep)  # Fixed small time step for consistency
            self.hider.update(timestep)
            
            # Track path length
            current_pos = self.seeker.position.to_grid_pos()
            if last_position != current_pos:
                path_length += 1
                last_position = current_pos
            
            # Check if caught
            if self._is_caught():
                return {
                    'caught': True,
                    'steps': steps,
                    'time_elapsed': steps / FPS,
                    'path_length': path_length,
                    'final_distance': self._get_distance()
                }
        
        return {
            'caught': False,
            'steps': steps,
            'time_elapsed': steps / FPS,
            'path_length': path_length,
            'final_distance': self._get_distance()
        }
    
    def _get_distance(self) -> int:
        # Get Manhattan distance between seeker and hider
        seeker_pos = self.seeker.position.to_grid_pos()
        hider_pos = self.hider.position.to_grid_pos()
        return abs(seeker_pos[0] - hider_pos[0]) + abs(seeker_pos[1] - hider_pos[1])
    
    # You have to change file name here each time, I'll fix that 
    def generate_report(self, csv_filename: str = "sim_results1.csv") -> None:
        # Save results to CSV
        if not self.results:
            print("No results to export")
            return
        
        # file path to save csv file
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        sim_folder = os.path.join(project_root, "simulation")
        file_path = os.path.join(sim_folder, csv_filename)

        # Prepare CSV file
        try:
            with open(file_path, mode='w', newline='') as file:
                writer = csv.DictWriter(file, fieldnames=self.results[0].keys())
                writer.writeheader()
                writer.writerows(self.results)
            print(f"Results saved to {os.path.abspath(file_path)}")
        except Exception as e:
            print(f"Failed to save CSV: {e}")
    