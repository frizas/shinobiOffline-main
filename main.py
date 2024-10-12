import pygame
import sys
from player import Player
from settings import *
from level import Level
from button import *
from enum import Enum
from key_pressed_notifier import KeyPressedNotifier

class GameState(Enum):
    MENU = 1
    VILLAGE = 2
    PLAYING = 3
    MISSION_COMPLETE = 4
    GAME_OVER = 5
    PAUSED = 6
    OFFICE = 7
    SHOP = 8
    BARRACKS = 9

class Game:
    def __init__(self):
        pygame.init()
        self.window = pygame.display.set_mode((WIDTH, HEIGHT))  # , pygame.FULLSCREEN
        pygame.display.set_caption('Shinobi Offline')
        self.running = True
        self.state = GameState.MENU
        self.level = None
        self.font = pygame.font.Font(None, 74)
        self.level_number = 1
        self.menu_background = pygame.image.load('images/mainmenu.png').convert()
        self.village_background = pygame.image.load('images/map/konoha/village_background.png').convert()
        self.office_building = pygame.image.load('images/map/konoha/office_building.png').convert_alpha()
        self.shop_building = pygame.image.load('images/map/konoha/shop_building.png').convert_alpha()
        self.barracks_building = pygame.image.load('images/map/konoha/barracks_building.png').convert_alpha()
        self.office_inside = pygame.image.load('images/map/konoha/office_inside.png').convert()
        self.shop_inside = pygame.image.load('images/map/konoha/shop_inside.png').convert()
        self.barracks_inside = pygame.image.load('images/map/konoha/barracks_inside.png').convert()
        
        self.buildings = {
            'office': self.office_building,
            'shop': self.shop_building,
            'barracks': self.barracks_building
        }

        # Zoom settings
        self.GAME_WIDTH, self.GAME_HEIGHT = WIDTH // 2, HEIGHT // 2  # The game's internal resolution
        self.ZOOM_FACTOR = 2  # Adjust this to change the zoom level
        self.game_surface = pygame.Surface((self.GAME_WIDTH, self.GAME_HEIGHT))

        self.pause_buttons = {
            'resume': Button(self.GAME_WIDTH // 2 - 100, self.GAME_HEIGHT // 2, 200, 50, "Resume", 'green'),
            'quit': Button(self.GAME_WIDTH // 2 - 100, self.GAME_HEIGHT // 2 + 60, 200, 50, "Quit to Menu", 'red')
        }

        self.current_mission = None
        self.mission_level_index = 0
        self.mission_buttons = {}
        self.player = None
        self.create_default_player()

    def pixel_perfect_collision(self, surface, pos):
        try:
            mask = pygame.mask.from_surface(surface)
            pos_in_mask = (pos[0] - surface.get_rect().x, pos[1] - surface.get_rect().y)
            return mask.get_at(pos_in_mask)
        except IndexError:
            return False

    def create_default_player(self):
        # Create a dummy level to pass to the player
        dummy_level = type('DummyLevel', (), {'spawn_blood': lambda *args: None})()
        self.player = Player((0, 0), [], [], [], dummy_level)
        # No need to set gold here, as it's initialized in the Player class

    def show_mission_complete_screen(self):
        self.game_surface.fill('black')
        self.draw_text('Mission Complete!', 48, self.GAME_WIDTH // 2, self.GAME_HEIGHT // 2 - 50)
        self.draw_text(f'Gold earned: {self.current_mission["gold_reward"]}', 24, self.GAME_WIDTH // 2, self.GAME_HEIGHT // 2 + 50)
        self.draw_text('Press any key to continue', 24, self.GAME_WIDTH // 2, self.GAME_HEIGHT // 2 + 100)
        self.apply_zoom()
        pygame.display.flip()
        self.wait_for_keypress(self.return_to_village)

    def return_to_village(self):
        self.state = GameState.VILLAGE

    def start_next_level(self):
        if self.current_mission and self.mission_level_index < len(self.current_mission['levels']):
            level_number = self.current_mission['levels'][self.mission_level_index]
            player_state = self.player.save_state() if self.player else None
            self.level = Level(self.game_surface, level_number, player_state)
            self.player = self.level.player  # Update the game's player reference
            self.state = GameState.PLAYING
            self.mission_level_index += 1
        else:
            self.complete_mission()

    def complete_mission(self):
        if self.current_mission:
            self.player.gold += self.current_mission['gold_reward']
            self.show_mission_complete_screen()
        self.current_mission = None
        self.state = GameState.VILLAGE

    def reset(self):
        player_state = self.level.player.save_state() if self.level else None
        self.level_number += 1
        self.level = Level(self.game_surface, self.level_number)
        self.state = GameState.PLAYING

    def show_game_over_screen(self):
        self.game_surface.fill('black')
        game_over_text = self.font.render("You are dead.", True, (255, 255, 255))
        self.game_surface.blit(game_over_text, (self.GAME_WIDTH // 2 - game_over_text.get_width() // 2, self.GAME_HEIGHT // 2 - game_over_text.get_height() // 2))
        
        restart_button = Button(self.GAME_WIDTH // 2 - 100, self.GAME_HEIGHT // 2 + 100, 200, 50, "Restart", 'green')
        quit_button = Button(self.GAME_WIDTH // 2 - 100, self.GAME_HEIGHT // 2 + 160, 200, 50, "Quit to Menu", 'red')
        
        while self.state == GameState.GAME_OVER:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.MOUSEBUTTONDOWN:
                    scaled_pos = (event.pos[0] // self.ZOOM_FACTOR, event.pos[1] // self.ZOOM_FACTOR)
                    #if restart_button.is_clicked(scaled_pos):
                    #    self.reset_game()
                    #    self.state = GameState.PLAYING
                    if quit_button.is_clicked(scaled_pos):
                        self.reset_game()
                        self.state = GameState.MENU

            #restart_button.draw(self.game_surface)
            quit_button.draw(self.game_surface)
            self.apply_zoom()
            pygame.display.flip()

    def reset_game(self):
        self.level_number = 1
        self.mission_level_index = 0
        self.current_mission = None
        self.state = GameState.MENU
        self.create_default_player()  # Reset the player to default state
        if self.level:
            self.level.reset()  # Add a reset method to your Level class
        # Reset any other game state variables as needed

    def run(self):
        while self.running:
            if self.state == GameState.MENU:
                self.show_menu()
            elif self.state == GameState.VILLAGE:
                self.show_village()
            elif self.state == GameState.PLAYING:
                self.playing()
            elif self.state == GameState.MISSION_COMPLETE:
                self.show_mission_complete_screen()
            elif self.state == GameState.GAME_OVER:
                self.show_game_over_screen()
            elif self.state == GameState.PAUSED:
                self.handle_pause()
            elif self.state in [GameState.OFFICE, GameState.SHOP, GameState.BARRACKS]:
                self.show_building_interior(self.state)

    def wait_for_keypress(self, action):
        waiting = True
        while waiting:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN or event.type == pygame.MOUSEBUTTONDOWN:
                    waiting = False
                    action()

    def show_menu(self):
        # Calculate new y-positions (15% lower)
        start_y = int(self.GAME_HEIGHT * 0.65)  # 65% down the screen instead of 50%
        quit_y = start_y + 60  # Keep the same spacing between buttons

        start_game_button = Button(self.GAME_WIDTH // 2 - 100, start_y, 200, 50, "Start Game", 'green')
        quit_button = Button(self.GAME_WIDTH // 2 - 100, quit_y, 200, 50, "Quit", 'red')
        while self.state == GameState.MENU:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.MOUSEBUTTONDOWN:
                    scaled_pos = (event.pos[0] // self.ZOOM_FACTOR, event.pos[1] // self.ZOOM_FACTOR)
                    if start_game_button.is_clicked(scaled_pos):
                        self.state = GameState.VILLAGE
                    elif quit_button.is_clicked(scaled_pos):
                        self.running = False
                        pygame.quit()
                        sys.exit()

            self.game_surface.blit(pygame.transform.scale(self.menu_background, (self.GAME_WIDTH, self.GAME_HEIGHT)), (0, 0))
            self.draw_text('Shinobi Offline', 48, self.GAME_WIDTH // 2, self.GAME_HEIGHT // 4)
            start_game_button.draw(self.game_surface)
            quit_button.draw(self.game_surface)
            self.apply_zoom()
            pygame.display.flip()

    def draw_text(self, text, size, x, y, color=(255, 255, 255)):
        font = pygame.font.Font(None, size)
        text_surface = font.render(text, True, color)
        text_rect = text_surface.get_rect()
        text_rect.midtop = (x, y)
        self.game_surface.blit(text_surface, text_rect)

    def playing(self):
        while self.state == GameState.PLAYING:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                    pygame.quit()
                    sys.exit()

                if event.type == pygame.KEYDOWN:
                    KeyPressedNotifier.notify(event.key)
                    if event.key == pygame.K_ESCAPE:
                        self.state = GameState.PAUSED
                        self.show_pause_menu()

            self.game_surface.fill('white')
            self.level.run(self.game_surface)
            self.apply_zoom()
            pygame.display.update()

            if self.level.player.hp <= 0:
                self.state = GameState.GAME_OVER
                break  # Exit the playing loop to show the game over screen

            if self.level.enemy_count == 0 and self.level.player.rect.right >= self.level.get_map_rect().right - 64:
                if self.mission_level_index < len(self.current_mission['levels']):
                    self.start_next_level()
                else:
                    self.complete_mission()

    def apply_zoom(self):
        scaled_surface = pygame.transform.scale(self.game_surface, (self.GAME_WIDTH * self.ZOOM_FACTOR, self.GAME_HEIGHT * self.ZOOM_FACTOR))
        self.window.blit(scaled_surface, ((WIDTH - self.GAME_WIDTH * self.ZOOM_FACTOR) // 2, 
                                          (HEIGHT - self.GAME_HEIGHT * self.ZOOM_FACTOR) // 2))

    def show_village(self):
        while self.state == GameState.VILLAGE:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.MOUSEBUTTONDOWN:
                    mouse_pos = pygame.mouse.get_pos()
                    scaled_pos = (mouse_pos[0] // self.ZOOM_FACTOR, mouse_pos[1] // self.ZOOM_FACTOR)
                    
                    # Divide the screen into three vertical sections
                    if scaled_pos[0] < self.GAME_WIDTH // 3:
                        self.state = GameState.BARRACKS
                    elif scaled_pos[0] < (self.GAME_WIDTH * 2) // 3:
                        self.state = GameState.OFFICE
                    else:
                        self.state = GameState.SHOP

            self.game_surface.blit(pygame.transform.scale(self.village_background, (self.GAME_WIDTH, self.GAME_HEIGHT)), (0, 0))
            
            # Draw building images
            for building, image in self.buildings.items():
                if building == 'office':
                    self.game_surface.blit(image, (self.GAME_WIDTH // 3, 0))
                else:
                    self.game_surface.blit(image, (0, 0))

            # Highlight the section the mouse is over
            mouse_pos = pygame.mouse.get_pos()
            scaled_pos = (mouse_pos[0] // self.ZOOM_FACTOR, mouse_pos[1] // self.ZOOM_FACTOR)
            highlight_rect = pygame.Rect(0, 0, self.GAME_WIDTH // 3, self.GAME_HEIGHT)
            
            if scaled_pos[0] < self.GAME_WIDTH // 3:
                highlight_rect.left = 0
            elif scaled_pos[0] < (self.GAME_WIDTH * 2) // 3:
                highlight_rect.left = self.GAME_WIDTH // 3
            else:
                highlight_rect.left = (self.GAME_WIDTH * 2) // 3

            pygame.draw.rect(self.game_surface, (255, 255, 0, 100), highlight_rect, 3)  # Yellow outline

            self.draw_text(f"Gold: {self.player.gold}", 24, self.GAME_WIDTH - 100, 50, color=(255, 215, 0))
            self.apply_zoom()
            pygame.display.flip()

        if self.state in [GameState.OFFICE, GameState.SHOP, GameState.BARRACKS]:
            self.show_building_interior(self.state)

    def start_mission(self, mission_id):
        self.current_mission = mission_data[mission_id]
        self.mission_level_index = 0
        self.start_next_level()

    def show_building_interior(self, building_state):
        if building_state == GameState.OFFICE:
            self.show_office()
        elif building_state == GameState.SHOP:
            self.show_shop()
        elif building_state == GameState.BARRACKS:
            self.show_barracks()

    def show_office(self):
        back_button = Button(50, self.GAME_HEIGHT - 70, 100, 50, "Back", 'red')
        mission_buttons = {}
        y_offset = 100
        for mission_id, mission in mission_data.items():
            button = Button(self.GAME_WIDTH // 2 - 150, y_offset, 300, 50, f"Mission {mission_id}: {mission['name']}", 'blue')
            mission_buttons[mission_id] = button
            y_offset += 60

        while self.state == GameState.OFFICE:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.MOUSEBUTTONDOWN:
                    scaled_pos = (event.pos[0] // self.ZOOM_FACTOR, event.pos[1] // self.ZOOM_FACTOR)
                    if back_button.is_clicked(scaled_pos):
                        self.state = GameState.VILLAGE
                    for mission_id, button in mission_buttons.items():
                        if button.is_clicked(scaled_pos):
                            self.start_mission(mission_id)

            self.game_surface.blit(pygame.transform.scale(self.office_inside, (self.GAME_WIDTH, self.GAME_HEIGHT)), (0, 0))
            for button in mission_buttons.values():
                button.draw(self.game_surface)
            back_button.draw(self.game_surface)
            self.draw_text("Available Missions", 36, self.GAME_WIDTH // 2, 50)
            self.apply_zoom()
            pygame.display.flip()

    def show_shop(self):
        back_button = Button(50, self.GAME_HEIGHT - 70, 100, 50, "Back", 'red')
        weapon_buttons = {}
        y_offset = 100
        for weapon_name, weapon_info in weapon_data.items():
            if weapon_info.get('type') in ['melee', 'ranged']:  # Only show melee and ranged weapons
                price = weapon_info.get('price', 100)  # Default price if not specified
                button = Button(self.GAME_WIDTH // 2 - 150, y_offset, 300, 50, f"Buy {weapon_name.capitalize()} ({price} gold)", 'green')
                weapon_buttons[weapon_name] = button
                y_offset += 60

        while self.state == GameState.SHOP:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.MOUSEBUTTONDOWN:
                    scaled_pos = (event.pos[0] // self.ZOOM_FACTOR, event.pos[1] // self.ZOOM_FACTOR)
                    if back_button.is_clicked(scaled_pos):
                        self.state = GameState.VILLAGE
                    for weapon_name, button in weapon_buttons.items():
                        if button.is_clicked(scaled_pos):
                            price = weapon_data[weapon_name].get('price', 100)
                            if self.player.gold >= price:
                                self.player.gold -= price
                                # Add weapon to player's inventory (you'll need to implement this)
                                print(f"Bought {weapon_name}")  # Placeholder for inventory addition

            self.game_surface.blit(pygame.transform.scale(self.shop_inside, (self.GAME_WIDTH, self.GAME_HEIGHT)), (0, 0))
            for button in weapon_buttons.values():
                button.draw(self.game_surface)
            back_button.draw(self.game_surface)
            self.draw_text("Weapon Shop", 36, self.GAME_WIDTH // 2, 50)
            self.draw_text(f"Gold: {self.player.gold}", 24, self.GAME_WIDTH - 100, 50, color=(255, 215, 0))
            self.apply_zoom()
            pygame.display.flip()

    def show_barracks(self):
        back_button = Button(50, self.GAME_HEIGHT - 70, 100, 50, "Back", 'red')
        ally_buttons = {}
        y_offset = 100
        for ally_name, ally_info in ally_data.items():
            price = ally_info.get('price', 200)  # Default price if not specified
            button = Button(self.GAME_WIDTH // 2 - 150, y_offset, 300, 50, f"Hire {ally_name} ({price} gold)", 'gold')
            ally_buttons[ally_name] = button
            y_offset += 60

        while self.state == GameState.BARRACKS:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.MOUSEBUTTONDOWN:
                    scaled_pos = (event.pos[0] // self.ZOOM_FACTOR, event.pos[1] // self.ZOOM_FACTOR)
                    if back_button.is_clicked(scaled_pos):
                        self.state = GameState.VILLAGE
                    for ally_name, button in ally_buttons.items():
                        if button.is_clicked(scaled_pos):
                            price = ally_data[ally_name].get('price', 200)
                            if self.player.gold >= price:
                                self.player.gold -= price
                                # Add ally to player's team (you'll need to implement this)
                                print(f"Hired {ally_name}")  # Placeholder for ally addition

            self.game_surface.blit(pygame.transform.scale(self.barracks_inside, (self.GAME_WIDTH, self.GAME_HEIGHT)), (0, 0))
            for button in ally_buttons.values():
                button.draw(self.game_surface)
            back_button.draw(self.game_surface)
            self.draw_text("Mercenary Barracks", 36, self.GAME_WIDTH // 2, 50)
            self.draw_text(f"Gold: {self.player.gold}", 24, self.GAME_WIDTH - 100, 50, color=(255, 215, 0))
            self.apply_zoom()
            pygame.display.flip()

    def show_pause_menu(self):
        pause_surface = pygame.Surface((self.GAME_WIDTH, self.GAME_HEIGHT), pygame.SRCALPHA)
        pause_surface.fill((0, 0, 0, 128))
        self.game_surface.blit(pause_surface, (0, 0))
        
        for button in self.pause_buttons.values():
            button.draw(self.game_surface)
        
        self.apply_zoom()
        pygame.display.flip()

    def handle_pause(self):
        while self.state == GameState.PAUSED:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.MOUSEBUTTONDOWN:
                    scaled_pos = (event.pos[0] // self.ZOOM_FACTOR, event.pos[1] // self.ZOOM_FACTOR)
                    if self.pause_buttons['resume'].is_clicked(scaled_pos):
                        self.state = GameState.PLAYING
                    elif self.pause_buttons['quit'].is_clicked(scaled_pos):
                        self.state = GameState.MENU
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.state = GameState.PLAYING

            self.show_pause_menu()

def main():
    game = Game()
    game.run()

if __name__ == "__main__":
    main()