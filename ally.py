import pygame
import random
from projectile import Projectile
from settings import *
from tile import Tile
from effects import *
from text_display import FloatingText

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

class Ally(pygame.sprite.Sprite):
    RANK_MULTIPLIERS = {
        'D': 1.0,
        'C': 1.2,
        'B': 1.5,
        'A': 2.0,
        'S': 3.5
    }

    def __init__(self, name, rank, pos, groups, projectile_group, level):
        super().__init__(groups)
        self.level = level
        self.groups_list = groups
        
        # Pega os dados do aliado a partir do nome
        data = ally_data.get(name)
        if not data:
            raise ValueError(f"Ally data for '{name}' not found.")
        
        multiplier = self.RANK_MULTIPLIERS.get(rank, 1.0)
        self.multiplier = multiplier
        self.hp = int(data['hp'] * multiplier)
        self.max_hp = self.hp
        self.speed = int(data['speed'] * multiplier)
        self.behavior = data['behavior']
        self.vision_radius = int(data['vision_radius'] * multiplier)
        self.melee_skill = int(data['melee_skill'] * multiplier)
        self.defense_skill = int(data['defense_skill'] * multiplier)
        self.rank = rank
        self.name = name
        self.throw_speed = 0.8 * multiplier

        self.sprites = load_spritesheet(data['graphic'], 64, 64, 4, 4)
        self.current_sprite = 0
        self.image = self.sprites[0][self.current_sprite]
        self.rect = self.image.get_rect(center=pos)
        self.mask = pygame.mask.from_surface(self.image)

        self.target = None
        self.last_attack_time = 0
        self.attack_cooldown = 3.5
        self.animation_time = 0.2
        self.current_time = 0
        self.action = 'idle_down'
        self.last_direction = 'down'
        self.projectile_group = projectile_group
        self.is_dying = False

        self.is_knockedback = False
        self.knockback_start_time = 0
        self.knockback_duration = 50
        self.knockback_velocity = 70
        
        self.action_map = {
            'down_walk': 0,
            'up_walk': 1,
            'walk_right': 2,
            'walk_left': 3,
            'idle_down': 4,
            'idle_up': 5,
            'idle_right': 6,
            'idle_left': 7,
        }
        self.special_attack_active = False
        self.special_attack_timer = 0
        self.special_attack_stage = 0
        self.special_attack_duration = 200
        # Variáveis para movimento aleatório
        self.random_move_timer = 0
        self.random_move_duration = 1000  # 1 segundo
        self.random_move_direction = (0, 0)
        self.random_move_action = 'idle'
        self.rect.width = self.rect.width // 2
        self.rect.height = self.rect.height // 2
        self.target =self.find_closest_enemy(5000)

        self.death_start_time = 0
        self.current_death_frame = 0
        self.death_sprites = load_spritesheet('images/effects/blood_splash.png', 64, 64, 1, 16)
        self.floating_texts = pygame.sprite.Group()
        self.font = pygame.font.Font(None, 20)
         # Cooldown para habilidades especiais
        self.special_attack_cooldown = 10
        self.last_special_attack_time = 0

        self.element = self.assign_element()
        self.ninjutsu = self.assign_ninjutsu()

    def assign_element(self):
        if self.rank in ['S', 'A', 'B', 'C']:
            return random.choice(list(ninjutsu_data.keys()))
        return None

    def assign_ninjutsu(self):
        if not self.element:
            return []
        
        available_jutsu = list(ninjutsu_data[self.element].keys())
        num_jutsu = min(len(available_jutsu), {
            'S': 4,
            'A': 3,
            'B': 2,
            'C': 1
        }.get(self.rank, 0))
        
        return random.sample(available_jutsu, num_jutsu)

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

    def handle_knockback(self, dt):
        if self.is_knockedback:
            self.rect.center += self.knockback_velocity * dt
            if pygame.time.get_ticks() - self.knockback_start_time >= self.knockback_duration:
                self.is_knockedback = False

    def get_rank_color(self):
        rank_colors = {
            'S': (100, 0, 0),    # Red
            'A': (50, 50, 0),  # Orange
            'B': (80, 80, 0),  # Yellow
            'C': (50, 100, 50),    # Green
            'D': (0, 0, 120)     # Blue
        }
        return rank_colors.get(self.rank, (255, 255, 255))  # White as default
            
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


    def find_closest_enemy(self, radius):
        closest_enemy = None
        closest_distance = radius
        for enemy in self.level.enemies:
            distance = pygame.math.Vector2(enemy.rect.center).distance_to(pygame.math.Vector2(self.rect.center))
            if distance < closest_distance:
                closest_distance = distance
                closest_enemy = enemy
        return closest_enemy


    import random

    def cast_insect_swarm_spell(self, target):
        for _ in range(25):
            direction = pygame.math.Vector2(target.rect.center) - pygame.math.Vector2(self.rect.center)
            direction.normalize_ip()
            
            # Adiciona um deslocamento aleatório à posição inicial
            offset_x = random.randint(-20, 20)  # Ajuste o valor do deslocamento conforme necessário
            offset_y = random.randint(-20, 20)  # Ajuste o valor do deslocamento conforme necessário
            initial_position = (self.rect.centerx + offset_x, self.rect.centery + offset_y)
            
            InsectSwarm(initial_position, user=self, target=target, groups=[self.level.all_sprites, self.level.projectiles], level=self.level)


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


    def animate_death_step(self, dt, all_sprites, tiles):
        now = pygame.time.get_ticks()
        Tile('images/dead_human.png', (self.rect.x+60, self.rect.y+60), [all_sprites, tiles])
  
        self.kill()
        if now - self.death_start_time > self.current_death_frame * 15:
            self.death_start_time = now
            if self.current_death_frame < len(self.death_sprites[0]):
                self.image = self.death_sprites[0][self.current_death_frame]
                self.current_death_frame += 1

    def random_move(self, dt):
        now = pygame.time.get_ticks()

        # Verifica a distância do jogador
        player_pos = pygame.math.Vector2(self.level.player.rect.center)
        ally_pos = pygame.math.Vector2(self.rect.center)
        distance_to_player = ally_pos.distance_to(player_pos)

        if distance_to_player > 200:
            # Mover na direção do jogador
            direction_to_player = (player_pos - ally_pos).normalize()
            self.rect.x += direction_to_player.x * self.speed * dt
            self.rect.y += direction_to_player.y * self.speed * dt

            # Definir a ação com base na direção do movimento
            if abs(direction_to_player.x) > abs(direction_to_player.y):
                if direction_to_player.x > 0:
                    self.action = 'walk_right'
                    self.last_direction = 'right'
                else:
                    self.action = 'walk_left'
                    self.last_direction = 'left'
            else:
                if direction_to_player.y > 0:
                    self.action = 'down_walk'
                    self.last_direction = 'down'
                else:
                    self.action = 'up_walk'
                    self.last_direction = 'up'
        else:
            # Verifica se o tempo para a próxima ação aleatória chegou
            if now - self.random_move_timer > self.random_move_duration:
                self.random_move_timer = now
                self.random_move_duration = random.randint(500, 1000)  # Duração entre 0.8 e 1.2 segundos

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

            # Atualiza a posição do aliado baseado na direção escolhida
            self.rect.x += self.random_move_direction[0] * self.speed * dt
            self.rect.y += self.random_move_direction[1] * self.speed * dt
            self.action = self.random_move_action


    def move(self, dt):
        if self.target:
            direction_vector = pygame.math.Vector2(self.target.rect.center) - pygame.math.Vector2(self.rect.center)
            distance = direction_vector.length()
            if distance > 0:
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

    def can_see_target(self):
        if self.target is None:
            return False
        distance = pygame.math.Vector2(self.target.rect.center).distance_to(pygame.math.Vector2(self.rect.center))
        return distance <= self.vision_radius
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

    def perform_ninjutsu(self, jutsu, direction):
        print(f"{self.name} uses {jutsu['name']} ({jutsu['element']})!")
        target_pos = self.rect.center + direction * 200  # Adjust as needed
        
        if jutsu['name'] == 'Fireball Jutsu':
            FireballEffect(self.rect.center, [self.groups_list[0]], target_pos)
        elif jutsu['name'] == 'Phoenix Flower Jutsu':
            PhoenixFlowerEffect(self.rect.center, [self.groups_list[0]])
        elif jutsu['name'] == 'Water Bullet':
            WaterBulletEffect(self.rect.center, [self.groups_list[0]], target_pos)
        elif jutsu['name'] == 'Water Dragon Jutsu':
            WaterDragonEffect(self.rect.center, [self.groups_list[0]], target_pos)
        elif jutsu['name'] == 'Earth Wall':
            EarthWallEffect(self.rect.center, [self.level.all_sprites, self.level.collidable_tiles])
        elif jutsu['name'] == 'Chidori':
            ChidoriEffect(self.rect.center, [self.groups_list[0]])
        elif jutsu['name'] == 'Wind Blade':
            WindBladeEffect(self.rect.center, [self.groups_list[0]], target_pos)
        # Add more conditions for other jutsu as needed

    def perform_normal_attack(self, direction):
        projectile_type = random.choice(['kunai', 'shuriken', 'fuuma'] if self.rank in ['S', 'A', 'B'] else ['kunai', 'shuriken'])
        Projectile(self.rect.center, direction, [self.groups_list[0], self.projectile_group], 
                   projectile_type, self.level, self.throw_speed, side='player_projectile')

    def borderless(self, tile_size, map_width, map_height):
        if self.rect.right > map_width * tile_size:
            self.rect.left = 0
        elif self.rect.left < 0:
            self.rect.right = map_width * tile_size
        
        if self.rect.bottom > map_height * tile_size:
            self.rect.top = 0
        elif self.rect.top < 0:
            self.rect.bottom = map_height * tile_size

    def animate_death(self):
        self.death_start_time = pygame.time.get_ticks()
        self.current_death_frame = 0
        self.is_dying = True

    def take_damage(self, amount, all_sprites, tiles, knockback_direction, color=(220,44,0)):
        self.hp -= amount        
        self.vision_radius += 300
        FloatingText(str(amount), self.rect, color, self.level.camera, all_sprites)
        self.knockback_velocity = knockback_direction * 200
        self.is_knockedback = True
        self.knockback_start_time = pygame.time.get_ticks()
        self.level.spawn_blood(self.rect.center, amount=max(1, int(amount)))  # Add this line
        if self.hp <= 0:
            self.is_dying = True
            self.rect.size = (0, 0)
            self.animate_death_step(0, all_sprites, tiles)

    def draw(self, screen):
        #screen.blit(self.image, self.rect)
        self.floating_texts.draw(screen)
        self.draw_health_bar(screen)

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
        # Create an area attack around the ally
        for angle in range(0, 360, int(90 // self.multiplier)):  # Create projectiles in all directions
            direction = pygame.math.Vector2(1, 0).rotate(angle)
            Projectile(self.rect.center, direction, [self.groups_list[0], self.projectile_group], 'fuuma', self.level, self.throw_speed, side='player_projectile')
