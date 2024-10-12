import pygame
from settings import *
import random
from tile import Tile
import math
import numpy as np
# Remove the following line:
# from noise import pnoise2  # Perlin noise library

# Add this function to replace Perlin noise
def simple_noise(x, y):
    return random.uniform(0, 1)

def load_spritesheet(image_path, sprite_width, sprite_height, rows, columns):
    sheet = pygame.image.load(image_path).convert_alpha()
    sheet_width, sheet_height = sheet.get_size()
    sprites = []

    for row in range(rows):
        row_sprites = []
        for col in range(columns):
            rect = pygame.Rect(col * sprite_width, row * sprite_height, sprite_width, sprite_height)
            if rect.right <= sheet_width and rect.bottom <= sheet_height:
                sprite = sheet.subsurface(rect).copy()
                row_sprites.append(sprite)
        sprites.append(row_sprites)

    return sprites
def play_sound(effect_type):
    sound_path = sound_data.get(effect_type)
    if isinstance(sound_path, list):
        sound_path = random.choice(sound_path)
    sound = pygame.mixer.Sound(sound_path)
    sound.play()
import pygame

class MeleeEffect(pygame.sprite.Sprite):
    def __init__(self, pos, direction, groups, weapon_type):
        if not isinstance(groups, (list, tuple)):
            groups = [groups]
        super().__init__(groups)
        self.pos = pygame.math.Vector2(pos)
        self.direction = direction
        self.weapon_type = weapon_type

        if self.weapon_type == 'fist':
            self.sprites = load_spritesheet('images/effects/punch.png', 32, 32, 4, 8)
            self.image = self.sprites[0][0]  # Start with the first sprite
            self.rect = self.image.get_rect(center=pos)
            self.animation_time = 0.05
            self.total_frames = 4 * 8
        elif self.weapon_type == 'sword':
            self.sprites = load_spritesheet('images/effects/sword_slash.png', 64, 64, 1, 5)[0]
            self.image = self.sprites[0]
            angle = math.degrees(math.atan2(-self.direction.y, self.direction.x))
            self.image = pygame.transform.rotate(self.image, angle)
            self.rect = self.image.get_rect(center=pos)
            self.animation_time = 0.05
            self.total_frames = 5

        self.current_sprite = 0
        self.current_time = 0
        self.speed = 300  # Pixels per second

    def update(self, dt):
        self.current_time += dt
        if self.current_time >= self.animation_time:
            self.current_time = 0
            self.current_sprite += 1
            if self.current_sprite >= self.total_frames:
                self.kill()
            else:
                if self.weapon_type == 'fist':
                    row = self.current_sprite // 8
                    col = self.current_sprite % 8
                    self.image = self.sprites[row][col]
                elif self.weapon_type == 'sword':
                    self.image = self.sprites[self.current_sprite]
                    angle = math.degrees(math.atan2(-self.direction.y, self.direction.x))
                    self.image = pygame.transform.rotate(self.image, angle)

        if self.weapon_type == 'sword':
            movement = self.direction * self.speed * dt
            self.pos += movement
            self.rect.center = self.pos
class BloodParticle(pygame.sprite.Sprite):
    def __init__(self, pos, groups, velocity=None):
        super().__init__(groups)
        self.radius = 3  # Start with a small radius
        self.image = pygame.Surface((3, 3), pygame.SRCALPHA)
        pygame.draw.circle(self.image, (200, 0, 0), (1.5, 1.5), self.radius)
        self.rect = self.image.get_rect(center=pos)
        self.pos = pygame.math.Vector2(pos)
        self.velocity = velocity or pygame.math.Vector2(random.uniform(-1, 1), random.uniform(-2, 0))
        self.gravity = pygame.math.Vector2(0.5, 0.5)  # 45-degree fall
        self.alpha = 255
        self.fade_speed = random.uniform(0.5, 1)
        self.stopped = False
        self.stop_time = random.uniform(0.2, 0.5)  # Time before stopping
        self.time_alive = 0
        self.grow_speed = random.uniform(0.5, 1)
        self.max_radius = random.uniform(3, 5)

    def update(self, dt):
        self.time_alive += dt
        if not self.stopped:
            self.velocity += self.gravity * dt
            self.pos += self.velocity * dt
            self.rect.center = (round(self.pos.x), round(self.pos.y))
            
            if self.time_alive >= self.stop_time:
                self.stopped = True
        else:
            # Grow the particle
            if self.radius < self.max_radius:
                self.radius += self.grow_speed * dt
                self.redraw()
            
            # Start fading after growing
            if self.radius >= self.max_radius:
                self.alpha -= self.fade_speed
                if self.alpha <= 0:
                    self.kill()
                else:
                    self.image.set_alpha(int(self.alpha))

    def redraw(self):
        size = math.ceil(self.radius * 2)
        self.image = pygame.Surface((size, size), pygame.SRCALPHA)
        pygame.draw.circle(self.image, (200, 0, 0), (size // 2, size // 2), self.radius)
        self.rect = self.image.get_rect(center=self.rect.center)

class RainParticle(pygame.sprite.Sprite):
    def __init__(self, pos, groups, screen_width, screen_height, lifespan=2000, wind_direction=pygame.math.Vector2(0, 0), wind_speed=0):
        super().__init__(groups)
        self.image = pygame.Surface((2, 2), pygame.SRCALPHA)
        self.image.fill((80, 100, 200, 150))
        self.rect = self.image.get_rect(center=pos)
        self.pos = pygame.math.Vector2(pos)
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.lifespan = lifespan
        self.birth_time = pygame.time.get_ticks()
        self.wind_direction = wind_direction
        self.wind_speed = wind_speed
        self.fall_speed = random.randint(200, 300)
        self.diagonal_speed = math.sqrt(2) * self.fall_speed  # 45-degree angle speed
        self.trail_timer = 0
        self.trail_interval = 0.05  # Create a trail particle every 0.05 seconds

    def update(self, dt):
        if pygame.time.get_ticks() - self.birth_time > self.lifespan:
            self.kill()
        # Move diagonally down and to the right
        self.pos.x += self.diagonal_speed * dt + self.wind_direction.x * self.wind_speed * dt
        self.pos.y += self.diagonal_speed * dt + self.wind_direction.y * self.wind_speed * dt
        self.rect.center = (round(self.pos.x), round(self.pos.y))

        # Create trail
        self.trail_timer += dt
        if self.trail_timer >= self.trail_interval:
            self.trail_timer = 0
            ParticleTrail(self.rect.center, self.groups(), (80, 100, 200), initial_size=3, lifespan=200)

    def is_on_screen(self):
        return 0 <= self.rect.top < self.screen_height and 0 <= self.rect.left < self.screen_width

class Particle2(pygame.sprite.Sprite):
    def __init__(self, pos, groups, color, screen_width, screen_height, initial_size=2, lifespan=3000, wind_direction=pygame.math.Vector2(0, 0), wind_speed=0):
        super().__init__(groups)
        self.image = pygame.Surface((initial_size, initial_size), pygame.SRCALPHA)
        self.image.fill(color)
        self.rect = self.image.get_rect(center=pos)
        self.pos = pygame.math.Vector2(pos)
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.lifespan = lifespan
        self.birth_time = pygame.time.get_ticks()
        self.wind_direction = wind_direction
        self.wind_speed = wind_speed
        self.fall_speed = random.uniform(30, 50)
        self.base_direction = pygame.math.Vector2(1, 1).normalize()

    def update(self, dt):
        if pygame.time.get_ticks() - self.birth_time > self.lifespan:
            self.reset_position()
        
        movement = (self.base_direction * self.fall_speed + self.wind_direction * self.wind_speed) * dt
        self.pos += movement
        self.rect.center = (round(self.pos.x), round(self.pos.y))

    def reset_position(self):
        if random.choice([True, False]):  # 50% chance for top or left
            self.pos.x = random.randint(-50, self.screen_width)
            self.pos.y = random.randint(-50, 0)
        else:
            self.pos.x = random.randint(-50, 0)
            self.pos.y = random.randint(-50, self.screen_height)
        self.birth_time = pygame.time.get_ticks()

    def is_on_screen(self):
        return -50 <= self.rect.top < self.screen_height + 50 and -50 <= self.rect.left < self.screen_width + 50



class Spark(pygame.sprite.Sprite):
    def __init__(self, pos, groups):
        if not isinstance(groups, (list, tuple)):
            groups = [groups]
        super().__init__(groups)
        self.sprites = load_spritesheet('images/effects/spark.png', 32, 32, 1, 4)[0]  # Ajusta para obter a primeira linha de sprites
        self.current_sprite = 0
        self.image = self.sprites[self.current_sprite]
        self.rect = self.image.get_rect(center=pos)
        self.animation_time = 0.1
        self.current_time = 0
        

    def update(self, dt):
        self.current_time += dt
        if self.current_time >= self.animation_time:
            self.current_time = 0
            self.current_sprite = (self.current_sprite + 1) % len(self.sprites)
            self.image = self.sprites[self.current_sprite]
            if self.current_sprite == len(self.sprites) - 1:
                self.kill()

class Puff(pygame.sprite.Sprite):
    def __init__(self, pos, groups):
        if not isinstance(groups, (list, tuple)):
            groups = [groups]
        super().__init__(groups)
        self.sprites = load_spritesheet('images/effects/puff.png', 64, 64, 1, 9)[0]  # Ajusta para obter a primeira linha de sprites
        self.current_sprite = 0
        self.image = self.sprites[self.current_sprite]
        
        if isinstance(pos, tuple) and len(pos) == 2:
            self.rect = self.image.get_rect(center=pos)
        else:
            raise ValueError("Position must be a tuple with 2 elements (x, y).")
        
        self.animation_time = 0.1
        self.current_time = 0

    def update(self, dt):
        self.current_time += dt
        if self.current_time >= self.animation_time:
            self.current_time = 0
            self.current_sprite = (self.current_sprite + 1) % len(self.sprites)
            self.image = self.sprites[self.current_sprite]
            if self.current_sprite == len(self.sprites) - 1:
                self.kill()
class Kawarimi(pygame.sprite.Sprite):
    def __init__(self, pos, groups, all_sprites, tiles):
        super().__init__(groups)
        self.sprites = load_spritesheet('images/effects/kawarimi.png', 64, 64, 1, 11)[0]  # Ajusta para obter a primeira linha de sprites
        self.current_sprite = 0
        self.image = self.sprites[self.current_sprite]
        self.pos = pos
        
        if isinstance(pos, tuple) and len(pos) == 2:
            self.rect = self.image.get_rect(center=pos)
        else:
            raise ValueError("Position must be a tuple with 2 elements (x, y).")
        
        self.animation_time = 0.1
        self.current_time = 0
        self.all_sprites = all_sprites  # Referência para all_sprites
        self.tiles = tiles  # Referência para tiles

    def update(self, dt):
        self.current_time += dt
        if self.current_time >= self.animation_time:
            self.current_time = 0
            self.current_sprite = (self.current_sprite + 1) % len(self.sprites)
            self.image = self.sprites[self.current_sprite]
            if self.current_sprite == len(self.sprites) - 1:
                new_pos = (self.pos[0] + 32, self.pos[1] + 32)
                Tile('images/effects/kawarimi_remain.png', new_pos, [self.all_sprites, self.tiles])
                self.kill()



    
class BloodHit(pygame.sprite.Sprite):
    def __init__(self, pos, groups):
        super().__init__(groups)
        self.pos = pos
        self.groups = groups
        self.create_particles()

    def create_particles(self):
        for _ in range(20):  # Ajuste o número de partículas conforme necessário
            Particle(self.pos, self.groups, initial_size=8, lifespan=1000, color=(255, 0, 0))


class ElectricAura(pygame.sprite.Sprite):
    def __init__(self, player, groups):
        if not isinstance(groups, (list, tuple)):
            groups = [groups]
        super().__init__(groups)
        self.sprites = load_spritesheet('images/effects/electric_aura.png', 64, 64, 1, 11)[0]
        self.current_sprite = 0
        self.image = self.sprites[self.current_sprite]
        self.rect = self.image.get_rect(center=player.rect.center)
        self.current_time = 0
        self.animation_time = 0.1
        
        self.player = player
        self.groups = groups
       # play_sound('raikiri')
        

    def destroy(self):
        self.kill()

    def create_particles(self):
        # Cria um rastro de partículas amarelas
        #FireWork(self.rect.center, self.groups, initial_size=20, lifespan=1000, num_particles=40)
        
        if not isinstance(self.groups, (list, tuple)):
            groups = [self.groups]
        else:
            groups = self.groups
        ParticleTrail(self.rect.center, groups, color=(200, 200, 250), initial_size=10, lifespan=2000)                        
        

    def update(self, dt):
        self.current_time += dt

        if self.current_time >= self.animation_time:
            self.current_time = 0
            self.current_sprite = (self.current_sprite + 1) % len(self.sprites)
            self.image = self.sprites[self.current_sprite]
        self.rect.center = self.player.rect.center
        self.create_particles()
        


class Punch(pygame.sprite.Sprite):
    def __init__(self, pos, groups):
        if not isinstance(groups, (list, tuple)):
            groups = [groups]
        super().__init__(groups)
        self.sprites = load_spritesheet('images/effects/punch.png', 32, 32, 4, 8)
        self.current_sprite = 0
        self.image = self.sprites[0][0]  # Start with the first sprite
        self.rect = self.image.get_rect(center=pos)
        self.animation_time = 1  # Adjust this value to change animation speed
        self.current_time = 0
        self.total_frames = 4 * 8  # Total number of frames (4 rows * 8 columns)

    def update(self, dt):
        self.current_time += dt
        if self.current_time >= self.animation_time:
            self.current_time = 0
            self.current_sprite += 1
            if self.current_sprite >= self.total_frames:
                self.kill()
            else:
                row = self.current_sprite // 8
                col = self.current_sprite % 8
                self.image = self.sprites[row][col]

class Slash(pygame.sprite.Sprite):
    def __init__(self, pos, direction, groups, damage=10):
        if not isinstance(groups, (list, tuple)):
            groups = [groups]
        super().__init__(groups)
        self.current_time = 0

        self.sprites = load_spritesheet('images/effects/sword_slash.png', 64, 64, 1, 5)[0]  # Adjust size if needed
        self.current_sprite = 0
        self.image = self.sprites[self.current_sprite]
        
        # Calculate the angle
        angle = math.degrees(math.atan2(-direction.y, direction.x))
        self.image = pygame.transform.rotate(self.image, angle)
        
        self.rect = self.image.get_rect(center=pos)
        self.pos = pygame.math.Vector2(pos)
        self.direction = direction
        self.speed = 300  # Pixels per second
        self.damage = damage
        self.animation_time = 0.05  # Adjust as needed

    def update(self, dt):
        self.current_time += dt
        if self.current_time >= self.animation_time:
            self.current_time = 0
            self.current_sprite = (self.current_sprite + 1) % len(self.sprites)
            self.image = self.sprites[self.current_sprite]
            self.image = pygame.transform.rotate(self.image, math.degrees(math.atan2(-self.direction.y, self.direction.x)))

        movement = self.direction * self.speed * dt
        self.pos += movement
        self.rect.center = self.pos

        if self.current_sprite == len(self.sprites) - 1:
            self.kill()
            
class Explosion(pygame.sprite.Sprite):
    def __init__(self, pos, groups):
        if not isinstance(groups, (list, tuple)):
            groups = [groups]
        super().__init__(groups)
        self.sprites = load_spritesheet('images/effects/explosion.png', 96, 96, 1, 24)[0]  # Ajusta para obter a primeira linha de sprites
        self.current_sprite = 0
        self.image = self.sprites[self.current_sprite]
        self.rect = self.image.get_rect(center=pos)
        self.animation_time = 0.04
        self.current_time = 0

    def update(self, dt):
        self.current_time += dt
        if self.current_time >= self.animation_time:
            self.current_time = 0
            self.current_sprite = (self.current_sprite + 1) % len(self.sprites)
            self.image = self.sprites[self.current_sprite]
            if self.current_sprite == len(self.sprites) - 1:
                self.kill()


class Particle(pygame.sprite.Sprite):
    def __init__(self, pos, groups, color=(255, 255, 255), initial_size=10, lifespan=1000, wind_direction=pygame.math.Vector2(0, 0), wind_speed=0):
        if not isinstance(groups, (list, tuple)):
            groups = [groups]
        super().__init__(groups)
        self.initial_size = initial_size
        self.lifespan = lifespan
        self.start_time = pygame.time.get_ticks()
        self.image = pygame.Surface((initial_size, initial_size), pygame.SRCALPHA)
        self.image.fill(color)
        self.rect = self.image.get_rect(center=pos)
        self.alpha = 255  # Initial transparency
        self.color = color
        
        # Velocidade inicial aleatória para a explosão
        self.velocity = pygame.math.Vector2(random.uniform(-1, -3), random.uniform(-1, -3)) * 1

        self.gravity = pygame.math.Vector2(0.05, 0.05)  # Gravidade aplicada nas partículas
        self.wind_direction = wind_direction
        self.wind_speed = wind_speed
    


    def update(self, dt):
        # Calculate the elapsed time
        elapsed_time = pygame.time.get_ticks() - self.start_time

        # Update position with velocity and gravity
        self.velocity += self.gravity
        self.rect.x += self.wind_direction.x * self.wind_speed * dt + self.velocity.x
        self.rect.y += self.wind_direction.y * self.wind_speed * dt + self.velocity.y


        # Calculate the new size and alpha
        if elapsed_time < self.lifespan:
            size_factor = 1 - (elapsed_time / self.lifespan)
            new_size = max(1, int(self.initial_size * size_factor))
            self.alpha = int(255 * size_factor/size_factor)
            
            # Calculate the new color (interpolating from yellow to black)
            red =   self.color[0] * size_factor
            green = self.color[1] * size_factor
            blue =  self.color[2] * size_factor

            # Update the image size, color, and alpha
          
            self.image = pygame.Surface((new_size, new_size), pygame.SRCALPHA)
            pygame.draw.circle(self.image, (red, green, blue, self.alpha), (new_size // 2, new_size // 2), new_size // 2)
            self.rect = self.image.get_rect(center=self.rect.center)
        else:
            self.kill()

class FireSmoke(pygame.sprite.Sprite):
    def __init__(self, pos, groups, color, initial_size=7, lifespan=5000):
        super().__init__(groups)
        self.initial_size = initial_size
        self.lifespan = lifespan
        self.start_time = pygame.time.get_ticks()
        self.image = pygame.Surface((initial_size, initial_size), pygame.SRCALPHA)
        self.image.fill(color)
        self.rect = self.image.get_rect(center=pos)
        self.alpha = 200  # Initial transparency
        self.color = color
        
        # Velocidade inicial aleatória para a explosão
        self.velocity = pygame.math.Vector2(random.uniform(-3, -4), random.uniform(-3, -4))

    def update(self, dt):
        # Calculate the elapsed time
        elapsed_time = pygame.time.get_ticks() - self.start_time

        

        # Calculate the new size and alpha
        if elapsed_time < self.lifespan:
            size_factor = elapsed_time / self.lifespan
            new_size = int(self.initial_size * (1 + size_factor))
            self.alpha = int(200 * (1 - size_factor))
            
            # Calculate the new color (interpolating from the initial color to black)
            red = self.color[0] *   (1 - size_factor)
            green = self.color[1] * (1 - size_factor)
            blue = self.color[2] *  (1 - size_factor)
            # Update position with velocity and gravity
            self.rect.x += self.velocity.x* (1 + size_factor)*0.3
            self.rect.y += self.velocity.y* (1 + size_factor)*0.3

            # Update the image size, color, and alpha
            self.image = pygame.Surface((new_size, new_size), pygame.SRCALPHA)
            pygame.draw.circle(self.image, (red, green, blue, self.alpha), (new_size // 2, new_size // 2), new_size // 2)
            self.rect = self.image.get_rect(center=self.rect.center)
            
        else:
            self.kill()
class SmokeEmitter(pygame.sprite.Sprite):
    def __init__(self, pos, groups, color, initial_size=7, particle_lifespan=2000, emission_duration=10000, emission_interval=150):
        if not isinstance(groups, (list, tuple)):
            groups = [groups]
        super().__init__(groups)
        self.pos = pos
        self.groups = groups
        self.color = color
        self.initial_size = initial_size
        self.particle_lifespan = particle_lifespan
        self.emission_duration = emission_duration
        self.emission_interval = emission_interval
        self.start_time = pygame.time.get_ticks()
        self.last_emission_time = self.start_time
        self.image = pygame.Surface((initial_size, initial_size), pygame.SRCALPHA)
        self.rect = self.image.get_rect(center=pos)
    def update(self, dt):
        current_time = pygame.time.get_ticks()
        elapsed_time = current_time - self.start_time

        if elapsed_time < self.emission_duration:
            if current_time - self.last_emission_time >= self.emission_interval:
                FireSmoke(self.pos, self.groups, self.color, self.initial_size, self.particle_lifespan)
                self.last_emission_time = current_time
        else:
            self.kill()



class FireRemains(pygame.sprite.Sprite):
    def __init__(self, pos, groups, area_size=30, initial_size=3, lifespan=1000):
        if not isinstance(groups, (list, tuple)):
            groups = [groups]
        super().__init__(groups)
        self.pos = pos
        self.area_size = area_size
        self.initial_size = initial_size
        self.lifespan = lifespan
        self.start_time = pygame.time.get_ticks()
        self.color = random.choice([(255, 255, 0), (255, 100, 0), (255, 165, 0)])  # Amarelo, vermelho, laranja
        self.image = pygame.Surface((initial_size, initial_size), pygame.SRCALPHA)
        self.image.fill(self.color)
        self.rect = self.image.get_rect(center=pos)

        self.alpha = 200  # Initial transparency

    def update(self, dt):
        elapsed_time = pygame.time.get_ticks() - self.start_time

        if elapsed_time < self.lifespan:
            alpha_factor = 1 - (elapsed_time / self.lifespan)
            self.alpha = int(200 * alpha_factor)
            self.rect.x -= 1
            self.rect.y -= 1
            self.image.fill((*self.color, self.alpha))
        else:
            self.kill()


class FireWork(pygame.sprite.Sprite):
    def __init__(self, pos, groups, num_particles=30, initial_size=5, lifespan=2000):
        if not isinstance(groups, (list, tuple)):
            groups = [groups]
        super().__init__(groups)
        self.pos = pos
        self.num_particles = num_particles
        self.initial_size = initial_size
        self.lifespan = lifespan
        self.start_time = pygame.time.get_ticks()
        self.particles = []
        self.image = pygame.Surface((initial_size, initial_size), pygame.SRCALPHA)
        self.rect = self.image.get_rect(center=pos)
        for _ in range(num_particles):
            velocity = pygame.math.Vector2(random.uniform(-1, 1), random.uniform(-1, 1)) * 3
            particle = {
                'image': pygame.Surface((initial_size, initial_size), pygame.SRCALPHA),
                'rect': pygame.Surface((initial_size, initial_size), pygame.SRCALPHA).get_rect(center=pos),
                'velocity': velocity,
                'color': (255, 255, 255),
                'alpha': 200
            }
            particle['image'].fill(particle['color'])
            self.particles.append(particle)

    def update(self, dt):
        elapsed_time = pygame.time.get_ticks() - self.start_time

        for particle in self.particles:
            particle['rect'].x += particle['velocity'].x
            particle['rect'].y += particle['velocity'].y
            particle['rect'].x += 0.05
            particle['rect'].y += 0.05

            if elapsed_time < self.lifespan:
                alpha_factor = 1 - (elapsed_time / self.lifespan)
                particle['alpha'] = int(255 * alpha_factor)
                particle['image'].fill((*particle['color'], particle['alpha']))
            else:
                self.particles.remove(particle)

        if not self.particles:
            self.kill()

    def draw(self, screen):
        for particle in self.particles:
            screen.blit(particle['image'], particle['rect'])

class FireEmitter(pygame.sprite.Sprite):
    def __init__(self, pos, groups, area_size=35, emit_duration=5000, emit_interval=200):
        if not isinstance(groups, (list, tuple)):
            groups = [groups]
        super().__init__(groups)
        self.pos = pos
        self.groups = groups
        self.area_size = area_size
        self.emit_duration = emit_duration
        self.emit_interval = emit_interval
        self.start_time = pygame.time.get_ticks()
        self.last_emit_time = 0
        self.colors = [(255, 255, 0), (255, 100, 0), (255, 165, 0)]  # Amarelo, vermelho, laranja
        self.image = pygame.Surface((3, 3), pygame.SRCALPHA)
        self.rect = self.image.get_rect(center=pos)
    def update(self, dt):
        current_time = pygame.time.get_ticks()
        elapsed_time = current_time - self.start_time

        if elapsed_time < self.emit_duration:
            if current_time - self.last_emit_time > self.emit_interval:
                self.last_emit_time = current_time
                self.emit_particles()
        else:
            self.kill()

    def emit_particles(self):
        for _ in range(15):  # Emitir 5 partículas de cada vez
            color = random.choice(self.colors)
            offset_x = random.randint(-self.area_size // 2, self.area_size // 2)
            offset_y = random.randint(-self.area_size // 2, self.area_size // 2)
            pos = (self.pos[0] + offset_x, self.pos[1] + offset_y)
            if not isinstance(self.groups, (list, tuple)):
                groups = [self.groups]
            else:
                groups = self.groups
            particle = FireRemains(pos, groups, color)

class Bonfire(pygame.sprite.Sprite):
    def __init__(self, pos, groups):
        super().__init__(groups)
        self.sprites = load_spritesheet('images/effects/bonfire.png', 32, 32, 1, 4)[0]  # Ajuste o caminho da imagem e o tamanho dos sprites
        self.current_sprite = 0
        self.image = self.sprites[self.current_sprite]
        self.rect = self.image.get_rect(center=pos)
        self.animation_time = 0.2
        self.current_time = 0

    def update(self, dt):
        self.current_time += dt
        if self.current_time >= self.animation_time:
            self.current_time = 0
            self.current_sprite = (self.current_sprite + 1) % len(self.sprites)
            self.image = self.sprites[self.current_sprite]
            
            
class ParticleTrail(pygame.sprite.Sprite):
    def __init__(self, pos, groups, color, initial_size=6, lifespan=700):
        super().__init__(groups)
        self.initial_size = initial_size
        self.lifespan = lifespan
        self.start_time = pygame.time.get_ticks()
        self.image = pygame.Surface((initial_size, initial_size), pygame.SRCALPHA)
        self.image.fill(color)
        self.rect = self.image.get_rect(center=pos)
        self.alpha = 255
        self.color = color

    def update(self, dt):
        elapsed_time = pygame.time.get_ticks() - self.start_time
        size_factor = 1 - (elapsed_time / self.lifespan)
        new_size = max(1, int(self.initial_size * size_factor))
        self.alpha = int(255 * size_factor)
        
        if elapsed_time < self.lifespan:
            self.image = pygame.Surface((new_size, new_size), pygame.SRCALPHA)
            self.image.set_alpha(self.alpha)
            pygame.draw.circle(self.image, self.color, (new_size // 2, new_size // 2), new_size // 2)
            self.rect = self.image.get_rect(center=self.rect.center)
        else:
            self.kill()
class WaterParticle(pygame.sprite.Sprite):
    def __init__(self, pos, groups, initial_size=3, lifespan=1000):
        super().__init__(groups)
        self.initial_size = initial_size
        self.lifespan = lifespan
        self.start_time = pygame.time.get_ticks()
        self.image = pygame.Surface((initial_size, initial_size), pygame.SRCALPHA)
        # Randomly choose a shade of blue
        # Define the shades of blue
        self.blue_shades = [(100, 100, 250), (50, 100, 250), (50, 150, 250), (50, 180, 250)]
        # Randomly choose a starting color index
        self.color_index = random.randint(0, len(self.blue_shades) - 1)
        self.image.fill(self.color_index)
        self.rect = self.image.get_rect(center=(pos[0] + random.uniform(-1, 5), pos[1] + random.uniform(-15, 15)))
        self.alpha = 255  # Initial transparency
        self.gravity = 0  #pygame.math.Vector2(0, 0.1)
        self.velocity = pygame.math.Vector2(0, random.uniform(1, 2))

    def update(self, dt):
        # Calculate the elapsed time
        elapsed_time = pygame.time.get_ticks() - self.start_time

        # Update position with velocity and gravity
        self.rect.y += self.velocity.y
        
        

        # Calculate the new size and alpha
        if elapsed_time < self.lifespan:
            size_factor = 1 - (elapsed_time / self.lifespan)
            new_size = max(1, int(self.initial_size * size_factor))
            self.alpha = int(200 )
            
            # Update the color index based on elapsed time
            color_progress = int(elapsed_time / (self.lifespan / len(self.blue_shades)))
            current_color = self.blue_shades[(self.color_index + color_progress) % len(self.blue_shades)]

            # Update the image size, color, and alpha
           # self.image = pygame.Surface((new_size, new_size), pygame.SRCALPHA)
            self.image.fill((*current_color, self.alpha))
            self.rect = self.image.get_rect(center=self.rect.center)

        else:
            self.kill()
class WaterEmitter2:
    def __init__(self, pos, direction, groups, speed=1, particle_count=10, lifespan=1000):
        self.pos = pos
        self.direction = direction
        self.groups = groups
        self.speed = speed
        self.particle_count = particle_count
        self.lifespan = lifespan
        self.emit_particles()

    def emit_particles(self):
        for _ in range(self.particle_count):
            WaterProjectile(self.pos, self.direction, self.groups, self.speed, self.lifespan)

class WaterProjectile(pygame.sprite.Sprite):
    def __init__(self, pos, direction, groups, speed=1, lifespan=1000):
        super().__init__(groups)
        self.image = pygame.Surface((7,8), pygame.SRCALPHA)
        self.image.fill((30, 100, 255))  # Azul para a gota de água
        self.rect = self.image.get_rect(center=pos)
        self.direction = direction
        self.speed = speed
        self.lifespan = lifespan
        self.start_time = pygame.time.get_ticks()

    def update(self, dt):
        elapsed_time = pygame.time.get_ticks() - self.start_time
        if elapsed_time > self.lifespan:
            self.kill()
        else:
            self.rect.x += self.direction.x * self.speed * dt
            self.rect.y += self.direction.y * self.speed * dt

class WaterEmitter(pygame.sprite.Sprite):
    def __init__(self, pos, groups, initial_size=4, emission_interval=800):
        super().__init__(groups)
        self.pos = pos
        self.groups = groups
        self.emission_interval = emission_interval
        self.last_emit_time = pygame.time.get_ticks()
        self.image = pygame.Surface((initial_size, initial_size), pygame.SRCALPHA)
        self.rect = self.image.get_rect(center=pos)
        
    def update(self, dt):
        current_time = pygame.time.get_ticks()
        if current_time - self.last_emit_time >= self.emission_interval:
            self.last_emit_time = current_time
            WaterParticle(self.rect.center, self.groups)

class WaterLoad(pygame.sprite.Sprite):
    def __init__(self, pos, direction, target_pos, groups, speed=1, lifespan=1000):
        super().__init__(groups)
        self.image = pygame.Surface((5, 5), pygame.SRCALPHA)
        self.image.fill((0, 100, 255))  # Azul para a gota de água
        self.rect = self.image.get_rect(center=pos)
        self.direction = direction
        self.target_pos = target_pos
        self.speed = speed
        self.lifespan = lifespan
        self.start_time = pygame.time.get_ticks()

    def update(self, dt):
        elapsed_time = pygame.time.get_ticks() - self.start_time
        if elapsed_time > self.lifespan:
            self.kill()
        else:
            self.rect.x += self.direction.x * self.speed * dt
            self.rect.y += self.direction.y * self.speed * dt

            if pygame.math.Vector2(self.rect.center).distance_to(self.target_pos) < 5:
                self.kill()
                # Adicionar ao acúmulo de água do jogador
                self.groups[0].player.water_mass += 1
                self.groups[0].player.water_particles.remove(self)

class InsectSwarm(pygame.sprite.Sprite):
    def __init__(self, pos, user, target, groups, level, speed=200, lifespan=6000):
        super().__init__(groups)
        self.image = pygame.Surface((2, 2))
        self.image.fill((5, 5, 0))                        # cor
        self.rect = self.image.get_rect(center=pos)
        self.user = user
        self.target = target
        self.speed = speed
        self.level = level
        self.angle = random.uniform(0, 360)
        self.radius = random.uniform(20, 50)
        self.lifespan = lifespan

        direction_vector = pygame.math.Vector2(self.target.rect.center) - pygame.math.Vector2(self.rect.center)
        if direction_vector.length() != 0:
            self.direction = direction_vector.normalize()
        else:
            self.direction = pygame.math.Vector2(0, 0)

        self.start_time = pygame.time.get_ticks()
        self.moving_to_target = True
        self.circling_target = False
        self.returning_to_user = False

    def update(self, dt):
        elapsed_time = pygame.time.get_ticks() - self.start_time
        if elapsed_time > self.lifespan:
            self.kill()
            return

        if self.moving_to_target:
            self.move_towards_target(dt)
        elif self.circling_target:
            self.circle_around_target(dt)
        elif self.returning_to_user:
            self.move_towards_user(dt)

        if pygame.sprite.collide_rect(self, self.target) and self.moving_to_target:
            self.moving_to_target = False
            self.circling_target = True
            self.start_time = pygame.time.get_ticks()  # Reset the timer for circling
        elif pygame.sprite.collide_rect(self, self.user) and self.returning_to_user:
            self.kill()

    def move_towards_target(self, dt):
        target_pos = self.target.rect.center
        direction = pygame.math.Vector2(target_pos) - pygame.math.Vector2(self.rect.center)
        distance = direction.length()

        if distance <= self.speed * dt:
            self.moving_to_target = False
            self.circling_target = True
            self.start_time = pygame.time.get_ticks()  # Reset the timer for circling
        else:
            direction.normalize_ip()
            tremor = pygame.math.Vector2(random.uniform(-1, 1), random.uniform(-1, 1)) * 3  # Add tremor effect
            self.rect.x += (direction.x * self.speed + tremor.x) * dt
            self.rect.y += (direction.y * self.speed + tremor.y) * dt

    def circle_around_target(self, dt):
        self.angle += 100 * dt
        target_pos = self.target.rect.center
        offset_x = self.radius * math.cos(math.radians(self.angle))
        offset_y = self.radius * math.sin(math.radians(self.angle))
        self.rect.centerx = target_pos[0] + offset_x
        self.rect.centery = target_pos[1] + offset_y

        # Check if enough time has passed to start returning to user
        if pygame.time.get_ticks() - self.start_time > 3000:  # Circle for 3 seconds
            self.circling_target = False
            self.returning_to_user = True

    def move_towards_user(self, dt):
        user_pos = self.user.rect.center
        direction = pygame.math.Vector2(user_pos) - pygame.math.Vector2(self.rect.center)
        distance = direction.length()

        if distance <= self.speed * dt:
            self.kill()  # Reached the user
        else:
            direction.normalize_ip()
            self.rect.x += direction.x * self.speed * dt
            self.rect.y += direction.y * self.speed * dt
from pygame.locals import BLEND_RGB_ADD

class NinjutsuEffect(pygame.sprite.Sprite):
    def __init__(self, pos, groups, duration=1000):
        if not isinstance(groups, (list, tuple)):
            groups = [groups]
        super().__init__(groups)
        self.pos = pygame.math.Vector2(pos)
        self.groups = groups  # Store groups as a list
        self.start_time = pygame.time.get_ticks()
        self.duration = duration
        self.image = pygame.Surface((20, 20), pygame.SRCALPHA)
        self.rect = self.image.get_rect(center=pos)

    def update(self, dt):
        if pygame.time.get_ticks() - self.start_time > self.duration:
            self.kill()

class FireballEffect(NinjutsuEffect):
    def __init__(self, pos, groups, target_pos):
        super().__init__(pos, groups)
        self.image = pygame.Surface((20, 20), pygame.SRCALPHA)
        pygame.draw.circle(self.image, (255, 100, 0), (10, 10), 10)
        self.rect = self.image.get_rect(center=pos)
        self.direction = (pygame.math.Vector2(target_pos) - self.pos).normalize()
        self.speed = 300

    def update(self, dt):
        super().update(dt)
        self.pos += self.direction * self.speed * dt
        self.rect.center = self.pos
        Particle(self.rect.center, self.groups, color=(255, 100, 0), initial_size=5, lifespan=500)


class PhoenixFlowerEffect(NinjutsuEffect):
    def __init__(self, pos, groups):
        super().__init__(pos, groups)
        self.fireballs = []
        for _ in range(5):
            angle = random.uniform(0, 2 * math.pi)
            direction = pygame.math.Vector2(math.cos(angle), math.sin(angle))
            self.fireballs.append(FireballEffect(pos, groups, pos + direction * 100))
        self.image = pygame.Surface((1, 1), pygame.SRCALPHA)
        self.rect = self.image.get_rect(center=pos)

    def update(self, dt):
        super().update(dt)
        for fireball in self.fireballs:
            fireball.update(dt)

class WaterBulletEffect(NinjutsuEffect):
    def __init__(self, pos, groups, target_pos):
        super().__init__(pos, groups)
        self.image = pygame.Surface((15, 15), pygame.SRCALPHA)
        pygame.draw.circle(self.image, (0, 100, 255), (7, 7), 7)
        self.rect = self.image.get_rect(center=pos)
        self.direction = (pygame.math.Vector2(target_pos) - self.pos).normalize()
        self.speed = 250

    def update(self, dt):
        super().update(dt)
        self.pos += self.direction * self.speed * dt
        self.rect.center = self.pos
        Particle(self.rect.center, self.groups, color=(0, 100, 255), initial_size=3, lifespan=300)

class WaterDragonEffect(NinjutsuEffect):
    def __init__(self, pos, groups, target_pos):
        super().__init__(pos, groups, duration=2000)
        self.target_pos = pygame.math.Vector2(target_pos)
        self.control_points = [self.pos, self.pos + (self.target_pos - self.pos) * 0.5 + pygame.math.Vector2(random.uniform(-100, 100), random.uniform(-100, 100)), self.target_pos]
        self.t = 0
        self.image = pygame.Surface((20, 20), pygame.SRCALPHA)
        pygame.draw.circle(self.image, (0, 100, 255), (10, 10), 10)
        self.rect = self.image.get_rect(center=pos)
        self.particles = []

    def update(self, dt):
        super().update(dt)
        self.t = min(1, self.t + dt * 0.001)
        current_pos = self.bezier(self.t, self.control_points)
        self.rect.center = current_pos
        new_particle = Particle(current_pos, self.groups, color=(0, 100, 255), initial_size=10, lifespan=500)
        self.particles.append(new_particle)
        
        for particle in self.particles[:]:
            particle.update(dt)
            if particle.alpha <= 0:
                self.particles.remove(particle)

    def bezier(self, t, points):
        return (1-t)**2 * points[0] + 2*(1-t)*t * points[1] + t**2 * points[2]

class EarthWallEffect(NinjutsuEffect):
    def __init__(self, pos, groups):
        super().__init__(pos, groups, duration=5000)
        self.image = pygame.image.load('images/effects/earth_wall.png').convert_alpha()
        self.rect = self.image.get_rect(center=pos)
        
        # Create a collidable tile
        self.wall_tile = Tile('images/effects/earth_wall.png', pos, [groups[0]], collidable=True)
        
        # Add the wall tile to the projectile and particle collision groups
       

    def update(self, dt):
        super().update(dt)
        if pygame.time.get_ticks() - self.start_time > self.duration:
            self.wall_tile.kill()  # Remove the wall tile when the effect ends
class ChidoriEffect(NinjutsuEffect):
    def __init__(self, pos, groups):
        super().__init__(pos, groups, duration=1500)
        self.radius = 30
        self.image = pygame.Surface((60, 60), pygame.SRCALPHA)
        self.rect = self.image.get_rect(center=pos)

    def update(self, dt):
        super().update(dt)
        self.image.fill((0, 0, 0, 0))
        for _ in range(5):
            angle = random.uniform(0, 2 * math.pi)
            offset = pygame.math.Vector2(math.cos(angle), math.sin(angle)) * self.radius
            pygame.draw.circle(self.image, (200, 200, 255), (int(offset.x + 30), int(offset.y + 30)), 3)

class WindBladeEffect(NinjutsuEffect):
    def __init__(self, pos, groups, target_pos):
        if not isinstance(groups, (list, tuple)):
            groups = [groups]
        super().__init__(pos, groups)
        self.image = pygame.Surface((30, 10), pygame.SRCALPHA)
        pygame.draw.ellipse(self.image, (200, 200, 200), (0, 0, 30, 10))
        self.rect = self.image.get_rect(center=pos)
        self.direction = (pygame.math.Vector2(target_pos) - self.pos).normalize()
        self.speed = 400
        angle = math.atan2(self.direction.y, self.direction.x)
        self.image = pygame.transform.rotate(self.image, -math.degrees(angle))

    def update(self, dt):
        super().update(dt)
        self.pos += self.direction * self.speed * dt
        self.rect.center = self.pos
        Particle(self.rect.center, self.groups, color=(200, 200, 200), initial_size=2, lifespan=100)

# Add more effect classes for other ninjutsu as needed