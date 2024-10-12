import pygame

class FloatingText(pygame.sprite.Sprite):
    def __init__(self, text, target_rect, color, camera, groups, duration=1, speed=30):
        super().__init__(groups)
        self.text = text
        self.color = color
        self.camera = camera
        self.image = self.create_image(text, color)
        if isinstance(target_rect, pygame.Rect):
            self.rect = self.image.get_rect(midbottom=target_rect.midtop)
        else:
            raise TypeError("target_rect must be a pygame.Rect instance")
        self.duration = duration
        self.speed = speed
        self.start_time = pygame.time.get_ticks()

    def create_image(self, text, color):
        font = pygame.font.Font('freesansbold.ttf', 14)  # Use uma fonte diferente aqui
        text_surface = font.render(text, True, color)
        
        # Create outline
        outline_color = (0, 0, 0)
        outline_surface = pygame.Surface((text_surface.get_width() + 2, text_surface.get_height() + 2), pygame.SRCALPHA)
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                if dx != 0 or dy != 0:
                    outline_surface.blit(font.render(text, True, outline_color), (dx + 1, dy + 1))
        outline_surface.blit(text_surface, (1, 1))
        
        return outline_surface

    def update(self, dt):
        
        now = pygame.time.get_ticks()
        elapsed_time = (now - self.start_time) / 1000
        if elapsed_time < self.duration:
            self.rect.y -= self.speed * dt
        else:
            self.kill()

    def draw(self, screen):
        screen.blit(self.image, self.camera.apply(self))
