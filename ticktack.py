import tkinter as tk
from tkinter import ttk, font as tkFont, messagebox
import math
import time
import random

# --- Game Logic ---
class TicTacToe:
    WIN_CONDITIONS = [
        [0, 1, 2], [3, 4, 5], [6, 7, 8],  # Rows
        [0, 3, 6], [1, 4, 7], [2, 5, 8],  # Columns
        [0, 4, 8], [2, 4, 6]             # Diagonals
    ]

    def __init__(self):
        self.board = [' ' for _ in range(9)]
        self.human_player = 'X'
        self.ai_player = 'O'

    def print_board(self):
        for i in range(0, 9, 3):
            print('|'.join(self.board[i:i+3]))

    def make_move(self, position, player):
        if self.board[position] == ' ':
            self.board[position] = player
            return True
        return False

    def check_winner(self):
        """Checks if there is a winner and returns the player and the winning line."""
        for condition in self.WIN_CONDITIONS:
            line = [self.board[i] for i in condition]
            if line[0] == line[1] == line[2] and line[0] != ' ':
                return line[0], condition # Return winner ('X' or 'O') and the line indices
        return None, None # No winner yet

    def is_draw(self):
        winner, _ = self.check_winner()
        return ' ' not in self.board and winner is None

    def is_game_over(self):
        winner, _ = self.check_winner()
        return winner is not None or self.is_draw()

    def get_available_moves(self):
        return [i for i, spot in enumerate(self.board) if spot == ' ']

    def reset_board(self):
        self.board = [' ' for _ in range(9)]

# --- Minimax AI Logic (remains the same) ---
def minimax(board_state, player, maximizing_player, human_player, ai_player):
    winner, _ = board_state.check_winner()
    if winner == ai_player: return 1
    if winner == human_player: return -1
    if board_state.is_draw(): return 0

    available_moves = board_state.get_available_moves()
    scores = []

    for move in available_moves:
        board_state.make_move(move, player)
        if maximizing_player: # AI trying to maximize
             score = minimax(board_state, human_player, False, human_player, ai_player)
        else: # Human trying to minimize (from AI perspective)
             score = minimax(board_state, ai_player, True, human_player, ai_player)
        board_state.board[move] = ' ' # Backtrack
        scores.append(score)

    return max(scores) if maximizing_player else min(scores)


def find_best_move(board_state, ai_player, human_player):
    best_score = -math.inf
    best_move = -1
    available_moves = board_state.get_available_moves()

    for move in available_moves:
        board_state.make_move(move, ai_player)
        score = minimax(board_state, human_player, False, human_player, ai_player)
        board_state.board[move] = ' '
        if score > best_score:
            best_score = score
            best_move = move

    # Fallback if no move improves score (should only happen in losing scenarios)
    if best_move == -1 and available_moves:
        # Deterministic fallback: choose the first available move
        best_move = available_moves[0]
        # Or random fallback: best_move = random.choice(available_moves)

    return best_move


# --- Tkinter UI ---
class TicTacToeApp:
    def __init__(self, master):
        self.master = master
        self.master.title("Tic-Tac-Toe AI")
        self.master.geometry("450x600") # Adjusted size for title
        self.master.resizable(False, False)

        self.game = TicTacToe()
        self.human_turn = True
        self.buttons = {} # Use dictionary for easier access by index

        # --- Styling ---
        self.style = ttk.Style()
        self.style.theme_use('clam')

        # Colors (Refined Palette)
        self.bg_color = "#2C3E50"      # Dark Slate Blue
        self.board_bg = "#34495E"    # Wet Asphalt (Slightly lighter)
        self.button_bg = "#7F8C8D"    # Greyish
        self.button_active_bg = "#95A5A6" # Lighter Greyish on hover
        self.button_fg = "#ECF0F1"    # Clouds (Light text)
        self.x_color = "#E74C3C"      # Alizarin Red
        self.o_color = "#3498DB"      # Peter River Blue
        self.win_bg = "#F1C40F"     # Sunflower Yellow for winning line
        self.win_fg = "#2C3E50"     # Dark text on yellow
        self.status_fg = "#BDC3C7"   # Silver (Status label color)
        self.title_fg = "#ECF0F1"   # Clouds (Title color)
        self.restart_bg = "#2ECC71"   # Emerald Green
        self.restart_active = "#27AE60" # Nephritis Green

        self.master.configure(bg=self.bg_color)

        # Fonts
        self.title_font = tkFont.Font(family="Impact", size=28) # More impactful title
        self.board_font = tkFont.Font(family="Verdana", size=38, weight="bold")
        self.status_font = tkFont.Font(family="Segoe UI", size=16) # Slightly larger status
        self.restart_font = tkFont.Font(family="Segoe UI Semibold", size=12)

        # --- Configure Styles ---
        self.style.configure("TFrame", background=self.bg_color)
        self.style.configure("Board.TFrame", background=self.board_bg, relief="raised", borderwidth=3)
        self.style.configure("Title.TLabel", background=self.bg_color, foreground=self.title_fg, font=self.title_font, anchor="center")
        self.style.configure("Status.TLabel", background=self.bg_color, foreground=self.status_fg, font=self.status_font, anchor="center")

        # Default button style
        self.style.configure("Board.TButton", font=self.board_font, padding=5, background=self.button_bg, foreground=self.button_fg, borderwidth=0, focuscolor=self.button_bg) # Remove focus highlight ring
        self.style.map("Board.TButton",
                       background=[('active', self.button_active_bg), ('disabled', self.button_bg)], # Keep bg color when disabled
                       foreground=[('disabled', self.button_fg)]) # Keep text color when disabled

        # Style for buttons with 'X'
        self.style.configure("X.TButton", foreground=self.x_color)
        # Style for buttons with 'O'
        self.style.configure("O.TButton", foreground=self.o_color)
        # Style for winning buttons
        self.style.configure("Win.TButton", background=self.win_bg, foreground=self.win_fg)
        self.style.map("Win.TButton",
                       background=[('active', self.win_bg), ('disabled', self.win_bg)], # Keep win color always
                       foreground=[('disabled', self.win_fg)])

        # Restart button style
        self.style.configure("Restart.TButton", font=self.restart_font, padding=(15, 8), background=self.restart_bg, foreground="white", borderwidth=0, focuscolor=self.restart_bg)
        self.style.map("Restart.TButton", background=[('active', self.restart_active)])

        # --- UI Elements ---
        # Title Label
        title_label = ttk.Label(master, text="TIC - TAC - TOE", style="Title.TLabel")
        title_label.pack(pady=(30, 15)) # More padding top

        # Status Label
        self.status_label = ttk.Label(master, text="Your Turn (X)", style="Status.TLabel")
        self.status_label.pack(pady=15)

        # Board Frame
        self.board_frame = ttk.Frame(master, style="Board.TFrame", padding=15) # More padding inside frame
        self.board_frame.pack()

        # Create buttons and store in dictionary
        for i in range(9):
            row, col = divmod(i, 3)
            button = ttk.Button(self.board_frame, text=' ', width=3, style="Board.TButton",
                                command=lambda i=i: self.on_button_click(i))
            button.grid(row=row, column=col, padx=6, pady=6, ipady=12) # Adjust padding
            self.buttons[i] = button # Store button using its index as key

        # Restart Button
        self.restart_button = ttk.Button(master, text="Restart Game", style="Restart.TButton", command=self.restart_game)
        self.restart_button.pack(pady=25)


    def on_button_click(self, index):
        if not self.human_turn or self.game.board[index] != ' ' or self.game.is_game_over():
            return

        self.game.make_move(index, self.game.human_player)
        self.update_button_ui(index, self.game.human_player)

        winner, winning_line = self.game.check_winner()
        if self.check_game_state(winner, winning_line):
            return

        self.human_turn = False
        self.status_label.config(text="AI Thinking...")
        self.toggle_buttons_state(enabled=False)
        self.master.after(600, self.ai_turn) # Slightly longer delay


    def ai_turn(self):
        winner, winning_line = self.game.check_winner()
        if winner or self.game.is_draw(): # Check if game ended before AI could move
             self.toggle_buttons_state(enabled=True)
             return

        best_move = find_best_move(self.game, self.game.ai_player, self.game.human_player)

        if best_move != -1:
             self.game.make_move(best_move, self.game.ai_player)
             self.update_button_ui(best_move, self.game.ai_player)

        winner, winning_line = self.game.check_winner()
        if self.check_game_state(winner, winning_line):
            return

        self.human_turn = True
        self.status_label.config(text="Your Turn (X)")
        self.toggle_buttons_state(enabled=True)


    def update_button_ui(self, index, player):
        button = self.buttons[index]
        button.config(text=player)
        style_suffix = "X" if player == self.game.human_player else "O"
        button.config(style=f"{style_suffix}.TButton")
        button.config(command=lambda: None) # Disable command after click


    def check_game_state(self, winner, winning_line):
        """Checks if the game has ended and updates status."""
        game_over = False
        if winner:
            status_text = f"{winner} Wins!"
            self.highlight_winner(winning_line)
            game_over = True
        elif self.game.is_draw():
            status_text = "It's a Draw!"
            game_over = True

        if game_over:
             self.status_label.config(text=status_text)
             self.toggle_buttons_state(enabled=False, keep_winner_style=True, winning_line=winning_line)
             return True # Game is over

        return False # Game not over


    def highlight_winner(self, winning_line):
        """Change style of the winning buttons."""
        if winning_line:
            for index in winning_line:
                # Determine if X or O won to keep the color
                player = self.game.board[index]
                style_suffix = "X" if player == self.game.human_player else "O"
                # Apply base winning style first, then player color on top if needed
                self.buttons[index].config(style=f"Win.TButton")
                # We might not need to re-apply X/O style if Win.TButton handles foreground
                # self.style.configure(f"Win.{style_suffix}.TButton", foreground=self.x_color if player == 'X' else self.o_color)
                # self.buttons[index].config(style=f"Win.{style_suffix}.TButton")


    def toggle_buttons_state(self, enabled=True, keep_winner_style=False, winning_line=None):
         """Enable or disable board buttons, preserving winning style if needed."""
         state = tk.NORMAL if enabled else tk.DISABLED
         for index, button in self.buttons.items():
             is_winning_button = keep_winner_style and winning_line and index in winning_line
             # Don't change state of winning buttons if keep_winner_style is True
             if not is_winning_button:
                  # Only toggle if the button hasn't been played or game is restarting
                  if button['text'] == ' ' or state == tk.NORMAL:
                      button.config(state=state)


    def restart_game(self):
        self.game.reset_board()
        for i in range(9):
            button = self.buttons[i]
            button.config(text=' ', style="Board.TButton") # Reset to default style
            button.config(command=lambda i=i: self.on_button_click(i))

        self.human_turn = True
        self.status_label.config(text="Your Turn (X)")
        self.toggle_buttons_state(enabled=True)


def launch_app():
    """Entry point function for launching this application from Flask"""
    root = tk.Tk()
    app = TicTacToeApp(root)  # Adjust class name to match your actual implementation
    root.mainloop()

if __name__ == "__main__":
    launch_app()
