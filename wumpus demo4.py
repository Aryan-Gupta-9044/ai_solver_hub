import tkinter as tk
from tkinter import simpledialog, messagebox
from PIL import Image, ImageTk
import os
import random
import io
import collections
import threading

# Constants
CELL_SIZE = 80
ICON_SCALE_FACTOR = 0.7
ICON_SIZE = (int(CELL_SIZE * ICON_SCALE_FACTOR), int(CELL_SIZE * ICON_SCALE_FACTOR))
WIN_EXIT_DELAY_MS = 3000

# WumpusSolverAgent - ADD THIS CLASS HERE, BEFORE ANY OTHER CLASSES
class WumpusSolverAgent:
    def __init__(self, world_instance):
        self.world = world_instance
        self.size = world_instance.size
        
        # Agent's internal state
        self.agent_pos = world_instance.agent_pos
        self.has_gold = False
        self.knowledge = self._initialize_knowledge()
        self.plan = []
        self.actions_taken = []

    def _initialize_knowledge(self):
        knowledge = {
            'visited': [[False for _ in range(self.size)] for _ in range(self.size)],
            'safe': [[False for _ in range(self.size)] for _ in range(self.size)],
            # Initially, assume hazards could be anywhere except start
            'possible_wumpus': [[True for _ in range(self.size)] for _ in range(self.size)],
            'possible_pit': [[True for _ in range(self.size)] for _ in range(self.size)],
        }
        # Start cell is visited and known safe, cannot contain hazards
        start_x, start_y = self.agent_pos
        knowledge['visited'][start_x][start_y] = True
        knowledge['safe'][start_x][start_y] = True
        knowledge['possible_wumpus'][start_x][start_y] = False
        knowledge['possible_pit'][start_x][start_y] = False
        return knowledge

    def _is_valid(self, x, y):
        return 0 <= x < self.size and 0 <= y < self.size

    def _get_adjacent(self, x, y):
        adj = []
        for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]: # Right, Left, Up, Down
            nx, ny = x + dx, y + dy
            if self._is_valid(nx, ny):
                adj.append((nx, ny))
        return adj

    def _update_knowledge(self):
        x, y = self.agent_pos
        if not self.knowledge['visited'][x][y]:
             self.knowledge['visited'][x][y] = True

        # Get percepts at the current location
        perceived_stench = (x, y) in self.world.stench
        perceived_breeze = (x, y) in self.world.breeze

        adjacent_cells = self._get_adjacent(x, y)

        # Update safety based on lack of percepts
        if not perceived_stench:
            for nx, ny in adjacent_cells:
                self.knowledge['possible_wumpus'][nx][ny] = False
        if not perceived_breeze:
            for nx, ny in adjacent_cells:
                self.knowledge['possible_pit'][nx][ny] = False
        
        # Mark cells as safe if known no wumpus AND no pit
        for r in range(self.size):
            for c in range(self.size):
                if not self.knowledge['possible_wumpus'][r][c] and not self.knowledge['possible_pit'][r][c]:
                    self.knowledge['safe'][r][c] = True
                
        # Try to locate the gold through more aggressive exploration
        if self.world.gold_pos is not None:
            gold_x, gold_y = self.world.gold_pos
            # If we can see the gold position (through the world object), mark a path to it
            self._mark_path_to_goal(gold_x, gold_y)

    def _find_safe_path(self, start, goal_condition_func):
        """Uses BFS to find shortest path in known safe squares."""
        # If already at goal, return empty path
        if goal_condition_func(start):
            return []
        
        # Special case: If at start and looking for a path to a non-start goal
        if start == (0, 0) and not goal_condition_func((0, 0)):
            # Ensure start is properly marked as safe
            self.knowledge['safe'][0][0] = True
        
        q = collections.deque([(start, [])]) # ((x, y), path_list)
        visited_path = {start}

        while q:
            (curr_x, curr_y), path = q.popleft()

            for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]: # Up, Down, Right, Left
                next_x, next_y = curr_x + dx, curr_y + dy
                
                if self._is_valid(next_x, next_y) and \
                   self.knowledge['safe'][next_x][next_y] and \
                   (next_x, next_y) not in visited_path:
                    
                    new_path = path + [(dx, dy)]
                    if goal_condition_func((next_x, next_y)):
                        return new_path # Found path
                    
                    visited_path.add((next_x, next_y))
                    q.append(((next_x, next_y), new_path))
        
        # Special case: if at start and no safe path found, at least try exploring one direction
        if start == (0, 0) and len(self.actions_taken) == 0:
            # Try moving up first if valid
            if self._is_valid(1, 0):
                return [(1, 0)]  # Move Up
            # Otherwise try moving right
            elif self._is_valid(0, 1):
                return [(0, 1)]  # Move Right
        
        return None # No path found

    def _get_action_name(self, move):
        if move == 'Grab': return 'Grab Gold'
        if move == 'Climb': return 'Climb Out'
        dx, dy = move
        if dx == 1: return 'Move Up'
        if dx == -1: return 'Move Down'
        if dy == 1: return 'Move Right'
        if dy == -1: return 'Move Left'
        return 'Unknown Move'

    def _find_risky_path_home(self, home_x, home_y):
        """When stuck with gold, try to find any path home, accepting some risk."""
        # Simple BFS through all squares, weighing risk but not avoiding all risk
        from collections import deque
        queue = deque([(self.agent_pos, [])])  # (position, path)
        visited = {self.agent_pos}
        
        while queue:
            (x, y), path = queue.popleft()
            
            if (x, y) == (home_x, home_y):
                return path  # Found a path home!
            
            for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
                nx, ny = x + dx, y + dy
                
                if self._is_valid(nx, ny) and (nx, ny) not in visited:
                    # Avoid the wumpus location if known, but allow some risk otherwise
                    if (self.world.wumpus_pos is not None and (nx, ny) != self.world.wumpus_pos) or \
                       not self.knowledge['possible_wumpus'][nx][ny]:
                        visited.add((nx, ny))
                        new_path = path + [(dx, dy)]
                        queue.append(((nx, ny), new_path))
                    
        return None  # No path found

    def _mark_path_to_goal(self, goal_x, goal_y):
        """Try to mark a path to the gold with decreased risk assessment."""
        # Define a path from current position to gold using BFS with risk tolerance
        from collections import deque
        
        # If already safe, no need for special path
        if self.knowledge['safe'][goal_x][goal_y]:
            return
        
        queue = deque([(self.agent_pos, [])])
        visited = {self.agent_pos}
        
        while queue:
            (x, y), path = queue.popleft()
            
            if (x, y) == (goal_x, goal_y):
                # Found gold location! Mark the entire path as "worth the risk"
                current_x, current_y = self.agent_pos
                for dx, dy in path:
                    next_x, next_y = current_x + dx, current_y + dy
                    # Mark this cell as safer (not guaranteed safe, but worth exploring)
                    self.knowledge['safe'][next_x][next_y] = True
                    current_x, current_y = next_x, next_y
                return
            
            for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
                nx, ny = x + dx, y + dy
                
                if self._is_valid(nx, ny) and (nx, ny) not in visited:
                    # Skip cells we know contain the Wumpus, but be more tolerant of risk
                    if (self.world.wumpus_pos is None or (nx, ny) != self.world.wumpus_pos):
                        visited.add((nx, ny))
                        new_path = path + [(dx, dy)]
                        queue.append(((nx, ny), new_path))

    def solve(self):
        """Attempts to solve the Wumpus World instance."""
        start_x, start_y = self.agent_pos
        
        # SPECIAL CASE: Handle agent at start position (0,0)
        if self.agent_pos == (0, 0):
            # If already has gold, just climb out
            if self.world.has_gold:
                self.actions_taken.append('Climb Out')
                self.world.game_over = True
                self.world.won = True
                return self.actions_taken
            
            # If gold is at starting position, grab it and climb out
            if self.world.gold_pos == (0, 0):
                self.has_gold = True
                self.world.has_gold = True
                self.world.gold_pos = None
                self.actions_taken.append('Grab Gold')
                self.actions_taken.append('Climb Out')
                self.world.game_over = True
                self.world.won = True
                return self.actions_taken
            
            # Otherwise, we're at start but need to search for gold
            # Mark starting cell as safe and visited
            self.knowledge['safe'][0][0] = True
            self.knowledge['visited'][0][0] = True
            self.knowledge['possible_wumpus'][0][0] = False
            self.knowledge['possible_pit'][0][0] = False
        
        # Continue with regular algorithm...
        max_steps = self.size * self.size * 3  # Limit steps to prevent infinite loops
        steps_taken = 0
        
        while not self.world.game_over and steps_taken < max_steps:
            steps_taken += 1
            self._update_knowledge()
            
            # Helper debug output - print where gold is
            if self.world.gold_pos:
                gold_x, gold_y = self.world.gold_pos
                print(f"Gold is at ({gold_x}, {gold_y})")
            else:
                print("Gold not found/already collected")

            # --- Decision Making ---
            current_x, current_y = self.agent_pos
            
            # 1. Grab gold if present
            if self.world.gold_pos == self.agent_pos and not self.has_gold:
                self.has_gold = True
                # Simulate grabbing in the internal world representation
                self.world.has_gold = True
                self.world.gold_pos = None
                self.actions_taken.append('Grab Gold')
                continue # Re-evaluate state after grabbing

            # 2. Climb out if has gold and at start
            if self.has_gold and self.agent_pos == (0, 0):
                self.actions_taken.append('Climb Out')
                self.world.game_over = True
                self.world.won = True
                break # Solved

            # 3. Execute existing plan if any
            if self.plan:
                dx, dy = self.plan.pop(0)
                action_name = self._get_action_name((dx, dy))
                success, message = self.world.move_agent(dx, dy)
                self.actions_taken.append(action_name)
                self.agent_pos = self.world.agent_pos # Update internal tracker
                if not success or self.world.game_over:
                     break # Plan failed or game ended unexpectedly
                continue

            # 4. Find a new plan: Explore safe unvisited square or return home
            target_condition = None
            if self.has_gold:
                # Plan to go home
                target_condition = lambda pos: pos == (start_x, start_y)
            else:
                # Plan to explore nearest safe, unvisited square
                target_condition = lambda pos: self.knowledge['safe'][pos[0]][pos[1]] and \
                                               not self.knowledge['visited'][pos[0]][pos[1]]

            self.plan = self._find_safe_path(self.agent_pos, target_condition)

            if self.plan is None:
                # If we have gold, prioritize getting home even with some risk
                if self.has_gold:
                    # Try to find any path home, even if uncertain
                    self.actions_taken.append('Take Risk - Return Home')
                    risk_path = self._find_risky_path_home(start_x, start_y)
                    if risk_path:
                        self.plan = risk_path
                        continue
                        
                # Truly stuck with no options
                self.actions_taken.append('Get Stuck')
                break

            # Execute the first step of the new plan immediately
            if self.plan:
                 dx, dy = self.plan.pop(0)
                 action_name = self._get_action_name((dx, dy))
                 success, message = self.world.move_agent(dx, dy)
                 self.actions_taken.append(action_name)
                 self.agent_pos = self.world.agent_pos
                 if not success or self.world.game_over:
                     break
            else:
                 # If target was current location (e.g., goal=start and agent is at start), handle appropriately
                 if self.has_gold and self.agent_pos == (start_x, start_y):
                     continue
                 else:
                     # Maybe stuck exploring?
                      self.actions_taken.append('Get Stuck')
                      break

        # --- Return Solution ---
        if self.world.won:
            return self.actions_taken
        else:
            # Return partial path or indicate failure
            return self.actions_taken + ["FAILED"]

class WumpusWorld:
    # ... (WumpusWorld class remains the same) ...
    def __init__(self, size):
        self.size = size
        self.grid = [['' for _ in range(size)] for _ in range(size)]
        self.agent_pos = None
        self.wumpus_pos = None
        self.gold_pos = None
        self.pits = []
        self.breeze = set()
        self.stench = set()
        self.game_over = False
        self.has_gold = False
        self.score = 0
        self.won = False # Flag to indicate win state

    def set_wumpus(self, x, y):
        if 0 <= x < self.size and 0 <= y < self.size:
            self.grid[x][y] = 'Wumpus'
            self.wumpus_pos = (x, y)
            self._add_adjacent(x, y, self.stench, 'Stench')

    def set_gold(self, x, y):
        if 0 <= x < self.size and 0 <= y < self.size:
            self.grid[x][y] = 'Gold'
            self.gold_pos = (x, y)

    def set_pit(self, x, y):
        if 0 <= x < self.size and 0 <= y < self.size:
            self.grid[x][y] = 'Pit'
            self.pits.append((x, y))
            self._add_adjacent(x, y, self.breeze, 'Breeze')

    def _add_adjacent(self, x, y, effect_set, effect_name):
        for dx, dy in [(-1,0), (1,0), (0,-1), (0,1)]:
            nx, ny = x + dx, y + dy
            if 0 <= nx < self.size and 0 <= ny < self.size:
                    effect_set.add((nx, ny))
    

    def move_agent(self, dx, dy):
        if self.game_over:
            return False, "Game Over"
            
        x, y = self.agent_pos
        new_x, new_y = x + dx, y + dy
        
        if not (0 <= new_x < self.size and 0 <= new_y < self.size):
            self.score -= 10
            return False, "Bump! Cannot move outside the grid. (-10 score)"
            
        self.agent_pos = (new_x, new_y)
        self.score -= 1
        
        message = ""
        current_cell_content = self.grid[new_x][new_y]

        if self.agent_pos == self.wumpus_pos:
            self.game_over = True
            self.score -= 1000
            message = "You were eaten by the Wumpus! Game Over."
        elif self.agent_pos in self.pits:
            self.game_over = True
            self.score -= 1000
            message = "You fell into a pit! Game Over."
        elif self.agent_pos == self.gold_pos and not self.has_gold:
            self.has_gold = True
            self.score += 1000
            self.grid[new_x][new_y] = ''
            self.gold_pos = None
            message = "You found the gold! Score +1000"
        else:
             percepts = []
             if (new_x, new_y) in self.stench:
                 percepts.append("Stench")
             if (new_x, new_y) in self.breeze:
                 percepts.append("Breeze")
             if not percepts:
                 message = "Moved to a safe square."
             else:
                 message = "You perceive: " + ", ".join(percepts)

        # Check win condition *after* checking for death/gold pickup
        if self.has_gold and self.agent_pos == (0, 0): # Assuming (0,0) is the starting/exit square
            self.game_over = True
            self.won = True # Set win flag
            self.score += 100
            message = "You escaped with the gold! YOU WIN! (+100 score)"
        
        return True, message

class WumpusWorldUI(tk.Frame):
    def __init__(self, master, world: WumpusWorld):
        super().__init__(master, bg='#f0f0f0')
        self.world = world
        self.master = master
        self.pack(padx=10, pady=10, fill="both", expand=True)
        
        self.load_images() # Load images using new ICON_SIZE
        
        self.colors = {
            'background': '#f0f0f0', 'cell': '#e0e0e0', 'cell_border': '#483D8B',
            'agent': '#3498db', 'wumpus': '#e74c3c', 'gold': '#f1c40f', 'pit': '#34495e',
            'controls': '#2ecc71', 'exit_button': '#e74c3c', # Red for exit button
            'text': '#2c3e50'
        }
        self.configure(bg=self.colors['background'])
        
        # --- Layout Frames ---
        content_frame = tk.Frame(self, bg=self.colors['background'])
        content_frame.pack(side=tk.LEFT, padx=10, pady=10, fill="both", expand=True)

        self.grid_frame = tk.Frame(content_frame, bg=self.colors['cell_border'], bd=3, relief='raised')
        self.grid_frame.pack(pady=10, anchor='center')

        sidebar_frame = tk.Frame(self, bg=self.colors['background'], width=200)
        sidebar_frame.pack(side=tk.RIGHT, padx=10, pady=10, fill="y")
        sidebar_frame.pack_propagate(False)

        # --- Widgets ---
        self.create_widgets()
        self.create_position_indicator(sidebar_frame)
        self.create_controls(sidebar_frame)
        self.create_status_labels(sidebar_frame)
        self.create_solver_controls(sidebar_frame)
        self.create_utility_buttons(sidebar_frame)

        self.update_grid()
        self.update_position_display()

    def load_images(self):
        # Use the global ICON_SIZE constant
        self.icons = {}
        icon_folder = "icons"
        if not os.path.exists(icon_folder):
            print(f"Warning: '{icon_folder}' directory not found. Using fallback symbols.")

        icon_files = {
            'agent': os.path.join(icon_folder, "agent.png"),
            'wumpus': os.path.join(icon_folder, "wumpus.png"),
            'gold': os.path.join(icon_folder, "gold.png"),
            'pit': os.path.join(icon_folder, "pit.png"),
        }

        for element, filepath in icon_files.items():
            try:
                if os.path.isfile(filepath):
                    img = Image.open(filepath)
                    if img.mode != 'RGBA': img = img.convert('RGBA')
                    # Use the ICON_SIZE constant here
                    img = img.resize(ICON_SIZE, Image.Resampling.LANCZOS)
                    self.icons[element] = ImageTk.PhotoImage(img)
                    print(f"Loaded icon: {filepath}")
                else:
                     self.icons[element] = None
            except Exception as e:
                print(f"Error loading icon {filepath}: {e}")
            self.icons[element] = None

    def create_widgets(self):
        size = self.world.size
        self.cell_widgets = {}
        for row in range(size):
            for col in range(size):
                x, y = row, col
                # Use the CELL_SIZE constant here for the placeholder
                cell_placeholder = tk.Frame(self.grid_frame, width=CELL_SIZE, height=CELL_SIZE,
                                            bg=self.colors['cell'],
                                            highlightbackground=self.colors['cell_border'],
                                            highlightthickness=1)
                display_row = (size - 1 - x)
                display_col = y
                cell_placeholder.grid(row=display_row, column=display_col, padx=1, pady=1)
                self.cell_widgets[(x, y)] = cell_placeholder

    def create_position_indicator(self, parent_frame):
        """Creates a visual indicator showing the agent's current position in the grid."""
        position_frame = tk.LabelFrame(parent_frame, text="Agent Position", font=("Arial", 10, "bold"),
                                     bg=self.colors['background'], fg=self.colors['text'], padx=10, pady=10)
        position_frame.pack(pady=10, fill="x")

        self.position_label = tk.Label(position_frame, 
                                      text="Position: (?, ?)",
                                      font=("Arial", 12),
                                      bg=self.colors['background'],
                                      fg=self.colors['text'])
        self.position_label.pack(pady=5)

        # Add a sense indicator to show what the agent perceives
        self.sense_label = tk.Label(position_frame,
                                   text="Senses: None",
                                   font=("Arial", 10),
                                   bg=self.colors['background'],
                                   fg=self.colors['text'],
                                   wraplength=180,
                                   justify='left')
        self.sense_label.pack(pady=5)

    def create_controls(self, parent_frame):
        control_frame = tk.LabelFrame(parent_frame, text="Controls", font=("Arial", 10, "bold"),
                                     bg=self.colors['background'], fg=self.colors['text'], padx=10, pady=10)
        control_frame.pack(pady=10, fill="x")

        # Button style
        button_style = {'width': 5, 'height': 2, 'font': ('Arial', 10, 'bold'), 
                         'bg': self.colors['controls'], 'fg': 'white', 'relief': 'raised', 'bd': 2}
        
        # Control Button Layout
        up_button = tk.Button(control_frame, text="↑", command=lambda: self.move_agent(1, 0), **button_style)
        up_button.grid(row=0, column=1, padx=5, pady=5)
        left_button = tk.Button(control_frame, text="←", command=lambda: self.move_agent(0, -1), **button_style)
        left_button.grid(row=1, column=0, padx=5, pady=5)
        right_button = tk.Button(control_frame, text="→", command=lambda: self.move_agent(0, 1), **button_style)
        right_button.grid(row=1, column=2, padx=5, pady=5)
        down_button = tk.Button(control_frame, text="↓", command=lambda: self.move_agent(-1, 0), **button_style)
        down_button.grid(row=2, column=1, padx=5, pady=5)

        control_frame.grid_columnconfigure(0, weight=1)
        control_frame.grid_columnconfigure(1, weight=0)
        control_frame.grid_columnconfigure(2, weight=1)

    def create_status_labels(self, parent_frame):
        """Creates status labels for game information."""
        status_frame = tk.LabelFrame(parent_frame, text="Game Status", font=("Arial", 10, "bold"),
                                   bg=self.colors['background'], fg=self.colors['text'], padx=10, pady=10)
        status_frame.pack(pady=10, fill="x")

        # Status message label
        self.status_label = tk.Label(status_frame, 
                                    text="Find the gold and return to start!",
                                    font=("Arial", 10),
                                    bg=self.colors['background'],
                                    fg=self.colors['text'],
                                    wraplength=180,
                                    justify='left')
        self.status_label.pack(pady=5, fill="x")

        # Score label
        self.score_label = tk.Label(status_frame,
                                   text=f"Score: {self.world.score}",
                                   font=("Arial", 12, "bold"),
                                   bg=self.colors['background'],
                                   fg=self.colors['text'])
        self.score_label.pack(pady=5)

        # Gold status indicator with initial state
        gold_status = "Gold: Found! 🏆" if self.world.has_gold else "Gold: Not Found"
        gold_color = "gold" if self.world.has_gold else self.colors['text']
        
        self.gold_label = tk.Label(status_frame,
                                  text=gold_status,
                                  font=("Arial", 10),
                                  bg=self.colors['background'],
                                  fg=gold_color)
        self.gold_label.pack(pady=5)

    def create_solver_controls(self, parent_frame):
        """Creates controls related to the AI solver."""
        solver_frame = tk.LabelFrame(parent_frame, text="AI Solver", font=("Arial", 10, "bold"),
                                     bg=self.colors['background'], fg=self.colors['text'], padx=10, pady=10)
        solver_frame.pack(pady=10, fill="x")

        self.solve_button = tk.Button(solver_frame, text="Show Solution Path",
                                      font=("Arial", 10),
                                      bg=self.colors['controls'], fg='white',
                                      command=self.show_solution)
        self.solve_button.pack(pady=5, fill="x")

    def create_utility_buttons(self, parent_frame):
        """Creates utility buttons like Exit."""
        utility_frame = tk.Frame(parent_frame, bg=self.colors['background'])
        utility_frame.pack(pady=20, fill="x", side=tk.BOTTOM) # Place at bottom of sidebar

        exit_button = tk.Button(utility_frame, text="Exit Game",
                                font=("Arial", 10, "bold"),
                                bg=self.colors['exit_button'], fg='white',
                                relief='raised', bd=2,
                                command=self.master.destroy) # Command to close window
        exit_button.pack(fill="x", padx=10)


    def make_cell(self, x, y):
        # Use the CELL_SIZE constant here
        cell_frame = tk.Frame(self.grid_frame, width=CELL_SIZE, height=CELL_SIZE, bd=0,
                              highlightbackground=self.colors['cell_border'],
                              highlightthickness=1)
        cell_frame.pack_propagate(False)
        cell_bg = self.colors['cell']
        cell_frame.configure(bg=cell_bg)
        
        elements_to_display = []
        has_primary_element = False
        
        if (x, y) == self.world.agent_pos:
            elements_to_display.append('agent')
            has_primary_element = True
        if self.world.game_over:
            if (x, y) == self.world.wumpus_pos:
                if 'agent' not in elements_to_display: elements_to_display.append('wumpus')
                has_primary_element = True
            if (x, y) in self.world.pits:
                if 'agent' not in elements_to_display: elements_to_display.append('pit')
                has_primary_element = True
        if (x, y) == self.world.gold_pos and not self.world.has_gold:
            if 'agent' not in elements_to_display: elements_to_display.append('gold')
            has_primary_element = True

        percept_labels = []
        if not has_primary_element:
            if (x, y) in self.world.breeze: percept_labels.append("Breeze")
            if (x, y) in self.world.stench: percept_labels.append("Stench")

        # Place primary icons
        positions = [(0.5, 0.5)] # Center
        for i, element_key in enumerate(elements_to_display):
            relx, rely = positions[0]
            if element_key in self.icons and self.icons[element_key]:
                icon_label = tk.Label(cell_frame, image=self.icons[element_key], bd=0, bg=cell_bg)
                icon_label.place(relx=relx, rely=rely, anchor='center')
            else: # Fallback symbol
                 symbol = element_key[0].upper() if element_key else ''
                 color = self.colors.get(element_key, self.colors['text'])
                 fallback_label = tk.Label(cell_frame, text=symbol, bg=color, fg='white',
                                          font=("Arial", 10, "bold"), width=2, height=1, relief='solid', bd=1)
                 fallback_label.place(relx=relx, rely=rely, anchor='center')

        # Place percept labels
        if percept_labels:
             label_text = "\n".join(percept_labels)
             # Adjust font size based on cell size if needed
             percept_font_size = max(6, int(CELL_SIZE / 10))
             percept_label_widget = tk.Label(cell_frame, text=label_text,
                                             font=("Arial", percept_font_size),
                                             bg=cell_bg, fg=self.colors['text'], justify="center")
             percept_label_widget.place(relx=0.5, rely=0.9, anchor='s') # Place slightly higher
        
        return cell_frame
    
    def update_position_display(self):
        """Updates the position indicator with the agent's current position"""
        if self.world.agent_pos:
            x, y = self.world.agent_pos
            # Convert internal coordinates to display coordinates (1-indexed)
            display_x, display_y = y + 1, self.world.size - x
            self.position_label.config(text=f"Position: ({display_x}, {display_y})")
            
            # Update sense information
            senses = []
            if (x, y) in self.world.breeze:
                senses.append("Breeze")
            if (x, y) in self.world.stench:
                senses.append("Stench")
            if self.world.has_gold and not self.world.gold_pos:
                senses.append("Gold in bag")
            
            if senses:
                self.sense_label.config(text=f"Senses: {', '.join(senses)}")
            else:
                self.sense_label.config(text="Senses: None")

    def move_agent(self, dx, dy):
        success, message = self.world.move_agent(dx, dy)
        if success:
            self.update_grid()
            self.update_position_display()
            
            # Update gold status whenever a move is successful
            if self.world.has_gold:
                self.gold_label.config(text="Gold: Found! 🏆", fg="gold")
            
            if message:
                self.status_label.config(text=message)
            self.score_label.config(text=f"Score: {self.world.score}")
            
            # Check for game over conditions
            if self.world.game_over:
                if self.world.won:
                    # If the game is won, update UI to reflect victory
                    messagebox.showinfo("Victory!", "Congratulations! You escaped with the gold!")
                    # Schedule auto-exit after delay
                    self.master.after(WIN_EXIT_DELAY_MS, self.master.destroy)
        else:
            self.status_label.config(text=message)
    
    def update_grid(self):
        size = self.world.size
        for pos, old_widget in self.cell_widgets.items():
            old_widget.destroy()
            x, y = pos
            new_cell = self.make_cell(x, y)
            self.cell_widgets[pos] = new_cell
            display_row = size - 1 - x
            display_col = y
            new_cell.grid(row=display_row, column=display_col, padx=1, pady=1)

    def show_solution(self):
        """Runs the AI solver and displays the sequence of moves."""
        try:
            self.status_label.config(text="AI Solver running...")
            self.master.update_idletasks()  # Force UI update
            
            # SPECIAL CASE: Check if agent is at start
            if self.world.agent_pos == (0, 0):
                # Agent is at starting position (0,0)
                solution_text = "AI Solution Steps:\n" + "-"*20 + "\n"
                
                # Check if gold is already collected or at start
                if self.world.has_gold:
                    solution_text += "1. Climb Out\n\n✅ You already have the gold! Just climb out to win."
                elif self.world.gold_pos == (0, 0):
                    solution_text += "1. Grab Gold\n2. Climb Out\n\n✅ The gold is right here! Grab it and climb out."
                else:
                    solution_text += "Agent is at the starting position.\n\n"
                    solution_text += "From here, you need to:\n"
                    solution_text += "1. Explore to find the gold\n"
                    solution_text += "2. Grab the gold when found\n"
                    solution_text += "3. Return to this starting position\n"
                    solution_text += "4. Climb out to win\n\n"
                    solution_text += "Use the directional controls to start exploring!"
                
                try:
                    messagebox.showinfo("Agent at Starting Position", solution_text, parent=self.master)
                    self.status_label.config(text="You're at the starting position")
                    return  # Skip the regular solver
                except:
                    print("Window closed during showing message")
                    return
            
            # REGULAR CASE: If not at start, use the solver
            import copy
            temp_world = copy.deepcopy(self.world)
            solver = WumpusSolverAgent(temp_world)
            
            # Run the solver to get the solution path
            solution_moves = solver.solve()
            
            # Try-except blocks for all UI operations
            try:
                # Display the solution in a message box
                solution_text = "AI Solution Steps:\n" + "-"*20 + "\n"
                if solution_moves and len(solution_moves) > 0:
                    for i, move in enumerate(solution_moves):
                        solution_text += f"{i+1}. {move}\n"
                    
                    success = "FAILED" not in solution_moves
                    if success:
                        solution_text += "\n✅ AI found a successful path!"
                    else:
                        solution_text += "\n❌ AI could not find a guaranteed safe solution."
                    
                    try:
                        messagebox.showinfo("AI Solution Path", solution_text, parent=self.master)
                        self.status_label.config(text="Solution found and displayed")
                    except:
                        print("Window closed during showing message")
                else:
                    try:
                        messagebox.showinfo("AI Solution", "No solution path was found by the AI.", parent=self.master)
                        self.status_label.config(text="No solution path found")
                    except:
                        print("Window closed during showing message")
            except Exception as e:
                print(f"Error in displaying results: {str(e)}")
            
        except Exception as e:
            print(f"Error in solver: {str(e)}")
            try:
                messagebox.showerror("Solver Error", f"An error occurred during solving: {str(e)}", parent=self.master)
                self.status_label.config(text="Error during AI solving")
            except:
                print("Window closed during error reporting")

# --- Helper Functions for Setup ---
# ... (get_grid_size remains the same) ...
# ... (get_positions remains the same, uses root for parenting) ...
def get_grid_size(parent):
    """
    Asks the user to input the grid size for the Wumpus World.
    Returns the grid size as an integer, or None if canceled.
    """
    try:
        size = simpledialog.askinteger(
            "Grid Size", 
            "Enter grid size (e.g., 4):", 
            minvalue=2, 
            maxvalue=10,
            parent=parent
        )
        return size
    except Exception as e:
        messagebox.showerror("Error", f"Invalid grid size: {str(e)}", parent=parent)
        return None

def create_position_indicator(self, parent_frame):
    """Creates a visual indicator showing the agent's current position in the grid."""
    position_frame = tk.LabelFrame(parent_frame, text="Agent Position", font=("Arial", 10, "bold"),
                                 bg=self.colors['background'], fg=self.colors['text'], padx=10, pady=10)
    position_frame.pack(pady=10, fill="x")

    self.position_label = tk.Label(position_frame, 
                                  text="Position: (?, ?)",
                                  font=("Arial", 12),
                                  bg=self.colors['background'],
                                  fg=self.colors['text'])
    self.position_label.pack(pady=5)

    # Add a sense indicator to show what the agent perceives
    self.sense_label = tk.Label(position_frame,
                               text="Senses: None",
                               font=("Arial", 10),
                               bg=self.colors['background'],
                               fg=self.colors['text'],
                               wraplength=180,
                               justify='left')
    self.sense_label.pack(pady=5)

def create_status_labels(self, parent_frame):
    """Creates status labels for game information."""
    status_frame = tk.LabelFrame(parent_frame, text="Game Status", font=("Arial", 10, "bold"),
                               bg=self.colors['background'], fg=self.colors['text'], padx=10, pady=10)
    status_frame.pack(pady=10, fill="x")

    # Status message label
    self.status_label = tk.Label(status_frame, 
                                text="Find the gold and return to start!",
                                font=("Arial", 10),
                                bg=self.colors['background'],
                                fg=self.colors['text'],
                                wraplength=180,
                                justify='left')
    self.status_label.pack(pady=5, fill="x")

    # Score label
    self.score_label = tk.Label(status_frame,
                               text=f"Score: {self.world.score}",
                               font=("Arial", 12, "bold"),
                               bg=self.colors['background'],
                               fg=self.colors['text'])
    self.score_label.pack(pady=5)

    # Gold status indicator with initial state
    gold_status = "Gold: Found! 🏆" if self.world.has_gold else "Gold: Not Found"
    gold_color = "gold" if self.world.has_gold else self.colors['text']
    
    self.gold_label = tk.Label(status_frame,
                              text=gold_status,
                              font=("Arial", 10),
                              bg=self.colors['background'],
                              fg=gold_color)
    self.gold_label.pack(pady=5)

def get_positions(size, parent):
    """
    Gets the positions for the agent, wumpus, gold, and pits.
    """
    def get_valid_position(prompt):
        while True:
            try:
                pos = simpledialog.askstring(
                    "Position Input", 
                    prompt + f"\n(Enter as x,y where 1,1 is bottom-left and {size},{size} is top-right)",
                    parent=parent
                )
                if pos is None:  # User clicked Cancel
                    return None
                    
                x, y = map(int, pos.strip().split(','))
                if 1 <= x <= size and 1 <= y <= size:
                    # Convert from user coordinates (starting at 1,1) to internal coordinates (starting at 0,0)
                    return (y-1, x-1)  # Convert and swap to match internal representation
                else:
                    messagebox.showerror(
                        "Invalid Input", 
                        f"Coordinates must be within (1,1) to ({size},{size})",
                        parent=parent
                    )
            except Exception as e:
                messagebox.showerror(
                    "Invalid Input", 
                    f"Please enter format: x,y (e.g., 2,3)\nError: {str(e)}",
                    parent=parent
                )

    # Get agent position (default to bottom-left)
    agent_pos = simpledialog.askstring(
        "Agent Position",
        f"Enter Agent position (x,y) or leave empty for default (1,1):",
        parent=parent
    )
    
    if agent_pos is None:  # User clicked Cancel
        return None
    
    if agent_pos.strip() == "":
        agent_pos = (0, 0)  # Default to bottom-left (0,0) in internal coordinates
    else:
        try:
            x, y = map(int, agent_pos.strip().split(','))
            if 1 <= x <= size and 1 <= y <= size:
                agent_pos = (y-1, x-1)  # Convert to internal coordinates
            else:
                messagebox.showerror(
                    "Invalid Input", 
                    f"Agent coordinates must be within (1,1) to ({size},{size})",
                    parent=parent
                )
                return None
        except Exception:
            messagebox.showerror(
                "Invalid Input", 
                "Please enter format: x,y (e.g., 2,3) for agent position",
                parent=parent
            )
            return None
    
    # Get wumpus position
    wumpus_pos = get_valid_position("Enter Wumpus position")
    if wumpus_pos is None:
        return None
    
    # Get gold position
    gold_pos = get_valid_position("Enter Gold position")
    if gold_pos is None:
        return None
    
    # Get pit positions
    try:
        pit_count = simpledialog.askinteger(
            "Pit Count", 
            "How many pits?", 
            minvalue=0, 
            maxvalue=(size * size - 3),  # Max pits (excluding agent, wumpus, gold)
            parent=parent
        )
        
        if pit_count is None:  # User clicked Cancel
            return None
    except Exception:
        messagebox.showerror("Invalid Input", "Please enter a valid number of pits", parent=parent)
        return None
    
    pits = []
    for i in range(pit_count):
        pit_pos = get_valid_position(f"Enter Pit {i+1} position")
        if pit_pos is None:
            return None
        pits.append(pit_pos)
    
    return {
        'agent': agent_pos,
        'wumpus': wumpus_pos,
        'gold': gold_pos,
        'pits': pits
    }

# --- Main Execution ---
# Add this function to make it launchable from the Flask app
def launch_wumpus(self):
    """Launch the Wumpus World demo with configuration options"""
    self.clear_content()
    
    # Description frame
    desc_frame = Frame(self.content_frame, bg="#f5f5f5", padx=10, pady=10)
    desc_frame.pack(fill=X)
    
    title = Label(desc_frame, text="Wumpus World", font=("Arial", 18, "bold"), bg="#f5f5f5")
    title.pack(anchor="w")
    
    description = """
    The Wumpus World is a classic AI problem where an agent must navigate through a dangerous cave to find gold.
    The cave contains a gold treasure, deadly pits, and a monster called the Wumpus.
    
    The agent uses logical reasoning to identify safe squares and find a path to the gold.
    
    Configure your world below:
    """
    
    desc_label = Label(desc_frame, text=description, font=("Arial", 11), 
                       bg="#f5f5f5", justify=LEFT, wraplength=600)
    desc_label.pack(anchor="w", pady=10)
    
    # Configuration frame
    config_frame = Frame(self.content_frame, bg="#f5f5f5", padx=10, pady=10)
    config_frame.pack(fill=X)
    
    # Grid size selection
    size_frame = Frame(config_frame, bg="#f5f5f5")
    size_frame.pack(anchor="w", pady=5)
    
    Label(size_frame, text="Grid Size:", font=("Arial", 11), bg="#f5f5f5").pack(side=LEFT, padx=(0, 10))
    
    size_var = StringVar(value="4")
    size_combo = ttk.Combobox(size_frame, textvariable=size_var, values=["3", "4", "5", "6"], width=5)
    size_combo.pack(side=LEFT)
    
    # Wumpus position
    wumpus_frame = Frame(config_frame, bg="#f5f5f5")
    wumpus_frame.pack(anchor="w", pady=5)
    
    Label(wumpus_frame, text="Wumpus Position (x,y):", font=("Arial", 11), bg="#f5f5f5").pack(side=LEFT, padx=(0, 10))
    
    wumpus_var = StringVar(value="2,1")
    wumpus_entry = ttk.Entry(wumpus_frame, textvariable=wumpus_var, width=10)
    wumpus_entry.pack(side=LEFT)
    
    # Gold position
    gold_frame = Frame(config_frame, bg="#f5f5f5")
    gold_frame.pack(anchor="w", pady=5)
    
    Label(gold_frame, text="Gold Position (x,y):", font=("Arial", 11), bg="#f5f5f5").pack(side=LEFT, padx=(0, 10))
    
    gold_var = StringVar(value="1,3")
    gold_entry = ttk.Entry(gold_frame, textvariable=gold_var, width=10)
    gold_entry.pack(side=LEFT)
    
    # Pit positions
    pit_frame = Frame(config_frame, bg="#f5f5f5")
    pit_frame.pack(anchor="w", pady=5)
    
    Label(pit_frame, text="Pit Positions (x1,y1;x2,y2;...):", font=("Arial", 11), bg="#f5f5f5").pack(side=LEFT, padx=(0, 10))
    
    pit_var = StringVar(value="0,2;2,3")
    pit_entry = ttk.Entry(pit_frame, textvariable=pit_var, width=20)
    pit_entry.pack(side=LEFT)
    
    # Note with coordinate info
    note_text = "Note: Coordinates start at (0,0) at the bottom-left corner."
    note_label = Label(config_frame, text=note_text, font=("Arial", 10, "italic"), bg="#f5f5f5", fg="#666")
    note_label.pack(anchor="w", pady=(5, 10))
    
    # Launch button
    launch_frame = Frame(self.content_frame, bg="#f5f5f5", pady=15)
    launch_frame.pack()
    
    def on_launch():
        # Get the configuration values
        size = int(size_var.get())
        
        try:
            wx, wy = map(int, wumpus_var.get().split(','))
            gx, gy = map(int, gold_var.get().split(','))
            
            pit_positions = []
            if pit_var.get().strip():
                for pit_pos in pit_var.get().split(';'):
                    if pit_pos.strip():
                        px, py = map(int, pit_pos.strip().split(','))
                        pit_positions.append((px, py))
            
            # Launch with the provided configuration
            self.run_wumpus_world_with_config(size, (wx, wy), (gx, gy), pit_positions)
        except Exception as e:
            self.wumpus_status.set(f"Error parsing positions: {str(e)}")
    
    launch_btn = Button(launch_frame, text="Launch Wumpus World", font=("Arial", 12, "bold"),
                        bg="#3498db", fg="white", padx=15, pady=10,
                        command=on_launch)
    launch_btn.pack()
    
    # Status label
    self.wumpus_status = StringVar(value="Configure the Wumpus World and click Launch.")
    status_label = Label(self.content_frame, textvariable=self.wumpus_status, 
                         font=("Arial", 10), bg="#f5f5f5", fg="#555555")
    status_label.pack(pady=10)

def run_wumpus_world_with_config(self, size, wumpus_pos, gold_pos, pit_positions):
    """Run the Wumpus World with the specified configuration"""
    try:
        self.wumpus_status.set("Launching Wumpus World...")
        
        if "wumpus_module" not in self.modules:
            self.wumpus_status.set("Error: Wumpus World module not loaded.")
            return
        
        # Create a new thread to run the Wumpus World
        def run_app():
            try:
                # Get a reference to the module
                wumpus_module = self.modules["wumpus_module"]
                
                # Create a new Tkinter window for the Wumpus World
                wumpus_window = tk.Toplevel(self)
                wumpus_window.title("Wumpus World")
                wumpus_window.geometry("900x700")
                
                # Initialize the Wumpus World with the specified size
                world = wumpus_module.WumpusWorld(size)
                
                # Set agent position (bottom-left corner)
                world.agent_pos = (0, 0)
                
                # Set wumpus position
                try:
                    wx, wy = wumpus_pos
                    world.set_wumpus(wx, wy)
                except Exception as e:
                    print(f"Error setting wumpus: {e}")
                
                # Set gold position
                try:
                    gx, gy = gold_pos
                    world.set_gold(gx, gy)
                except Exception as e:
                    print(f"Error setting gold: {e}")
                
                # Add pits
                for pit_pos in pit_positions:
                    try:
                        px, py = pit_pos
                        world.set_pit(px, py)
                    except Exception as e:
                        print(f"Error setting pit at {pit_pos}: {e}")
                
                # Create the UI with the configured world
                app = wumpus_module.WumpusWorldUI(wumpus_window, world)
                
                # Store a reference to the window
                self.module_windows["wumpus"] = wumpus_window
                
                self.wumpus_status.set("Wumpus World launched successfully!")
            except Exception as e:
                import traceback
                traceback.print_exc()
                self.wumpus_status.set(f"Error launching Wumpus World: {e}")
        
        # Start the thread
        threading.Thread(target=run_app).start()
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        self.wumpus_status.set(f"Error: {str(e)}")

if __name__ == "__main__":
    launch_wumpus()