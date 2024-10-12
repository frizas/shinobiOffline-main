import pygame
import random
from settings import weapon_data, drop_data

class ItemDrop(pygame.sprite.Sprite):
    def __init__(self, pos, groups):
        super().__init__(groups)
        self.item = random.choice(list(drop_data.keys()))
        self.image = pygame.image.load(drop_data[self.item]['graphic']).convert_alpha()
        self.rect = self.image.get_rect(center=pos)
        self.start_pos = pygame.math.Vector2(pos)
        self.bounce_height = 20  # Altura do quique
        self.bounce_speed = 30  # Velocidade do quique
        self.bounce_offset = 0
        self.bounce_direction = 1  # 1 para subir, -1 para descer

    def update(self, dt):
        self.bounce_offset += self.bounce_direction * self.bounce_speed * dt
        if self.bounce_offset > self.bounce_height:
            self.bounce_offset = self.bounce_height
            self.bounce_direction = -1
        elif self.bounce_offset < 0:
            self.bounce_offset = 0
            self.bounce_direction = 1
        self.rect.y = self.start_pos.y - self.bounce_offset
