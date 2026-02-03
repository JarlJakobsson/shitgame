# ============================================
# MENU HANDLING
# ============================================

from constants import MAIN_MENU_TEXT, RACE_MENU_TEXT, GAME_MENU_TEXT


# Display the main start menu.
def display_start_menu():
    print(MAIN_MENU_TEXT)
    choice = input("Enter your choice: ").strip()
    return choice


# Display the race selection menu.
def display_race_menu():
    print(RACE_MENU_TEXT)
    choice = input("Enter your choice: ").strip()
    return choice


# Display the main game menu after gladiator creation.
def display_main_game_menu():
    print(GAME_MENU_TEXT)
    choice = input("Enter your choice: ").strip()
    return choice
