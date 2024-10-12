import pygame
from settings import *

class Tile(pygame.sprite.Sprite):
    def __init__(self, image_path, pos, groups, collidable=False, rect_size=None, tile_type="default", effects=None):
        super().__init__(*groups)
        self.image = pygame.image.load(image_path).convert_alpha()
        self.rect = self.image.get_rect(bottomright=pos)
        self.collidable = collidable
        self.tile_type = tile_type
        self.effects = effects if effects is not None else []
        self.image_path = image_path
        self.mask = pygame.mask.from_surface(self.image)
        self.pos = pos*32

        
        

    def add_effect(self, effect):
        """Adiciona um efeito ao tile."""
        self.effects.append(effect)

    def remove_effect(self, effect):
        """Remove um efeito do tile."""
        if effect in self.effects:
            self.effects.remove(effect)

    def trigger_effects(self, entity):
        """Dispara todos os efeitos no tile para uma entidade."""
        for effect in self.effects:
            effect.apply(entity)

    def update(self, *args):
        """Atualizações específicas do tile, como animações ou interações."""
        pass

class Effect:
    """Classe base para efeitos que podem ser aplicados a tiles."""
    def __init__(self, name, duration):
        self.name = name
        self.duration = duration

    def apply(self, entity):
        """Aplica o efeito a uma entidade."""
        pass

class SlowEffect(Effect):
    """Efeito que reduz a velocidade da entidade."""
    def __init__(self, duration, slow_amount):
        super().__init__("Slow", duration)
        self.slow_amount = slow_amount

    def apply(self, entity):
        entity.speed -= self.slow_amount

class DamageEffect(Effect):
    """Efeito que causa dano à entidade."""
    def __init__(self, duration, damage_amount):
        super().__init__("Damage", duration)
        self.damage_amount = damage_amount

    def apply(self, entity):
        entity.take_damage(self.damage_amount, pygame.math.Vector2(0, 0))  # Sem knockback
