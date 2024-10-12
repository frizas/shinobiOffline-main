# characters.py

import pygame
import random
from projectile import Projectile
from settings import *
from effects import *
from text_display import FloatingText
from ItemDrop import ItemDrop
from tile import Tile

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
                if not is_sprite_empty(sprite):
                    row_sprites.append(sprite)
        if row_sprites:
            sprites.append(row_sprites)

    return sprites

def is_sprite_empty(sprite):
    """Verifica se o sprite é vazio (transparente)"""
    for x in range(sprite.get_width()):
        for y in range(sprite.get_height()):
            if sprite.get_at((x, y)).a != 0:
                return False
    return True

class Character(pygame.sprite.Sprite):
    RANK_MULTIPLIERS = {
        'D': 1.0, 'C': 1.2, 'B': 1.5, 'A': 2.0, 'S': 3.5
    }

    def __init__(self, name, rank, pos, groups, projectile_group, level, clan=None):
        super().__init__(groups)
        self.level = level
        self.groups_list = groups
        self.projectile_group = projectile_group
        self.name = name
        self.rank = rank
        self.multiplier = self.RANK_MULTIPLIERS.get(rank, 1.0)

        # Common attributes
        self.hp = 0
        self.max_hp = 0
        self.speed = 0
        self.vision_radius = 0
        self.melee_skill = 0
        self.defense_skill = 0
        self.throw_speed = 0.8 * self.multiplier

        self.target = None
        self.last_attack_time = 0
        self.attack_cooldown = 3.5
        self.animation_time = 0.2
        self.current_time = 0
        self.action = 'idle_down'
        self.last_direction = 'down'
        self.is_dying = False

        self.is_knockedback = False
        self.knockback_start_time = 0
        self.knockback_duration = 50
        self.knockback_velocity = 70

        self.special_attack_active = False
        self.special_attack_timer = 0
        self.special_attack_stage = 0
        self.special_attack_duration = 200
        self.special_attack_cooldown = 10
        self.last_special_attack_time = 0

        self.element = self.assign_element()
        self.ninjutsu = self.assign_ninjutsu()

        # Initialize sprites, rect, and mask
        self.initialize_sprites()

    def animate(self, dt):
        self.current_time += dt
        action_index = self.get_action_index(self.action)
        if action_index is not None and action_index < len(self.sprites):
            if self.current_time >= self.animation_time:
                self.current_time = 0
                self.current_sprite = (self.current_sprite + 1) % len(self.sprites[action_index])
                self.image = self.sprites[action_index][self.current_sprite]

    def assign_element(self):
        if self.rank in ['S', 'A', 'B', 'C']:
            return random.choice(list(ninjutsu_data.keys()))
        return None

    def assign_ninjutsu(self):
        if not self.element:
            return []
        
        available_jutsu = list(ninjutsu_data[self.element].keys())
        num_jutsu = min(len(available_jutsu), {
            'S': 4, 'A': 3, 'B': 2, 'C': 1
        }.get(self.rank, 0))
        
        return random.sample(available_jutsu, num_jutsu)
    
    def draw_health_bar(self, screen):
        # Desenhar barra de HP
        hp_ratio = self.hp / self.max_hp
        hp_bar_width = self.rect.width
        hp_bar_height = 5
        hp_bar = pygame.Rect(self.rect.left, self.rect.top - 20, int(hp_ratio * hp_bar_width), hp_bar_height)
        hp_border = pygame.Rect(self.rect.left, self.rect.top - 20, hp_bar_width, hp_bar_height)

        hp_bar = self.level.camera.apply_rect(hp_bar)
        hp_border = self.level.camera.apply_rect(hp_border)

        pygame.draw.rect(screen, (255, 0, 0), hp_border)
        pygame.draw.rect(screen, (0, 255, 0), hp_bar)

        # Desenhar nome e rank
        rank_color = self.get_rank_color()
        text_surface = self.font.render(f'Rank {self.rank}  {self.name}', True, rank_color)
        text_rect = text_surface.get_rect(midbottom=self.rect.midtop)
        text_rect = self.level.camera.apply_rect(text_rect)
        screen.blit(text_surface, text_rect)

    def get_rank_color(self):
        rank_colors = {
            'S': (100, 0, 0),    # Red
            'A': (50, 50, 0),  # Orange
            'B': (80, 80, 0),  # Yellow
            'C': (50, 100, 50),    # Green
            'D': (0, 0, 120)     # Blue
        }
        return rank_colors.get(self.rank, (255, 255, 255))  # White as default
            
    def random_move(self, dt):
        now = pygame.time.get_ticks()

        # Verifica se o tempo para a próxima ação aleatória chegou
        if now - self.random_move_timer > self.random_move_duration:
            self.random_move_timer = now
            self.random_move_duration = random.randint(800, 1200)  # Duração entre 0.8 e 1.2 segundos

            # Decide se vai se mover ou parar
            if random.random() < 0.5:  # 50% de chance de se mover ou parar
                directions = [
                    (1, 0),    # Direita
                    (-1, 0),   # Esquerda
                    (0, 1),    # Baixo
                    (0, -1)    # Cima
                ]
                self.random_move_direction = random.choice(directions)
                if self.random_move_direction == (1, 0):
                    self.random_move_action = 'walk_right'
                    self.last_direction = 'right'
                elif self.random_move_direction == (-1, 0):
                    self.random_move_action = 'walk_left'
                    self.last_direction = 'left'
                elif self.random_move_direction == (0, 1):
                    self.random_move_action = 'down_walk'
                    self.last_direction = 'down'
                elif self.random_move_direction == (0, -1):
                    self.random_move_action = 'up_walk'
                    self.last_direction = 'up'
            else:
                self.random_move_direction = (0, 0)
                self.random_move_action = f'idle_{self.last_direction}'

        # Atualiza a posição do monstro baseado na direção escolhida
        self.rect.x += self.random_move_direction[0] * self.speed * dt
        self.rect.y += self.random_move_direction[1] * self.speed * dt
        self.action = self.random_move_action

    def move(self, dt):
        if self.target:
            direction_vector = pygame.math.Vector2(self.target.rect.center) - pygame.math.Vector2(self.rect.center)
            distance = direction_vector.length()
            if distance >0:
                direction_vector.normalize_ip()
                if distance > 40:
                    
                    if self.behavior == 'aggressive':
                        self.rect.center += direction_vector * self.speed * dt
                    elif self.behavior == 'defensive' and distance < 150:
                        self.rect.center -= direction_vector * self.speed * dt
                    elif self.behavior == 'defensive' and distance > 250:
                        self.rect.center += direction_vector * self.speed * dt
                    else:
                        self.random_move(dt)

                    if abs(direction_vector.x) > abs(direction_vector.y):
                        if direction_vector.x > 0:
                            self.action = 'walk_right'
                            self.last_direction = 'right'
                        else:
                            self.action = 'walk_left'
                            self.last_direction = 'left'
                    else:
                        if direction_vector.y > 0:
                            self.action = 'down_walk'
                            self.last_direction = 'down'
                        else:
                            self.action = 'up_walk'
                            self.last_direction = 'up'
            else:
                return
  
    def find_closest_enemy(self):
        closest_enemy = None
        closest_distance = self.vision_radius
        
        if isinstance(self, Ally):  # If the character is an Ally
            # Check enemies
            for enemy in self.level.enemies:
                distance = pygame.math.Vector2(enemy.rect.center).distance_to(pygame.math.Vector2(self.rect.center))
                if distance < closest_distance:
                    closest_distance = distance
                    closest_enemy = enemy
            
            # Check player (assuming player is also an enemy for allies)
            player_distance = pygame.math.Vector2(self.level.player.rect.center).distance_to(pygame.math.Vector2(self.rect.center))
            if player_distance < closest_distance:
                closest_distance = player_distance
                closest_enemy = self.level.player

        elif isinstance(self, Enemy):  # If the character is an Enemy
            # Check allies
            for ally in self.level.allies:
                distance = pygame.math.Vector2(ally.rect.center).distance_to(pygame.math.Vector2(self.rect.center))
                if distance < closest_distance:
                    closest_distance = distance
                    closest_enemy = ally
            
            # Check player
            player_distance = pygame.math.Vector2(self.level.player.rect.center).distance_to(pygame.math.Vector2(self.rect.center))
            if player_distance < closest_distance:
                closest_distance = player_distance
                closest_enemy = self.level.player

        self.target = closest_enemy
        return closest_enemy

    def use_ninjutsu(self):
        if not self.ninjutsu:
            return None
        
        jutsu = random.choice(self.ninjutsu)
        jutsu_data = ninjutsu_data[self.element][jutsu]
        
        return {
            'name': jutsu,
            'element': self.element,
            'mana_cost': jutsu_data['mana_cost'],
            'damage': jutsu_data['damage']
        }

    def attack(self):
        now = pygame.time.get_ticks() / 1000
        if now - self.last_attack_time > self.attack_cooldown:
            self.last_attack_time = now
            direction = pygame.math.Vector2(self.target.rect.center) - pygame.math.Vector2(self.rect.center)
            if direction.length() > 0:
                direction.normalize_ip()
                attack_choice = random.random()
                if attack_choice < 0.2:  # 20% chance for special attacks
                    special_attack = random.choice(['area_attack', 'special_teleport_attack', 'cast_insect_swarm_spell'])
                    if special_attack == 'area_attack':
                        self.area_attack()
                    elif special_attack == 'special_teleport_attack':
                        self.special_attack_active = True
                        self.special_teleport_attack(0)
                    elif special_attack == 'cast_insect_swarm_spell':
                        self.cast_insect_swarm_spell(self.target)
                elif self.rank in ['S', 'A', 'B', 'C'] and random.random() < (0.4 * self.multiplier):
                    jutsu = self.use_ninjutsu()
                    if jutsu:
                        self.perform_ninjutsu(jutsu, direction)
                    else:
                        self.perform_normal_attack(direction)
                else:
                    self.perform_normal_attack(direction)

    def handle_knockback(self, dt):
        if self.is_knockedback:
            self.rect.center += self.knockback_velocity * dt
            if pygame.time.get_ticks() - self.knockback_start_time >= self.knockback_duration:
                self.is_knockedback = False

    def take_damage(self, amount, all_sprites, tiles, knockback_direction, color=(220,44,0)):
        self.hp -= amount        
        self.vision_radius += 300
        FloatingText(str(amount), self.rect, color, self.level.camera, all_sprites)
        self.knockback_velocity = knockback_direction * 200
        self.is_knockedback = True
        self.knockback_start_time = pygame.time.get_ticks()
        self.level.spawn_blood(self.rect.center, amount=max(1, int(amount)))
        if self.hp <= 0:
            self.is_dying = True
            self.rect.size = (0, 0)
            self.animate_death_step(0, all_sprites, tiles)

    def animate_death_step(self, dt, all_sprites, tiles):
        now = pygame.time.get_ticks()
        Tile('images/dead_human.png', (self.rect.x+60, self.rect.y+60), [all_sprites, tiles])
  
        self.kill()
        if now - self.death_start_time > self.current_death_frame * 15:
            self.death_start_time = now
            if self.current_death_frame < len(self.death_sprites[0]):
                self.image = self.death_sprites[0][self.current_death_frame]
                self.current_death_frame += 1

    def perform_ninjutsu(self, jutsu, direction):
        print(f"{self.name} uses {jutsu['name']} ({jutsu['element']})!")
        target_pos = self.rect.center + direction * 200

        effect_class = {
            'Fireball Jutsu': FireballEffect,
            'Phoenix Flower Jutsu': PhoenixFlowerEffect,
            'Water Bullet': WaterBulletEffect,
            'Water Dragon Jutsu': WaterDragonEffect,
            'Earth Wall': EarthWallEffect,
            'Chidori': ChidoriEffect,
            'Wind Blade': WindBladeEffect
        }.get(jutsu['name'])

        if effect_class:
            if effect_class in [FireballEffect, WaterBulletEffect, WaterDragonEffect, WindBladeEffect]:
                effect_class(self.rect.center, [self.groups_list[0]], target_pos)
            else:
                effect_class(self.rect.center, [self.groups_list[0]])

    def perform_normal_attack(self, direction):
        projectile_type = random.choice(['kunai', 'shuriken', 'fuuma'] if self.rank in ['S', 'A', 'B'] else ['kunai', 'shuriken'])
        Projectile(self.rect.center, direction, [self.groups_list[0], self.projectile_group], 
                   projectile_type, self.level, self.throw_speed, side=self.projectile_side)

    def special_teleport_attack(self, dt):
        if self.special_attack_stage == 0:
            # Etapa 1: Teletransportar
            directions = [(1, 0), (-1, 0), (0, 1), (0, -1)]
            direction = random.choice(directions)
            Puff(self.rect.center, [self.level.all_sprites, self.level.overlay_sprites])
            self.rect.x += direction[0] * 3 * 32  # 3 tiles de distância
            self.rect.y += direction[1] * 3 * 32
            self.special_attack_stage = 1
            Puff(self.rect.center, [self.level.all_sprites, self.level.overlay_sprites])
            self.special_attack_timer = pygame.time.get_ticks()
        elif self.special_attack_stage == 1:
            # Etapa 2: Pausar
            if pygame.time.get_ticks() - self.special_attack_timer >= self.special_attack_duration:
                self.special_attack_stage = 2
                self.special_attack_timer = pygame.time.get_ticks()
        elif self.special_attack_stage == 2:
            # Etapa 3: Lançar Fireball
            if self.target:
                fireball_direction = pygame.math.Vector2(self.target.rect.center) - pygame.math.Vector2(self.rect.center)
                fireball_direction.normalize_ip()
                Projectile(self.rect.center, fireball_direction, [self.groups_list[0], self.projectile_group], 'fireball', self.level, self.throw_speed, side='player_projectile')
                self.special_attack_active = False  # Finaliza o ataque especial
                self.special_attack_stage = 0
                if self.rank in ['S', 'A', 'B', 'C', 'D']:
                    if random.random() > (1.5 / self.multiplier):
                        self.special_attack_active = True
                        self.special_teleport_attack(0)
    
    def area_attack(self):
        for angle in range(0, 360, int(90 // self.multiplier)):
            direction = pygame.math.Vector2(1, 0).rotate(angle)
            Projectile(self.rect.center, direction, [self.groups_list[0], self.projectile_group], 
                       'fuuma', self.level, self.throw_speed, side=self.projectile_side)

    # Add other common methods here

class Ally(Character):
    def __init__(self, name, rank, pos, groups, projectile_group, level):
        super().__init__(name, rank, pos, groups, projectile_group, level)
        self.projectile_side = 'player_projectile'
        # Ally-specific sprite initialization
        data = ally_data.get(self.name)
        if not data:
            raise ValueError(f"Ally data for '{self.name}' not found.")
        self.name = name
        self.sprites = load_spritesheet(data['graphic'], 64, 64, 4, 4)
        self.current_sprite = 0
        self.image = self.sprites[0][self.current_sprite]
        self.rect = self.image.get_rect(center=pos)
        self.mask = pygame.mask.from_surface(self.image)
        self.data = data
        self.pos = pos
        # Ally-specific initialization

    def initialize_sprites(self):
        
        
        self.sprites = load_spritesheet(self.data['graphic'], 64, 64, 4, 4)
        self.current_sprite = 0
        self.image = self.sprites[0][self.current_sprite]
        self.rect = self.image.get_rect(center=self.pos)
        self.mask = pygame.mask.from_surface(self.image)

    # Add Ally-specific methods here
    def cast_insect_swarm_spell(self, target):
        # Implement cast_insect_swarm_spell logic
        pass

    def update(self, dt, all_sprites, tiles, screen=None):
        self.target = self.find_closest_enemy(self.vision_radius)
        self.handle_knockback(dt)
        if self.is_dying:
            self.animate_death_step(dt, all_sprites, tiles)
        else:
            self.floating_texts.update(dt)
            if self.special_attack_active:
                self.special_teleport_attack(dt)
            elif self.can_see_target():
                self.move(dt)
                self.animate(dt)
                self.attack()
            else:
                self.random_move(dt)
                self.animate(dt)
        self.draw_health_bar(screen)

    def find_closest_enemy(self, radius):
        # Implement find_closest_enemy logic
        pass

    def can_see_target(self):
        if self.target is None:
            return False
        distance = pygame.math.Vector2(self.target.rect.center).distance_to(pygame.math.Vector2(self.rect.center))
        return distance <= self.vision_radius

    def random_move(self, dt):
        # Implement random_move logic
        pass

class Enemy(Character):
    def __init__(self, name, rank, pos, groups, projectile_group, level):
        super().__init__(name, rank, pos, groups, projectile_group, level)
        self.projectile_side = 'enemy_projectile'
         # Pega os dados do monstro a partir do nome
        data = monster_data.get(name)
        if not data:
            raise ValueError(f"Monster data for '{name}' not found.")
        
        self.name = name
        self.data = data
        self.pos = pos

        # Enemy-specific initialization

    def initialize_sprites(self):
        # Enemy-specific sprite initialization
        self.sprites = load_spritesheet(self.data['graphic'], 64, 64, 4, 4)
        self.current_sprite = 0
        self.image = self.sprites[0][self.current_sprite]
        self.rect = self.image.get_rect(center=self.pos)
        self.mask = pygame.mask.from_surface(self.image)

    # Add Enemy-specific methods here
    def update(self, dt, all_sprites, tiles, screen=None):
        self.target = self.find_closest_enemy()
        self.handle_knockback(dt)
        if self.is_dying:
            self.animate_death_step(dt, all_sprites, tiles)
        else:
            self.floating_texts.update(dt)
            if self.special_attack_active:
                self.special_teleport_attack(dt)
            elif self.can_see_target():
                self.move(dt)
                self.animate(dt)
                self.attack()
            else:
                self.random_move(dt)
                self.animate(dt)
        self.draw_health_bar(screen)

    def find_closest_enemy(self):
        # Implement find_closest_enemy logic (as shown in your enemy.py file)
        pass

    def can_see_target(self):
        if self.target is None:
            return False
        distance = pygame.math.Vector2(self.target.rect.center).distance_to(pygame.math.Vector2(self.rect.center))
        return distance <= self.vision_radius

    def random_move(self, dt):
        # Implement random_move logic
        pass
    def drop_item(self):
         if random.random() < 0.2:  # 50% de chance de drop
            
            ItemDrop(self.rect.center, [self.level.all_sprites, self.level.overlay_sprites])


    def drop_item(self):
        if random.random() < 0.2:  # 20% chance of drop
            ItemDrop(self.rect.center, [self.level.all_sprites, self.level.overlay_sprites])

    def take_damage(self, amount, all_sprites, tiles, color, knockback_direction):
        self.kawarimi(amount)  # Try to activate Kawarimi ability
        super().take_damage(amount, all_sprites, tiles, knockback_direction, color)
        if self.hp <= 0:
            self.drop_item()