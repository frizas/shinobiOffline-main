import pygame
import random
import math

class GrassManager:
    def __init__(self, grass_path='images/map', tile_size=32, max_unique=10):
        self.grass_images = self.load_grass_images(grass_path)
        if not self.grass_images:
            raise ValueError("No grass images found in the specified path")
        self.tile_size = tile_size
        self.grass_tiles = {}
        self.wind_force = pygame.math.Vector2(0, 0)
        self.player_pos = pygame.math.Vector2(0, 0)

    def load_grass_images(self, path):
        images = []
        img_path = f'{path}/grass.png'
        try:
            img = pygame.image.load(img_path).convert_alpha()
            images.append(img)
        except pygame.error as e:
            print(f"Error loading image {img_path}: {e}")
        return images

    def place_tile(self, location, density):
        if tuple(location) not in self.grass_tiles:
            self.grass_tiles[tuple(location)] = GrassTile(self.tile_size, location, density, self.grass_images, self)
        print(f"Placed grass at {location} with density {density}")  # Debug print

    def update_wind(self, wind_vector):
        self.wind_force = wind_vector * 0.2

    def update_player_position(self, player_pos):
        self.player_pos = pygame.math.Vector2(player_pos)

    def apply_force(self, location, radius, dropoff):
        for tile_location, tile in self.grass_tiles.items():
            tile_center = pygame.math.Vector2(tile_location) * self.tile_size + pygame.math.Vector2(self.tile_size // 2, self.tile_size // 2)
            distance_to_player = (tile_center - self.player_pos).length()
            wind_factor = min(1.0, distance_to_player / 500)

            if (tile_center - pygame.math.Vector2(location)).length_squared() < (radius + dropoff) ** 2:
                tile.apply_force(location, radius, dropoff)

            tile.apply_wind(self.wind_force * wind_factor)

    def update_render(self, screen, dt, camera):
        for tile in self.grass_tiles.values():
            tile.render(screen, dt, camera)
        print(f"Rendering {len(self.grass_tiles)} grass tiles")  # Debug print

class GrassTile:
    def __init__(self, tile_size, location, density, grass_images, manager):
        self.manager = manager
        self.location = location
        self.blades = [GrassBlade(random.random() * tile_size, random.random() * tile_size / 2 + tile_size / 2, 
                                  random.choice(grass_images)) for _ in range(density)]

    def apply_force(self, force_point, force_radius, force_dropoff):
        for blade in self.blades:
            blade.apply_force(force_point, force_radius, force_dropoff, self.location)

    def apply_wind(self, wind_force):
        for blade in self.blades:
            blade.apply_wind(wind_force)

    def render(self, screen, dt, camera):
        for blade in self.blades:
            blade.render(screen, dt, camera, self.location, self.manager.tile_size)

class GrassBlade:
    def __init__(self, x, y, image):
        self.pos = pygame.math.Vector2(x, y)
        self.original_image = image
        self.image = image.copy()
        self.rotation = 0
        self.target_rotation = 0
        self.max_rotation = 25
        self.wind_factor = random.uniform(0.5, 1.5)
        self.max_wind_rotation = 11

    def apply_force(self, force_point, force_radius, force_dropoff, tile_location):
        blade_pos = self.pos + pygame.math.Vector2(tile_location) * 32
        force_vector = blade_pos - pygame.math.Vector2(force_point)
        distance = force_vector.length()
        if distance < force_radius + force_dropoff:
            force = max(0, 1 - (distance - force_radius) / force_dropoff)
            angle = math.degrees(math.atan2(force_vector.y, force_vector.x))
            target_angle = angle + 180
            self.target_rotation = max(-self.max_rotation, min(self.max_rotation, target_angle * force * 0.8))

    def apply_wind(self, wind_force):
        wind_angle = math.degrees(math.atan2(wind_force.y, wind_force.x))
        wind_strength = wind_force.length() * self.wind_factor
        wind_rotation = wind_angle * wind_strength
        wind_rotation = max(-self.max_wind_rotation, min(self.max_wind_rotation, wind_rotation))
        self.target_rotation += wind_rotation

    def render(self, screen, dt, camera, tile_location, tile_size):
        if abs(self.target_rotation) < 0.1:
            self.target_rotation = 0
        else:
            self.target_rotation *= 0.95

        self.rotation = self.rotation * 0.9 + self.target_rotation * 0.1

        rotated_image = pygame.transform.rotate(self.original_image, self.rotation)
        
        toned_down_image = rotated_image.copy()
        toned_down_image.fill((200, 200, 200, 180), special_flags=pygame.BLEND_RGBA_MULT)
        
        pos = self.pos + pygame.math.Vector2(tile_location) * tile_size
        grass_rect = pygame.Rect(pos.x, pos.y, toned_down_image.get_width(), toned_down_image.get_height())
        screen_pos = camera.apply_rect(grass_rect)
        screen.blit(toned_down_image, (screen_pos.x - toned_down_image.get_width() // 2, screen_pos.y - toned_down_image.get_height()))
