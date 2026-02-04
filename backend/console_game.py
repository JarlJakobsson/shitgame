# ============================================
# CONSOLE VERSION - MAIN GAME LOGIC
# ============================================

from menu import display_start_menu, display_race_menu, display_main_game_menu
from gladiator import Gladiator
from combat import Combat
import random


class Game:
    """Main game controller."""
    
    def __init__(self):
        """Initialize the game."""
        self.player_gladiator = None
        self.running = True
    
    def create_gladiator(self):
        """Create a new gladiator for the player."""
        print("\n" + "="*50)
        print(" "*10 + "CREATE YOUR GLADIATOR")
        print("="*50)
        
        # Get name
        name = input("\nEnter your gladiator's name: ").strip()
        if not name:
            name = "Unnamed"
        
        # Get race
        while True:
            race_choice = display_race_menu()
            if race_choice == "1":
                race = "Human"
                break
            elif race_choice == "2":
                race = "Orc"
                break
            else:
                print("\nInvalid choice. Please try again.")
        
        # Create gladiator
        self.player_gladiator = Gladiator(name, race, use_race_stats=True)
        print(f"\n✓ {self.player_gladiator.name} the {self.player_gladiator.race} has entered the arena!")
        self.player_gladiator.display_stats()
    
    def train(self):
        """Train the gladiator to improve stats."""
        print("\n" + "="*50)
        print(" "*18 + "TRAINING")
        print("="*50)
        print("\nTraining costs 10 gold and increases all stats by 1!")
        
        if self.player_gladiator.gold >= 10:
            confirm = input("\nTrain? (y/n): ").strip().lower()
            if confirm == "y":
                self.player_gladiator.gold -= 10
                self.player_gladiator.strength += 1
                self.player_gladiator.dodge += 1
                self.player_gladiator.defense += 1
                self.player_gladiator.max_health += 5
                self.player_gladiator.current_health = self.player_gladiator.max_health
                self.player_gladiator.add_experience(10)
                print("\n✓ Training complete! Stats improved!")
            else:
                print("\nTraining cancelled.")
        else:
            print("\nYou don't have enough gold to train! (Need 10, have " 
                  f"{self.player_gladiator.gold})")
    
    def fight(self):
        """Fight in the arena against a random opponent."""
        print("\n" + "="*50)
        print(" "*18 + "ARENA FIGHT")
        print("="*50)
        
        # Restore health for new fight
        self.player_gladiator.current_health = self.player_gladiator.max_health
        
        # Create opponent
        opponent_races = ["Human", "Orc"]
        opponent_race = random.choice(opponent_races)
        difficulty = random.choice(["Weak", "Normal", "Strong"])
        opponent = Gladiator(f"{difficulty} {opponent_race}", opponent_race, use_race_stats=True)
        
        # Adjust opponent stats based on difficulty
        if difficulty == "Weak":
            opponent.strength = int(opponent.strength * 0.8)
            opponent.dodge = int(opponent.dodge * 0.8)
            opponent.max_health = int(opponent.max_health * 0.9)
        elif difficulty == "Strong":
            opponent.strength = int(opponent.strength * 1.2)
            opponent.dodge = int(opponent.dodge * 1.2)
            opponent.max_health = int(opponent.max_health * 1.1)
        
        opponent.current_health = opponent.max_health
        
        # Start combat
        combat = Combat(self.player_gladiator, opponent)
        winner = combat.start_battle()
        
        # Determine rewards
        print("\n" + "="*50)
        if winner == self.player_gladiator:
            print("✓ VICTORY!")
            reward_exp = 60 if difficulty == "Strong" else (45 if difficulty == "Normal" else 30)
            reward_gold = 30 if difficulty == "Strong" else (20 if difficulty == "Normal" else 10)
            self.player_gladiator.add_experience(reward_exp)
            self.player_gladiator.gold += reward_gold
            self.player_gladiator.wins += 1
            print(f"\nYou earned {reward_exp} experience and {reward_gold} gold!")
        else:
            print("✗ DEFEAT!")
            self.player_gladiator.losses += 1
            print(f"\nYou were defeated...")
        print("="*50)
    
    def main_game_loop(self):
        """Main game loop after gladiator creation."""
        while self.running and self.player_gladiator:
            choice = display_main_game_menu()
            
            if choice == "1":
                self.player_gladiator.display_stats()
            elif choice == "2":
                self.train()
            elif choice == "3":
                self.fight()
            elif choice == "4":
                print("\nThanks for playing! Goodbye.")
                self.running = False
            else:
                print("\nInvalid choice. Please try again.")
    
    def start(self):
        """Start the game."""
        while self.running:
            choice = display_start_menu()
            
            if choice == "1":
                self.create_gladiator()
                self.main_game_loop()
            elif choice == "2":
                print("\nThanks for playing! Goodbye.")
                self.running = False
            else:
                print("\nInvalid choice. Please try again.")


if __name__ == "__main__":
    game = Game()
    game.start()
