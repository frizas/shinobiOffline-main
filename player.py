import pygame
from projectile import Projectile
from settings import *
from ui import *
from effects import *
import random
from enemy import Enemy
from ItemDrop import ItemDrop
from key_pressed_notifier import KeyPressedNotifier
from text_display import FloatingText
import time

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

def is_sprite_empty(sprite):

    for x in range(sprite.get_width()):
        for y in range(sprite.get_height()):
            if sprite.get_at((x, y)).a != 0:
                return False
    return True

    
class Player(pygame.sprite.Sprite):
    def __init__(self, pos, groups, collidable_tiles, projectile_group, level,state=None):
        super().__init__(groups)
        self.gold = 0

        self.level = level
        self.sprites = load_spritesheet('images/kakashi.png', 64, 64, 36, 4)

        self.current_sprite = 0
        self.image = self.sprites[0][self.current_sprite]
        self.rect = self.image.get_rect(topleft=pos)
        self.mask = pygame.mask.from_surface(self.image)
        self.current_time = 0
        self.action = 'idle_down'
        self.last_direction = 'down'
        self.collidable_tiles = collidable_tiles
        self.projectile_group = projectile_group
      ##               ##              ##              ##              ##                  ##
        self.speed = 60
        self.running_speed = 1.8*self.speed
        self.animation_time = 0.15
        self.max_hp = 60
        self.experience = 1
        self.hp = self.max_hp 
        self.hp_regeneration = 0.5
        self.max_mana = 250
        self.mana = self.max_mana
        self.attack_range = 350
        self.mana_regeneration = 0.5
        self.throw_speed = 1
        self.ninjutsu = 1
            ##              ##              ##              ##              ##              ##
        self.water_mass = 0
        self.water_particles = pygame.sprite.Group()
        self.charging_water_magic = False
        self.releasing_water_magic = False

        self.last_attack_time = 0
        self.last_attack = 0
        self.inventory = {
            'ranged_weapon': 'kunai',
            'melee_weapon': 'fist',
            'armor': None
            }
        if state:
            self.load_state(state)
        self.nivel = self.calculate_level()
        
        self.attack_charge_start = 0
        self.is_charging_attack = False
        self.is_performing_special_attack = False
        self.raikiri_duration = 1300
        self.raikiri_start_time = 0
        self.raikiri_target = None
        self.raikiri_moving = False  # Indica se o jogador está se movendo para o alvo
        self.raikiri_end_time = 0  # Tempo para terminar a aura elétrica após o ataque
        self.aura = None
        self.hp_bar = UIBar(3, 10, 100, 10, self.max_hp, (255, 0, 0))
        self.mana_bar = UIBar(3, 25, 100, 10, self.max_mana, (0, 0, 255))
        self.charge_bar = UIBar(3, 40, 100, 10, 2000, (255, 255, 0))
        

        # Criação dos slots de inventário
        slot_size = 32
        slot_margin = 1
        start_x = 0
        start_y = 54
        self.melee_slot = InventorySlot(start_x, start_y, slot_size, slot_size)
        self.ranged_slot = InventorySlot(start_x + slot_size + slot_margin, start_y, slot_size, slot_size)
        self.k_key_last_pressed = 0  # Armazena o tempo da última vez que a tecla 'K' foi pressionada
        self.k_key_cooldown = 200
        self.action_map = { 
            'down_walk':        0,   'up_walk':                  1,  'idle_down':              2,  'casting_spell_down': 3,
            'casting_spell_up': 4,   'sharingan_down':           5,  'casting_sharingan_down': 6,
            'run_down':         7,   'run_up':                   8,  'raikiri_down':           9,
            'raikiri_up':      10,   'walk_left':               11,  'walk_right':            12,
            'idle_right':      13,   'casting_spell_right':     14,  'casting_spell_left':    15,
            'sharingan_right': 16,   'casting_sharingan_right': 17,  'run_right':             18,
            'run_left':        19,   'raikiri_right':           20,  'raikiri_left':          21,
            'idle_left':       22,   'idle_up':                 23,  'attack_down':           24,
            'attack_up':       25,   'attack_left':             26,  'attack_right':          27,
            'jump_down':       28,   'jump_up':                 29,  'jump_right':            30,
            'jump_left':       31,   'kick_down':             32,  'kick_up':               33,
            'kick_right':      34,   'kick_left':             35,   
        }
        self.melee_skill = 20  # Habilidade de combate corpo a corpo
        self.defense_skill = 20  # Habilidade de defesa

        
        self.rect.width = self.rect.width // 2
        self.rect.height =  self.rect.height // 2

        self.jump_start_time = None
        self.last_jump = 0
        self.is_jumping = False
        self.jump_height = 1.3
        self.jump_speed = 1.4
        self.gravity = 1.3
        self.vertical_velocity = 0
        self.horizontal_velocity = 0

        self.is_knockedback = False
        self.knockback_start_time = 0
        self.knockback_duration = 50
        self.knockback_velocity = 20
        self.invincible = False
        self.invincible_start_time = 0
        self.invincible_duration = 900

        self.floating_texts = pygame.sprite.Group()
        self.is_attacking = False
        self.melee_cooldown = 500  # Cooldown time in milliseconds
        self.last_melee_time = 0
        self.attack_start_time = 0

        self.last_shuriken_message_time = 0
        self.shuriken_message_cooldown = 5  # 5 seconds cooldown

        KeyPressedNotifier.subscribe(self.on_keydown_event)
        self.reset_raikiri_state()
        self.raikiri_max_duration = 5000  # Maximum duration for Raikiri state (5 seconds)
        self.raikiri_animation_duration = 1000  # Duration of the initial Raikiri animation in milliseconds
        self.raikiri_animation_complete = False

    def reset_raikiri_state(self):
        self.is_performing_special_attack = False
        self.raikiri_target = None
        self.raikiri_moving = False
        self.invincible = False
        self.raikiri_animation_complete = False
        if self.aura:
            self.aura.destroy()
            self.aura = None
        self.action = f'idle_{self.last_direction}'

    def get_melee_animation(self):
        if self.inventory['melee_weapon'] == 'fist':
            action_type = random.choice(['attack', 'kick'])
        else:
            action_type = 'attack'
        
        return f'{action_type}_{self.last_direction}'
    def handle_melee_attack(self):
        current_time = pygame.time.get_ticks()
        if current_time - self.last_melee_time > self.melee_cooldown:
            self.last_melee_time = current_time
            self.perform_melee_attack()

    def perform_melee_attack(self):
        self.is_attacking = True
        self.attack_start_time = pygame.time.get_ticks()
        
        self.action = self.get_melee_animation()
        self.current_sprite = 0

        weapon = self.inventory['melee_weapon']
        if weapon == 'fist':
            self.punch_attack()
        elif weapon == 'sword':
            self.sword_attack()
        # Add more weapon types here if needed
    def reset(self):
        self.hp = self.max_hp
        self.is_dying = False
        self.rect.center = self.initial_position  # You'll need to store the initial position in __init__
        self.direction = pygame.math.Vector2()
        self.last_attack_time = 0
        self.jump_start_time = None
        self.last_jump = 0
        self.is_jumping = False
        self.jump_height = 1.3
        self.jump_speed = 1.4
        self.gravity = 1.3
        self.vertical_velocity = 0
        self.horizontal_velocity = 0
        self.is_knockedback = False
        self.knockback_start_time = 0
        self.knockback_duration = 50
        self.knockback_velocity = 20
        self.invincible = False
        self.invincible_start_time = 0
        self.invincible_duration = 900
        
    def punch_attack(self):
        damage = 10  # Base damage for punch
        attack_range = 50  # Close range for punch
        effect_type = 'punch'  # We'll keep the effect type as 'punch' for simplicity
        self.melee_attack_effect(damage, attack_range, effect_type)
    def sword_attack(self):
        damage = 20  # Base damage for sword
        attack_range = 70  # Slightly longer range for sword
        self.melee_attack_effect(damage, attack_range, 'slash')

    def melee_attack_effect(self, damage, attack_range, effect_type):
        direction = self.get_attack_direction()
        effect_pos = self.rect.center + direction * 20

        if effect_type == 'punch':
            weapon_type = 'fist'
        elif effect_type == 'slash':
            weapon_type = 'sword'
        else:
            weapon_type = 'fist'  # default

        MeleeEffect(effect_pos, direction, [self.level.all_sprites, self.level.top_sprites], weapon_type)

        self.check_melee_collisions(effect_pos, direction, damage, attack_range)
    def get_attack_direction(self):
        direction_map = {
            'up': pygame.math.Vector2(0, -1),
            'down': pygame.math.Vector2(0, 1),
            'left': pygame.math.Vector2(-1, 0),
            'right': pygame.math.Vector2(1, 0)
        }
        return direction_map.get(self.last_direction, pygame.math.Vector2(0, 1))

    def check_melee_collisions(self, attack_pos, direction, damage, attack_range):
        attack_rect = pygame.Rect(0, 0, attack_range * 2, attack_range * 2)
        attack_rect.center = attack_pos
        for enemy in self.level.enemies:
            if attack_rect.colliderect(enemy.rect):
                knockback_direction = pygame.math.Vector2(enemy.rect.center) - pygame.math.Vector2(self.rect.center)
                if knockback_direction.length() > 0:
                    knockback_direction.normalize_ip()
                    enemy.take_damage(damage, self.level.all_sprites, self.level.tiles, (255, 255, 255), knockback_direction)

    def perform_special_attack(self, charge_time):
        if charge_time < 1000:
            # Do nothing for short charge times
            pass
        elif charge_time < 2000:
            if self.mana > 10:
                self.medium_attack()
        else:
            if self.mana > 30:
                self.strong_attack()




   

    def calculate_level(self):
        level = 1
        self.max_hp =60
        self.max_mana=55
        self.speed  = 55
        self.attack_range = 350
        self.mana_regeneration = 5.5
        while True:
            level_xp = 50/3 * (level**3 - 6*level**2 + 17*level - 12)
            if self.experience  < level_xp:
                return level
            level += 1
            self.max_hp +=5
            self.max_mana +=5
            self.speed +=3
            self.attack_range +=5
            self.mana_regeneration += 0.1
            self.throw_speed += 0.1
            self.ninjutsu +=0.2

    def charge_water_magic(self):
        if not self.find_nearest_river_tile():
            return

        river_pos = self.find_nearest_river_tile()
        direction = pygame.math.Vector2(self.rect.center) - pygame.math.Vector2(river_pos)
        direction.normalize_ip()
        target_pos = (self.rect.centerx - 44, self.rect.top - 44)
        self.charging_water_magic = True
        
        WaterLoad(river_pos, direction, target_pos, [self.level.all_sprites, self.water_particles], speed=200, lifespan=2000)
        
        ParticleTrail(river_pos,[self.level.all_sprites],color=(100, 100, 255),initial_size=3,lifespan=2000)
       
    def find_nearest_river_tile(self):
        nearest_tile = None
        nearest_distance = float('inf')
        for tile in self.level.tiles:
            if hasattr(tile, 'image_path') and tile.image_path == 'images/map/river1.png':
                distance = pygame.math.Vector2(self.rect.center).distance_to(tile.rect.center)
                if distance < nearest_distance:
                    nearest_distance = distance
                    nearest_tile = tile.rect.center
        return nearest_tile

    def release_water_magic(self):
        if self.water_mass > 0:
            direction = pygame.math.Vector2(self.target.rect.center) - pygame.math.Vector2(self.rect.center)
            direction.normalize_ip()
            WaterEmitter(self.rect.center, direction, [self.level.all_sprites, self.level.projectiles], speed=300, particle_count=self.water_mass, lifespan=1500)
            


    def save_state(self):
        return {
            'experience': self.experience,
            'hp': self.hp,
            'max_hp': self.max_hp,
            'mana': self.mana,
            'max_mana': self.max_mana,
            'inventory': self.inventory,
            'gold': self.gold  # Add this line to include gold in the saved state
        }

    def load_state(self, state):
        if state:
            self.experience = state.get('experience', self.experience)
            self.hp = state.get('hp', self.hp)
            self.max_hp = state.get('max_hp', self.max_hp)
            self.mana = state.get('mana', self.mana)
            self.max_mana = state.get('max_mana', self.max_mana)
            self.inventory = state.get('inventory', self.inventory)
            self.gold = state.get('gold', self.gold)
            self.gold = state.get('gold', 0)  # Use 0 as default if 'gold' is not in the state
        
    def play_sound(effect_type):
        sound_path = sound_data.get(effect_type)
        if isinstance(sound_path, list):
            sound_path = random.choice(sound_path)
        sound = pygame.mixer.Sound(sound_path)
        sound.play()
        
    def on_keydown_event(self, key):
        now = pygame.time.get_ticks()
        if key == pygame.K_j:
            self.handle_melee_attack()
        elif key == pygame.K_k:
            if not self.is_jumping and not self.is_charging_attack:
                self.is_charging_attack = True
                self.attack_charge_start = now
                self.action = f'casting_spell_{self.last_direction}'
        elif key == pygame.K_SPACE and not self.is_jumping:
            self.is_jumping = True
            self.vertical_velocity = -self.jump_speed
            self.horizontal_velocity = -self.jump_speed
            self.jump_start_time = now

    def on_keyup_event(self, key):
        if key == pygame.K_k and self.is_charging_attack:
            charge_time = pygame.time.get_ticks() - self.attack_charge_start
            self.is_charging_attack = False
            self.perform_special_attack(charge_time)



    def update_bars(self):
        now = pygame.time.get_ticks()
        self.hp_bar.update(self.hp)
        self.mana_bar.update(self.mana)
        self.find_closest_enemy(900)
        if self.is_charging_attack:
            charge_time = now - self.attack_charge_start
            self.charge_bar.update(charge_time)
        else:
            self.charge_bar.update(0)

    def borderless(self, tile_size, map_width, map_height):
        if self.rect.right > (map_width+1)*tile_size:
            self.rect.left = 0
        elif self.rect.left < 0:
            self.rect.left = (map_width)*tile_size

        if self.rect.top > (map_height)*tile_size:
            self.rect.top = 0
        elif self.rect.bottom < 0: #perfeito
            self.rect.bottom = map_height*tile_size
    
    def handle_movement(self, dt):
        if self.is_performing_special_attack:
            return
        
        move_x = move_y = 0
        keys = pygame.key.get_pressed()

        if keys[pygame.K_a]:
            self.action = 'run_left' if keys[pygame.K_LSHIFT] else 'walk_left'
            move_x = -self.running_speed if keys[pygame.K_LSHIFT] else -self.speed
            self.last_direction = 'left'
        elif keys[pygame.K_d]:
            self.action = 'run_right' if keys[pygame.K_LSHIFT] else 'walk_right'
            move_x = self.running_speed if keys[pygame.K_LSHIFT] else self.speed
            self.last_direction = 'right'
        elif keys[pygame.K_w]:
            self.action = 'run_up' if keys[pygame.K_LSHIFT] else 'up_walk'
            move_y = -self.running_speed if keys[pygame.K_LSHIFT] else -self.speed
            self.last_direction = 'up'
        elif keys[pygame.K_s]:
            self.action = 'run_down' if keys[pygame.K_LSHIFT] else 'down_walk'
            move_y = self.running_speed if keys[pygame.K_LSHIFT] else self.speed
            self.last_direction = 'down'
        elif not self.is_charging_attack:
            self.action = f'idle_{self.last_direction}'
        
        self.move(move_x * dt, move_y * dt)
        if self.is_jumping:
            self.action = f'jump_{self.last_direction}'

    def move(self, dx, dy):
        if not self.is_jumping:
            self.rect.x += dx
            if pygame.sprite.spritecollideany(self, self.collidable_tiles):
                self.rect.x -= 0.3*dx
                self.rect.y += 0.5*dx

            self.rect.y += dy
            if pygame.sprite.spritecollideany(self, self.collidable_tiles):
                self.rect.y -= 0.3*dy
                self.rect.x += 0.5*dy
        else:
            self.rect.x += dx
            self.rect.y += dy


    def attack_with_sword(self, charge_time):
        if self.inventory['melee_weapon']:
            weapon = self.inventory['melee_weapon']
            now = pygame.time.get_ticks()
            if now - self.last_attack_time > weapon_data[weapon]['cooldown']:
                self.last_attack_time = now
                direction_map = {
                    'up': pygame.math.Vector2(0, -1),
                    'down': pygame.math.Vector2(0, 1),
                    'left': pygame.math.Vector2(-1, 0),
                    'right': pygame.math.Vector2(1, 0)
                }
                direction = direction_map.get(self.last_direction, pygame.math.Vector2(0, 1))
                multiplier = charge_time / 300
                damage = int(weapon_data[weapon]['damage'] * multiplier)
                slash_pos = self.rect.center + direction * 10
                Slash(slash_pos, direction, [self.level.all_sprites], damage)
                self.action = f'attack_{self.last_direction}'
                self.current_sprite = 0  # Reset the sprite to the beginning of the attack animation
                self.check_slash_collisions(slash_pos, direction, damage)
                
                # Set a flag to indicate that an attack animation is in progress
                self.is_attacking = True
                self.attack_start_time = pygame.time.get_ticks()

    def check_slash_collisions(self, slash_pos, direction, damage):
        slash_rect = pygame.Rect(0, 0, 60, 60)
        slash_rect.center = slash_pos
        for enemy in self.level.enemies:
            if slash_rect.colliderect(enemy.rect):
                knockback_direction = pygame.math.Vector2(enemy.rect.center) - pygame.math.Vector2(self.rect.center)
                if knockback_direction.length() > 0:
                    knockback_direction.normalize_ip()
                    enemy.take_damage(damage, self.level.all_sprites, self.level.tiles, (255, 0, 0), knockback_direction)

    def find_closest_enemy(self, max_distance):
        closest_enemy = None
        closest_distance = float('inf')
        for enemy in self.level.enemies:
            distance = pygame.math.Vector2(self.rect.center).distance_to(enemy.rect.center)
            if distance < closest_distance and distance <= max_distance:
                closest_distance = distance
                closest_enemy = enemy
        return closest_enemy

            
    def attack_with_shuriken(self):
        if not self.inventory['ranged_weapon']:
            return
        weapon = self.inventory['ranged_weapon']
        now = pygame.time.get_ticks()
        if now - self.last_attack_time <= weapon_data[weapon]['cooldown']:
            return
        
        closest_enemy = self.find_closest_enemy(self.attack_range)
        if not closest_enemy:
            current_time = time.time()
            if current_time - self.last_shuriken_message_time > self.shuriken_message_cooldown:
                print("No enemy found within range to attack with shuriken")
                self.last_shuriken_message_time = current_time
            return
        
        direction = pygame.math.Vector2(closest_enemy.rect.center) - pygame.math.Vector2(self.rect.center)
        if direction.length() <= 0:
            return
        direction.normalize_ip()
        
        new_projectile = Projectile(
            pos=self.rect.center,
            direction=direction,
            throw_speed=self.throw_speed,
            groups=[self.projectile_group],
            projectile_type=weapon,
            level=self.level,
            side='player_projectile',
            from_collision=False
        )
        self.last_attack_time = now
        print(f"Shuriken fired: Position: {new_projectile.rect.center}, Direction: {direction}, Speed: {new_projectile.speed}")
    def medium_attack(self):
        closest_enemy = self.find_closest_enemy(900)  # Raio de 500 pixels para fireball
        if closest_enemy and self.mana >= 10:
            direction = pygame.math.Vector2(closest_enemy.rect.center) - pygame.math.Vector2(self.rect.center)
            if direction.length() > 0:
                direction.normalize_ip()
                fireball = Projectile(pos=self.rect.center,direction=direction,throw_speed=self.throw_speed, groups=[self.level.all_sprites, self.projectile_group],projectile_type='fireball',level=self.level,side='player_projectile',

                )
                self.mana -= 10
                fireball.explosion_damage = 20  # Dano da explosão
                fireball.explosion_radius = 200  # Raio da explosão
                fireball.explosion_effect = Explosion  # Efeito da explosão
                print(f"Fireball fired: Position: {fireball.rect.center}, Direction: {direction}")
        else:
            print("No enemy found or not enough mana to attack with fireball")

    def strong_attack(self):
        self.is_performing_special_attack = True
        self.invincible = True
        self.current_sprite = 0
        self.raikiri_start_time = pygame.time.get_ticks()
        self.mana -= 30
        self.perform_raikiri_attack()

    def perform_raikiri_attack(self):
        self.action = f'raikiri_{self.last_direction}'
        closest_enemy = self.find_closest_enemy(900)
        if closest_enemy:
            self.raikiri_target = closest_enemy
            
            self.aura = ElectricAura(self, [self.groups()[0], self.level.all_sprites])
            self.raikiri_start_time = pygame.time.get_ticks()
            self.raikiri_end_time = self.raikiri_start_time + self.raikiri_max_duration
            self.raikiri_animation_complete = False
        else:
            self.reset_raikiri_state()

    def move_to_target(self, dt):
        if self.raikiri_target and self.raikiri_target.hp > 0:
            direction = pygame.math.Vector2(self.raikiri_target.rect.center) - pygame.math.Vector2(self.rect.center)
            distance = direction.length()
            if distance > 0:
                direction.normalize_ip()
                self.update_direction(direction)
                self.action = f'run_{self.last_direction}'
                self.rect.center += direction * self.running_speed * 2 * dt
                self.invincible = True
                if distance < 40:
                    raikiridmg = 150 * self.ninjutsu
                    self.raikiri_target.take_damage(raikiridmg, self.level.all_sprites, self.level.tiles, (0, 150, 240), direction)
                    for _ in range(20):
                        Particle(self.raikiri_target.rect.bottomright, [self.level.all_sprites], (230,230,250), initial_size=8, lifespan=2000)
                        Particle(self.raikiri_target.rect.bottomright, [self.level.all_sprites], (230,10,0), initial_size=4, lifespan=2000)
                    self.reset_raikiri_state()
            else:
                self.reset_raikiri_state()
        else:
            self.reset_raikiri_state()

    def update_direction(self, direction):
        if abs(direction.x) > abs(direction.y):
            if direction.x > 0:
                self.last_direction = 'right'
            else:
                self.last_direction = 'left'
        else:
            if direction.y > 0:
                self.last_direction = 'down'
            else:
                self.last_direction = 'up'

    def get_direction_vector(self):
        direction_vectors = {
            'left': (-1, 0),
            'right': (1, 0),
            'up': (0, -1),
            'down': (0, 1)
        }
        return direction_vectors.get(self.last_direction, (0, 0))

    def regenerate_mana(self, dt):
        self.mana += self.mana_regeneration * dt
        self.mana = min(self.mana, self.max_mana)
        self.hp += self.hp_regeneration * dt
        self.hp = min(self.hp, self.max_hp)

    def kawarimi(self,amount):
        # Chance de ativação da habilidade Kawarimi (ajuste conforme necessário)
        if random.random() < 0.22:
            directions = [(1, 0), (-1, 0), (0, 1), (0, -1)]
            direction = random.choice(directions)
            Kawarimi(self.rect.center, [self.level.all_sprites], self.level.all_sprites, self.level.top_sprites)
            self.rect.x += direction[0] * 4 * 32  # 4 tiles de distância
            self.rect.y += direction[1] * 4 * 32
            Puff(self.rect.center, [self.level.all_sprites])
            self.hp += amount  # Recupera o dano sofrido

    def take_damage(self, amount, knockback_direction, color):
        if self.is_performing_special_attack:
            FloatingText('MISS', self.rect, 'white', self.level.camera, self.level.all_sprites)      
        if not self.invincible:
            self.kawarimi(amount)  # Tenta ativar a habilidade Kawarimi
            self.hp -= amount
            self.level.spawn_blood(self.rect.center, amount=int(amount * 2))
            #FloatingText(str(amount), self.rect, color, self.level.camera, self.level.all_sprites)
            if self.hp <= 0:
                self.kill()
            else:
                self.invincible = True
                self.invincible_start_time = pygame.time.get_ticks()
                self.knockback_velocity = knockback_direction * 200
                self.is_knockedback = True
                self.knockback_start_time = pygame.time.get_ticks()

    def check_item_collisions(self):
        hits = pygame.sprite.spritecollide(self, self.level.overlay_sprites, False)  # Não remover os sprites ainda
        for hit in hits:
            if isinstance(hit, ItemDrop) and self.is_jumping == False:
                self.absorb_item(hit)
                hit.kill()  # Remover o item após ser absorvido

    def draw_inventory_slots(self, screen):
        self.melee_slot.draw(screen)
        self.ranged_slot.draw(screen)
        # Atualizar slots com os itens atuais
        if self.inventory['melee_weapon']:
            self.melee_slot.set_item(weapon_data[self.inventory['melee_weapon']])
        if self.inventory['ranged_weapon']:
            self.ranged_slot.set_item(weapon_data[self.inventory['ranged_weapon']])

    def absorb_item(self, item):
            print(f'Absorveu {item.item}')
            item_type = item.item
            if item_type in weapon_data:
                if weapon_data[item_type]['type'] == 'ranged':
                    self.inventory['ranged_weapon'] = item_type
                elif weapon_data[item_type]['type'] == 'melee':
                    self.inventory['melee_weapon'] = item_type
            # Exemplo: self.inventory.append(item.item)

    def update(self, dt):
        keys = pygame.key.get_pressed()
        now = pygame.time.get_ticks()

        if self.is_attacking:
            if now - self.attack_start_time > 500:  # Attack animation duration
                self.is_attacking = False
                self.action = f'idle_{self.last_direction}'
        elif self.is_charging_attack:
            if not keys[pygame.K_k]:
                charge_time = now - self.attack_charge_start
                self.is_charging_attack = False
                self.perform_special_attack(charge_time)
        else:
            self.handle_movement(dt)
      #  self.handle_movement(dt)
        self.animate(dt)
        self.regenerate_mana(dt)
        self.update_bars()
        self.handle_jump(dt)
        self.handle_knockback(dt)
        self.handle_invincibility()
        self.floating_texts.update(dt)
        self.check_item_collisions()
        self.attack_with_shuriken()
        if self.is_performing_special_attack:
            now = pygame.time.get_ticks()
            if not self.raikiri_animation_complete:
                if now - self.raikiri_start_time >= self.raikiri_animation_duration:
                    self.raikiri_animation_complete = True
                else:
                    # During animation, just update the electric effect
                    if self.aura:
                        self.aura.update(dt)
            elif self.raikiri_target and self.raikiri_target.hp > 0:
                self.move_to_target(dt)
            elif now >= self.raikiri_end_time or not self.raikiri_target or self.raikiri_target.hp <= 0:
                self.reset_raikiri_state()
    

   

    def handle_jump(self, dt):
        if self.is_jumping:
            self.action = f'jump_{self.last_direction}'
            self.vertical_velocity += self.gravity * dt
            self.rect.y += self.vertical_velocity * dt * 100
            self.horizontal_velocity += self.gravity * dt
            self.rect.x += self.horizontal_velocity * dt * 100
            self.invincible = True
            self.invincible_start_time = pygame.time.get_ticks()-450
            if pygame.time.get_ticks() - self.jump_start_time >= 1100:
                self.is_jumping = False
                self.jump_start_time = None

    def handle_knockback(self, dt):
        if self.is_knockedback:
            self.rect.center += self.knockback_velocity * dt
            if pygame.time.get_ticks() - self.knockback_start_time >= self.knockback_duration:
                self.is_knockedback = False

    def handle_invincibility(self):
        if self.invincible:
            now = pygame.time.get_ticks()
            if now - self.invincible_start_time >= self.invincible_duration:
                self.invincible = False
            else:
                if (now // 100) % 2 == 0:
                    self.image.set_alpha(120)
                else:
                    self.image.set_alpha(255)
        else:
            self.image.set_alpha(255)

    def animate(self, dt):
        self.current_time += dt
        action_index = self.get_action_index(self.action)
        if action_index is not None and action_index < len(self.sprites):
            if self.current_time >= self.animation_time:
                self.current_time = 0
                self.current_sprite = (self.current_sprite + 1) % len(self.sprites[action_index])
                self.image = self.sprites[action_index][self.current_sprite]

    def get_action_index(self, action):
        return self.action_map.get(action, 0)

    def draw(self, screen):
        screen.blit(self.image, self.rect)
        self.hp_bar.draw(screen)
        self.mana_bar.draw(screen)
        self.charge_bar.draw(screen)
        self.draw_inventory_slots(screen)
        self.floating_texts.draw(screen)
        
    def move(self, dx, dy):
        if not self.is_jumping:
            self.rect.x += dx
            if pygame.sprite.spritecollideany(self, self.collidable_tiles):
                self.rect.x -= 0.3*dx
                self.rect.y += 0.5*dx

            self.rect.y += dy
            if pygame.sprite.spritecollideany(self, self.collidable_tiles):
                self.rect.y -= 0.3*dy
                self.rect.x += 0.5*dy
        else:
            self.rect.x += dx
            self.rect.y += dy
