from instagrapi import Client
import time
import instagrapi.exceptions

# Instagram Login Credentials
USERNAME = "sevenaka7world@gmail.com"
PASSWORD = "U$QyTp'hP:ux43'"

cl = Client()

def debug_login():
    try:
        print("Attempting to login...")
        cl.login(USERNAME, PASSWORD)
        print("Login successful!")
    except instagrapi.exceptions.TwoFactorRequired:
        print("Two-factor authentication required.")
        verification_code = input("Enter the 2FA code: ")
        print(f"Entered 2FA code: {verification_code}")  # Debugging line
        try:
            cl.login(USERNAME, PASSWORD, verification_code=verification_code)
            print("2FA successful!")
        except instagrapi.exceptions.UnknownError as e:
            print(f"Error with 2FA: {e}")
            print("Please check if the 2FA code is correct or if there are any API issues.")
        except Exception as e:
            print(f"Unexpected error during login: {e}")
    except instagrapi.exceptions.BadRequest as e:
        print(f"Bad request error: {e}")
    except instagrapi.exceptions.LoginRequired as e:
        print(f"Login required error: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")

# Call the login function
debug_login()

# Game Board Setup
game_board = None

def reset_board():
    global game_board
    game_board = [["⬜", "⬜", "⬜"],
                  ["⬜", "⬜", "⬜"],
                  ["⬜", "⬜", "⬜"]]

def board_to_str():
    return "\n".join([" ".join(row) for row in game_board])

def update_board(position, symbol="❌"):
    mapping = {
        "oben links": (0, 0), "oben mitte": (0, 1), "oben rechts": (0, 2),
        "mitte links": (1, 0), "mitte": (1, 1), "mitte rechts": (1, 2),
        "unten links": (2, 0), "unten mitte": (2, 1), "unten rechts": (2, 2)
    }
    if position in mapping and game_board[mapping[position][0]][mapping[position][1]] == "⬜":
        game_board[mapping[position][0]][mapping[position][1]] = symbol
        return True
    return False

def check_messages():
    try:
        print("Checking messages...")
        last_messages = cl.direct_threads()
        if last_messages:
            for thread in last_messages:
                messages = cl.direct_messages(thread.id)
                for message in messages:
                    text = message.text.lower()
                    print(f"Message received: {text}")

                    if text == "!start":
                        reset_board()
                        cl.direct_send("New Tic-Tac-Toe game started!\n" + board_to_str(), thread.id)
                        print("Game started.")
                    elif text.startswith("!"):
                        pos = text[1:].strip()
                        if game_board is None:
                            cl.direct_send("Please start a game first with !start", thread.id)
                            print("Game has not been started yet.")
                        elif update_board(pos):
                            cl.direct_send(board_to_str(), thread.id)
                            print(f"Move made at {pos}.")
                        else:
                            cl.direct_send("Invalid move!", thread.id)
                            print(f"Invalid move attempt at {pos}.")
        else:
            print("No new messages.")
    except Exception as e:
        print(f"Error checking messages: {e}")

# Add a longer delay for the 2FA confirmation to give you time to confirm in the Instagram app
def wait_before_next_login_attempt():
    print("Waiting for a while before trying again...")
    time.sleep(30)  # Wait 30 seconds before retrying the login

# Start the game loop
while True:
    check_messages()
    wait_before_next_login_attempt()  # Add the wait time between login attempts
