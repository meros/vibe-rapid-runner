# Full Code - Rapid Runner v7 (Unified Generation)

import pygame
import random
import sys
import math

# --- Constants ---
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60

# Player settings
PLAYER_SIZE = 35
PLAYER_COLOR = (0, 0, 200)
PLAYER_GRAVITY = 0.6
PLAYER_JUMP_STRENGTH = -15
PLAYER_JUMP_CUTOFF_MULTIPLIER = 3
PLAYER_BOOST_STRENGTH = -7
PLAYER_MAX_FALL_SPEED = 18
PLAYER_ANIM_SPEED = 8
PLAYER_START_X = 100
PLAYER_START_Y = SCREEN_HEIGHT // 2

# Platform settings
PLATFORM_HEIGHT = 25
PLATFORM_MIN_WIDTH = 90
PLATFORM_MAX_WIDTH = 160
PLATFORM_START_SPEED = 4.0
PLATFORM_SPEED_INCREASE = 0.0025
PLATFORM_MIN_GAP_X = 75   # Min horizontal distance between platforms' edges (Increased slightly)
PLATFORM_MAX_GAP_X = 200  # DESIGN Max horizontal distance (may be less if unreachable)
PLATFORM_MIN_GAP_Y = -125 # DESIGN Max UPWARD distance relative to last platform's top edge
PLATFORM_MAX_GAP_Y = 110  # DESIGN Max DOWNWARD distance relative to last platform's top edge
PLATFORM_REACH_MARGIN = 25 # How many pixels below basic jump trajectory the platform top can be

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)

# --- Player Class (Identical to v6) ---
class Player(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.size = PLAYER_SIZE
        self.image = pygame.Surface([self.size, self.size], pygame.SRCALPHA)
        self.rect = self.image.get_rect(centerx=PLAYER_START_X, bottom=PLAYER_START_Y)
        self.velocity_y = 0; self.on_ground = False; self.is_jumping = False
        self.can_boost = False; self.has_boosted = False
        self.anim_frame = 0; self.anim_timer = 0
        self._define_anim_frames(); self._update_image()

    def _define_anim_frames(self):
        s=self.size;h=s//2;q=s//4;t=s*3//4
        self.run_frame_1=[(h,0),(h,h),(h,h),(q,t),(q,t),(0,s),(h,h),(t,t),(t,t),(s,t),(h,q),(0,h),(h,q),(s,h)]
        self.run_frame_2=[(h,0),(h,h),(h,h),(h,t),(h,t),(q,s),(h,h),(h,t),(h,t),(t,s),(h,q),(q,q),(h,q),(t,q)]
        self.run_frame_3=[(h,0),(h,h),(h,h),(t,t),(t,t),(s,s),(h,h),(q,t),(q,t),(0,t),(h,q),(s,h),(h,q),(0,h)]
        self.run_frame_4=self.run_frame_2
        self.jump_frame=[(h,0),(h,h),(h,h),(q,t),(q,t),(q,s),(h,h),(t,t),(t,t),(t,s),(h,q),(0,q),(h,q),(s,q)]
        self.frames=[self.run_frame_1,self.run_frame_2,self.run_frame_3,self.run_frame_4]

    def _update_image(self):
        self.image.fill((0,0,0,0))
        verts=self.jump_frame if not self.on_ground else self.frames[self.anim_frame]
        if self.on_ground:
            self.anim_timer+=1
            if self.anim_timer>=PLAYER_ANIM_SPEED: self.anim_timer=0;self.anim_frame=(self.anim_frame+1)%len(self.frames)
        for i in range(0,len(verts),2): pygame.draw.aaline(self.image,PLAYER_COLOR,verts[i],verts[i+1],1)

    def update(self,platforms):
        eff_grav=PLAYER_GRAVITY*(PLAYER_JUMP_CUTOFF_MULTIPLIER if not self.is_jumping and self.velocity_y<0 else 1)
        self.velocity_y+=eff_grav
        self.velocity_y=min(self.velocity_y,PLAYER_MAX_FALL_SPEED)
        self.rect.y+=self.velocity_y
        self.on_ground=False
        hit_list=pygame.sprite.spritecollide(self,platforms,False)
        for p in hit_list:
            if self.velocity_y>=0 and self.rect.bottom<=p.rect.top+self.velocity_y+1: self.rect.bottom=p.rect.top;self.velocity_y=0;self.on_ground=True;self.has_boosted=False;self.can_boost=True;self.is_jumping=False
            elif self.velocity_y<0 and self.rect.top>=p.rect.bottom+self.velocity_y-1: self.rect.top=p.rect.bottom;self.velocity_y=0
        self.rect.centerx=PLAYER_START_X
        self._update_image()

    def jump(self):
        if self.on_ground: self.velocity_y=PLAYER_JUMP_STRENGTH;self.on_ground=False;self.is_jumping=True;self.can_boost=True;self.has_boosted=False
        elif self.can_boost and not self.has_boosted: self.velocity_y+=PLAYER_BOOST_STRENGTH;self.has_boosted=True;self.can_boost=False;self.is_jumping=True

    def stop_jump(self): self.is_jumping=False

# --- Platform Class (Identical to v6) ---
class Platform(pygame.sprite.Sprite):
    def __init__(self, x, y, width):
        super().__init__()
        self.width = width; self.height = PLATFORM_HEIGHT
        self.image = self._create_platform_surface()
        self.rect = self.image.get_rect(topleft=(x,y))

    def _create_platform_surface(self):
        surf=pygame.Surface([self.width,self.height],pygame.SRCALPHA)
        rc=(110,100,90);gc=(0,150,0);gh=max(4,self.height//4)
        pygame.draw.rect(surf,rc,(0,gh,self.width,self.height-gh))
        for _ in range(int(self.width/10)):
             ly=random.randint(gh+2,self.height-3);sx=random.randint(0,self.width-5);ex=sx+random.randint(2,8)
             lcv=random.randint(-15,15);lc=tuple(max(0,min(255,c+lcv))for c in rc)
             try: pygame.draw.line(surf,lc,(sx,ly),(ex,ly),1)
             except TypeError: pygame.draw.line(surf,(90,80,70),(sx,ly),(ex,ly),1)
        pygame.draw.rect(surf,gc,(0,0,self.width,gh))
        for _ in range(int(self.width/3)):
            bx=random.randint(0,self.width-1);bh=random.randint(3,7)
            bcg=random.randint(10,60);bcrb=random.randint(0,30)
            bc=(max(0,min(255,gc[0]+bcrb)),max(0,min(255,gc[1]+bcg)),max(0,min(255,gc[2]+bcrb)))
            try: pygame.draw.line(surf,bc,(bx,gh),(bx+random.randint(-1,1),gh-bh),random.choice([1,1,2]))
            except TypeError: pygame.draw.line(surf,(10,180,10),(bx,gh),(bx,gh-4),1)
        return surf

    def update(self, current_speed):
        self.rect.x -= current_speed
        if self.rect.right < 0: self.kill()

# --- Helper: Draw Sky (Identical to v6) ---
def draw_sky(screen):
    tc=(100,180,255);bc=(220,240,255);h=screen.get_height();w=screen.get_width()
    for i in range(h): r=i/h;col=tuple(int(tc[c]*(1-r)+bc[c]*r) for c in range(3));pygame.draw.line(screen,col,(0,i),(w,i))

# --- Helper: Calculate Max Air Time (Identical to v6) ---
def calculate_max_air_time():
    if PLAYER_GRAVITY<=0: return float('inf')
    biv=PLAYER_JUMP_STRENGTH+PLAYER_BOOST_STRENGTH
    t_pb=-biv/PLAYER_GRAVITY if PLAYER_GRAVITY>0 else 0; t_pb = max(0, t_pb)
    mth=(biv*t_pb)+(0.5*PLAYER_GRAVITY*t_pb**2) if t_pb>0 else 0
    fd=abs(mth)+PLATFORM_MAX_GAP_Y;fd=max(0,fd)
    t_f=math.sqrt(2*fd/PLAYER_GRAVITY) if PLAYER_GRAVITY>0 else 0
    return (t_pb+t_f)*1.15 # Safety factor

# --- Helper: Show Game Over Screen (Identical to v6) ---
def show_game_over_screen(screen, font, score):
    sw,sh=screen.get_size();ov=pygame.Surface((sw,sh),pygame.SRCALPHA);ov.fill((0,0,0,180));screen.blit(ov,(0,0))
    try:
        t = [font.render(txt,True,WHITE) for txt in ["GAME OVER!",f"Score: {score}","Press SPACE to Restart","Press ESCAPE to Quit"]]
        screen.blit(t[0],(sw//2-t[0].get_width()//2,sh//3)); screen.blit(t[1],(sw//2-t[1].get_width()//2,sh//2))
        screen.blit(t[2],(sw//2-t[2].get_width()//2,sh*2//3)); screen.blit(t[3],(sw//2-t[3].get_width()//2,sh*2//3+40))
    except Exception as e: print(f"Font error: {e}");pygame.draw.rect(screen,WHITE,(100,100,sw-200,sh-200),2)
    pygame.display.flip(); w=True
    while w:
        pygame.time.Clock().tick(15)
        for e in pygame.event.get():
            if e.type==pygame.QUIT: pygame.quit();sys.exit()
            if e.type==pygame.KEYDOWN:
                if e.key==pygame.K_SPACE: w=False
                if e.key==pygame.K_ESCAPE: pygame.quit();sys.exit()

# --- *** NEW HELPER: Unified Platform Generation Logic *** ---
def generate_next_platform(reference_platform, current_speed, max_air_time):
    """Calculates position and size for the next reachable platform."""
    if not reference_platform: return None # Safety check

    # 1. Determine Max Possible Horizontal Gap based on Physics & Speed
    max_physics_reach_x = max_air_time * current_speed
    # Ensure minimum design gap is always possible, even if physics calc is smaller
    max_possible_gap_x = max(max_physics_reach_x, PLATFORM_MIN_GAP_X * 1.05)

    # 2. Choose Actual Horizontal Gap within allowed range
    # Combine design limits and physics limits
    min_gap = PLATFORM_MIN_GAP_X
    max_gap = min(PLATFORM_MAX_GAP_X, max_possible_gap_x)
    if min_gap > max_gap: # Should not happen if constants are sane, but handle anyway
        # print(f"Warning: Min gap {min_gap} > max possible gap {max_gap}. Forcing to min.")
        max_gap = min_gap * 1.1 # Allow a small range above min

    actual_gap_x = random.uniform(min_gap, max_gap)

    # 3. Estimate Player Landing Y (using basic jump trajectory)
    time_cross = actual_gap_x / current_speed if current_speed > 0 else 0
    # Vertical displacement (dy) relative to the reference platform's top
    player_dy = (PLAYER_JUMP_STRENGTH * time_cross) + (0.5 * PLAYER_GRAVITY * time_cross**2) if time_cross > 0 else 0
    # Absolute Y coordinate the player's feet would reach at this horizontal distance
    player_reach_y = reference_platform.rect.y + player_dy

    # 4. Determine Valid Vertical Offset (Y Range) for New Platform
    # Minimum Y offset based on reachability (platform top must be below player feet trajectory)
    # Player needs to land ON the platform, so top should be below player_reach_y
    min_plat_top_y = player_reach_y + PLATFORM_REACH_MARGIN
    min_y_offset_physics = min_plat_top_y - reference_platform.rect.y

    # Maximum Y offset based on design limit (downward)
    max_y_offset_design = PLATFORM_MAX_GAP_Y

    # Minimum Y offset based on design limit (upward - negative value)
    min_y_offset_design = PLATFORM_MIN_GAP_Y

    # Combine constraints:
    # Final Min Offset: Must be >= design min AND >= physics min
    final_min_offset_y = max(min_y_offset_design, min_y_offset_physics)
    # Final Max Offset: Must be <= design max
    final_max_offset_y = max_y_offset_design

    # Handle impossible range (min > max) - can happen if player trajectory is below max downward gap
    if final_min_offset_y > final_max_offset_y:
        # If physics forces it lower than max design drop, allow it, but cap it slightly below physics reach
        # print(f"Warning: Y offset range impossible ({final_min_offset_y:.1f} > {final_max_offset_y:.1f}). Adjusting.")
        final_max_offset_y = final_min_offset_y + 40 # Allow a small range below the physics limit
        # Ensure it doesn't exceed the absolute design max downward gap still
        final_max_offset_y = min(final_max_offset_y, PLATFORM_MAX_GAP_Y)
        # If min is still > max after adjustment (very unlikely), force level placement
        if final_min_offset_y > final_max_offset_y:
             final_min_offset_y = 0
             final_max_offset_y = 20


    # 5. Choose the actual Vertical Offset randomly within the valid range
    actual_offset_y = random.uniform(final_min_offset_y, final_max_offset_y)

    # 6. Calculate final absolute X, Y position
    next_plat_x = reference_platform.rect.right + actual_gap_x
    next_plat_y = reference_platform.rect.y + actual_offset_y

    # 7. Final clamping of Y position to screen bounds (important!)
    next_plat_y = max(PLATFORM_HEIGHT * 3, next_plat_y) # Keep away from top edge
    next_plat_y = min(SCREEN_HEIGHT - PLATFORM_HEIGHT * 4, next_plat_y) # Keep away from bottom edge

    # 8. Choose Platform Width
    plat_width = random.randint(PLATFORM_MIN_WIDTH, PLATFORM_MAX_WIDTH)

    return next_plat_x, next_plat_y, plat_width
# --- *** END OF NEW HELPER *** ---


# --- Main Game Loop Function (MODIFIED) ---
def game_loop(screen, clock, font):
    """Runs the main game logic with unified platform generation."""
    MAX_ESTIMATED_AIR_TIME = calculate_max_air_time() # Calculate once at start

    all_sprites = pygame.sprite.Group()
    platforms = pygame.sprite.Group()

    player = Player()
    all_sprites.add(player)

    # --- Start Platform ---
    start_platform_width = 150
    start_platform = Platform(player.rect.centerx - start_platform_width // 2,
                              PLAYER_START_Y,
                              start_platform_width)
    all_sprites.add(start_platform)
    platforms.add(start_platform)

    last_platform_generated = start_platform # Keep track of the rightmost platform

    # --- Initial Screen Population ---
    # Generate platforms until the right edge goes off screen
    while last_platform_generated.rect.right < SCREEN_WIDTH + PLATFORM_MAX_GAP_X: # Generate slightly past edge
        platform_data = generate_next_platform(last_platform_generated,
                                               PLATFORM_START_SPEED, # Use START speed for initial fill
                                               MAX_ESTIMATED_AIR_TIME)
        if platform_data:
            px, py, pw = platform_data
            new_platform = Platform(px, py, pw)
            all_sprites.add(new_platform)
            platforms.add(new_platform)
            last_platform_generated = new_platform # Update reference
        else:
            print("Error: Could not generate initial platform.")
            break # Avoid infinite loop if generation fails

    # --- Game Variables ---
    current_platform_speed = PLATFORM_START_SPEED
    score = 0
    game_over = False
    running = True

    # --- Main Game Loop ---
    while running:
        # --- Event Handling ---
        for event in pygame.event.get():
            if event.type == pygame.QUIT: running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE and not game_over: player.jump()
                if event.key == pygame.K_ESCAPE: running = False
            if event.type == pygame.KEYUP:
                 if event.key == pygame.K_SPACE and not game_over: player.stop_jump()

        if not running: break
        if game_over:
            show_game_over_screen(screen, font, score // 10)
            game_loop(screen, clock, font); return # Restart

        # --- Update ---
        current_platform_speed += PLATFORM_SPEED_INCREASE
        player.update(platforms)
        platforms.update(current_platform_speed)

        # --- Dynamic Platform Spawning ---
        platform_count = len(platforms) # Get current count

        # Spawn trigger: Check if the rightmost platform is sufficiently on screen
        # Use a fixed distance from the right edge as trigger for consistency
        spawn_trigger_x = SCREEN_WIDTH - PLATFORM_MIN_GAP_X # Spawn when last platform's right edge is visible

        if last_platform_generated and last_platform_generated.rect.right < spawn_trigger_x and platform_count < 12: # Limit total platforms slightly more
             platform_data = generate_next_platform(last_platform_generated,
                                                   current_platform_speed, # Use CURRENT speed for dynamic spawns
                                                   MAX_ESTIMATED_AIR_TIME)
             if platform_data:
                px, py, pw = platform_data
                # Dynamic spawns *always* start off-screen conceptually,
                # but their X is calculated relative to the last one.
                # The generate function gives the correct absolute X.
                new_platform = Platform(px, py, pw)
                all_sprites.add(new_platform)
                platforms.add(new_platform)
                last_platform_generated = new_platform # Update reference
             else:
                 print(f"Warning: Failed to generate dynamic platform at speed {current_platform_speed:.2f}")


        # --- Score & Game Over Check ---
        score += 1
        if player.rect.top > SCREEN_HEIGHT + PLAYER_SIZE: game_over = True

        # --- Draw ---
        draw_sky(screen)
        all_sprites.draw(screen)
        try: score_display = font.render(f"Score: {score // 10}", True, BLACK); screen.blit(score_display, (10, 10))
        except Exception: pass

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()
    sys.exit()

# --- Initialization and Game Start ---
if __name__ == '__main__':
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Rapid Runner Vector v7 - Unified Gen")
    clock = pygame.time.Clock()
    if not pygame.font.get_init(): pygame.font.init()
    try: game_font = pygame.font.Font(None, 50)
    except OSError: game_font = pygame.font.SysFont(pygame.font.get_default_font(), 50)
    try: game_loop(screen, clock, game_font)
    except Exception as e: print(f"\nFATAL ERROR: {e}"); import traceback; traceback.print_exc()
    finally: pygame.quit(); sys.exit()