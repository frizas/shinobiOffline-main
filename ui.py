import pygame

class UIBar:
    def __init__(self, x, y, width, height, max_value, color):
        self.rect = pygame.Rect(x, y, width, height)
        self.max_value = max_value
        self.current_value = max_value
        self.color = color

    def update(self, current_value):
        self.current_value = current_value

    def draw(self, screen):
        pygame.draw.rect(screen, (255, 255, 255), self.rect, 1)  # Desenhar a borda branca
        inner_rect = self.rect.copy()
        inner_rect.width = int(self.rect.width * (self.current_value / self.max_value))
        pygame.draw.rect(screen, self.color, inner_rect)
class InventorySlot:
    def __init__(self, x, y, width, height):
        self.rect = pygame.Rect(x, y, width, height)
        self.item = None

    def set_item(self, item):
        self.item = item

    def draw(self, screen):
      #  pygame.draw.rect(screen, (255, 255, 255), self.rect, 2)
        if self.item:
            item_image = pygame.image.load(self.item['graphic']).convert_alpha()
            item_image = pygame.transform.scale(item_image, (self.rect.width, self.rect.height))
            screen.blit(item_image, self.rect.topleft)
