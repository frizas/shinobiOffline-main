import pygame
from settings import *
import math
from effects import *
class Projectile(pygame.sprite.Sprite):
    def __init__(self, pos, direction, groups, projectile_type, level, throw_speed=1, side=None, from_collision=False):
        super().__init__(groups)
        self.image = pygame.image.load(weapon_data[projectile_type]['graphic']).convert_alpha()
        self.rect = self.image.get_rect(center=pos)
        self.direction = direction
        self.speed = weapon_data[projectile_type]['speed'] * throw_speed
        self.damage = weapon_data[projectile_type]['damage']
        self.level = level
        self.side = side
        self.from_collision = from_collision  # Novo sinalizador para verificar se foi criado a partir de uma colisão
        self.mask = pygame.mask.from_surface(self.image)

        self.original_image = self.image  # Guardar a imagem original
        self.type = projectile_type
        self.explosion_damage = 35
        self.explosion_radius = 100
        self.explosion_effect = Explosion
        self.is_indestructible = weapon_data[projectile_type].get('indestructible')  # Adiciona esta linha
        self.rotating = weapon_data[projectile_type].get('rotating')
        self.rotation_angle = 0
        if not self.rotating:
            self.set_fixed_angle()
        print("Created projectile " + side)

    def set_fixed_angle(self):
        angle = math.degrees(math.atan2(-self.direction.y, self.direction.x))  # Calcular o ângulo em graus
        self.image = pygame.transform.rotate(self.original_image, angle)
        self.rect = self.image.get_rect(center=self.rect.center)

    def check_bounds(self):
        if self.rect.right < -160 or self.rect.left > ((self.level.grid_width * 32)+160) or \
           self.rect.bottom < -160 or self.rect.top > ((self.level.grid_height * 32)+160):
            self.kill()

    def update(self, dt):
        self.rect.x += self.direction.x * self.speed * dt
        self.rect.y += self.direction.y * self.speed * dt

        if self.type == 'fireball':
            self.fireball_collision_with_enemies()

        if self.rotating:
            self.rotation_angle += 14  # Ajuste a velocidade de rotação conforme necessário
            self.image = pygame.transform.rotate(pygame.image.load(weapon_data[self.type]['graphic']).convert_alpha(), self.rotation_angle)
            self.rect = self.image.get_rect(center=self.rect.center)
        else:
            self.set_fixed_angle()
        self.check_bounds()
        # Criar partículas de rastro
        if self.type == 'fireball':
            ParticleTrail(self.rect.center, [self.level.all_sprites], color=(250, 150, 0), initial_size=25, lifespan=400)
        elif self.type =='poison_kunai':
            ParticleTrail(self.rect.center, [self.level.all_sprites], color=(200, 0, 200), initial_size=8, lifespan=800)
        elif self.type =='fuuma':
            ParticleTrail(self.rect.center, [self.level.all_sprites], color=(100, 100, 100), initial_size=10, lifespan=600)

        else:
            ParticleTrail(self.rect.center, [self.level.all_sprites], color=(100, 100, 100), initial_size=5, lifespan=500)

    def fireball_collision_with_enemies(self): 
        # Verifica colisão com troncos
        if pygame.sprite.spritecollideany(self, self.level.trunk, pygame.sprite.collide_mask):
            self.create_explosion()
            self.kill()
            FireEmitter(self.rect.topleft, [self.level.all_sprites, self.level.top_sprites], 55, 20000, 300)
            return

        # Verifica colisão com o jogador
        if self.side == 'enemy_projectile':
            if pygame.sprite.spritecollideany(self, [self.level.player], pygame.sprite.collide_mask):
                if not self.level.player.is_jumping:
                    self.create_explosion()
                    self.level.player.take_damage(self.damage, pygame.math.Vector2(0, 0), (255, 120, 0))
                    self.kill()
                elif self.level.player.is_performing_special_attack:
                    return
                else: 
                    return

        # Verifica colisão com aliados
       
        if pygame.sprite.collide_rect(self, self.level.Ally):
            if self.side == 'enemy_projectile':
                self.create_explosion()
                self.level.Ally.take_damage(self.damage,self.level.all_sprites,self.level.tiles,self.direction)
                self.kill()
            else:
                return  

        # Verifica colisão com EarthWall
        earth_walls = [sprite for sprite in self.level.all_sprites if isinstance(sprite, EarthWallEffect)]
        for wall in earth_walls:
            if pygame.sprite.collide_rect(self, wall):
                if self.type == 'fireball':
                    self.create_explosion()
                else:
                    Spark(self.rect.center, [self.level.all_sprites, self.level.overlay_sprites])
                    self.level.play_random_spark_sound()
                self.kill()
                return

        # Verifica colisão com inimigos
        hits = pygame.sprite.spritecollide(self, self.level.enemies, False, pygame.sprite.collide_mask)
        for enemy in hits:
            if self.side == 'enemy_projectile':
                continue
            self.create_explosion()
            enemy.take_damage(self.damage, self.level.all_sprites, self.level.tiles, (255, 120, 0), self.direction)
            self.kill()
            return



    def create_explosion(self):
        explosion = self.explosion_effect(self.rect.center, [self.level.all_sprites])
        for enemy in self.level.enemies:
            if self.side == 'player_projectile':
                distance = pygame.math.Vector2(self.rect.center).distance_to(enemy.rect.center)
                if distance <= self.explosion_radius:
                    enemy.take_damage(self.explosion_damage, self.level.all_sprites, self.level.tiles, (255, 100, 0), self.direction)
                    SmokeEmitter(self.rect.center,groups=[self.level.all_sprites], color=(200,130,100),initial_size=7)
                    self.create_particles()
                    FireEmitter(self.rect.center,groups=[self.level.all_sprites])
                    FireWork(self.rect.center,groups=[self.level.all_sprites])
        if self.side == 'enemy_projectile':
            distance_to_player = pygame.math.Vector2(self.rect.center).distance_to(self.level.player.rect.center)
            if distance_to_player <= self.explosion_radius:
                self.level.player.take_damage(self.explosion_damage, pygame.math.Vector2(0, 0), (255, 100, 0))
                SmokeEmitter(self.rect.center,groups=[self.level.all_sprites], color=(200,130,100),initial_size=10)
                self.create_particles()
                FireEmitter(self.rect.center,groups=[self.level.all_sprites])
                FireWork(self.rect.center,groups=[self.level.all_sprites])
    def create_particles(self):
        for _ in range(11):  # Cria 10 partículas
            Particle(
                pos=self.rect.center,
                groups=[self.level.all_sprites],
                color=(255, 160, 0),  # Vermelho
                initial_size=30,
                lifespan=1400
            )

# Adicione essa função ao seu arquivo de nível (level.py)
def check_collisions(self):
    # Verificar colisão do player com inimigos
    self.check_player_enemy_collisions()
    # Verificar colisão de projéteis
    self.check_projectile_collisions()
    # Verificar colisão de projéteis com o jogador
    self.check_projectile_player_collisions()

# Adicione essa função ao seu arquivo de nível (level.py)
def check_projectile_player_collisions(self):
    for projectile in self.projectiles:
        if isinstance(projectile, Projectile) and projectile.side == 'enemy_projectile':
            if pygame.sprite.collide_rect(projectile, self.player):
                if not self.player.is_jumping:
                    self.player.take_damage(projectile.damage, pygame.math.Vector2(0, 0), (255, 0, 0))
                projectile.kill()
        if isinstance(projectile, Projectile) and projectile.side == 'player_projectile':
            if pygame.sprite.collide_rect(projectile, self.enemy):
                self.enemy.take_damage(projectile.damage, pygame.math.Vector2(0, 0), (255, 0, 0))
                projectile.kill()
