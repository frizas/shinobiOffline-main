import pygame

class Camera:
    def __init__(self, width, height, zoom=1):
        self.camera = pygame.Rect(0, 0, width, height)
        self.width = width
        self.height = height
        self.zoom = zoom
        self.target = None

    def apply(self, entity):
        if isinstance(entity, pygame.Rect):
            return entity.move(self.camera.topleft)
        return entity.rect.move(self.camera.topleft)
    
    def update(self, target):
        self.target = target
        if self.target:
            self.camera = self.get_target_camera_rect(target)

    def get_target_camera_rect(self, target):
        l, t, _, _ = target.rect
        _, _, w, h = self.camera
        return pygame.Rect(-l + int(self.width / 2), -t + int(self.height / 2), w, h)

    def apply_rect(self, rect):
        return rect.move(self.camera.topleft)

    def get_visible_rect(self):
        # Return the rectangle representing the visible area in world coordinates
        return pygame.Rect(-self.camera.x, -self.camera.y, self.width, self.height)