import random
import pygame
from player import Player
from tile import Tile
from camera import Camera
from enemy import Enemy
from settings import *
from projectile import Projectile
from effects import *
from text_display import *
import os
#import sys
from ally import Ally
from grass import GrassManager
from weather_controller import create_weather_controller
GREEN = (0, 255, 0)
BROWN = (139, 69, 19)
GRAY = (130, 130, 130)
BLUE = (0, 50, 255)
ORANGE = (220, 165, 0)

class MapController:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.map = pygame.Surface((width, height))
        self.map.fill(GREEN)
        self.elements = {
            'tree': BROWN,
            'rock': GRAY,
            'river': BLUE,
            'bridge': ORANGE,
            'grass': GREEN,
            'empty': GREEN,
            'bonfire': (255, 100, 0)  # Add this line with an appropriate color for bonfire
        }
        self.element_grid = [[None for _ in range(height)] for _ in range(width)]

    def add_element(self, x, y, element_type):
        if element_type in self.elements:
            color = self.elements[element_type]
            if 0 <= x < self.width and 0 <= y < self.height:
                self.map.set_at((x, y), color)
                self.element_grid[x][y] = element_type
            else:
                # If out of range, place a grass tile at the edge of the map
                edge_x = max(0, min(x, self.width - 1))
                edge_y = max(0, min(y, self.height - 1))
                self.map.set_at((edge_x, edge_y), self.elements['grass'])
                self.element_grid[edge_x][edge_y] = 'grass'
        else:
            raise ValueError(f"Unknown element: {element_type}")

    def add_rect(self, x, y, width, height, element_type):
        if element_type in self.elements:
            color = self.elements[element_type]
            for i in range(x, x + width):
                for j in range(y, y + height):
                    if 0 <= i < self.width and 0 <= j < self.height:
                        self.map.set_at((i, j), color)
                        self.element_grid[i][j] = element_type
                    else:
                        # If out of range, place a grass tile at the edge of the map
                        edge_i = max(0, min(i, self.width - 1))
                        edge_j = max(0, min(j, self.height - 1))
                        self.map.set_at((edge_i, edge_j), self.elements['grass'])
                        self.element_grid[edge_i][edge_j] = 'grass'
        else:
            raise ValueError(f"Unknown element: {element_type}")
    def is_area_empty(self, x, y):
        if not (0 <= x < self.width and 0 <= y < self.height):
            return False

        for dy in [-1, 0, 1]:
            for dx in [-1, 0, 1]:
                nx, ny = x + dx, y + dy
                if 0 <= nx < self.width and 0 <= ny < self.height:
                    if self.element_grid[nx][ny] != 'empty':
                        return False
        return True

    def find_empty_areas(self):
        empty_areas = []
        for y in range(self.height):
            for x in range(self.width):
                if self.is_area_empty(x, y):
                    empty_areas.append((x, y))
        return empty_areas

    def get_element_at(self, x, y):
        if 0 <= x < self.width and 0 <= y < self.height:
            return self.element_grid[x][y]
        return None

    def find_elements_of_type(self, element_type):
        positions = []
        for y in range(self.height):
            for x in range(self.width):
                if self.element_grid[x][y] == element_type:
                    positions.append((x, y))
        return positions

    def draw_map(self, screen, scale_factor=2):
        scaled_map = pygame.transform.scale(self.map, (self.width * scale_factor, self.height * scale_factor))
        screen.blit(scaled_map, (600, 500))
        border_color = (139, 69, 19)
        border_width = 1
        pygame.draw.rect(screen, border_color, (600, 500, self.width * scale_factor, self.height * scale_factor), border_width)


class Level:
    
    def __init__(self, screen, level_number=1,player_state=None):
        self.all_sprites = pygame.sprite.Group()
        self.tiles = pygame.sprite.Group()
        self.collidable_tiles = pygame.sprite.Group()
        self.overlay_sprites = pygame.sprite.Group()
        self.trunk = pygame.sprite.Group()
        self.top_sprites = pygame.sprite.Group()
        self.tile_top_sprites = pygame.sprite.Group()  # New group for bridges and similar elements
        self.spark_sounds = [pygame.mixer.Sound(path) for path in sound_data['spark']]        
        self.enemies = pygame.sprite.Group()
        self.ally = pygame.sprite.Group()
        self.jogador = pygame.sprite.Group()
        self.projectiles = pygame.sprite.Group()
        self.level_number = level_number
        self.screen = screen
        self.camera = Camera(screen.get_width(), screen.get_height(), zoom=3)
        level_info = level_data.get(self.level_number, level_data[1])
        self.grid_width, self.grid_height = level_info['dimensions']
        self.clock = pygame.time.Clock()
        self.ui_image = pygame.image.load('images/ui.png').convert_alpha()  # Carregar a imagem da UI
        self.ui_rect = self.ui_image.get_rect()
        self.map_controller = MapController(self.grid_width, self.grid_height)
        self.weather_particles = pygame.sprite.Group()
        self.weather_controller = create_weather_controller(screen.get_width(), screen.get_height(), self.weather_particles)
        self.grass_manager = GrassManager('images/map', tile_size=32)
        self.place_grass()
        self.create_random_map()
        self.create_enemies()
        self.create_player(player_state)
        self.update_enemy_count()
        
        self.total_enemies = level_info['num_enemies']  # Total de inimigos neste nível
        self.player_last_melee_time = 0
        
        self.enemy_last_melee_time = 0
        self.night_surface = pygame.Surface((self.grid_width * 32, self.grid_height * 32), pygame.SRCALPHA)
        self.day_length = 240  # Full day-night cycle in seconds
        self.time_of_day = random.uniform(0, self.day_length)  # Random start time
        self.light_cache = {}
    
        self.tile_size =32
        
        self.grass_manager = GrassManager('images/map', tile_size=32)
        self.player_pos = (200, (self.grid_height*32)/2)

    def create_light_hole(self, pos, radius, color=(255, 200, 100)):
        radius = int(radius)
        cache_key = (radius, color)
        diameter = radius * 2
        
        if cache_key not in self.light_cache:
            temp_surface = pygame.Surface((diameter, diameter), pygame.SRCALPHA)
            for x in range(diameter):
                for y in range(diameter):
                    distance = math.hypot(x - radius, y - radius)
                    if distance <= radius:
                        # Use a quadratic falloff for smoother light
                        intensity = 1 - (distance / radius) ** 2
                        # Apply an additional power function to concentrate light at the center
                        intensity = intensity ** 1.5
                        alpha = int(150 * intensity)
                        temp_surface.set_at((x, y), (*color, alpha))
            self.light_cache[cache_key] = temp_surface

        light_surface = self.light_cache[cache_key].copy()
        
        # Use BLEND_RGBA_SUB for subtractive blending
        self.night_surface.blit(light_surface, (int(pos.x - radius), int(pos.y - radius)), special_flags=pygame.BLEND_RGBA_SUB)
    
    def update_night_surface(self, dt):
        # Update time of day
        self.time_of_day += dt
        if self.time_of_day >= self.day_length:
            self.time_of_day -= self.day_length

        # Calculate alpha using a smooth sinusoidal function
        day_progress = self.time_of_day / self.day_length
        self.alpha = int(95 * (math.sin(2 * math.pi * day_progress - math.pi/2) + 1))

        # Clear the night surface with the current alpha
        self.night_surface.fill((0, 0, 0, self.alpha))

        # Apply light effects
        light_sources = [
            (sprite, 120, (255, 200, 100)) for sprite in self.all_sprites if isinstance(sprite, Bonfire)
        ] + [
            (self.player, 50, (100, 50, 22))
        ] + [
            (self.Ally, 45, (100, 50, 22))
        ]+ [
            (sprite, 70, (255, 150, 50)) for sprite in self.all_sprites if isinstance(sprite, Projectile) and sprite.type == 'fireball'
        ] + [
            (sprite, 60, (255, 180, 80)) for sprite in self.all_sprites if isinstance(sprite, FireEmitter)
        ]+ [
            (sprite, 45, (255, 180, 80)) for sprite in self.all_sprites if isinstance(sprite, Enemy)
        ]

        camera_offset = pygame.math.Vector2(self.camera.camera.topleft)
        for source, base_radius, color in light_sources:
            screen_pos = pygame.math.Vector2(source.rect.center) + camera_offset
            self.create_light_hole(screen_pos, base_radius, color)
    
    def update_enemy_count(self):
        self.enemy_count = len(self.enemies)

    def play_random_spark_sound(self):
        random.choice(self.spark_sounds).play()

    def draw_enemy_counter(self, screen):
        font = pygame.font.Font(None, 14)
        text = f"Killed Enemies: {self.total_enemies-self.enemy_count} / {self.total_enemies}"
        text_surface = font.render(text, True, (30, 0, 0))
        screen.blit(text_surface, (20, 107))  # Desenha o texto no canto superior esquerdo

    def draw_level(self,screen):
        font = pygame.font.Font(None, 18)
        text = f"{self.player.nivel-1}"
        text_surface = font.render(text, True, (250, 200, 255))
        screen.blit(text_surface, (135, 51))  # Desenha o texto no canto superior esquerdo

    def get_random_free_position_near_bonfire(self, buffer=2, max_attempts=100):
            tile_size = 32
            bonfire_pos = (self.grid_width // 2, self.grid_height // 2)
            for _ in range(max_attempts):
                x = bonfire_pos[0] + random.randint(-buffer, buffer) * tile_size
                y = bonfire_pos[1] + random.randint(-buffer, buffer) * tile_size
                rect = pygame.Rect(x, y, tile_size * 2, tile_size * 2)
                if not any(rect.colliderect(tile.rect) for tile in self.collidable_tiles) and \
                        not any(rect.colliderect(enemy.rect) for enemy in self.enemies):
                    return x, y
            return None, None
    
    def get_random_free_position(self, buffer=2, max_attempts=100):
        tile_size = 32
        for _ in range(max_attempts):
            x = random.randint(buffer, self.grid_width - 1 - buffer) * tile_size
            y = random.randint(buffer, self.grid_height - 1 - buffer) * tile_size
            rect = pygame.Rect(x, y, tile_size * 2, tile_size * 2)
            if not any(rect.colliderect(tile.rect) for tile in self.collidable_tiles) and \
               not any(rect.colliderect(enemy.rect) for enemy in self.enemies):
                if x >= 400:
                    return x, y
        return None, None

    def get_map_rect(self):
        return pygame.Rect(0, 0, self.grid_width * 32, self.grid_height * 32)

    def create_player(self,state=None):
        player_pos = (200, (self.grid_height*32)/2)
        self.player = Player(player_pos, [self.all_sprites, self.jogador], self.collidable_tiles, self.projectiles, self,state)
        if state:
            self.player.load_state(state)
    def create_enemies(self):
        level_info = level_data.get(self.level_number, level_data[1])

        num_enemies = level_info['num_enemies']
        for _ in range(num_enemies):
            pos = self.get_random_free_position_near_bonfire(buffer=3)
            if pos == (None, None):
                continue
            monster_name = random.choice(list(monster_data.keys()))

            # Determina o rank do inimigo baseado em chances
            chance = random.random()
            if chance < 0.03:
                rank = 'S'
            elif chance < 0.08:
                rank = 'A'
            elif chance < 0.18:
                rank = 'B'
            elif chance < 0.33:
                rank = 'C'
            else:
                rank = 'D'

            # Cria o inimigo com o rank determinado
            enemy = Enemy(monster_name, rank, pos, [self.all_sprites, self.enemies], self.projectiles, self)
            self.enemies.add(enemy)
            self.all_sprites.add(enemy)

    def create_ally(self):
      #  level_info = level_data.get(self.level_number, level_data[1])
      #  num_enemies = level_info['num_enemies']
        
            ally_name = random.choice(list(ally_data.keys()))

            # Determina o rank do inimigo baseado em chances
            chance = random.random()
            if chance < 0.3:
                rank = 'S'
            elif chance < 0.5:
                rank = 'A'
            elif chance < 0.7:
                rank = 'B'
            elif chance < 0.8:
                rank = 'C'
            else:
                rank = 'D'

            # Cria o inimigo com o rank determinado
            self.Ally = Ally(ally_name, rank, (300, (self.grid_height*32)/2), [self.all_sprites, self.ally], self.projectiles, self)
            self.ally.add(self.Ally)
            self.all_sprites.add(self.Ally)
    
    def create_random_map(self):
        level_info = level_data.get(self.level_number, level_data[1])
        grid_width, grid_height = level_info['dimensions']
        tile_size = 32
        self.create_ally()

        for y in range(grid_height):
            for x in range(grid_width):
                Tile('images/map/grass.png', ((x-grid_width) * tile_size, y * tile_size), [self.all_sprites, self.tiles], collidable=False)
                Tile('images/map/grass.png', ((x-grid_width) * tile_size, (y-grid_height) * tile_size), [self.all_sprites, self.tiles], collidable=False)
                Tile('images/map/grass.png', ((x-grid_width) * tile_size, (y+grid_height) * tile_size), [self.all_sprites, self.tiles], collidable=False)
                Tile('images/map/grass.png', (x * tile_size, y * tile_size), [self.all_sprites, self.tiles], collidable=False)
                Tile('images/map/grass.png', (x * tile_size, (y-grid_height) * tile_size), [self.all_sprites, self.tiles], collidable=False)
                Tile('images/map/grass.png', (x * tile_size, (y+grid_height) * tile_size), [self.all_sprites, self.tiles], collidable=False)
                Tile('images/map/grass.png', ((x+grid_width) * tile_size, y * tile_size), [self.all_sprites, self.tiles], collidable=False)
                Tile('images/map/grass.png', ((x+grid_width) * tile_size, (y-grid_height) * tile_size), [self.all_sprites, self.tiles], collidable=False)
                Tile('images/map/grass.png', ((x+grid_width) * tile_size, (y+grid_height) * tile_size), [self.all_sprites, self.tiles], collidable=False)
                self.map_controller.add_element(x, y, 'empty')
  
        
        self.create_bonfire()
        self.create_river_with_bridge()
        self.create_walls(grid_width, grid_height, tile_size)
    def create_walls(self, grid_width, grid_height, tile_size):
        top_wall = bottom_wall = 1
        for x in range(grid_width):
            if x in ((grid_width // 2), (grid_width // 2) - 1, (grid_width // 2) + 1):
                pass
            else:
                for i in range(top_wall):
                    if random.random() < 0.35 and self.map_controller.is_area_empty(x, i):
                        self.create_tree(x, i, tile_size)
                        self.map_controller.add_element(x, i, 'tree')
                        self.create_tree(x, grid_height+i, tile_size)
                        self.create_tree(x+grid_width, i, tile_size)
                        self.create_tree(x+grid_width, grid_height+i, tile_size)
                        self.create_tree(x-grid_width, i, tile_size)
                        self.create_tree(x-grid_width, grid_height+i, tile_size)
                for i in range(bottom_wall):
                    if random.random() < 0.25 and self.map_controller.is_area_empty(x, grid_height - i - 1):
                        self.create_tree(x, grid_height - i - 1, tile_size)
                        self.map_controller.add_element(x, grid_height - i - 1, 'tree')
                        self.create_tree(x, -i - 1, tile_size)
                        self.create_tree(x+grid_width, grid_height - i - 1, tile_size)
                        self.create_tree(x+grid_width, -i - 1, tile_size)
                        self.create_tree(x-grid_width, grid_height - i - 1, tile_size)
                        self.create_tree(x-grid_width, -i - 1, tile_size)

                top_wall = self.adjust_wall_thickness(top_wall)
                bottom_wall = self.adjust_wall_thickness(bottom_wall)
                open_area_start = top_wall
                open_area_end = grid_height - bottom_wall

                if random.random() < 0.9:
                    if open_area_start < open_area_end and self.map_controller.is_area_empty(x, open_area_start):
                        y = random.randint(open_area_start, open_area_end - 1)
                        self.create_tree(x, y, tile_size)
                        self.map_controller.add_element(x, y, 'tree')
                        self.create_tree(x+grid_width, y, tile_size)
                        self.create_tree(x-grid_width, y, tile_size)
                        self.create_tree(x, y+grid_height, tile_size)
                        self.create_tree(x, y-grid_height, tile_size)
                        self.create_tree(x+grid_width, y-grid_height, tile_size)
                        self.create_tree(x-grid_width, y+grid_height, tile_size)
                        self.create_tree(x+grid_width, y+grid_height, tile_size)
                        self.create_tree(x-grid_width, y-grid_height, tile_size)

                        y = random.randint(open_area_start, open_area_end - 1)
                        self.create_rock(x, y, tile_size)
                        self.map_controller.add_element(x, y, 'rock')
                        self.create_rock(x+grid_width, y, tile_size)
                        self.create_rock(x-grid_width, y, tile_size)
                        self.create_rock(x, y+grid_height, tile_size)
                        self.create_rock(x, y-grid_height, tile_size)
                        self.create_rock(x+grid_width, y-grid_height, tile_size)
                        self.create_rock(x-grid_width, y+grid_height, tile_size)
                        self.create_rock(x+grid_width, y+grid_height, tile_size)
                        self.create_rock(x-grid_width, y-grid_height, tile_size)

    def adjust_wall_thickness(self, wall_thickness):
        if random.random() < 0.5:
            return max(1, wall_thickness - 1)
        else:
            return wall_thickness + 1
        
    def create_rock ( self,x,y,tile_size):
        if x < -20 or x > (self.grid_width + 20) or y < -15 or y > (self.grid_height + 15):           
            return
        else:
            rock_image_path = 'images/map/rock.png'
            rock_pos = (x * tile_size, y * tile_size)
            rock_tile = Tile(rock_image_path, rock_pos, [self.all_sprites, self.tiles, self.collidable_tiles], collidable=True, rect_size=(10, 10))

    def create_bonfire(self):
        tile_size = 32
        empty_areas = self.map_controller.find_empty_areas()

        if empty_areas:
            bonfire_pos = random.choice(empty_areas)
            if bonfire_pos[0] > self.grid_width//2:
                bonfire_x = bonfire_pos[0] * tile_size
                bonfire_y = bonfire_pos[1] * tile_size

                bonfire_image_path = 'images/effects/bonfire.png'
                Bonfire((bonfire_x, bonfire_y), [self.all_sprites, self.tiles])
                SmokeEmitter((bonfire_x, bonfire_y), [self.all_sprites, self.top_sprites], color=(200, 100, 100), emission_interval=300, emission_duration=60000)
                
                Bonfire((bonfire_x + self.grid_width*tile_size, bonfire_y), [self.all_sprites, self.tiles])
                SmokeEmitter((bonfire_x+ self.grid_width*tile_size, bonfire_y), [self.all_sprites, self.top_sprites], color=(200, 100, 100), emission_interval=300, emission_duration=60000)
                
                Bonfire((bonfire_x - self.grid_width*tile_size, bonfire_y), [self.all_sprites, self.tiles])
                SmokeEmitter((bonfire_x- self.grid_width*tile_size, bonfire_y), [self.all_sprites, self.top_sprites], color=(200, 100, 100), emission_interval=300, emission_duration=60000)
                
                Bonfire((bonfire_x, bonfire_y + self.grid_height*tile_size), [self.all_sprites, self.tiles])
                SmokeEmitter((bonfire_x, bonfire_y+ self.grid_height*tile_size), [self.all_sprites, self.top_sprites], color=(200, 100, 100), emission_interval=300, emission_duration=60000)
                
                Bonfire((bonfire_x, bonfire_y - self.grid_height*tile_size), [self.all_sprites, self.tiles])
                SmokeEmitter((bonfire_x, bonfire_y- self.grid_height*tile_size), [self.all_sprites, self.top_sprites], color=(200, 100, 100), emission_interval=300, emission_duration=60000)
                
                self.map_controller.add_element(bonfire_pos[0], bonfire_pos[1], 'bonfire')
            else:
                self.create_bonfire()
        else:
            print("No empty areas found for bonfire.")
    
    def create_tree(self, x, y, tile_size):
        if x < -20 or x > (self.grid_width + 20) or y < -15 or y > (self.grid_height + 15):
         return
        tree_type = random.choice(list(tree_data.keys()))
        trunk_image_path = tree_data[tree_type]['trunk_path']
        overlay_image_path = tree_data[tree_type]['overlay_path']

        # Verifique se os arquivos de imagem existem
        if not os.path.exists(trunk_image_path):
            print(f"File not found: {trunk_image_path}")
            return
        if not os.path.exists(overlay_image_path):
            print(f"File not found: {overlay_image_path}")
            return
        if x == (self.grid_width // 2,1+(self.grid_width // 2),(self.grid_width // 2)-1):
            return
        else:
            trunk_pos = (x * tile_size, y * tile_size)
            trunk_tile = Tile(trunk_image_path, trunk_pos, [self.all_sprites, self.trunk], collidable=False,tile_type='tree_trunk', rect_size=(20, 20))

            overlay_pos = (x * tile_size, y * tile_size)
            overlay_tile = Tile(overlay_image_path, overlay_pos, [self.all_sprites, self.overlay_sprites], collidable=False)
    def create_river_with_bridge(self):
        grid_width = self.grid_width
        grid_height = self.grid_height
        tile_size = 32
        river_x = grid_width // 2

        for y in range(-9, grid_height+9):
            # Create river tiles
            Tile('images/map/river1.png', (river_x * tile_size, y * tile_size), [self.all_sprites, self.tiles], collidable=True)
            Tile('images/map/river2.png', ((river_x + 1) * tile_size, y * tile_size), [self.all_sprites, self.tiles], collidable=True)
            self.map_controller.add_element(river_x, y, 'river')
            self.map_controller.add_element(river_x+1, y, 'river')
            for i in range(-22, 22, 4):
                tile_pos = (((river_x) * tile_size)-i, y * tile_size)
                WaterEmitter(tile_pos, [self.all_sprites, self.tiles])

        # Create bridge
        bridge_y = grid_height // 2
        for x in range(river_x+4, river_x + 5):
            Tile('images/map/bridge.png', (x * tile_size, bridge_y * tile_size), [self.all_sprites, self.tile_top_sprites], collidable=False)
            self.map_controller.add_rect(x, bridge_y, 8, 5, 'bridge')

    def get_clearing_positions(self):
        # Create a list of potential clearing positions
        tile_size = 32
        clearings = []
        for x in range(3, self.grid_width - 3, 10):
            for y in range(3, self.grid_height - 3, 10):
                clearings.append((x * tile_size, y * tile_size))
        random.shuffle(clearings)
        return clearings[:3]  # Return the first three clearings
    def melee_combat(self, player, enemy):
        current_time = pygame.time.get_ticks()
        cooldown = 2000  # Cooldown de 1 segundo em milissegundos

        if current_time - self.player_last_melee_time < cooldown or current_time - self.enemy_last_melee_time < cooldown:
            return 0, 0

        self.player_last_melee_time = current_time
        self.enemy_last_melee_time = current_time

        player_attack_chance = player.melee_skill / (player.melee_skill + enemy.defense_skill)
        enemy_attack_chance = enemy.melee_skill / (enemy.melee_skill + player.defense_skill)
        
        player_damage = 0
        enemy_damage = 0

        if random.random() < player_attack_chance:
            player_damage = max(5, (player.melee_skill-enemy.melee_skill)-player.defense_skill)  # Garante ao menos 1 de dano
        else:
            FloatingText('MISS', player.rect, 'white', self.camera, self.all_sprites)
                
            
        if random.random() < enemy_attack_chance:
            enemy_damage = max(5, player.melee_skill-enemy.defense_skill)  # Garante ao menos 1 de dano
            
        else:
                    FloatingText('MISS', enemy.rect, 'white', self.camera, self.all_sprites)
               
        return player_damage, enemy_damage

    def check_collisions(self):
        self.check_player_enemy_collisions()
        self.check_projectile_collisions()
        self.check_projectile_player_collisions()
        self.check_projectile_projectile_collisions()

    def check_player_enemy_collisions(self):
        hits = pygame.sprite.spritecollide(self.player, self.enemies, False,pygame.sprite.collide_mask)
        for hit in hits:
            if not self.player.invincible:
                player_damage, enemy_damage = self.melee_combat(self.player, hit)
                
                if player_damage > 0:
                    knockback_direction = pygame.math.Vector2(self.player.rect.center) - pygame.math.Vector2(hit.rect.center)
                    if knockback_direction.length() > 0:
                        knockback_direction.normalize_ip()

                        self.player.take_damage(player_damage, knockback_direction, (255, 0, 0))
                
                    
                if enemy_damage > 0:
                    knockback_direction2 = pygame.math.Vector2(hit.rect.center) -pygame.math.Vector2(self.player.rect.center)  
                    if knockback_direction2.length() > 0:
                        knockback_direction2.normalize_ip()
                       
                        hit.take_damage(enemy_damage, self.all_sprites, self.tiles, (255, 0, 0),knockback_direction2)

    #def check_projectile_player_collisions(self):
    #    for projectile in self.projectiles:
    #        if isinstance(projectile, Projectile):
    #            if projectile.side == 'enemy_projectile' and pygame.sprite.collide_rect(projectile, self.player):
    #                if not self.player.is_jumping:
    #                    self.player.take_damage(projectile.damage, pygame.math.Vector2(0, 0), (255, 0, 0))
    #                projectile.kill()
    #            elif projectile.side == 'player_projectile' and pygame.sprite.collide_rect(projectile, self.enemy):
    #                self.enemy.take_damage(projectile.damage, pygame.math.Vector2(0, 0), (255, 0, 0))
    #                projectile.kill()

    def check_projectile_collisions(self):
        for projectile in self.projectiles:
            if isinstance(projectile, Projectile) and projectile.side == 'player_projectile' and not projectile.type =='fireball' :
                enemy_hits = pygame.sprite.spritecollide(projectile, self.enemies, False,pygame.sprite.collide_mask)
                for enemy in enemy_hits:
                    enemy.take_damage(projectile.damage, self.all_sprites, self.tiles, (255, 0, 0),projectile.direction)
                    projectile.kill()    
                  
            if isinstance(projectile, InsectSwarm):
                collisions = pygame.sprite.groupcollide(self.projectiles, self.enemies, True, False, pygame.sprite.collide_mask)
                for particle, enemies in collisions.items():
                    for enemy in enemies:
                        enemy.take_damage(1 * self.Ally.multiplier, self.all_sprites, self.tiles, (255, 0, 0), projectile.direction)
                        projectile.kill()
    def check_projectile_projectile_collisions(self):
        projectiles = [p for p in self.projectiles if isinstance(p, Projectile)]
        for i in range(len(projectiles)):
            for j in range(i + 1, len(projectiles)):
                if pygame.sprite.collide_rect(projectiles[i], projectiles[j]):
                    projectile_i = projectiles[i]
                    projectile_j = projectiles[j]

                    # Verificar se a colisão envolve um InsectSwarm e uma fireball
                    if isinstance(projectile_i, InsectSwarm) and projectile_j.type == 'fireball':
                        self.handle_projectile_destruction(projectile_i)
                        continue
                    if isinstance(projectile_j, InsectSwarm) and projectile_i.type == 'fireball':
                        self.handle_projectile_destruction(projectile_j)
                        continue

                    # Verificar se os projéteis são indestrutíveis
                    projectile_i_indestructible = weapon_data.get(projectile_i.type, {}).get('indestructible', False)
                    projectile_j_indestructible = weapon_data.get(projectile_j.type, {}).get('indestructible', False)

                    # Verificar se os projéteis são                    projectile_i_from_collision = getattr(projectile_i, 'from_collision', False)
                    projectile_j_from_collision = getattr(projectile_j, 'from_collision', False)

                    # Lógica de colisão para projéteis de colisão
                    if projectile_j_from_collision and projectile_j_from_collision:
                        continue

                    if not projectile_i_indestructible and not projectile_j_indestructible:
                        print(f"Collision between {projectile_i.type} and {projectile_j.type}")
                        Spark(projectile_i.rect.center, [self.all_sprites, self.overlay_sprites])
                        Spark(projectile_j.rect.center, [self.all_sprites, self.overlay_sprites])
                        self.handle_projectile_destruction(projectile_i)
                        self.handle_projectile_destruction(projectile_j)
                        self.play_random_spark_sound()
                    elif not projectile_i_indestructible:
                        print(f"Collision destroying {projectile_i.type}")
                        Spark(projectile_i.rect.center, [self.all_sprites, self.overlay_sprites])
                        self.handle_projectile_destruction(projectile_i)
                        self.play_random_spark_sound()
                    elif not projectile_j_indestructible:
                        print(f"Collision destroying {projectile_j.type}")
                        Spark(projectile_j.rect.center, [self.all_sprites, self.overlay_sprites])
                        self.handle_projectile_destruction(projectile_j)
                        self.play_random_spark_sound()

    def handle_projectile_destruction(self, projectile):
        if projectile.type == 'kunai' and not projectile.from_collision:
            direction = pygame.math.Vector2(random.uniform(-1, 1), random.uniform(-1, 1))*2
            if direction.length() > 0:
                direction.normalize_ip()
                new_kunai = Projectile(
                    pos=projectile.rect.center,
                    direction=direction,
                    groups=[self.projectiles],
                    projectile_type='kunai',
                    level=self,
                    side=projectile.side,
                    from_collision=True)  # Sinalizador definido para verdadeiro)
                print(f"New kunai created at {new_kunai.rect.center} with direction {direction}")
        projectile.kill()

    def check_projectile_player_collisions(self):
        for projectile in self.projectiles:
            if isinstance(projectile, Projectile) and projectile.side == 'enemy_projectile':
                if pygame.sprite.spritecollide(projectile, self.jogador,False,pygame.sprite.collide_mask):
                    if not self.player.is_jumping:
                      self.player.take_damage(projectile.damage, pygame.math.Vector2(0, 0), (255, 0, 0))
                      projectile.kill()
                    else:
                        continue
                for ally in self.ally:  # Iterar sobre cada aliado no grupo self.allies
                    if pygame.sprite.spritecollide(projectile, self.ally,False,pygame.sprite.collide_mask):
                        ally.take_damage(projectile.damage,self.all_sprites,self.tiles,knockback_direction = pygame.math.Vector2(0, 0),color= (255, 0, 0))
                        projectile.kill()


                      # função que rebate projeteis enquanto tiver pulando
                      #  projectile.kill()
                      #  Spark(projectile.rect.center,[self.all_sprites])
                      #  Projectile(projectile.rect.center,(-1*projectile.direction),groups=[ self.projectiles],projectile.type,self.projectiles,side='player_projectile')
                        
    def next_level(self):
        self.level_number += 1
        self.player.experience += level_data[self.level_number]['experience']
        player_state = self.player.save_state()
        
        self.__init__(self.screen, self.level_number,player_state)


    def prevent_stacking(self):
        all_characters = [self.player] + list(self.enemies) + [self.Ally]
        for i, char1 in enumerate(all_characters):
            for char2 in all_characters[i + 1:]:
                if pygame.sprite.collide_rect(char1, char2):
                    # Calculate the vector separating the two sprites
                    separation_vector = pygame.math.Vector2(char1.rect.center) - pygame.math.Vector2(char2.rect.center)
                    if separation_vector.length() != 0:
                        separation_vector.normalize_ip()
                    else:
                        separation_vector = pygame.math.Vector2(1, 0)
                    
                    # Calculate the overlap
                    overlap = (char1.rect.width / 2 + char2.rect.width / 2) - separation_vector.length()

                    # Push the characters apart
                    if self.player.is_jumping:
                        return
                    else:
                        char1.rect.center += separation_vector * 2#(overlap / 2)//2
                        char2.rect.center -= separation_vector * 2#(overlap / 2)//2

    def place_grass(self):
        grass_probability = 0.1
        tile_size = 32

        empty_positions = self.map_controller.find_elements_of_type('empty')
        
        for x, y in empty_positions:
            if random.random() < grass_probability:
                density = random.randint(2, 5)
                self.grass_manager.place_tile((x, y), density)
                self.map_controller.add_element(x, y, 'grass')
    def reset(self):
        self.player.hp = self.player.max_hp
        self.player.is_dying = False
        self.player.rect.center = self.player_pos  # You'll need to store the initial position in __init__
        self.player.direction = pygame.math.Vector2()
        self.player.last_attack_time = 0
        self.player.invincible = False
    def spawn_blood(self, pos, amount):
        for _ in range(min(amount, 5)):  # Limit to a maximum of 5 particles
            angle = random.uniform(0, 360)
            speed = random.uniform(50, 100)
            velocity = pygame.math.Vector2(speed, 0).rotate(angle)
            BloodParticle(pos, [self.all_sprites, self.tile_top_sprites], velocity)
    
    def run(self, screen):
        dt = self.clock.tick(60) / 1000
        self.weather_controller.update(dt)

        # Update grass with wind information and player position
        #wind_vector = self.weather_controller.get_wind_vector()

        
        # Atualizar todos os sprites
        
        for sprite in self.all_sprites:
            if isinstance(sprite, Enemy):
                sprite.update(dt, self.player, self.all_sprites, self.tiles, screen)
                sprite.borderless(32, self.grid_width, self.grid_height)
            elif isinstance(sprite, Ally):
                sprite.update(dt, self.all_sprites, self.tiles, screen)
                sprite.borderless(32, self.grid_width, self.grid_height)
            else:
                sprite.update(dt)

        # Atualizar projéteis
        for projectile in self.projectiles:
            projectile.update(dt)

        self.update_enemy_count()
        self.camera.update(self.player)
        self.check_collisions()
        self.player.borderless(32, self.grid_width, self.grid_height)
        self.prevent_stacking()
        # Verificar colisão do player com os sprites de overlay
        overlay_collision = pygame.sprite.spritecollideany(self.player, self.overlay_sprites)
        overlay_alpha = 150 if overlay_collision else 255
        for sprite in self.overlay_sprites:
            sprite.image.set_alpha(overlay_alpha)

        # Draw the background and tiles
        screen.fill((0, 0, 0))
 # Desenhar todos os sprites, exceto o jogador e os overlay sprites
        for sprite in self.all_sprites:
            if sprite != self.player and sprite not in self.overlay_sprites:
                screen.blit(sprite.image, self.camera.apply(sprite))

        # Draw snow accumulation
        camera_offset = self.camera.apply(pygame.Rect(0, 0, 0, 0)).topleft
        self.weather_controller.draw_snow_accumulation(screen, camera_offset)

        # Draw the tile_top sprites (like bridges)
        for sprite in self.tile_top_sprites:
            screen.blit(sprite.image, self.camera.apply(sprite))

      
        for ally in self.ally:  # Adicionar esta linha para desenhar os aliados
            self.screen.blit(ally.image, self.camera.apply(ally))
        for enemy in self.enemies:
            self.screen.blit(enemy.image, self.camera.apply(enemy))

        # Desenhar o jogador
        self.player.update(dt)
        screen.blit(self.player.image, self.camera.apply(self.player))
        for enemy in self.enemies:
            screen.blit(enemy.image, self.camera.apply(enemy))
            enemy.draw_health_bar(screen)
            enemy.floating_texts.draw(screen)

        # Desenhar projéteis
        for projectile in self.projectiles:
            screen.blit(projectile.image, self.camera.apply(projectile))

        # Desenhar os sprites de overlay
        for sprite in self.overlay_sprites:
            screen.blit(sprite.image, self.camera.apply(sprite))
                # Desenhar os sprites superiores
        for sprite in self.top_sprites:
            screen.blit(sprite.image, self.camera.apply(sprite))
            
        self.weather_particles.draw(screen)
        self.weather_particles.update(dt)
        # Desenhar barras do jogador

        self.Ally.draw(screen)

        # Desenhar os textos flutuantes do jogador
        self.player.floating_texts.draw(screen)
        # Draw the night surface last
        self.update_night_surface(dt)
        screen.blit(self.night_surface, (0, 0))

        self.player.hp_bar.draw(screen)
        self.player.mana_bar.draw(screen)
        self.player.charge_bar.draw(screen)

        # Desenhar a interface do usuário
        screen.blit(self.ui_image, (0, 0))
        self.player.draw_inventory_slots(screen)
        self.draw_enemy_counter(screen)
        self.draw_level(screen)
        self.map_controller.draw_map(screen)

        

        pygame.display.flip()
