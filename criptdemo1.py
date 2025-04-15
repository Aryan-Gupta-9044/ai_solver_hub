import tkinter as tk
from tkinter import ttk # Import themed widgets
from tkinter import font as tkFont
from tkinter import scrolledtext, messagebox
import itertools
import re
import threading

# --- Solver Class (remains the same) ---
class CryptarithmeticSolver:
    """Handles the logic for solving cryptarithmetic puzzles."""

    def parse_puzzle(self, puzzle_str):
        """Parses the puzzle string into operands and result."""
        puzzle_str = puzzle_str.upper().replace(" ", "")
        if '=' not in puzzle_str:
            raise ValueError("Puzzle must contain '=' sign.")

        parts = puzzle_str.split('=')
        if len(parts) != 2:
            raise ValueError("Puzzle must have exactly one '=' sign.")

        result = parts[1]
        operands_str = parts[0]

        # Allow multiplication as well? For now, just addition
        if '+' in operands_str:
             operands = operands_str.split('+')
        # elif '*' in operands_str: # Example for future extension
        #     operands = operands_str.split('*')
        #     operator = '*'
        else:
             # Handle single operand case (e.g., ABC = DEF) - less common
             operands = [operands_str]
             # operator = None # Or handle differently

        if not result or not all(operands):
            raise ValueError("Operands and result cannot be empty.")
        if not all(s.isalpha() for s in operands + [result]):
            raise ValueError("Words must contain only letters.")

        return operands, result # Add operator if needed later

    def get_unique_letters(self, operands, result):
        """Extracts unique letters and leading letters."""
        all_letters = set("".join(operands) + result)
        leading_letters = set(op[0] for op in operands) | set(result[0])
        unique_letters_list = sorted(list(all_letters)) # Ensure consistent order
        return unique_letters_list, leading_letters

    def solve(self, puzzle_str):
        """Attempts to solve the cryptarithmetic puzzle."""
        try:
            operands, result = self.parse_puzzle(puzzle_str)
            unique_letters, leading_letters = self.get_unique_letters(operands, result)
            num_unique_letters = len(unique_letters)

            if num_unique_letters > 10:
                return None, "Error: More than 10 unique letters."

            digits = range(10)
            # Use yield to potentially find multiple solutions? For now, find first.
            for p in itertools.permutations(digits, num_unique_letters):
                assignment = dict(zip(unique_letters, p))

                if any(assignment[leading] == 0 for leading in leading_letters):
                    continue

                try:
                    operand_values = [self.word_to_num(op, assignment) for op in operands]
                    result_value = self.word_to_num(result, assignment)

                    # Assuming addition for now
                    if sum(operand_values) == result_value:
                        return assignment, None # Found a solution
                except KeyError:
                    continue

            return None, "No solution found."

        except ValueError as e:
            return None, f"Error: {e}"
        except Exception as e:
            return None, f"An unexpected error occurred: {e}"

    def word_to_num(self, word, assignment):
        """Converts a word to its numerical value based on the assignment."""
        num_str = "".join(str(assignment[letter]) for letter in word)
        return int(num_str)

# --- UI Class ---

class CryptarithmeticApp:
    def __init__(self, master):
        self.master = master
        self.master.title("Cryptarithmetic Solver")
        self.master.geometry("600x550") # Slightly larger window
        self.master.configure(bg="#f0f0f0") # Light grey background

        self.solver = CryptarithmeticSolver()

        # --- Styling ---
        self.style = ttk.Style()
        self.style.theme_use('clam') # 'clam', 'alt', 'default', 'classic'

        # Define colors
        self.bg_color = "#f0f0f0"
        self.entry_bg = "#ffffff"
        self.text_bg = "#e9e9e9"
        self.button_bg = "#4a90e2" # Blue button
        self.button_fg = "#ffffff"
        self.button_active_bg = "#357ABD"
        self.header_color = "#333333"
        self.text_color = "#111111"

        # Configure styles
        self.style.configure("TFrame", background=self.bg_color)
        self.style.configure("TLabel", background=self.bg_color, foreground=self.text_color, font=("Segoe UI", 11))
        self.style.configure("Header.TLabel", font=("Segoe UI Semibold", 16), foreground=self.header_color)
        self.style.configure("TEntry", fieldbackground=self.entry_bg, foreground=self.text_color, font=("Segoe UI", 11))
        self.style.configure("TButton", background=self.button_bg, foreground=self.button_fg, font=("Segoe UI Semibold", 11), padding=(10, 5), borderwidth=0)
        self.style.map("TButton", background=[('active', self.button_active_bg)])

        # Specific style for Clear button
        self.style.configure("Clear.TButton", background="#f44336", foreground="#ffffff") # Red button
        self.style.map("Clear.TButton", background=[('active', "#d32f2f")])


        # Fonts
        self.mono_font = tkFont.Font(family="Consolas", size=11) # Monospaced for output

        # --- UI Elements ---
        main_frame = ttk.Frame(master, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Title
        ttk.Label(main_frame, text="Cryptarithmetic Puzzle Solver", style="Header.TLabel").pack(pady=(0, 20))

        # Input Section
        input_frame = ttk.Frame(main_frame, padding=(0, 10))
        input_frame.pack(fill=tk.X)

        ttk.Label(input_frame, text="Puzzle:", width=8, anchor="w").pack(side=tk.LEFT, padx=(0,10))
        self.puzzle_entry = ttk.Entry(input_frame, font=("Segoe UI", 11), width=45)
        self.puzzle_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.puzzle_entry.insert(0, "SEND + MORE = MONEY") # Example

        # Buttons Frame
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(pady=15, fill=tk.X)
        button_frame.columnconfigure(0, weight=1) # Make buttons expand
        button_frame.columnconfigure(1, weight=1)

        self.solve_button = ttk.Button(button_frame, text="Solve Puzzle", command=self.trigger_solve, style="TButton")
        self.solve_button.grid(row=0, column=0, padx=(0, 5), sticky="ew")

        self.clear_button = ttk.Button(button_frame, text="Clear", command=self.clear_fields, style="Clear.TButton")
        self.clear_button.grid(row=0, column=1, padx=(5, 0), sticky="ew")


        # Output Section
        output_frame = ttk.Frame(main_frame)
        output_frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(output_frame, text="Solution:", style="TLabel", font=("Segoe UI Semibold", 12)).pack(pady=(5, 5), anchor="w")

        self.output_text = scrolledtext.ScrolledText(
            output_frame, height=15, width=60,
            font=self.mono_font,
            state=tk.DISABLED, wrap=tk.WORD, borderwidth=1, relief=tk.SUNKEN,
            bg=self.text_bg, fg=self.text_color, padx=10, pady=10
        )
        self.output_text.pack(fill=tk.BOTH, expand=True)

    def clear_fields(self):
        """Clears the input and output fields."""
        self.puzzle_entry.delete(0, tk.END)
        self.output_text.config(state=tk.NORMAL)
        self.output_text.delete('1.0', tk.END)
        self.output_text.config(state=tk.DISABLED)
        self.solve_button.config(state=tk.NORMAL, text="Solve Puzzle") # Ensure solve is re-enabled


    def display_result(self, assignment, error):
        """Displays the solution or error in the output text area."""
        self.output_text.config(state=tk.NORMAL)
        self.output_text.delete('1.0', tk.END)

        if error:
            messagebox.showerror("Solver Error", error)
            self.output_text.insert(tk.END, f"Status: Error\n\n{error}")
        elif assignment:
            self.output_text.insert(tk.END, "Status: Solution Found!\n\n")
            self.output_text.insert(tk.END, "-- Mapping --\n")
            # Determine max letter length for alignment
            max_len = max(len(l) for l in assignment.keys()) if assignment else 1
            for letter in sorted(assignment.keys()):
                self.output_text.insert(tk.END, f"  {letter:<{max_len}} : {assignment[letter]}\n") # Align output

            self.output_text.insert(tk.END, "\n-- Equation --\n")
            try:
                puzzle_str = self.puzzle_entry.get() # Get original puzzle for display
                operands, result = self.solver.parse_puzzle(puzzle_str)
                operand_nums = [self.solver.word_to_num(op, assignment) for op in operands]
                result_num = self.solver.word_to_num(result, assignment)

                # Format equation vertically aligned
                max_word_len = max(len(op) for op in operands + [result])
                max_num_len = max(len(str(n)) for n in operand_nums + [result_num])
                display_len = max(max_word_len, max_num_len) + 2 # Add padding

                for i, op in enumerate(operands):
                    op_num_str = str(operand_nums[i])
                    prefix = "  " if i == 0 else "+ "
                    self.output_text.insert(tk.END, f"{prefix}{op:<{max_word_len}}   ->   {op_num_str:>{max_num_len}}\n")

                self.output_text.insert(tk.END, "  " + "-" * max_word_len + "   ->   " + "-" * max_num_len + "\n")
                result_num_str = str(result_num)
                self.output_text.insert(tk.END, f"= {result:<{max_word_len}}   ->   {result_num_str:>{max_num_len}}\n")


                # Verify check
                if sum(operand_nums) == result_num:
                     self.output_text.insert(tk.END, "\n(Verification: OK)")
                else:
                     self.output_text.insert(tk.END, "\n(Verification: FAILED - Check Logic!)")

            except Exception as e:
                 self.output_text.insert(tk.END, f"\nError formatting equation: {e}")

        else: # Should mean "No solution found" from solver
             self.output_text.insert(tk.END, "Status: No solution found for this puzzle.")

        self.output_text.config(state=tk.DISABLED)
        self.solve_button.config(state=tk.NORMAL, text="Solve Puzzle")
        self.clear_button.config(state=tk.NORMAL) # Re-enable clear

    def solve_puzzle_thread(self):
        """Runs the solver in a separate thread."""
        puzzle_str = self.puzzle_entry.get()
        if not puzzle_str:
            messagebox.showwarning("Input Missing", "Please enter a puzzle.")
            self.solve_button.config(state=tk.NORMAL, text="Solve Puzzle")
            self.clear_button.config(state=tk.NORMAL)
            return

        assignment, error = self.solver.solve(puzzle_str)
        self.master.after(0, self.display_result, assignment, error)


    def trigger_solve(self):
        """Starts the solving process in a thread."""
        self.solve_button.config(state=tk.DISABLED, text="Solving...")
        self.clear_button.config(state=tk.DISABLED) # Disable clear while solving
        solve_thread = threading.Thread(target=self.solve_puzzle_thread, daemon=True)
        solve_thread.start()


def launch_app():
    """Entry point function for launching this application from Flask"""
    root = tk.Tk()
    app = CryptarithmeticApp(root)
    root.mainloop()

if __name__ == "__main__":
    launch_app()