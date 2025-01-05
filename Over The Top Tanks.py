import pygame
import math
import random
import os
import sys

def resource_path(relative_path):
    """Krijg het pad naar een resource, werkt voor zowel ontwikkeling als bij een gebundelde .exe"""
    try:
        # Bij PyInstaller gebundelde .exe
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

# Initialize Pygame
pygame.init()

# Initialize the mixer module
pygame.mixer.init()

# Screen settings
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Over The Top Tanks")

# Load the game icon
try:
    GAME_ICON = pygame.image.load(resource_path(os.path.join("gfx", "tanks.png"))).convert_alpha()
    pygame.display.set_icon(GAME_ICON)
except Exception as e:
    print(f"Could not load tanks.png image. Exception: {e}")
    pygame.quit()
    sys.exit()

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREEN = (34, 139, 34)  # A darker green for better visuals
RED = (255, 0, 0)
BLUE = (0, 0, 255)
GRAY = (200, 200, 200)
TRANSPARENT_BLACK = (0, 0, 0, 128)

# Load heart icon for health points
try:
    HEART_ICON = pygame.image.load(resource_path(os.path.join("gfx", "heart.png"))).convert_alpha()
    HEART_ICON = pygame.transform.scale(HEART_ICON, (20, 20))
except Exception as e:
    print(f"Could not load heart.png image. Exception: {e}")
    pygame.quit()
    sys.exit()

# Load tank sprites
try:
    RED_TANK_IMAGE = pygame.image.load(resource_path(os.path.join("gfx", "tank1.png"))).convert_alpha()
    BLUE_TANK_IMAGE = pygame.image.load(resource_path(os.path.join("gfx", "tank2.png"))).convert_alpha()
    RED_TANK_IMAGE = pygame.transform.scale(RED_TANK_IMAGE, (50, 30))
    BLUE_TANK_IMAGE = pygame.transform.scale(BLUE_TANK_IMAGE, (50, 30))
except Exception as e:
    print(f"Could not load tank images. Exception: {e}")
    pygame.quit()
    sys.exit()

# Load sound effects
try:
    shoot_sound = pygame.mixer.Sound(resource_path(os.path.join("sounds", "shoot.wav")))
    explosion_sound = pygame.mixer.Sound(resource_path(os.path.join("sounds", "explosion.wav")))
    moving_cannon_sound = pygame.mixer.Sound(resource_path(os.path.join("sounds", "movingcanon.wav")))
    wind_sound = pygame.mixer.Sound(resource_path(os.path.join("sounds", "wind.wav")))
    wind_sound.set_volume(1.0)  # Set wind sound volume to maximum
except Exception as e:
    print(f"Could not load sound effects. Exception: {e}")
    pygame.quit()
    sys.exit()

# Get dedicated channels for sounds
moving_cannon_channel = pygame.mixer.Channel(5)  # Using channel 5 arbitrarily
wind_sound_channel = pygame.mixer.Channel(6)  # Dedicated channel for wind sound

# Tank class
class Tank:
    def __init__(self, x, color, image):
        self.x = x
        self.color = color
        self.image = image
        self.power = 30  # Starting power adjusted to new max
        self.angle = 45
        self.health = 3  # Tanks can be hit three times
        self.y = 0  # Will be set based on ground height

    def draw(self, screen):
        # Draw the tank image
        screen.blit(self.image, (self.x - 25, self.y - 15))
        # Draw the cannon
        pygame.draw.line(
            screen,
            self.color,
            (self.x, self.y - 10),
            (
                self.x + math.cos(math.radians(self.angle)) * 30,
                self.y - 10 - math.sin(math.radians(self.angle)) * 30,
            ),
            3,
        )
        # Health icons are drawn separately

    def aim(self, delta_angle):
        self.angle += delta_angle
        self.angle = max(0, min(180, self.angle))

    def change_power(self, delta_power):
        self.power += delta_power
        self.power = max(10, min(70, self.power))  # Adjusted max power to 70

    def shoot(self):
        radian_angle = math.radians(self.angle)
        velocity_x = math.cos(radian_angle) * self.power
        velocity_y = -math.sin(radian_angle) * self.power
        return Projectile(self.x, self.y - 10, velocity_x, velocity_y)

    def is_hit(self, projectile):
        if projectile is None:
            return False
        return (
            self.x - 25 < projectile.x < self.x + 25
            and self.y - 15 < projectile.y < self.y + 15
        )

# Projectile class
class Projectile:
    def __init__(self, x, y, velocity_x, velocity_y):
        self.x = x
        self.y = y
        self.velocity_x = velocity_x
        self.velocity_y = velocity_y
        self.gravity = 0.5
        self.wind_resistance = 0.99  # Wind resistance to simulate more realistic physics
        self.active = True

    def move(self, wind):
        if self.active:
            self.velocity_x += wind  # Apply wind as a constant force
            self.x += self.velocity_x
            self.y += self.velocity_y
            self.velocity_y += self.gravity
            self.velocity_x *= self.wind_resistance  # Reduce speed due to air resistance
            self.velocity_y *= self.wind_resistance

            # Mark the projectile as inactive if it goes off-screen
            if self.x < 0 or self.x > WIDTH or self.y > HEIGHT:
                self.active = False

    def draw(self, screen):
        if (
            self.active
            and 0 <= self.x <= WIDTH
            and 0 <= self.y <= HEIGHT
        ):  # Draw only if within the screen
            pygame.draw.circle(screen, RED, (int(self.x), int(self.y)), 5)

# Explosion class
class Explosion:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.max_radius = 50
        self.current_radius = 0
        self.growth_rate = 5
        self.alpha = 255
        self.active = True

    def update(self):
        if self.current_radius < self.max_radius:
            self.current_radius += self.growth_rate
            self.alpha -= 255 / (self.max_radius / self.growth_rate)
        else:
            self.active = False

    def draw(self, screen):
        if self.active:
            # Create a surface with per-pixel alpha
            explosion_surface = pygame.Surface(
                (self.max_radius * 2, self.max_radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(
                explosion_surface,
                (255, 165, 0, int(self.alpha)),  # Orange color with fading alpha
                (self.max_radius, self.max_radius),
                int(self.current_radius)
            )
            # Blit the explosion surface onto the screen
            screen.blit(explosion_surface, (self.x - self.max_radius,
                                            self.y - self.max_radius))

# Function to draw stars for parallax background
def draw_stars(stars):
    for star in stars:
        pygame.draw.circle(screen, WHITE, (int(star[0]), int(star[1])), 2)
        star[0] -= star[2]  # Movement of stars to the left
        if star[0] < 0:
            star[0] = WIDTH
            star[1] = random.randint(0, HEIGHT)

# Function to draw the ground
def draw_ground(ground):
    for x in range(WIDTH):
        pygame.draw.line(screen, GREEN, (x, HEIGHT), (x, HEIGHT - ground[x]))

# Function to draw the health icons
def draw_health_icons(tank1, tank2):
    # Red tank health at top left
    for i in range(tank1.health):
        screen.blit(HEART_ICON, (10 + i * 25, 10))

    # Blue tank health at top right
    for i in range(tank2.health):
        screen.blit(HEART_ICON, (WIDTH - (i + 1) * 25 - 10, 10))

# Function to draw a rounded rectangle
def draw_rounded_rect(surface, color, rect, radius):
    x, y, w, h = rect
    pygame.draw.rect(surface, color, (x + radius, y, w - 2 * radius, h))
    pygame.draw.rect(surface, color, (x, y + radius, w, h - 2 * radius))
    pygame.draw.circle(surface, color, (x + radius, y + radius), radius)
    pygame.draw.circle(surface, color, (x + w - radius, y + radius), radius)
    pygame.draw.circle(surface, color, (x + radius, y + h - radius), radius)
    pygame.draw.circle(surface, color, (x + w - radius, y + h - radius), radius)

# Function to draw the main menu
def draw_main_menu(stars):
    screen.fill(BLACK)
    draw_stars(stars)
    font = pygame.font.Font(None, 74)
    title_text = font.render("Over The Top Tanks", True, WHITE)
    screen.blit(title_text, (WIDTH // 2 - title_text.get_width() // 2,
                             HEIGHT // 4))

    font = pygame.font.Font(None, 36)
    play_text = font.render("1. Play Game", True, WHITE)
    instructions_text = font.render("2. Instructions", True, WHITE)
    credits_text = font.render("3. Credits", True, WHITE)
    quit_text = font.render("4. Quit", True, WHITE)
    screen.blit(play_text, (WIDTH // 2 - play_text.get_width() // 2,
                            HEIGHT // 2))
    screen.blit(instructions_text, (WIDTH // 2 - instructions_text.get_width()
                                    // 2, HEIGHT // 2 + 50))
    screen.blit(credits_text, (WIDTH // 2 - credits_text.get_width() // 2,
                               HEIGHT // 2 + 100))
    screen.blit(quit_text, (WIDTH // 2 - quit_text.get_width() // 2,
                            HEIGHT // 2 + 150))

    pygame.display.flip()

# Function to draw the instructions
def draw_instructions(stars):
    running = True
    clock = pygame.time.Clock()
    while running:
        screen.fill(BLACK)
        draw_stars(stars)

        # Create a semi-transparent surface
        instructions_surface = pygame.Surface(
            (int(WIDTH * 0.9), int(HEIGHT * 0.9)), pygame.SRCALPHA)

        # Set transparency (alpha)
        transparency = int(255)  # 30% opacity
        instructions_surface.set_alpha(transparency)

        # Draw rounded rectangle background
        rect = instructions_surface.get_rect()
        rect.center = (WIDTH // 2, HEIGHT // 2)
        draw_rounded_rect(
            instructions_surface,
            (50, 50, 50, transparency),
            (0, 0, rect.width, rect.height),
            20
        )

        # Render text onto the instructions surface
        font = pygame.font.Font(None, 36)
        instructions = [
            "Instructions:",
            "- Left/Right Arrow: Aim the cannon",
            "- Up/Down Arrow: Adjust power",
            "- Space: Shoot",
            "- ESC: Pause the game",
            "- M: Mute/Unmute music",
            "- Wind affects the projectile's path",
            "- Each tank has 3 health points.",
            "",
            "Hit any key to go back!"
        ]
        for i, line in enumerate(instructions):
            text = font.render(line, True, WHITE)
            instructions_surface.blit(
                text,
                (rect.width // 2 - text.get_width() // 2, 80 + i * 40)
            )

        # Blit the instructions surface onto the main screen
        screen.blit(instructions_surface, rect.topleft)

        pygame.display.flip()
        clock.tick(60)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                running = False

# Function to draw the credits screen
def draw_credits(stars):
    running = True
    clock = pygame.time.Clock()
    while running:
        screen.fill(BLACK)
        draw_stars(stars)
        font_title = pygame.font.Font(None, 74)
        credits_title = font_title.render("Credits", True, WHITE)
        screen.blit(credits_title, (WIDTH // 2 - credits_title.get_width()
                                    // 2, HEIGHT // 4))

        font = pygame.font.Font(None, 36)
        name_text = font.render("Pascal Mariany", True, WHITE)
        website_text = font.render("www.pascalmariany.com", True, WHITE)
        screen.blit(name_text, (WIDTH // 2 - name_text.get_width() // 2,
                                HEIGHT // 2))
        screen.blit(website_text, (WIDTH // 2 - website_text.get_width() // 2,
                                   HEIGHT // 2 + 40))

        prompt_text = font.render("Press any key to return", True, WHITE)
        screen.blit(prompt_text, (WIDTH // 2 - prompt_text.get_width() // 2,
                                  HEIGHT - 100))

        pygame.display.flip()
        clock.tick(60)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                running = False

# Function to generate terrain with multiple peaks
def generate_terrain(width):
    # Start with a flat ground
    ground = [20 for _ in range(width)]

    # Determine the number of peaks (excluding start and end points)
    num_peaks = random.randint(3, 6)

    # Generate random peak positions and heights
    # Ensure peaks are not at the very edges
    peak_positions = sorted(random.sample(range(1, width - 1), num_peaks - 2))
    peak_positions = [0] + peak_positions + [width - 1]
    peak_heights = [20] + [random.randint(100, 400) for _ in
                           range(num_peaks - 2)] + [20]

    # Generate terrain heights using interpolation
    for i in range(len(peak_positions) - 1):
        start_x = peak_positions[i]
        end_x = peak_positions[i + 1]
        start_height = peak_heights[i]
        end_height = peak_heights[i + 1]
        for x in range(start_x, end_x):
            fraction = (x - start_x) / (end_x - start_x)
            # Use cosine interpolation for smooth curves
            fraction = (1 - math.cos(fraction * math.pi)) / 2
            ground[x] = start_height * (1 - fraction) + end_height * fraction

    # Ensure the last point is set correctly
    ground[width - 1] = 20

    # Apply smoothing
    ground = smooth_ground(ground, smoothing_passes=3)

    return ground

# Function to smooth the ground
def smooth_ground(ground, smoothing_passes=1):
    for _ in range(smoothing_passes):
        new_ground = ground.copy()
        for x in range(1, len(ground) - 1):
            new_ground[x] = (ground[x - 1] + ground[x] + ground[x + 1]) / 3
        ground = new_ground
    return ground

# Function to draw the difficulty selection menu
def draw_difficulty_menu(stars):
    running = True
    clock = pygame.time.Clock()
    while running:
        screen.fill(BLACK)
        draw_stars(stars)
        font = pygame.font.Font(None, 74)
        difficulty_text = font.render("Select Difficulty", True, WHITE)
        screen.blit(difficulty_text, (WIDTH // 2 - difficulty_text.get_width()
                                      // 2, HEIGHT // 4))

        font = pygame.font.Font(None, 36)
        easy_text = font.render("1. Easy (No Wind)", True, WHITE)
        medium_text = font.render("2. Medium (Weak Wind)", True, WHITE)
        hard_text = font.render("3. Hard (Strong Wind)", True, WHITE)
        screen.blit(easy_text, (WIDTH // 2 - easy_text.get_width() // 2,
                                HEIGHT // 2))
        screen.blit(medium_text, (WIDTH // 2 - medium_text.get_width() // 2,
                                  HEIGHT // 2 + 50))
        screen.blit(hard_text, (WIDTH // 2 - hard_text.get_width() // 2,
                                HEIGHT // 2 + 100))

        pygame.display.flip()
        clock.tick(60)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_1:
                    return "easy"
                elif event.key == pygame.K_2:
                    return "medium"
                elif event.key == pygame.K_3:
                    return "hard"

# Function to draw the pause menu
def draw_pause_menu(stars):
    running = True
    clock = pygame.time.Clock()
    while running:
        screen.fill(BLACK)
        draw_stars(stars)
        font = pygame.font.Font(None, 74)
        pause_text = font.render("Paused", True, WHITE)
        screen.blit(pause_text, (WIDTH // 2 - pause_text.get_width() // 2,
                                 HEIGHT // 4))

        font = pygame.font.Font(None, 36)
        continue_text = font.render("1. Continue", True, WHITE)
        main_menu_text = font.render("2. Main Menu", True, WHITE)
        quit_text = font.render("3. Quit", True, WHITE)
        screen.blit(continue_text, (WIDTH // 2 - continue_text.get_width() // 2,
                                    HEIGHT // 2))
        screen.blit(main_menu_text, (WIDTH // 2 - main_menu_text.get_width()
                                     // 2, HEIGHT // 2 + 50))
        screen.blit(quit_text, (WIDTH // 2 - quit_text.get_width() // 2,
                                HEIGHT // 2 + 100))

        pygame.display.flip()
        clock.tick(60)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_1:
                    return "continue"
                elif event.key == pygame.K_2:
                    return "main_menu"
                elif event.key == pygame.K_3:
                    pygame.quit()
                    sys.exit()

# Function to wait for a key press
def wait_for_key():
    waiting = True
    while waiting:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                waiting = False

# Function to draw the game over screen
def draw_game_over(winner_color):
    screen.fill(BLACK)
    font = pygame.font.Font(None, 74)
    game_over_text = font.render("Game Over", True, WHITE)
    winner_text = font.render(f"{winner_color} Tank Wins!",
                              True, RED if winner_color == "Red" else BLUE)
    screen.blit(game_over_text, (WIDTH // 2 - game_over_text.get_width() // 2,
                                 HEIGHT // 4))
    screen.blit(winner_text, (WIDTH // 2 - winner_text.get_width() // 2,
                              HEIGHT // 4 + 80))

    font = pygame.font.Font(None, 36)
    rematch_text = font.render("1. Rematch", True, WHITE)
    quit_text = font.render("2. Quit", True, WHITE)
    screen.blit(rematch_text, (WIDTH // 2 - rematch_text.get_width() // 2,
                               HEIGHT // 2))
    screen.blit(quit_text, (WIDTH // 2 - quit_text.get_width() // 2,
                            HEIGHT // 2 + 50))

    pygame.display.flip()
    choice = wait_for_game_over_choice()
    return choice

# Function to wait for the user's choice on the game over screen
def wait_for_game_over_choice():
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_1:
                    return "rematch"
                elif event.key == pygame.K_2:
                    return "quit"

# Function to draw an animated arrow above the current tank
def draw_animated_arrow(tank, offset):
    x = tank.x
    y = tank.y - 50 + offset  # Move the arrow higher above the tank
    # Points adjusted to flip the arrow vertically
    points = [(x, y + 20), (x - 10, y), (x + 10, y)]
    pygame.draw.polygon(screen, WHITE, points)

# Main game function
def main():
    while True:
        # Generate the terrain
        ground = generate_terrain(WIDTH)

        stars = [
            [
                random.randint(0, WIDTH),
                random.randint(0, HEIGHT),
                random.uniform(0.2, 0.5),
            ]
            for _ in range(100)
        ]
        clock = pygame.time.Clock()

        # Load and play main menu music
        try:
            pygame.mixer.music.load(os.path.join("music", "mainmenu.ogg"))
            pygame.mixer.music.play(-1)
            pygame.mixer.music.set_volume(0.5)
        except Exception as e:
            print(f"Could not load main menu music. Exception: {e}")
            pygame.quit()
            sys.exit()

        running = True
        in_menu = True

        while in_menu:
            draw_main_menu(stars)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_1:
                        # Display the difficulty selection menu
                        difficulty = draw_difficulty_menu(stars)
                        in_menu = False
                        # Load and play game music
                        try:
                            pygame.mixer.music.load(
                                os.path.join("music", "firefight.ogg"))
                            pygame.mixer.music.play(-1)
                            pygame.mixer.music.set_volume(0.5)
                        except Exception as e:
                            print(f"Could not load game music. Exception: {e}")
                            pygame.quit()
                            sys.exit()
                    elif event.key == pygame.K_2:
                        draw_instructions(stars)
                    elif event.key == pygame.K_3:
                        draw_credits(stars)
                    elif event.key == pygame.K_4:
                        running = False
                        pygame.quit()
                        sys.exit()

        # Initialize tanks and game variables
        tank1 = Tank(100, RED, RED_TANK_IMAGE)
        tank2 = Tank(700, BLUE, BLUE_TANK_IMAGE)
        current_tank = tank1

        projectile = None
        # Initialize wind based on difficulty
        if difficulty == "easy":
            wind = 0  # No wind
        elif difficulty == "medium":
            wind = random.uniform(-1, 1)  # Weak wind
        else:
            wind = random.uniform(-2, 2)  # Strong wind

        turn_counter = 0
        shot_fired = False
        turn_start_time = pygame.time.get_ticks()  # Initialize turn start time

        font = pygame.font.Font(None, 24)

        # Initialize explosions list
        explosions = []

        # Arrow animation variables
        arrow_offset = 0
        arrow_direction = 1
        arrow_speed = 0.5
        max_offset = 5

        # Function to handle the end of a turn
        def end_turn():
            nonlocal current_tank, turn_counter, shot_fired, projectile, wind, turn_start_time
            current_tank = tank2 if current_tank == tank1 else tank1
            turn_counter += 1
            projectile = None
            shot_fired = False
            turn_start_time = pygame.time.get_ticks()  # Reset turn start time

            previous_wind = wind  # Store the previous wind value

            if difficulty == "easy":
                wind = 0  # Wind remains zero
            elif turn_counter % 3 == 0:
                if difficulty == "medium":
                    wind = random.uniform(-1, 1)  # Weak wind
                else:
                    wind = random.uniform(-2, 2)  # Strong wind

            # If the wind has changed, play the wind sound
            if wind != previous_wind:
                # Add a slight delay to ensure the sound plays fully
                pygame.time.delay(100)
                wind_sound_channel.play(wind_sound)

        # Main game loop
        game_over = False
        while running and not game_over:
            screen.fill(BLACK)
            draw_stars(stars)
            draw_ground(ground)

            # Update tanks' positions based on ground height
            tank1.y = HEIGHT - ground[int(tank1.x)]
            tank2.y = HEIGHT - ground[int(tank2.x)]

            tank1.draw(screen)
            tank2.draw(screen)

            draw_health_icons(tank1, tank2)  # Draw health icons

            # Update arrow animation only if less than 3 seconds have passed
            if (pygame.time.get_ticks() - turn_start_time) < 3000:
                # Update arrow animation
                arrow_offset += arrow_direction * arrow_speed
                if arrow_offset > max_offset or arrow_offset < -max_offset:
                    arrow_direction *= -1

                # Draw animated arrow above the current tank
                draw_animated_arrow(current_tank, arrow_offset)

            if projectile and projectile.active:
                projectile.move(wind)
                projectile.draw(screen)

                # Check if the projectile hits the ground
                if 0 <= int(projectile.x) < WIDTH:
                    if projectile.y >= HEIGHT - ground[int(projectile.x)]:
                        # Play explosion sound
                        explosion_sound.play()

                        # Create explosion
                        explosion = Explosion(projectile.x, projectile.y)
                        explosions.append(explosion)

                        # Create crater
                        crater_radius = 15
                        for i in range(
                            int(projectile.x) - crater_radius,
                            int(projectile.x) + crater_radius,
                        ):
                            if 0 <= i < WIDTH:
                                distance = abs(i - projectile.x)
                                if distance <= crater_radius:
                                    depth = ((crater_radius - distance)
                                             ** 0.5) * 5
                                    ground[i] = max(0, ground[i] - int(depth))
                        projectile.active = False
                        end_turn()  # Switch turns

                # Check if the other tank is hit
                if tank1.is_hit(projectile) or tank2.is_hit(projectile):
                    hit_tank = tank1 if tank1.is_hit(projectile) else tank2
                    hit_tank.health -= 1
                    explosion_sound.play()  # Play explosion sound

                    # Create explosion
                    explosion = Explosion(projectile.x, projectile.y)
                    explosions.append(explosion)

                    projectile.active = False
                    if hit_tank.health <= 0:
                        winner_color = "Red" if hit_tank == tank2 else "Blue"
                        choice = draw_game_over(winner_color)
                        if choice == "rematch":
                            game_over = True  # Will restart the game loop
                        elif choice == "quit":
                            pygame.quit()
                            sys.exit()
                    else:
                        end_turn()  # Switch turns

            # Update and draw explosions
            for explosion in explosions[:]:
                explosion.update()
                explosion.draw(screen)
                if not explosion.active:
                    explosions.remove(explosion)

            # Check if the projectile is inactive after being fired
            if projectile and not projectile.active and shot_fired:
                end_turn()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        choice = draw_pause_menu(stars)
                        if choice == "main_menu":
                            game_over = True  # Exit to main menu
                            # Load and play main menu music
                            try:
                                pygame.mixer.music.load(
                                    os.path.join("music", "mainmenu.ogg"))
                                pygame.mixer.music.play(-1)
                                pygame.mixer.music.set_volume(0.5)
                            except Exception as e:
                                print(f"Could not load main menu music."
                                      f" Exception: {e}")
                                pygame.quit()
                                sys.exit()
                            break
                        elif choice == "quit":
                            pygame.quit()
                            sys.exit()
                        # If 'continue', do nothing
                    if event.key == pygame.K_m:
                        # Toggle mute for background music
                        if pygame.mixer.music.get_volume() > 0:
                            pygame.mixer.music.set_volume(0)
                        else:
                            pygame.mixer.music.set_volume(0.5)
                    if event.key == pygame.K_SPACE:
                        if not shot_fired and (projectile is None or not projectile.active):
                            projectile = current_tank.shoot()
                            shoot_sound.play()  # Play shooting sound
                            shot_fired = True

            keys = pygame.key.get_pressed()
            angle_adjusting = False

            if keys[pygame.K_LEFT]:
                current_tank.aim(-1)
                angle_adjusting = True
            if keys[pygame.K_RIGHT]:
                current_tank.aim(1)
                angle_adjusting = True

            # Play or stop the moving cannon sound
            if angle_adjusting:
                if not moving_cannon_channel.get_busy():
                    moving_cannon_channel.play(moving_cannon_sound, loops=-1)
            else:
                if moving_cannon_channel.get_busy():
                    moving_cannon_channel.stop()

            if keys[pygame.K_UP]:
                current_tank.change_power(1)
            if keys[pygame.K_DOWN]:
                current_tank.change_power(-1)

            # Display current power, angle, and wind speed as HUD elements
            hud_x = WIDTH // 2 - 100  # Centered HUD rectangle, width is 200
            pygame.draw.rect(screen, GRAY, (hud_x, 10, 200, 100))  # HUD bg
            pygame.draw.rect(screen, WHITE, (hud_x, 10, 200, 100), 2)  # Border

            # Power slider
            pygame.draw.line(screen, WHITE, (hud_x + 10, 40),
                             (hud_x + 190, 40), 3)
            power_pos = hud_x + 10 + int(((current_tank.power - 10) / 60)
                                         * 180)
            pygame.draw.circle(
                screen,
                RED,
                (power_pos, 40),
                10,
            )
            power_label = font.render("Power", True, WHITE)
            screen.blit(power_label, (hud_x + 10, 20))

            # Angle slider
            pygame.draw.line(screen, WHITE, (hud_x + 10, 70),
                             (hud_x + 190, 70), 3)
            angle_pos = hud_x + 10 + int((current_tank.angle / 180) * 180)
            pygame.draw.circle(
                screen,
                BLUE,
                (angle_pos, 70),
                10,
            )
            angle_label = font.render("Angle", True, WHITE)
            screen.blit(angle_label, (hud_x + 10, 50))

            # Wind indicator
            wind_label = font.render(f"Wind: {wind:.2f}", True, WHITE)
            screen.blit(wind_label, (hud_x + 10, 90))

            pygame.display.flip()
            clock.tick(60)  # Limit frame rate to 60 FPS

        # If the game is over and a rematch was selected, the loop restarts
        # If the game is over and quit was selected, the program exits

if __name__ == "__main__":
    main()
