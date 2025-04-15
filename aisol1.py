import tkinter as tk
from tkinter import ttk, Frame, Label, Button, TOP, BOTH, X, Y, LEFT, RIGHT, BOTTOM, RAISED, StringVar
import sys
import importlib.util
import os
import threading

class AISolverHub(tk.Tk):
    def __init__(self):
        super().__init__()
        
        self.title("AI Solver Hub")
        self.geometry("1000x700")
        self.configure(bg="#f5f5f5")
        
        self.create_header()
        self.create_menu()
        self.create_content_frame()
        
        # Dictionary to store module references
        self.modules = {}
        self.module_windows = {}
        
        # Load modules
        self.load_modules()
        
        # Initialize with welcome screen
        self.show_welcome()
    
    def create_header(self):
        header_frame = Frame(self, bg="#3498db", padx=20, pady=10)
        header_frame.pack(fill=X)
        
        title_label = Label(header_frame, text="AI Solver Hub", 
                            font=("Arial", 24, "bold"), bg="#3498db", fg="white")
        title_label.pack()
        
        subtitle_label = Label(header_frame, text="Explore AI Problem Solving Algorithms", 
                               font=("Arial", 12), bg="#3498db", fg="white")
        subtitle_label.pack(pady=(5, 0))
    
    def create_menu(self):
        menu_frame = Frame(self, bg="#2c3e50", padx=15, pady=15)
        menu_frame.pack(side=LEFT, fill=Y)
        
        # Title for the menu
        menu_title = Label(menu_frame, text="Select Demo", font=("Arial", 14, "bold"), 
                           bg="#2c3e50", fg="white", pady=10)
        menu_title.pack(fill=X)
        
        # Menu buttons
        self.create_menu_button(menu_frame, "Wumpus World", self.launch_wumpus)
        self.create_menu_button(menu_frame, "Cryptarithmetic", self.launch_cryptarithmetic)
        self.create_menu_button(menu_frame, "Minimax & Alpha-Beta", self.launch_minimax)
        self.create_menu_button(menu_frame, "Tic-Tac-Toe AI", self.launch_tictactoe)
        
        separator = ttk.Separator(menu_frame, orient="horizontal")
        separator.pack(fill=X, pady=15)
        
        self.create_menu_button(menu_frame, "Exit", self.quit, bg="#e74c3c")
    
    def create_menu_button(self, parent, text, command, bg="#3498db"):
        button = Button(parent, text=text, font=("Arial", 12), 
                        bg=bg, fg="white", padx=10, pady=8,
                        relief=RAISED, bd=0, width=20,
                        activebackground="#2980b9", activeforeground="white",
                        command=command)
        button.pack(fill=X, pady=5)
        return button
    
    def create_content_frame(self):
        self.content_frame = Frame(self, bg="#f5f5f5", padx=20, pady=20)
        self.content_frame.pack(side=RIGHT, fill=BOTH, expand=True)
    
    def clear_content(self):
        # Destroy all widgets in the content frame
        for widget in self.content_frame.winfo_children():
            widget.destroy()
    
    def show_welcome(self):
        self.clear_content()
        
        # Welcome message
        welcome_label = Label(self.content_frame, text="Welcome to AI Solver Hub", 
                             font=("Arial", 20, "bold"), bg="#f5f5f5")
        welcome_label.pack(pady=(30, 10))
        
        description = """
        This application showcases various AI algorithms for solving different types of problems.
        
        You can explore the following demos from the menu:
        
        • Wumpus World: Navigate through a dangerous cave to find gold
        • Cryptarithmetic: Solve letter-digit substitution puzzles
        • Minimax & Alpha-Beta: Compare search algorithms for game trees
        • Tic-Tac-Toe AI: Play against an unbeatable AI opponent
        
        Select a demo from the menu to get started!
        """
        
        desc_label = Label(self.content_frame, text=description, font=("Arial", 12), 
                          bg="#f5f5f5", justify=LEFT, wraplength=600)
        desc_label.pack(pady=20)
    
    def load_modules(self):
        """Load all the module files dynamically"""
        # Different possible naming patterns
        wumpus_files = ["wumpus demo4.py", "wumpus_demo4.py", "wumpusdemo4.py"]
        cript_files = ["criptdemo1.py", "cript_demo1.py", "cript demo1.py"]
        alpha_files = ["mini alpha.py", "mini_alpha.py", "minialpha.py"]
        tictactoe_files = ["ticktack.py", "tictactoe.py", "tic_tac_toe.py"]
        
        # Try each possible file name
        for wumpus_file in wumpus_files:
            if self.load_module("wumpus_module", wumpus_file):
                break
        
        for cript_file in cript_files:
            if self.load_module("cript_module", cript_file):
                break
        
        for alpha_file in alpha_files:
            if self.load_module("alpha_module", alpha_file):
                break
        
        for tictactoe_file in tictactoe_files:
            if self.load_module("tictactoe_module", tictactoe_file):
                break
    
    def load_module(self, module_name, file_path):
        """Load a specific module dynamically with better error handling"""
        try:
            print(f"Attempting to load {module_name} from {file_path}")
            # Try to find the file in current directory
            if not os.path.exists(file_path):
                print(f"File not found: {file_path}")
                # Try with full path
                full_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), file_path)
                print(f"Trying full path: {full_path}")
                if os.path.exists(full_path):
                    file_path = full_path
                else:
                    print(f"File also not found at: {full_path}")
                    return False
                
            spec = importlib.util.spec_from_file_location(module_name, file_path)
            if spec is None:
                print(f"Failed to create spec for {module_name}")
                return False
            
            module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = module
            spec.loader.exec_module(module)
            self.modules[module_name] = module
            print(f"Successfully loaded {module_name}")
            return True
        except Exception as e:
            print(f"Error loading module {module_name} from {file_path}: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def launch_wumpus(self):
        """Launch the Wumpus World demo"""
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
        """
        
        desc_label = Label(desc_frame, text=description, font=("Arial", 11), 
                          bg="#f5f5f5", justify=LEFT, wraplength=600)
        desc_label.pack(anchor="w", pady=10)
        
        # Launch button
        launch_frame = Frame(self.content_frame, bg="#f5f5f5", pady=15)
        launch_frame.pack()
        
        launch_btn = Button(launch_frame, text="Launch Wumpus World", font=("Arial", 12, "bold"),
                           bg="#3498db", fg="white", padx=15, pady=10,
                           command=self.run_wumpus_world)
        launch_btn.pack()
        
        # Status label
        self.wumpus_status = StringVar(value="Click the button to launch the Wumpus World demo.")
        status_label = Label(self.content_frame, textvariable=self.wumpus_status, 
                            font=("Arial", 10), bg="#f5f5f5", fg="#555555")
        status_label.pack(pady=10)
    
    def run_wumpus_world(self):
        """Run the Wumpus World application with forced image loading"""
        try:
            if "wumpus_module" not in self.modules:
                self.wumpus_status.set("Error: Wumpus World module not loaded.")
                return
            
            # Get reference to the module
            wumpus_module = self.modules["wumpus_module"]
            
            # First get grid size
            size = tk.simpledialog.askinteger("Grid Size", 
                                             "Enter grid size (2-10):", 
                                             parent=self,
                                             minvalue=2, maxvalue=10,
                                             initialvalue=4)
            if size is None:
                self.wumpus_status.set("Setup canceled.")
                return
            
            # Ask for agent position - default 1,1
            agent_pos = tk.simpledialog.askstring("Agent Position", 
                                                 f"Enter Agent position (x,y) from (1,1) to ({size},{size}):", 
                                                 parent=self,
                                                 initialvalue="1,1")
            if agent_pos is None:
                self.wumpus_status.set("Setup canceled.")
                return
            
            # Get wumpus position - default 1,3
            wumpus_pos = tk.simpledialog.askstring("Wumpus Position", 
                                                  f"Enter Wumpus position (x,y) from (1,1) to ({size},{size}):", 
                                                  parent=self,
                                                  initialvalue="1,3")
            if wumpus_pos is None:
                self.wumpus_status.set("Setup canceled.")
                return
            
            # Get gold position - default 2,3  
            gold_pos = tk.simpledialog.askstring("Gold Position", 
                                               f"Enter Gold position (x,y) from (1,1) to ({size},{size}):", 
                                               parent=self,
                                               initialvalue="2,3")
            if gold_pos is None:
                self.wumpus_status.set("Setup canceled.")
                return
            
            # Get pit positions - defaults as specified
            pit_pos = tk.simpledialog.askstring("Pit Positions", 
                                              f"Enter Pit positions (x1,y1;x2,y2;...) from (1,1) to ({size},{size}):", 
                                              parent=self,
                                              initialvalue="3,1;3,3;4,4")
            if pit_pos is None:
                self.wumpus_status.set("Setup canceled.")
                return
            
            # Parse the positions
            try:
                # Parse agent position
                agent_x, agent_y = map(int, agent_pos.split(','))
                
                # Parse wumpus position
                wumpus_x, wumpus_y = map(int, wumpus_pos.split(','))
                
                # Parse gold position
                gold_x, gold_y = map(int, gold_pos.split(','))
                
                # Parse pit positions
                pits = []
                if pit_pos.strip():
                    for pos in pit_pos.split(';'):
                        if pos.strip():
                            px, py = map(int, pos.strip().split(','))
                            pits.append((px, py))
                            
                # Validate positions
                if not (1 <= agent_x <= size and 1 <= agent_y <= size):
                    tk.messagebox.showerror("Error", f"Agent position must be within (1,1) to ({size},{size})")
                    return
                    
                if not (1 <= wumpus_x <= size and 1 <= wumpus_y <= size):
                    tk.messagebox.showerror("Error", f"Wumpus position must be within (1,1) to ({size},{size})")
                    return
                    
                if not (1 <= gold_x <= size and 1 <= gold_y <= size):
                    tk.messagebox.showerror("Error", f"Gold position must be within (1,1) to ({size},{size})")
                    return
                    
                for px, py in pits:
                    if not (1 <= px <= size and 1 <= py <= size):
                        tk.messagebox.showerror("Error", f"Pit position ({px},{py}) must be within (1,1) to ({size},{size})")
                        return
                
                # Check for overlaps
                position_set = {(agent_x, agent_y), (wumpus_x, wumpus_y), (gold_x, gold_y)}
                if len(position_set) < 3:  # If there are duplicates
                    tk.messagebox.showerror("Error", "Agent, Wumpus, and Gold must have different positions")
                    return
                
                for px, py in pits:
                    if (px, py) in position_set:
                        tk.messagebox.showerror("Error", f"Pit at ({px},{py}) overlaps with another element")
                        return
            
            except Exception as e:
                tk.messagebox.showerror("Error", f"Invalid position format: {str(e)}")
                return
            
            # Create and launch the Wumpus World
            self.wumpus_status.set("Launching Wumpus World...")
            
            # Create the window
            wumpus_window = tk.Toplevel(self)
            wumpus_window.title("Wumpus World")
            wumpus_window.geometry("900x700")
            
            # Initialize the world
            world = wumpus_module.WumpusWorld(size)
            
            # Debug print to understand the internal coordinate system
            print(f"Agent coordinates: User input={agent_x},{agent_y}, Internal={(agent_y-1, agent_x-1)}")
            print(f"Wumpus coordinates: User input={wumpus_x},{wumpus_y}, Internal={(wumpus_y-1, wumpus_x-1)}")
            print(f"Gold coordinates: User input={gold_x},{gold_y}, Internal={(gold_y-1, gold_x-1)}")
            for i, (px, py) in enumerate(pits):
                print(f"Pit {i+1} coordinates: User input={px},{py}, Internal={(py-1, px-1)}")
            
            # Convert from 1-based to 0-based coordinates and swap x,y to match internal format
            world.agent_pos = (agent_y-1, agent_x-1)
            world.set_wumpus(wumpus_y-1, wumpus_x-1)
            world.set_gold(gold_y-1, gold_x-1)
            
            for px, py in pits:
                world.set_pit(py-1, px-1)
            
            # Create the UI
            app = wumpus_module.WumpusWorldUI(wumpus_window, world)
            
            # Store reference to window
            self.module_windows["wumpus"] = wumpus_window
            
            self.wumpus_status.set("Wumpus World launched successfully!")
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            self.wumpus_status.set(f"Error: {str(e)}")
    
    def launch_cryptarithmetic(self):
        """Launch the Cryptarithmetic demo"""
        self.clear_content()
        
        # Description frame
        desc_frame = Frame(self.content_frame, bg="#f5f5f5", padx=10, pady=10)
        desc_frame.pack(fill=X)
        
        title = Label(desc_frame, text="Cryptarithmetic Solver", font=("Arial", 18, "bold"), bg="#f5f5f5")
        title.pack(anchor="w")
        
        description = """
        Cryptarithmetic is a type of mathematical puzzle where letters represent digits in an arithmetic equation.
        The goal is to find the digit substitution that makes the equation true.
        
        A classic example is: SEND + MORE = MONEY
        
        This solver uses constraint satisfaction to find the solution.
        """
        
        desc_label = Label(desc_frame, text=description, font=("Arial", 11), 
                          bg="#f5f5f5", justify=LEFT, wraplength=600)
        desc_label.pack(anchor="w", pady=10)
        
        # Examples
        examples_frame = Frame(desc_frame, bg="#f5f5f5")
        examples_frame.pack(anchor="w", pady=10)
        
        Label(examples_frame, text="Examples:", font=("Arial", 11, "bold"), 
             bg="#f5f5f5").pack(anchor="w")
        
        examples = [
            "SEND + MORE = MONEY",
            "TWO + TWO = FOUR",
            "BASE + BALL = GAMES"
        ]
        
        for example in examples:
            Label(examples_frame, text=f"• {example}", font=("Arial", 11), 
                 bg="#f5f5f5").pack(anchor="w", padx=(20, 0))
        
        # Launch button
        launch_frame = Frame(self.content_frame, bg="#f5f5f5", pady=15)
        launch_frame.pack()
        
        launch_btn = Button(launch_frame, text="Launch Cryptarithmetic Solver", font=("Arial", 12, "bold"),
                           bg="#3498db", fg="white", padx=15, pady=10,
                           command=self.run_cryptarithmetic)
        launch_btn.pack()
        
        # Status label
        self.crypt_status = StringVar(value="Click the button to launch the Cryptarithmetic Solver.")
        status_label = Label(self.content_frame, textvariable=self.crypt_status, 
                            font=("Arial", 10), bg="#f5f5f5", fg="#555555")
        status_label.pack(pady=10)
    
    def run_cryptarithmetic(self):
        """Run the Cryptarithmetic Solver in a new window"""
        try:
            self.crypt_status.set("Launching Cryptarithmetic Solver...")
            
            if "cript_module" not in self.modules:
                self.crypt_status.set("Error: Cryptarithmetic module not loaded.")
                return
            
            # Create a new thread to run the Cryptarithmetic Solver
            def run_app():
                try:
                    # Get a reference to the module
                    cript_module = self.modules["cript_module"]
                    
                    # Create a new Tkinter window
                    crypt_window = tk.Toplevel(self)
                    crypt_window.title("Cryptarithmetic Solver")
                    crypt_window.geometry("600x550")
                    
                    # Initialize the Cryptarithmetic app
                    app = cript_module.CryptarithmeticApp(crypt_window)
                    
                    # Store a reference to the window
                    self.module_windows["cryptarithmetic"] = crypt_window
                    
                    self.crypt_status.set("Cryptarithmetic Solver launched successfully!")
                except Exception as e:
                    self.crypt_status.set(f"Error launching Cryptarithmetic Solver: {e}")
            
            # Start the thread
            threading.Thread(target=run_app).start()
            
        except Exception as e:
            self.crypt_status.set(f"Error: {str(e)}")
    
    def launch_minimax(self):
        """Launch the Minimax & Alpha-Beta demo"""
        self.clear_content()
        
        # Description frame
        desc_frame = Frame(self.content_frame, bg="#f5f5f5", padx=10, pady=10)
        desc_frame.pack(fill=X)
        
        title = Label(desc_frame, text="Minimax & Alpha-Beta Pruning", font=("Arial", 18, "bold"), bg="#f5f5f5")
        title.pack(anchor="w")
        
        description = """
        Minimax is a decision-making algorithm used in game theory and artificial intelligence.
        It's commonly used for two-player games to find the optimal move.
        
        Alpha-Beta Pruning is an optimization technique for the Minimax algorithm that reduces
        the number of nodes evaluated in the search tree.
        
        This demo allows you to compare the performance of both algorithms on the same game tree.
        """
        
        desc_label = Label(desc_frame, text=description, font=("Arial", 11), 
                          bg="#f5f5f5", justify=LEFT, wraplength=600)
        desc_label.pack(anchor="w", pady=10)
        
        # Launch button
        launch_frame = Frame(self.content_frame, bg="#f5f5f5", pady=15)
        launch_frame.pack()
        
        launch_btn = Button(launch_frame, text="Launch Minimax Comparison", font=("Arial", 12, "bold"),
                           bg="#3498db", fg="white", padx=15, pady=10,
                           command=self.run_minimax)
        launch_btn.pack()
        
        # Status label
        self.minimax_status = StringVar(value="Click the button to launch the Minimax Comparison demo.")
        status_label = Label(self.content_frame, textvariable=self.minimax_status, 
                            font=("Arial", 10), bg="#f5f5f5", fg="#555555")
        status_label.pack(pady=10)
    
    def run_minimax(self):
        """Run the Minimax Comparison in a new window with a predefined sample tree"""
        try:
            self.minimax_status.set("Launching Minimax Comparison...")
            
            if "alpha_module" not in self.modules:
                self.minimax_status.set("Error: Minimax module not loaded.")
                return
            
            # Create a new thread to run the Minimax Comparison
            def run_app():
                try:
                    # Get a reference to the module
                    alpha_module = self.modules["alpha_module"]
                    
                    # Create a new Tkinter window
                    minimax_window = tk.Toplevel(self)
                    minimax_window.title("Minimax & Alpha-Beta Pruning Comparison")
                    minimax_window.geometry("1000x680")
                    
                    # Initialize the Minimax app
                    app = alpha_module.MinimaxComparisonApp(minimax_window)
                    
                    # Define a sample tree if the app has a tree_definition_text attribute
                    if hasattr(app, 'tree_definition_text'):
                        sample_tree = """A: children=[B, C]
B: children=[D, E]
C: children=[F, G]
D: value=3
E: value=5
F: value=6
G: value=9"""
                        app.tree_definition_text.delete("1.0", tk.END)
                        app.tree_definition_text.insert("1.0", sample_tree)
                        
                        # If the app has a parse_text_definition method, call it to parse the tree
                        if hasattr(app, 'parse_text_definition') and callable(app.parse_text_definition):
                            app.parse_text_definition()
                        
                        # Set root node if there's a field for it
                        if hasattr(app, 'root_node_entry'):
                            app.root_node_entry.delete(0, tk.END)
                            app.root_node_entry.insert(0, "A")
                    
                    # Store a reference to the window
                    self.module_windows["minimax"] = minimax_window
                    
                    self.minimax_status.set("Minimax Comparison launched successfully!")
                except Exception as e:
                    import traceback
                    traceback.print_exc()
                    self.minimax_status.set(f"Error launching Minimax Comparison: {e}")
            
            # Start the thread
            threading.Thread(target=run_app).start()
            
        except Exception as e:
            self.minimax_status.set(f"Error: {str(e)}")
    
    def launch_tictactoe(self):
        """Launch the Tic-Tac-Toe AI demo"""
        self.clear_content()
        
        # Description frame
        desc_frame = Frame(self.content_frame, bg="#f5f5f5", padx=10, pady=10)
        desc_frame.pack(fill=X)
        
        title = Label(desc_frame, text="Tic-Tac-Toe AI", font=("Arial", 18, "bold"), bg="#f5f5f5")
        title.pack(anchor="w")
        
        description = """
        Play Tic-Tac-Toe against an AI opponent that uses the Minimax algorithm.
        
        The AI explores all possible game states to make the optimal move, which means
        it's effectively unbeatable. The best outcome you can achieve is a draw.
        
        This demonstration shows how the Minimax algorithm can be applied to a simple game.
        """
        
        desc_label = Label(desc_frame, text=description, font=("Arial", 11), 
                          bg="#f5f5f5", justify=LEFT, wraplength=600)
        desc_label.pack(anchor="w", pady=10)
        
        # Launch button
        launch_frame = Frame(self.content_frame, bg="#f5f5f5", pady=15)
        launch_frame.pack()
        
        launch_btn = Button(launch_frame, text="Launch Tic-Tac-Toe Game", font=("Arial", 12, "bold"),
                           bg="#3498db", fg="white", padx=15, pady=10,
                           command=self.run_tictactoe)
        launch_btn.pack()
        
        # Status label
        self.tictactoe_status = StringVar(value="Click the button to launch the Tic-Tac-Toe game.")
        status_label = Label(self.content_frame, textvariable=self.tictactoe_status, 
                            font=("Arial", 10), bg="#f5f5f5", fg="#555555")
        status_label.pack(pady=10)
    
    def run_tictactoe(self):
        """Run the Tic-Tac-Toe game in a new window"""
        try:
            self.tictactoe_status.set("Launching Tic-Tac-Toe...")
            
            if "tictactoe_module" not in self.modules:
                self.tictactoe_status.set("Error: Tic-Tac-Toe module not loaded.")
                return
            
            # Create a new thread to run the Tic-Tac-Toe game
            def run_app():
                try:
                    # Get a reference to the module
                    tictactoe_module = self.modules["tictactoe_module"]
                    
                    # Create a new Tkinter window
                    tictactoe_window = tk.Toplevel(self)
                    tictactoe_window.title("Tic-Tac-Toe AI")
                    tictactoe_window.geometry("450x600")
                    
                    # Initialize the Tic-Tac-Toe app
                    app = tictactoe_module.TicTacToeApp(tictactoe_window)
                    
                    # Store a reference to the window
                    self.module_windows["tictactoe"] = tictactoe_window
                    
                    self.tictactoe_status.set("Tic-Tac-Toe launched successfully!")
                except Exception as e:
                    self.tictactoe_status.set(f"Error launching Tic-Tac-Toe: {e}")
            
            # Start the thread
            threading.Thread(target=run_app).start()
            
        except Exception as e:
            self.tictactoe_status.set(f"Error: {str(e)}")

def launch_app():
    """Launch the main AI Solver Hub application"""
    app = AISolverHub()
    app.mainloop()

if __name__ == "__main__":
    launch_app()