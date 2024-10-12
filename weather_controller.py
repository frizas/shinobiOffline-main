import pygame
import random
from effects import Particle2, RainParticle

class WeatherController:
    def __init__(self, screen_width, screen_height, particle_group):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.particle_group = particle_group
        
        self.weather_types = ['sunny', 'snowy']
        self.current_weather = random.choice(self.weather_types)
        self.target_weather = self.current_weather
        
        self.wind_direction = pygame.math.Vector2(1, 0)
        self.wind_speed = random.uniform(1, 4)  # Start with some wind
        
        self.rain_intensity = 100 if self.current_weather == 'rainy' else 0
        self.snow_intensity = 0  # Start with 0 snow intensity
        
        self.weather_change_timer = 0
        self.weather_change_interval = 30000  # Change weather every 30 seconds
        self.transition_speed = 0.1  # Speed of transition between weather states
        
        self.rain_spawn_area = pygame.Rect(-100, -100, screen_width + 200, 100)
        self.snow_particles = []
        self.max_snow_particles = 400  # Maximum number of snow particles
        self.current_max_snow_particles = 0  # Current maximum, starts at 0
        self.snow_spawn_area = pygame.Rect(-50, -50, screen_width + 100, screen_height + 100)
        
        self.snow_accumulation = pygame.Surface((screen_width, screen_height), pygame.SRCALPHA)
        self.snow_accumulation.fill((0, 0, 0, 0))  # Transparent surface

    def update(self, dt):
        self.weather_change_timer += dt * 1000  # Convert to milliseconds
        if self.weather_change_timer >= self.weather_change_interval:
            self.change_weather()
            self.weather_change_timer = 0
        
        self.update_wind(dt)
        self.update_weather_state(dt)
        self.update_particles(dt)

    def change_weather(self):
        self.target_weather = random.choice(self.weather_types)
        self.wind_direction = pygame.math.Vector2(random.uniform(-0.5, 0.5), random.uniform(-0.2, 0.2)).normalize()
        self.wind_speed = random.uniform(0.5, 2)  # Ensure some wind is always present
        
        if self.target_weather == 'sunny':
            for particle in self.particle_group:
                particle.kill()
            self.snow_particles.clear()
            self.current_max_snow_particles = 0
        elif self.target_weather == 'snowy':
            self.current_max_snow_particles = 0  # Reset snow particles for a gradual increase
            if self.target_weather != 'snowy':
                self.clear_snow_accumulation()

    def update_weather_state(self, dt):
        target_rain_intensity = 100 if self.target_weather == 'rainy' else 0
        target_snow_intensity = 100 if self.target_weather == 'snowy' else 0
        
        self.rain_intensity += (target_rain_intensity - self.rain_intensity) * self.transition_speed * dt
        self.snow_intensity += (target_snow_intensity - self.snow_intensity) * self.transition_speed * dt
        
        if self.target_weather == 'snowy':
            self.current_max_snow_particles = int(self.max_snow_particles * (self.snow_intensity / 100))
        
        self.current_weather = self.target_weather
        
    def update_wind(self, dt):
        self.wind_direction.rotate_ip(random.uniform(-1, 1))
        self.wind_speed += random.uniform(-0.1, 0.1)
        self.wind_speed = max(0.5, min(self.wind_speed, 3))  # Clamp between 0.5 and 3
        
    def update_particles(self, dt):
        self.create_precipitation()
        
        for particle in self.particle_group:
            particle.update(dt)
            if isinstance(particle, RainParticle) and not particle.is_on_screen():
                particle.kill()
            elif isinstance(particle, Particle2) and not particle.is_on_screen():
                self.add_snow_accumulation(particle.rect.center)
                particle.kill()

    def create_precipitation(self):
        if self.current_weather == 'rainy':
            for _ in range(int(self.rain_intensity / 5)):
                pos = (random.randint(self.rain_spawn_area.left, self.rain_spawn_area.right),
                       random.randint(self.rain_spawn_area.top, self.rain_spawn_area.bottom))
                RainParticle(pos, [self.particle_group], self.screen_width, self.screen_height, 
                             lifespan=2000, wind_direction=self.wind_direction, wind_speed=self.wind_speed)
        elif self.current_weather == 'snowy':
            while len(self.snow_particles) < self.current_max_snow_particles:
                if random.choice([True, False]):
                    pos = (random.randint(self.snow_spawn_area.left, self.snow_spawn_area.right),
                           random.randint(self.snow_spawn_area.top, 0))
                else:
                    pos = (random.randint(self.snow_spawn_area.left, 0),
                           random.randint(self.snow_spawn_area.top, self.snow_spawn_area.bottom))
                snow_particle = Particle2(pos, [self.particle_group], (255, 255, 255, 200), 
                                          self.screen_width, self.screen_height,
                                          initial_size=2, lifespan=random.randint(5000, 8000), 
                                          wind_direction=self.wind_direction, wind_speed=self.wind_speed)
                self.snow_particles.append(snow_particle)

    def add_snow_accumulation(self, pos):
        pygame.draw.circle(self.snow_accumulation, (255, 255, 255, 20), pos, 3)  # Increased opacity and size

    def draw_snow_accumulation(self, surface, camera_offset):
        surface.blit(self.snow_accumulation, camera_offset)

    def clear_snow_accumulation(self):
        self.snow_accumulation.fill((0, 0, 0, 0))

    def get_wind_vector(self):
        return self.wind_direction * self.wind_speed

def create_weather_controller(screen_width, screen_height, particle_group):
    return WeatherController(screen_width, screen_height, particle_group)
