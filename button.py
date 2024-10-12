import pygame

class Button:
    def __init__(self, x, y, width, height, text, color_scheme='blue'):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.color_scheme = color_scheme
        self.font = pygame.font.Font(None, 32)
        
        self.color_schemes = {
            'blue': {
                'normal': '#3498db',
                'hover': '#2980b9',
                'text': '#ffffff'
            },
            'green': {
                'normal': '#2ecc71',
                'hover': '#27ae60',
                'text': '#ffffff'
            },
            'red': {
                'normal': '#e74c3c',
                'hover': '#c0392b',
                'text': '#ffffff'
            },
            'gold': {
                'normal': '#f1c40f',
                'hover': '#f39c12',
                'text': '#ffffff'
            }
        }
        
    def draw(self, surface):
        color = self.color_schemes[self.color_scheme]['normal']
        if self.is_hovered():
            color = self.color_schemes[self.color_scheme]['hover']
        
        pygame.draw.rect(surface, color, self.rect, border_radius=10)
        pygame.draw.rect(surface, self.color_schemes[self.color_scheme]['text'], self.rect, 2, border_radius=10)
        
        text_surf = self.font.render(self.text, True, self.color_schemes[self.color_scheme]['text'])
        text_rect = text_surf.get_rect(center=self.rect.center)
        surface.blit(text_surf, text_rect)
        
    def is_clicked(self, pos):
        return self.rect.collidepoint(pos)
    
    def is_hovered(self):
        return self.rect.collidepoint(pygame.mouse.get_pos())
