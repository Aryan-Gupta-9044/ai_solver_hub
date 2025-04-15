import tkinter as tk
from tkinter import ttk, messagebox
import re
import time
import math
import threading

# --- Algorithm Implementation ---
def minimax_with_path(node_name, tree, is_maximizing, depth=None):
    node = tree[node_name]
    
    # Base case: terminal node or depth limit reached
    if node['is_terminal']:
        return node['value'], [node_name]
    if depth is not None and depth <= 0:
        # Return a heuristic value at depth limit (or a default value)
        # For simplicity, we'll use 0 as the heuristic when depth limit is reached
        return 0, [node_name]
    
    children = node['children']
    if not children:  # Safety check for non-terminal with no children
        return 0, [node_name]
    
    best_path = []
    if is_maximizing:
        best_value = -math.inf
        for child in children:
            value, path = minimax_with_path(child, tree, False, None if depth is None else depth - 1)
            if value > best_value:
                best_value = value
                best_path = [node_name] + path
    else:  # Minimizing player
        best_value = math.inf
        for child in children:
            value, path = minimax_with_path(child, tree, True, None if depth is None else depth - 1)
            if value < best_value:
                best_value = value
                best_path = [node_name] + path
    
    return best_value, best_path

def alpha_beta_with_path(node_name, tree, alpha, beta, is_maximizing, depth=None, pruned_info=None):
    if pruned_info is None:
        pruned_info = {"count": 0, "nodes": []}
    
    node = tree[node_name]
    
    # Base case: terminal node or depth limit reached
    if node['is_terminal']:
        return node['value'], [node_name], pruned_info
    if depth is not None and depth <= 0:
        # Return a heuristic value at depth limit
        return 0, [node_name], pruned_info
    
    children = node['children']
    if not children:  # Safety check
        return 0, [node_name], pruned_info
    
    best_path = []
    if is_maximizing:
        best_value = -math.inf
        for i, child in enumerate(children):
            value, path, pruned_info = alpha_beta_with_path(child, tree, alpha, beta, False, None if depth is None else depth - 1, pruned_info)
            if value > best_value:
                best_value = value
                best_path = [node_name] + path
            alpha = max(alpha, best_value)
            if beta <= alpha:
                # Beta cutoff - prune remaining children
                pruned_info["count"] += len(children) - (i + 1)
                for j in range(i + 1, len(children)):
                    pruned_info["nodes"].append(children[j])
                break  # Beta cutoff
    else:  # Minimizing player
        best_value = math.inf
        for i, child in enumerate(children):
            value, path, pruned_info = alpha_beta_with_path(child, tree, alpha, beta, True, None if depth is None else depth - 1, pruned_info)
            if value < best_value:
                best_value = value
                best_path = [node_name] + path
            beta = min(beta, best_value)
            if beta <= alpha:
                # Alpha cutoff - prune remaining children
                pruned_info["count"] += len(children) - (i + 1)
                for j in range(i + 1, len(children)):
                    pruned_info["nodes"].append(children[j])
                break  # Alpha cutoff
    
    return best_value, best_path, pruned_info

# --- GUI Application ---
class MinimaxComparisonApp:
    def __init__(self, master):
        self.master = master
        self.tree_data = {}  # Will store the parsed tree
        
        # Configure the window
        master.title("Minimax & Alpha-Beta Pruning Comparison")
        master.geometry("1000x680")
        master.minsize(800, 600)
        
        # Define styles and UI variables
        self.setup_styles()
        self.setup_ui_variables()
        
        # Create main layout
        self.setup_main_structure()
        
        # Set up the specific tabs
        self.setup_tree_definition_tab()
        self.setup_node_addition_tab()
        self.setup_tree_visualization_tab()
        self.setup_comparison_tab()
        
        # Setup status bar at bottom of window
        self.setup_status_bar()
        
    def setup_styles(self):
        self.style = ttk.Style()
        
        # Define some colors
        self.bg_color = "#f5f5f5"
        self.header_bg = "#4a6fa5"
        self.header_fg = "#ffffff"
        self.accent_color = "#6b8cae"
        self.button_color = "#5b8cb8"
        self.text_bg = "#ffffff"
        self.output_bg = "#f0f0f0"
        
        # Set theme and configure styles
        self.style.configure("TFrame", background=self.bg_color)
        self.style.configure("Header.TLabel", foreground=self.header_fg, background=self.header_bg, font=("Segoe UI", 14, "bold"))
        self.style.configure("HeaderBG.TLabel", foreground=self.header_fg, background=self.header_bg, font=("Segoe UI", 14, "bold"), padding=10, anchor="center")
        self.style.configure("TLabel", background=self.bg_color, font=("Segoe UI", 10))
        self.style.configure("TNotebook", background=self.bg_color)
        self.style.configure("TButton", font=("Segoe UI", 10))
        self.style.configure("Run.TButton", font=("Segoe UI", 12, "bold"))
        self.style.configure("Status.TLabel", background="#e0e0e0", padding=5)
        self.style.configure("Add.TButton", font=("Segoe UI", 10))
        self.style.configure("Output.TFrame", background=self.output_bg)
        self.style.configure("Value.TLabel", font=("Segoe UI", 12, "bold"))
        self.style.configure("Path.TLabel", font=("Segoe UI", 10))
        self.style.configure("AddNode.TFrame", background="#e8ecf0", relief="groove")
        
        # Font for code/text displays
        self.mono_font = ("Consolas", 10)
        
    def setup_ui_variables(self):
        self.status_var = tk.StringVar(value="Ready")
        self.depth_var = tk.StringVar(value="")
    
    def setup_main_structure(self):
        self.master.configure(background=self.bg_color)
        self.master.columnconfigure(0, weight=1)
        self.master.rowconfigure(0, weight=1)
        
        main_frame = ttk.Frame(self.master)
        main_frame.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(0, weight=1)
        
        # Create notebook with tabs
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.grid(row=0, column=0, sticky="nsew")
        
        # Create tab frames
        self.tree_tab = ttk.Frame(self.notebook)
        self.node_tab = ttk.Frame(self.notebook)
        self.viz_tab = ttk.Frame(self.notebook)
        self.comparison_tab = ttk.Frame(self.notebook)
        
        # Add tabs to notebook
        self.notebook.add(self.tree_tab, text="1. Define Tree")
        self.notebook.add(self.node_tab, text="2. Add Nodes")
        self.notebook.add(self.viz_tab, text="3. Visualize Tree")
        self.notebook.add(self.comparison_tab, text="4. Compare Algorithms")
        
    def setup_status_bar(self):
        status_frame = ttk.Frame(self.master, style="TFrame")
        status_frame.grid(row=1, column=0, sticky="ew", padx=5, pady=(0, 5))
        status_frame.columnconfigure(0, weight=1)
        
        self.status_label = ttk.Label(status_frame, textvariable=self.status_var, style="Status.TLabel", anchor="w")
        self.status_label.grid(row=0, column=0, sticky="ew")
        
    def setup_tree_definition_tab(self):
        tree_frame = ttk.Frame(self.tree_tab, padding=15)
        tree_frame.pack(fill=tk.BOTH, expand=True)
        
        # Top section with instructions
        ttk.Label(tree_frame, text="Tree Definition", style="HeaderBG.TLabel").pack(fill=tk.X, pady=(0, 10))
        ttk.Label(tree_frame, text="Define the game tree by specifying nodes and their relationships:").pack(anchor="w", pady=(0, 5))
        ttk.Label(tree_frame, text="• Non-terminal nodes: NodeName: children=[Child1, Child2, ...]").pack(anchor="w")
        ttk.Label(tree_frame, text="• Terminal nodes: NodeName: value=X").pack(anchor="w", pady=(0, 5))
        ttk.Label(tree_frame, text="Example: A: children=[B, C]").pack(anchor="w", pady=(0, 10))
        
        # Text area for tree definition
        text_frame = ttk.Frame(tree_frame)
        text_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        self.tree_definition_text = tk.Text(text_frame, height=15, font=self.mono_font, bg=self.text_bg)
        self.tree_definition_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(text_frame, orient=tk.VERTICAL, command=self.tree_definition_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree_definition_text['yscrollcommand'] = scrollbar.set
        
        # Buttons
        button_frame = ttk.Frame(tree_frame)
        button_frame.pack(fill=tk.X, pady=10)
        
        parse_button = ttk.Button(button_frame, text="Parse Tree Definition", command=self.parse_text_definition)
        parse_button.pack(side=tk.LEFT, padx=5)
        
        clear_button = ttk.Button(button_frame, text="Clear All", command=self.clear_all)
        clear_button.pack(side=tk.LEFT, padx=5)
        
        sample_button = ttk.Button(button_frame, text="Load Sample", command=lambda: self.tree_definition_text.insert("1.0", self._get_sample_tree_def()))
        sample_button.pack(side=tk.LEFT, padx=5)
        
        # Additional configuration for running the algorithms
        config_frame = ttk.Frame(tree_frame, style="Output.TFrame", padding=10)
        config_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Label(config_frame, text="Algorithm Configuration:", font=("Segoe UI", 11, "bold")).pack(anchor="w", pady=(0, 5))
        
        root_frame = ttk.Frame(config_frame)
        root_frame.pack(fill=tk.X, pady=5)
        ttk.Label(root_frame, text="Root Node Name:").pack(side=tk.LEFT, padx=(0, 5))
        self.root_node_entry = ttk.Entry(root_frame, width=15)
        self.root_node_entry.insert(0, "A")  # Default
        self.root_node_entry.pack(side=tk.LEFT)
        
        depth_frame = ttk.Frame(config_frame)
        depth_frame.pack(fill=tk.X, pady=5)
        ttk.Label(depth_frame, text="Max Depth (optional):").pack(side=tk.LEFT, padx=(0, 5))
        ttk.Entry(depth_frame, textvariable=self.depth_var, width=5).pack(side=tk.LEFT)
        ttk.Label(depth_frame, text="(Leave empty for unlimited depth)").pack(side=tk.LEFT, padx=5)
        
    def setup_comparison_tab(self):
        comparison_frame = ttk.Frame(self.comparison_tab, padding=15)
        comparison_frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(comparison_frame, text="Algorithm Comparison", style="HeaderBG.TLabel").pack(pady=(0, 15))
        
        # Run button
        button_frame = ttk.Frame(comparison_frame)
        button_frame.pack(fill=tk.X, pady=(0, 15))
        self.compare_button = ttk.Button(button_frame, text="Run Comparison", style="Run.TButton", command=self.run_comparison_threaded)
        self.compare_button.pack()
        
        # Results display
        output_frame = ttk.Frame(comparison_frame)
        output_frame.pack(fill=tk.BOTH, expand=True)
        output_frame.columnconfigure(0, weight=1)
        output_frame.columnconfigure(1, weight=1)
        
        minimax_frame = ttk.Frame(output_frame, style="Output.TFrame", padding=15)
        minimax_frame.grid(row=0, column=0, padx=(0, 10), pady=5, sticky="nsew")
        ttk.Label(minimax_frame, text="Minimax Result", style="Header.TLabel", anchor="center").pack(fill=tk.X, pady=(0, 10))
        ttk.Label(minimax_frame, text="Optimal Value:").pack(anchor='w')
        self.minimax_value_label = ttk.Label(minimax_frame, text="-", style="Value.TLabel")
        self.minimax_value_label.pack(anchor='w', pady=2)
        ttk.Label(minimax_frame, text="Optimal Path:").pack(anchor='w', pady=(10, 0))
        self.minimax_path_label = ttk.Label(minimax_frame, text="-", style="Path.TLabel", wraplength=350, justify=tk.LEFT)
        self.minimax_path_label.pack(anchor='w', pady=2, fill=tk.X)
        ttk.Label(minimax_frame, text="Nodes Evaluated:").pack(anchor='w', pady=(10, 0))
        self.minimax_nodes_label = ttk.Label(minimax_frame, text="-", style="Value.TLabel")
        self.minimax_nodes_label.pack(anchor='w', pady=2)
        
        ab_frame = ttk.Frame(output_frame, style="Output.TFrame", padding=15)
        ab_frame.grid(row=0, column=1, padx=(10, 0), pady=5, sticky="nsew")
        ttk.Label(ab_frame, text="Alpha-Beta Result", style="Header.TLabel", anchor="center").pack(fill=tk.X, pady=(0, 10))
        ttk.Label(ab_frame, text="Optimal Value:").pack(anchor='w')
        self.ab_value_label = ttk.Label(ab_frame, text="-", style="Value.TLabel")
        self.ab_value_label.pack(anchor='w', pady=2)
        ttk.Label(ab_frame, text="Optimal Path:").pack(anchor='w', pady=(10, 0))
        self.ab_path_label = ttk.Label(ab_frame, text="-", style="Path.TLabel", wraplength=350, justify=tk.LEFT)
        self.ab_path_label.pack(anchor='w', pady=2, fill=tk.X)
        ttk.Label(ab_frame, text="Nodes Pruned:").pack(anchor='w', pady=(10, 0))
        self.ab_pruned_label = ttk.Label(ab_frame, text="-", style="Value.TLabel")
        self.ab_pruned_label.pack(anchor='w', pady=2)
        
        # Add a section for displaying pruned nodes
        pruned_frame = ttk.Frame(comparison_frame, style="Output.TFrame", padding=15)
        pruned_frame.pack(fill=tk.X, pady=(15, 0))
        ttk.Label(pruned_frame, text="Pruned Nodes Visualization", style="Header.TLabel").pack(anchor='w', pady=(0, 10))
        
        pruned_text_frame = ttk.Frame(pruned_frame)
        pruned_text_frame.pack(fill=tk.BOTH, expand=True)
        self.pruned_nodes_text = tk.Text(pruned_text_frame, height=5, font=self.mono_font, bg=self.text_bg, relief=tk.FLAT, wrap=tk.WORD)
        self.pruned_nodes_text.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)
        pruned_scrollbar = ttk.Scrollbar(pruned_text_frame, orient=tk.VERTICAL, command=self.pruned_nodes_text.yview)
        pruned_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.pruned_nodes_text['yscrollcommand'] = pruned_scrollbar.set
        self.pruned_nodes_text.config(state=tk.DISABLED)
        
    def setup_node_addition_tab(self):
        node_frame = ttk.Frame(self.node_tab, padding=15)
        node_frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(node_frame, text="Add Nodes Interactively", style="HeaderBG.TLabel").pack(pady=(0, 10))
        
        add_forms_frame = ttk.Frame(node_frame)
        add_forms_frame.pack(fill=tk.X, pady=10)
        
        # Non-Terminal Node Form
        left_frame = ttk.Frame(add_forms_frame, style="AddNode.TFrame", padding=10)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        ttk.Label(left_frame, text="Add Non-Terminal Node", style="Header.TLabel", font=("Segoe UI", 12)).pack(pady=(0, 10))
        name_frame = ttk.Frame(left_frame); name_frame.pack(fill=tk.X, pady=5)
        # FIX: Added width to the label creation instead of pack method
        ttk.Label(name_frame, text="Node Name:", width=12).pack(side=tk.LEFT, anchor='w')
        self.new_node_name = ttk.Entry(name_frame); self.new_node_name.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        parent_frame = ttk.Frame(left_frame); parent_frame.pack(fill=tk.X, pady=5)
        # FIX: Added width to the label creation instead of pack method
        ttk.Label(parent_frame, text="Parent Node:", width=12).pack(side=tk.LEFT, anchor='w')
        self.new_node_parent = ttk.Entry(parent_frame); self.new_node_parent.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        ttk.Label(parent_frame, text="(Empty for root)").pack(side=tk.LEFT)
        add_node_button = ttk.Button(left_frame, text="Add Node", style="Add.TButton", command=self.add_non_terminal_node)
        add_node_button.pack(pady=10)
        
        # Terminal Node Form
        right_frame = ttk.Frame(add_forms_frame, style="AddNode.TFrame", padding=10)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))
        ttk.Label(right_frame, text="Add Terminal Node", style="Header.TLabel", font=("Segoe UI", 12)).pack(pady=(0, 10))
        term_name_frame = ttk.Frame(right_frame); term_name_frame.pack(fill=tk.X, pady=5)
        # FIX: Added width to the label creation instead of pack method
        ttk.Label(term_name_frame, text="Node Name:", width=12).pack(side=tk.LEFT, anchor='w')
        self.terminal_node_name = ttk.Entry(term_name_frame); self.terminal_node_name.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        term_parent_frame = ttk.Frame(right_frame); term_parent_frame.pack(fill=tk.X, pady=5)
        # FIX: Added width to the label creation instead of pack method
        ttk.Label(term_parent_frame, text="Parent Node:", width=12).pack(side=tk.LEFT, anchor='w')
        self.terminal_node_parent = ttk.Entry(term_parent_frame); self.terminal_node_parent.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        ttk.Label(term_parent_frame, text="(Required)").pack(side=tk.LEFT)
        value_frame = ttk.Frame(right_frame); value_frame.pack(fill=tk.X, pady=5)
        # FIX: Added width to the label creation instead of pack method
        ttk.Label(value_frame, text="Node Value:", width=12).pack(side=tk.LEFT, anchor='w')
        self.terminal_node_value = ttk.Entry(value_frame); self.terminal_node_value.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        add_terminal_button = ttk.Button(right_frame, text="Add Terminal", style="Add.TButton", command=self.add_terminal_node)
        add_terminal_button.pack(pady=10)
        
        # Current Node List Display
        list_frame = ttk.Frame(node_frame, style="Output.TFrame", padding=10)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=(15, 0))
        ttk.Label(list_frame, text="Current Nodes:", style="Header.TLabel", font=("Segoe UI", 12)).pack(anchor='w', pady=(0, 5))
        node_list_text_frame = ttk.Frame(list_frame)
        node_list_text_frame.pack(fill=tk.BOTH, expand=True)
        self.node_list_text = tk.Text(node_list_text_frame, height=10, font=self.mono_font, bg=self.text_bg, relief=tk.FLAT, wrap=tk.WORD)
        self.node_list_text.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)
        node_list_scrollbar = ttk.Scrollbar(node_list_text_frame, orient=tk.VERTICAL, command=self.node_list_text.yview)
        node_list_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.node_list_text['yscrollcommand'] = node_list_scrollbar.set
        self.node_list_text.config(state=tk.DISABLED) # Read-only
        
    def setup_tree_visualization_tab(self):
        viz_frame = ttk.Frame(self.viz_tab, padding=15)
        viz_frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(viz_frame, text="Tree Visualization", style="HeaderBG.TLabel").pack(pady=(0, 10))
        
        viz_text_frame = ttk.Frame(viz_frame, style="Output.TFrame", padding=10)
        viz_text_frame.pack(fill=tk.BOTH, expand=True)
        
        text_frame = ttk.Frame(viz_text_frame)
        text_frame.pack(fill=tk.BOTH, expand=True)
        
        self.viz_text = tk.Text(text_frame, font=self.mono_font, bg=self.text_bg, relief=tk.FLAT, wrap=tk.NONE) # No wrap for structure
        self.viz_text.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)
        
        viz_scrollbar_y = ttk.Scrollbar(text_frame, orient=tk.VERTICAL, command=self.viz_text.yview)
        viz_scrollbar_y.pack(side=tk.RIGHT, fill=tk.Y)
        self.viz_text['yscrollcommand'] = viz_scrollbar_y.set
        
        viz_scrollbar_x = ttk.Scrollbar(viz_text_frame, orient=tk.HORIZONTAL, command=self.viz_text.xview)
        viz_scrollbar_x.pack(side=tk.BOTTOM, fill=tk.X)
        self.viz_text['xscrollcommand'] = viz_scrollbar_x.set
        
        self.viz_text.config(state=tk.DISABLED) # Read-only
        
        refresh_button = ttk.Button(viz_frame, text="Refresh Visualization", command=self.update_tree_visualization)
        refresh_button.pack(pady=10)
        
    def _get_sample_tree_def(self):
        return """A: children=[B, C]
# Level 1
B: children=[D, E]
C: children=[F, G]
# Level 2 (Terminals)
D: value=3
E: value=12
F: value=8
G: value=2"""
        
    def parse_text_definition(self):
        """Parse the text definition and update the tree data."""
        try:
            tree_def = self.tree_definition_text.get("1.0", tk.END)
            parsed_tree = self.parse_tree_definition_logic(tree_def)
            self.tree_data = parsed_tree # Update main tree data
            self.update_node_list_display()
            self.update_tree_visualization()
            messagebox.showinfo("Success", f"Tree parsed successfully with {len(self.tree_data)} nodes.", parent=self.master)
            self.status_var.set(f"Tree parsed successfully with {len(self.tree_data)} nodes.")
        except Exception as e:
            messagebox.showerror("Parse Error", f"Error parsing tree: {e}", parent=self.master)
            self.status_var.set(f"Parse error: {e}")
            
    def parse_tree_definition_logic(self, definition_str):
        tree = {}
        lines = definition_str.strip().split('\n')
        node_pattern = re.compile(r"^\s*([a-zA-Z0-9_]+)\s*:\s*(.*)$")
        children_pattern = re.compile(r"children=\[(.*?)\]")
        value_pattern = re.compile(r"value=(-?\d+(\.\d+)?)") # Allow float values too
        
        defined_nodes = set()
        referenced_children = set()
        node_parents = {} # Track parent for validation {child: parent}
        
        for i, line in enumerate(lines):
            line = line.strip()
            if not line or line.startswith('#'): continue
            
            match = node_pattern.match(line)
            if not match: raise ValueError(f"Invalid format on line {i+1}: '{line}'. Expected 'NODE: definition'.")
            
            node_name, definition = match.groups()
            node_name = node_name.strip()
            definition = definition.strip()
            
            if node_name in tree: raise ValueError(f"Duplicate node '{node_name}' (line {i+1}).")
            defined_nodes.add(node_name)
            tree[node_name] = {'value': None, 'children': [], 'is_terminal': False}
            
            child_match = children_pattern.search(definition)
            value_match = value_pattern.search(definition)
            
            if child_match:
                children_str = child_match.group(1).strip()
                if value_match: raise ValueError(f"Node '{node_name}' cannot have both children and value (line {i+1}).")
                if children_str:
                    children = [c.strip() for c in children_str.split(',') if c.strip()]
                    if not children: raise ValueError(f"Invalid children format for '{node_name}' (line {i+1}).")
                    tree[node_name]['children'] = children
                    referenced_children.update(children)
                    for child in children: # Track parentage
                        if child in node_parents: raise ValueError(f"Node '{child}' has multiple parents (defined under '{node_name}' and '{node_parents[child]}')")
                        node_parents[child] = node_name
                else: # children=[]
                    # Mark as potentially terminal, will be error if no value later
                    tree[node_name]['is_terminal'] = True # Tentative
            elif value_match:
                try:
                    # Try parsing as float first, then int if possible
                    val = float(value_match.group(1))
                    if val == int(val): val = int(val)
                    tree[node_name]['value'] = val
                    tree[node_name]['is_terminal'] = True
                except ValueError: raise ValueError(f"Invalid value for '{node_name}' (line {i+1}).")
            else:
                raise ValueError(f"Node '{node_name}' must define 'children' or 'value' (line {i+1}).")
        
        # Validation
        undefined_children = referenced_children - defined_nodes
        if undefined_children: raise ValueError(f"Undefined children: {', '.join(sorted(list(undefined_children)))}")
        
        for name, node in tree.items():
            if node['is_terminal'] and node['children']: raise ValueError(f"Terminal node '{name}' cannot have children.")
            # Allow non-terminals with empty children list if they are added interactively later?
            # Let's require non-terminals parsed from text to have children defined here.
            if not node['is_terminal'] and not node['children']:
                 # Check if it was children=
             if not node['is_terminal'] and not node['children']:
                 # Check if it was children=[] and no value
                for line in lines:
                     if line.strip().startswith(f"{name}:"):
                         if "children=[]" in line and not value_pattern.search(line):
                             raise ValueError(f"Node '{name}' has empty children '[]' but no 'value'.")
                         break
                 # Otherwise, maybe okay if added interactively? Let's assume it's an error for now from text parse.
                if name in defined_nodes: # Ensure it was defined in the text
                      raise ValueError(f"Non-terminal node '{name}' must have children defined in text mode.")

        return tree

    def update_node_list_display(self):
        """Updates the text area in the 'Add Nodes' tab."""
        self.node_list_text.config(state=tk.NORMAL)
        self.node_list_text.delete("1.0", tk.END)
        if not self.tree_data:
            self.node_list_text.insert("1.0", "(Tree is empty)")
        else:
            for name, node in sorted(self.tree_data.items()):
                if node['is_terminal']:
                    self.node_list_text.insert(tk.END, f"- {name} (Terminal, Value: {node['value']})\n")
                else:
                    children_str = ", ".join(node['children']) if node['children'] else "(No children added yet)"
                    self.node_list_text.insert(tk.END, f"- {name} (Children: {children_str})\n")
        self.node_list_text.config(state=tk.DISABLED)

    def update_tree_visualization(self):
        """Updates the text area in the 'Visualize Tree' tab."""
        self.viz_text.config(state=tk.NORMAL)
        self.viz_text.delete("1.0", tk.END)
        if not self.tree_data:
            self.viz_text.insert("1.0", "(Tree is empty)")
            self.viz_text.config(state=tk.DISABLED)
            return

        root_node = self.root_node_entry.get().strip()
        if not root_node or root_node not in self.tree_data:
             # Find potential roots (nodes without parents)
             all_nodes = set(self.tree_data.keys())
             children_nodes = set()
             for node in self.tree_data.values():
                 children_nodes.update(node['children'])
             potential_roots = sorted(list(all_nodes - children_nodes))
             if potential_roots:
                 root_node = potential_roots[0] # Pick the first one
                 self.viz_text.insert(tk.END, f"(No valid root specified, visualizing from potential root: {root_node})\n\n")
             else:
                  self.viz_text.insert(tk.END, "(Cannot determine root node for visualization)")
                  self.viz_text.config(state=tk.DISABLED)
                  return
        else:
             self.viz_text.insert(tk.END, f"(Visualizing from root: {root_node})\n\n")


        def build_viz_string(node_name, prefix="", is_last=True):
            node = self.tree_data.get(node_name)
            if not node: return ""

            connector = "└── " if is_last else "├── "
            viz_str = prefix + connector + node_name
            if node['is_terminal']:
                viz_str += f" ({node['value']})\n"
            else:
                viz_str += "\n"

            new_prefix = prefix + ("    " if is_last else "│   ")
            children = node['children']
            for i, child_name in enumerate(children):
                viz_str += build_viz_string(child_name, new_prefix, i == len(children) - 1)
            return viz_str

        viz_output = build_viz_string(root_node)
        self.viz_text.insert("1.0", viz_output) # Insert at the beginning
        self.viz_text.config(state=tk.DISABLED)

    def update_text_definition(self):
        """Updates the text definition based on the internal tree_data."""
        lines = []
        # Process non-terminals first to improve readability
        for name, node in sorted(self.tree_data.items()):
             if not node['is_terminal']:
                 children_str = ", ".join(node['children'])
                 lines.append(f"{name}: children=[{children_str}]")
        # Process terminals next
        for name, node in sorted(self.tree_data.items()):
            if node['is_terminal']:
                 lines.append(f"{name}: value={node['value']}")

        new_def = "\n".join(lines)
        current_def = self.tree_definition_text.get("1.0", tk.END).strip()

        # Only update if definition changed to avoid losing undo history unnecessarily
        if new_def != current_def:
            self.tree_definition_text.delete("1.0", tk.END)
            self.tree_definition_text.insert("1.0", new_def)

    def add_node_base(self, node_name, parent_name, is_terminal, value=None):
        """Base logic for adding a node."""
        if not node_name or not node_name.isalnum(): # Basic validation
            raise ValueError("Node name must be alphanumeric.")
        if node_name in self.tree_data:
            raise ValueError(f"Node '{node_name}' already exists.")

        if parent_name:
            if parent_name not in self.tree_data:
                raise ValueError(f"Parent node '{parent_name}' does not exist.")
            parent = self.tree_data[parent_name]
            if parent['is_terminal']:
                raise ValueError(f"Cannot add child to terminal node '{parent_name}'.")

            # Check if child already exists under this parent (shouldn't happen with name check, but good practice)
            if node_name in parent['children']:
                 raise ValueError(f"Node '{node_name}' is already a child of '{parent_name}'.")

        # Create the node
        self.tree_data[node_name] = {
            'value': value,
            'children': [],
            'is_terminal': is_terminal
        }

        # Add to parent's children list
        if parent_name:
             self.tree_data[parent_name]['children'].append(node_name)
             # Ensure parent is marked non-terminal
             self.tree_data[parent_name]['is_terminal'] = False
             self.tree_data[parent_name]['value'] = None # Non-terminals don't have a direct value

        # Update displays
        self.update_node_list_display()
        self.update_tree_visualization()
        self.update_text_definition()

    def add_non_terminal_node(self):
        node_name = self.new_node_name.get().strip()
        parent_name = self.new_node_parent.get().strip()
        try:
            self.add_node_base(node_name, parent_name, is_terminal=False)
            self.new_node_name.delete(0, tk.END)
            self.new_node_parent.delete(0, tk.END)
            self.status_var.set(f"Added non-terminal node '{node_name}'.")
        except ValueError as e:
            messagebox.showerror("Input Error", str(e), parent=self.master)
            self.status_var.set(f"Error: {e}")
        except Exception as e:
            messagebox.showerror("Unexpected Error", f"An unexpected error occurred: {e}", parent=self.master)
            self.status_var.set(f"Error: {e}")

    def add_terminal_node(self):
        node_name = self.terminal_node_name.get().strip()
        parent_name = self.terminal_node_parent.get().strip()
        value_str = self.terminal_node_value.get().strip()
        try:
            if not parent_name:
                raise ValueError("Parent node name is required for terminal nodes.")
            if not value_str:
                raise ValueError("Node value is required for terminal nodes.")
            try:
                value = int(value_str) # Or float(value_str) if needed
            except ValueError:
                raise ValueError("Node value must be a number.")

            self.add_node_base(node_name, parent_name, is_terminal=True, value=value)
            self.terminal_node_name.delete(0, tk.END)
            self.terminal_node_parent.delete(0, tk.END)
            self.terminal_node_value.delete(0, tk.END)
            self.status_var.set(f"Added terminal node '{node_name}' with value {value}.")
        except ValueError as e:
            messagebox.showerror("Input Error", str(e), parent=self.master)
            self.status_var.set(f"Error: {e}")
        except Exception as e:
            messagebox.showerror("Unexpected Error", f"An unexpected error occurred: {e}", parent=self.master)
            self.status_var.set(f"Error: {e}")

    def clear_all(self):
        """Clears the tree data and all UI fields related to the tree."""
        if messagebox.askyesno("Confirm Clear", "Are you sure you want to clear the entire tree and results?", parent=self.master):
            self.tree_data = {}
            self.tree_definition_text.delete("1.0", tk.END)
            self.root_node_entry.delete(0, tk.END)
            self.depth_var.set("")
            # Clear Add Node fields
            self.new_node_name.delete(0, tk.END)
            self.new_node_parent.delete(0, tk.END)
            self.terminal_node_name.delete(0, tk.END)
            self.terminal_node_parent.delete(0, tk.END)
            self.terminal_node_value.delete(0, tk.END)
            # Clear results
            self.minimax_value_label.config(text="-")
            self.minimax_path_label.config(text="-")
            self.minimax_nodes_label.config(text="-")
            self.ab_value_label.config(text="-")
            self.ab_path_label.config(text="-")
            self.ab_pruned_label.config(text="-")
            self.pruned_nodes_text.config(state=tk.NORMAL)
            self.pruned_nodes_text.delete("1.0", tk.END)
            self.pruned_nodes_text.config(state=tk.DISABLED)
            # Clear displays
            self.update_node_list_display()
            self.update_tree_visualization()
            self.status_var.set("Tree cleared. Ready for new definition.")

    def run_comparison(self):
        """Parses input, runs algorithms, and updates UI."""
        self.status_var.set("Validating tree...")
        self.master.update_idletasks()

        # Use internal tree_data, assuming it's up-to-date via parsing or adding
        if not self.tree_data:
             messagebox.showerror("Error", "Tree is empty. Please define or parse a tree first.", parent=self.master)
             self.status_var.set("Error: Tree is empty.")
             return # Cannot run comparison

        try:
            root_node = self.root_node_entry.get().strip()
            depth_str = self.depth_var.get().strip()
            depth_limit = None

            if not root_node: raise ValueError("Root Node Name cannot be empty.")
            if root_node not in self.tree_data: raise ValueError(f"Root node '{root_node}' not found.")
            if self.tree_data[root_node]['is_terminal']: raise ValueError(f"Root node '{root_node}' cannot be a terminal node.")

            if depth_str:
                try:
                    depth_limit = int(depth_str)
                    if depth_limit < 0: raise ValueError("Depth cannot be negative.")
                except ValueError:
                    raise ValueError("Max Depth must be a non-negative integer if specified.")

            self.status_var.set(f"Running algorithms from root '{root_node}' (Depth limit: {depth_limit if depth_limit is not None else 'None'})...")
            self.master.update_idletasks()

            # Track node evaluations for minimax
            mm_evaluated = set()
            def minimax_tracker(node_name, tree, is_maximizing, depth=None):
                mm_evaluated.add(node_name)
                return minimax_with_path(node_name, tree, is_maximizing, depth)

            # Run Minimax
            mm_start_time = time.time()
            mm_value, mm_path = minimax_tracker(root_node, self.tree_data, True, depth=depth_limit)
            mm_time = time.time() - mm_start_time
            mm_nodes_evaluated = len(mm_evaluated)

            # Run Alpha-Beta
            ab_start_time = time.time()
            ab_value, ab_path, pruned_info = alpha_beta_with_path(root_node, self.tree_data, -math.inf, math.inf, True, depth=depth_limit)
            ab_time = time.time() - ab_start_time
            ab_pruned_count = pruned_info["count"]
            ab_pruned_nodes = pruned_info["nodes"]

            # Update UI
            self.minimax_value_label.config(text=str(mm_value))
            self.minimax_path_label.config(text=" -> ".join(mm_path))
            self.minimax_nodes_label.config(text=str(mm_nodes_evaluated))
            
            self.ab_value_label.config(text=str(ab_value))
            self.ab_path_label.config(text=" -> ".join(ab_path))
            self.ab_pruned_label.config(text=str(ab_pruned_count))
            
            # Update pruned nodes visualization
            self.pruned_nodes_text.config(state=tk.NORMAL)
            self.pruned_nodes_text.delete("1.0", tk.END)
            if ab_pruned_count > 0:
                pruned_str = f"Alpha-Beta pruned {ab_pruned_count} nodes: {', '.join(ab_pruned_nodes)}"
                self.pruned_nodes_text.insert("1.0", pruned_str)
                
                # Create visualization of the tree with pruned nodes highlighted
                def build_viz_string_with_pruning(node_name, prefix="", is_last=True):
                    node = self.tree_data.get(node_name)
                    if not node: return ""

                    connector = "└── " if is_last else "├── "
                    is_pruned = node_name in ab_pruned_nodes
                    
                    viz_str = prefix + connector + node_name
                    if is_pruned:
                        viz_str += " [PRUNED]"
                    if node['is_terminal']:
                        viz_str += f" ({node['value']})"
                    viz_str += "\n"

                    new_prefix = prefix + ("    " if is_last else "│   ")
                    children = node['children']
                    for i, child_name in enumerate(children):
                        viz_str += build_viz_string_with_pruning(child_name, new_prefix, i == len(children) - 1)
                    return viz_str
                
                pruned_viz = build_viz_string_with_pruning(root_node)
                self.pruned_nodes_text.insert(tk.END, "\n\nTree with pruned nodes:\n" + pruned_viz)
            else:
                self.pruned_nodes_text.insert("1.0", "No nodes were pruned during Alpha-Beta search.")
            self.pruned_nodes_text.config(state=tk.DISABLED)

            efficiency = (mm_nodes_evaluated - (mm_nodes_evaluated - ab_pruned_count)) / mm_nodes_evaluated * 100 if mm_nodes_evaluated > 0 else 0
            self.status_var.set(f"Comparison complete. MM: {mm_time:.4f}s, AB: {ab_time:.4f}s. Efficiency gain: {efficiency:.1f}%")

        except ValueError as e:
            messagebox.showerror("Input Error", str(e), parent=self.master)
            self.status_var.set(f"Error: {e}")
        except Exception as e:
            messagebox.showerror("Runtime Error", f"An unexpected error during solving: {e}", parent=self.master)
            self.status_var.set(f"Runtime Error: {e}")
        finally:
            self.compare_button.config(state=tk.NORMAL)

    def run_comparison_threaded(self):
        self.compare_button.config(state=tk.DISABLED)
        self.status_var.set("Processing...")
        self.minimax_value_label.config(text="-")
        self.minimax_path_label.config(text="-")
        self.minimax_nodes_label.config(text="-")
        self.ab_value_label.config(text="-")
        self.ab_path_label.config(text="-")
        self.ab_pruned_label.config(text="-")
        self.pruned_nodes_text.config(state=tk.NORMAL)
        self.pruned_nodes_text.delete("1.0", tk.END)
        self.pruned_nodes_text.config(state=tk.DISABLED)
        self.master.update_idletasks()
        thread = threading.Thread(target=self.run_comparison, daemon=True)
        thread.start()

def launch_app():
    """Entry point function for launching this application from Flask"""
    root = tk.Tk()
    app = MinimaxComparisonApp(root)
    root.mainloop()

if __name__ == "__main__":
    launch_app()