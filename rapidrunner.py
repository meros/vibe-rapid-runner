# Full Code - Rapid Runner v8.1 (Indentation Fix & Full Code)

import pygame
import random
import sys
import math

# --- Constants ---
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60

# Player settings
PLAYER_WIDTH = 30 # Base width for drawing calculations
PLAYER_HEIGHT = 45 # Base height
PLAYER_GRAVITY = 0.6
PLAYER_JUMP_STRENGTH = -15
PLAYER_JUMP_CUTOFF_MULTIPLIER = 3
PLAYER_BOOST_STRENGTH = -6     # SLIGHTLY reduced vertical boost for dash
PLAYER_MAX_FALL_SPEED = 18
PLAYER_ANIM_SPEED = 6 # Faster animation cycle
PLAYER_START_X = 100
PLAYER_START_Y = SCREEN_HEIGHT // 2

# Dash Constants
PLAYER_DASH_DURATION_FRAMES = 25 # How many frames the dash speed boost lasts
PLAYER_DASH_SPEED_BONUS = 4.5   # How much faster platforms move during dash

# Platform settings
PLATFORM_HEIGHT = 25
PLATFORM_MIN_WIDTH = 90
PLATFORM_MAX_WIDTH = 160
PLATFORM_START_SPEED = 4.0
PLATFORM_SPEED_INCREASE = 0.0025
PLATFORM_MIN_GAP_X = 75
PLATFORM_MAX_GAP_X = 200
PLATFORM_MIN_GAP_Y = -125
PLATFORM_MAX_GAP_Y = 110
PLATFORM_REACH_MARGIN = 25 # How many pixels below basic jump trajectory the platform top can be

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)

# --- Player Class ---
class Player(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.base_width = PLAYER_WIDTH
        self.base_height = PLAYER_HEIGHT
        self.image = pygame.Surface([self.base_width + 10, self.base_height + 10], pygame.SRCALPHA)
        self.rect = self.image.get_rect(centerx=PLAYER_START_X, bottom=PLAYER_START_Y)

        # Physics state
        self.velocity_y = 0
        self.on_ground = False
        self.is_jumping = False
        self.can_boost = False
        self.has_boosted = False

        # Dash state
        self.is_dashing = False
        self.dash_timer = 0

        # Animation state
        self.anim_frame = 0
        self.anim_timer = 0
        self.current_pose = {} # Holds the polygon data for the current frame

        # Define colors and body parts
        self.colors = {
            "skin": (255, 220, 180), "shirt": (50, 100, 200), "pants": (40, 40, 50),
            "shoes": (100, 80, 60), "dash_trail": (200, 200, 255, 150)
        }
        self.body_parts = ["torso", "head", "arm_upper_L", "arm_lower_L", "arm_upper_R", "arm_lower_R", "leg_upper_L", "leg_lower_L", "leg_upper_R", "leg_lower_R", "shoe_L", "shoe_R"]
        self.part_colors = {
             "torso": self.colors["shirt"], "head": self.colors["skin"],
             "arm_upper_L": self.colors["shirt"], "arm_lower_L": self.colors["skin"],
             "arm_upper_R": self.colors["shirt"], "arm_lower_R": self.colors["skin"],
             "leg_upper_L": self.colors["pants"], "leg_lower_L": self.colors["pants"],
             "leg_upper_R": self.colors["pants"], "leg_lower_R": self.colors["pants"],
             "shoe_L": self.colors["shoes"], "shoe_R": self.colors["shoes"]
        }

        self._define_anim_frames()
        self._set_pose("run", 0) # Initial pose

    def _define_anim_frames(self):
        """Defines polygon points for each body part in various animation poses."""
        self.poses = {"run": [], "jump_ascend": [], "jump_descend": [], "dash": []}
        w=self.base_width; h=self.base_height; cx=(self.base_width+10)//2; cy=(self.base_height+10)//2
        head_r=w*0.18; torso_w=w*0.4; torso_h=h*0.45; limb_w=w*0.15
        up_limb_h=h*0.25; lo_limb_h=h*0.30; shoe_h=h*0.1; shoe_w_f=limb_w*1.5; shoe_w_b=limb_w*0.8
        neck_y=cy-torso_h*0.45; shoulder_y=cy-torso_h*0.4; shoulder_x_off=torso_w*0.55
        hip_y=cy+torso_h*0.45; hip_x_off=torso_w*0.45; knee_off_y=up_limb_h*1.1

        for i in range(4): # Generate 4 run frames
            pose_data = {}
            angle1=math.sin(i*math.pi/2); angle2=math.sin((i+2)*math.pi/2); bob=abs(math.cos(i*math.pi/2))*3
            t_cx=cx+angle1*2; t_cy=cy+bob
            pose_data["torso"]=[(t_cx-torso_w/2,t_cy-torso_h/2),(t_cx+torso_w/2,t_cy-torso_h/2),(t_cx+torso_w/2*0.8,t_cy+torso_h/2),(t_cx-torso_w/2*0.8,t_cy+torso_h/2)]
            pose_data["head"]=[(t_cx,neck_y+bob-head_r*1.5),(t_cx+head_r,neck_y+bob-head_r*0.5),(t_cx,neck_y+bob+head_r*0.5),(t_cx-head_r,neck_y+bob-head_r*0.5)]
            sh_l=(t_cx-shoulder_x_off,shoulder_y+bob); elb_l=(sh_l[0]+math.cos(angle1*0.8+math.pi/2)*up_limb_h,sh_l[1]+math.sin(angle1*0.8+math.pi/2)*up_limb_h); hnd_l=(elb_l[0]+math.cos(angle1*0.6+math.pi/2)*lo_limb_h,elb_l[1]+math.sin(angle1*0.6+math.pi/2)*lo_limb_h)
            pose_data["arm_upper_L"]=self._make_limb_poly(sh_l,elb_l,limb_w); pose_data["arm_lower_L"]=self._make_limb_poly(elb_l,hnd_l,limb_w*0.9)
            sh_r=(t_cx+shoulder_x_off,shoulder_y+bob); elb_r=(sh_r[0]+math.cos(angle2*0.8+math.pi/2)*up_limb_h,sh_r[1]+math.sin(angle2*0.8+math.pi/2)*up_limb_h); hnd_r=(elb_r[0]+math.cos(angle2*0.6+math.pi/2)*lo_limb_h,elb_r[1]+math.sin(angle2*0.6+math.pi/2)*lo_limb_h)
            pose_data["arm_upper_R"]=self._make_limb_poly(sh_r,elb_r,limb_w); pose_data["arm_lower_R"]=self._make_limb_poly(elb_r,hnd_r,limb_w*0.9)
            hp_l=(t_cx-hip_x_off,hip_y+bob); kn_l=(hp_l[0]+math.cos(angle2*0.9-math.pi/2)*knee_off_y,hp_l[1]+math.sin(angle2*0.9-math.pi/2)*knee_off_y); ft_l=(kn_l[0]+math.cos(angle2*0.7-math.pi/2)*lo_limb_h,kn_l[1]+math.sin(angle2*0.7-math.pi/2)*lo_limb_h)
            pose_data["leg_upper_L"]=self._make_limb_poly(hp_l,kn_l,limb_w*1.1); pose_data["leg_lower_L"]=self._make_limb_poly(kn_l,ft_l,limb_w); pose_data["shoe_L"]=[(ft_l[0]-shoe_w_b,ft_l[1]-shoe_h/2),(ft_l[0]+shoe_w_f,ft_l[1]-shoe_h/3),(ft_l[0]+shoe_w_f*0.8,ft_l[1]+shoe_h/2),(ft_l[0]-shoe_w_b,ft_l[1]+shoe_h/2)]
            hp_r=(t_cx+hip_x_off,hip_y+bob); kn_r=(hp_r[0]+math.cos(angle1*0.9-math.pi/2)*knee_off_y,hp_r[1]+math.sin(angle1*0.9-math.pi/2)*knee_off_y); ft_r=(kn_r[0]+math.cos(angle1*0.7-math.pi/2)*lo_limb_h,kn_r[1]+math.sin(angle1*0.7-math.pi/2)*lo_limb_h)
            pose_data["leg_upper_R"]=self._make_limb_poly(hp_r,kn_r,limb_w*1.1); pose_data["leg_lower_R"]=self._make_limb_poly(kn_r,ft_r,limb_w); pose_data["shoe_R"]=[(ft_r[0]-shoe_w_b,ft_r[1]-shoe_h/2),(ft_r[0]+shoe_w_f,ft_r[1]-shoe_h/3),(ft_r[0]+shoe_w_f*0.8,ft_r[1]+shoe_h/2),(ft_r[0]-shoe_w_b,ft_r[1]+shoe_h/2)]
            self.poses["run"].append(pose_data)

        ja_pose={}; t_cx,t_cy=cx,cy-5
        ja_pose["torso"]=[(t_cx-torso_w/2,t_cy-torso_h/2),(t_cx+torso_w/2,t_cy-torso_h/2),(t_cx+torso_w/2*0.8,t_cy+torso_h/2),(t_cx-torso_w/2*0.8,t_cy+torso_h/2)]; ja_pose["head"]=[(t_cx,neck_y-5-head_r*1.5),(t_cx+head_r,neck_y-5-head_r*0.5),(t_cx,neck_y-5+head_r*0.5),(t_cx-head_r,neck_y-5-head_r*0.5)]
        sh_l=(t_cx-shoulder_x_off,shoulder_y-5); sh_r=(t_cx+shoulder_x_off,shoulder_y-5); elb_l=(sh_l[0]-limb_w,sh_l[1]-up_limb_h); elb_r=(sh_r[0]+limb_w,sh_r[1]-up_limb_h); hnd_l=(elb_l[0],elb_l[1]-lo_limb_h); hnd_r=(elb_r[0],elb_r[1]-lo_limb_h)
        ja_pose["arm_upper_L"]=self._make_limb_poly(sh_l,elb_l,limb_w); ja_pose["arm_lower_L"]=self._make_limb_poly(elb_l,hnd_l,limb_w*0.9); ja_pose["arm_upper_R"]=self._make_limb_poly(sh_r,elb_r,limb_w); ja_pose["arm_lower_R"]=self._make_limb_poly(elb_r,hnd_r,limb_w*0.9)
        hp_l=(t_cx-hip_x_off,hip_y-5); hp_r=(t_cx+hip_x_off,hip_y-5); kn_l=(hp_l[0]+limb_w*0.5,hp_l[1]-knee_off_y*0.3); kn_r=(hp_r[0]-limb_w*0.5,hp_r[1]-knee_off_y*0.3); ft_l=(kn_l[0]+limb_w,kn_l[1]+lo_limb_h*0.6); ft_r=(kn_r[0]-limb_w,kn_r[1]+lo_limb_h*0.6)
        ja_pose["leg_upper_L"]=self._make_limb_poly(hp_l,kn_l,limb_w*1.1); ja_pose["leg_lower_L"]=self._make_limb_poly(kn_l,ft_l,limb_w); ja_pose["shoe_L"]=[(ft_l[0]-shoe_w_b,ft_l[1]-shoe_h/2),(ft_l[0]+shoe_w_f,ft_l[1]-shoe_h/3),(ft_l[0]+shoe_w_f*0.8,ft_l[1]+shoe_h/2),(ft_l[0]-shoe_w_b,ft_l[1]+shoe_h/2)]
        ja_pose["leg_upper_R"]=self._make_limb_poly(hp_r,kn_r,limb_w*1.1); ja_pose["leg_lower_R"]=self._make_limb_poly(kn_r,ft_r,limb_w); ja_pose["shoe_R"]=[(ft_r[0]-shoe_w_b,ft_r[1]-shoe_h/2),(ft_r[0]+shoe_w_f,ft_r[1]-shoe_h/3),(ft_r[0]+shoe_w_f*0.8,ft_r[1]+shoe_h/2),(ft_r[0]-shoe_w_b,ft_r[1]+shoe_h/2)]
        self.poses["jump_ascend"].append(ja_pose)

        jd_pose={}; t_cx,t_cy=cx,cy
        jd_pose["torso"]=[(t_cx-torso_w/2,t_cy-torso_h/2),(t_cx+torso_w/2,t_cy-torso_h/2),(t_cx+torso_w/2*0.8,t_cy+torso_h/2),(t_cx-torso_w/2*0.8,t_cy+torso_h/2)]; jd_pose["head"]=[(t_cx,neck_y-head_r*1.5),(t_cx+head_r,neck_y-head_r*0.5),(t_cx,neck_y+head_r*0.5),(t_cx-head_r,neck_y-head_r*0.5)]
        sh_l=(t_cx-shoulder_x_off,shoulder_y); sh_r=(t_cx+shoulder_x_off,shoulder_y); elb_l=(sh_l[0]+limb_w*0.5,sh_l[1]+up_limb_h*0.8); elb_r=(sh_r[0]-limb_w*0.5,sh_r[1]+up_limb_h*0.8); hnd_l=(elb_l[0],elb_l[1]+lo_limb_h); hnd_r=(elb_r[0],elb_r[1]+lo_limb_h)
        jd_pose["arm_upper_L"]=self._make_limb_poly(sh_l,elb_l,limb_w); jd_pose["arm_lower_L"]=self._make_limb_poly(elb_l,hnd_l,limb_w*0.9); jd_pose["arm_upper_R"]=self._make_limb_poly(sh_r,elb_r,limb_w); jd_pose["arm_lower_R"]=self._make_limb_poly(elb_r,hnd_r,limb_w*0.9)
        hp_l=(t_cx-hip_x_off,hip_y); hp_r=(t_cx+hip_x_off,hip_y); kn_l=(hp_l[0]-limb_w*0.2,hp_l[1]+knee_off_y*0.9); kn_r=(hp_r[0]+limb_w*0.2,hp_r[1]+knee_off_y*0.9); ft_l=(kn_l[0]-limb_w*0.5,kn_l[1]+lo_limb_h); ft_r=(kn_r[0]+limb_w*0.5,kn_r[1]+lo_limb_h)
        jd_pose["leg_upper_L"]=self._make_limb_poly(hp_l,kn_l,limb_w*1.1); jd_pose["leg_lower_L"]=self._make_limb_poly(kn_l,ft_l,limb_w); jd_pose["shoe_L"]=[(ft_l[0]-shoe_w_b,ft_l[1]-shoe_h/2),(ft_l[0]+shoe_w_f*0.8,ft_l[1]-shoe_h/3),(ft_l[0]+shoe_w_f*0.6,ft_l[1]+shoe_h/2),(ft_l[0]-shoe_w_b,ft_l[1]+shoe_h/2)]
        jd_pose["leg_upper_R"]=self._make_limb_poly(hp_r,kn_r,limb_w*1.1); jd_pose["leg_lower_R"]=self._make_limb_poly(kn_r,ft_r,limb_w); jd_pose["shoe_R"]=[(ft_r[0]-shoe_w_b,ft_r[1]-shoe_h/2),(ft_r[0]+shoe_w_f*0.8,ft_r[1]-shoe_h/3),(ft_r[0]+shoe_w_f*0.6,ft_r[1]+shoe_h/2),(ft_r[0]-shoe_w_b,ft_r[1]+shoe_h/2)]
        self.poses["jump_descend"].append(jd_pose)

        d_pose={}; t_cx,t_cy=cx+5,cy; lean_angle=-math.pi/10
        d_pose["torso"]=self._rotate_poly([(t_cx-torso_w/2,t_cy-torso_h/2),(t_cx+torso_w/2,t_cy-torso_h/2),(t_cx+torso_w/2*0.8,t_cy+torso_h/2),(t_cx-torso_w/2*0.8,t_cy+torso_h/2)],(t_cx,t_cy),lean_angle)
        d_pose["head"]=self._rotate_poly([(t_cx,neck_y-head_r*1.5),(t_cx+head_r,neck_y-head_r*0.5),(t_cx,neck_y+head_r*0.5),(t_cx-head_r,neck_y-head_r*0.5)],(t_cx,t_cy),lean_angle)
        sh_l=(t_cx-shoulder_x_off,shoulder_y); sh_r=(t_cx+shoulder_x_off,shoulder_y); sh_l,sh_r=self._rotate_point(sh_l,(t_cx,t_cy),lean_angle),self._rotate_point(sh_r,(t_cx,t_cy),lean_angle)
        elb_l=(sh_l[0]-limb_w*0.5,sh_l[1]+up_limb_h*0.5); elb_r=(sh_r[0]-limb_w*0.5,sh_r[1]+up_limb_h*0.5); hnd_l=(elb_l[0]-lo_limb_h,elb_l[1]); hnd_r=(elb_r[0]-lo_limb_h,elb_r[1])
        d_pose["arm_upper_L"]=self._make_limb_poly(sh_l,elb_l,limb_w); d_pose["arm_lower_L"]=self._make_limb_poly(elb_l,hnd_l,limb_w*0.9); d_pose["arm_upper_R"]=self._make_limb_poly(sh_r,elb_r,limb_w); d_pose["arm_lower_R"]=self._make_limb_poly(elb_r,hnd_r,limb_w*0.9)
        hp_l=(t_cx-hip_x_off,hip_y); hp_r=(t_cx+hip_x_off,hip_y); hp_l,hp_r=self._rotate_point(hp_l,(t_cx,t_cy),lean_angle),self._rotate_point(hp_r,(t_cx,t_cy),lean_angle)
        kn_l=(hp_l[0]-knee_off_y*0.7,hp_l[1]+limb_w*0.3); kn_r=(hp_r[0]-knee_off_y*0.6,hp_r[1]-limb_w*0.2); ft_l=(kn_l[0]-lo_limb_h,kn_l[1]); ft_r=(kn_r[0]-lo_limb_h*0.9,kn_r[1])
        d_pose["leg_upper_L"]=self._make_limb_poly(hp_l,kn_l,limb_w*1.1); d_pose["leg_lower_L"]=self._make_limb_poly(kn_l,ft_l,limb_w); d_pose["shoe_L"]=[(ft_l[0]-shoe_w_f,ft_l[1]-shoe_h/2),(ft_l[0]+shoe_w_b,ft_l[1]-shoe_h/3),(ft_l[0]+shoe_w_b*0.8,ft_l[1]+shoe_h/2),(ft_l[0]-shoe_w_f,ft_l[1]+shoe_h/2)]
        d_pose["leg_upper_R"]=self._make_limb_poly(hp_r,kn_r,limb_w*1.1); d_pose["leg_lower_R"]=self._make_limb_poly(kn_r,ft_r,limb_w); d_pose["shoe_R"]=[(ft_r[0]-shoe_w_f,ft_r[1]-shoe_h/2),(ft_r[0]+shoe_w_b,ft_r[1]-shoe_h/3),(ft_r[0]+shoe_w_b*0.8,ft_r[1]+shoe_h/2),(ft_r[0]-shoe_w_f,ft_r[1]+shoe_h/2)]
        self.poses["dash"].append(d_pose)

    def _make_limb_poly(self, start_pos, end_pos, width):
        angle=math.atan2(end_pos[1]-start_pos[1],end_pos[0]-start_pos[0]); p_angle=angle+math.pi/2; w2=width/2
        p1=(start_pos[0]+math.cos(p_angle)*w2,start_pos[1]+math.sin(p_angle)*w2); p2=(start_pos[0]-math.cos(p_angle)*w2,start_pos[1]-math.sin(p_angle)*w2)
        p3=(end_pos[0]-math.cos(p_angle)*w2,end_pos[1]-math.sin(p_angle)*w2); p4=(end_pos[0]+math.cos(p_angle)*w2,end_pos[1]+math.sin(p_angle)*w2)
        return [p1, p2, p3, p4]

    def _rotate_point(self, point, center, angle_rad):
        x,y=point; cx,cy=center; cos_a=math.cos(angle_rad); sin_a=math.sin(angle_rad)
        nx=cos_a*(x-cx)-sin_a*(y-cy)+cx; ny=sin_a*(x-cx)+cos_a*(y-cy)+cy; return nx,ny

    def _rotate_poly(self, poly, center, angle_rad):
        return [self._rotate_point(p, center, angle_rad) for p in poly]

    def _set_pose(self, pose_name, frame_index):
        try: self.current_pose = self.poses[pose_name][frame_index]
        except (KeyError, IndexError): self.current_pose = self.poses["run"][0] # Fallback

    def _update_image(self):
        self.image.fill((0,0,0,0)) # Clear surface
        if not self.current_pose: return

        draw_order=["leg_upper_R","leg_lower_R","shoe_R","arm_upper_R","arm_lower_R","torso","leg_upper_L","leg_lower_L","shoe_L","arm_upper_L","arm_lower_L","head"]
        if self.is_dashing:
            trail_offset=8; trail_parts=["torso","leg_upper_L","leg_lower_L","leg_upper_R","leg_lower_R"]
            for part_name in trail_parts:
                 if part_name in self.current_pose:
                     poly=[(p[0]-trail_offset,p[1]) for p in self.current_pose[part_name]]
                     try: pygame.draw.polygon(self.image,self.colors["dash_trail"],poly)
                     except ValueError: pass
        for part_name in draw_order:
            if part_name in self.current_pose and part_name in self.part_colors:
                poly = self.current_pose[part_name]; color = self.part_colors[part_name]
                try:
                    int_poly = [(int(p[0]), int(p[1])) for p in poly]
                    if len(int_poly)>=3: pygame.draw.polygon(self.image, color, int_poly)
                except ValueError: pass

    def update(self, platforms):
        # --- Handle Dash Timer ---
        if self.is_dashing:
            self.dash_timer -= 1
            if self.dash_timer <= 0: self.is_dashing = False

        # --- Gravity & Vertical Movement ---
        eff_grav=PLAYER_GRAVITY*(PLAYER_JUMP_CUTOFF_MULTIPLIER if not self.is_jumping and self.velocity_y<0 else 1)
        self.velocity_y+=eff_grav; self.velocity_y=min(self.velocity_y,PLAYER_MAX_FALL_SPEED)
        self.rect.y += self.velocity_y

        # --- Collision Check ---
        self.on_ground=False
        hit_list=pygame.sprite.spritecollide(self,platforms,False)
        for p in hit_list:
            if self.velocity_y>=0 and self.rect.bottom<=p.rect.top+self.velocity_y+1:
                self.rect.bottom=p.rect.top;self.velocity_y=0;self.on_ground=True
                self.has_boosted=False;self.can_boost=True;self.is_jumping=False
                self.is_dashing=False;self.dash_timer=0 # Stop dash on land
            elif self.velocity_y<0 and self.rect.top>=p.rect.bottom+self.velocity_y-1:
                 self.rect.top=p.rect.bottom;self.velocity_y=0

        # --- Update Animation State ---
        if self.is_dashing: self._set_pose("dash", 0)
        elif not self.on_ground: self._set_pose("jump_ascend" if self.velocity_y < 0 else "jump_descend", 0)
        else: # On ground
            self.anim_timer+=1
            if self.anim_timer>=PLAYER_ANIM_SPEED: self.anim_timer=0;self.anim_frame=(self.anim_frame+1)%len(self.poses["run"])
            self._set_pose("run", self.anim_frame)

        # --- Horizontal Position & Final Draw ---
        self.rect.centerx = PLAYER_START_X
        self._update_image() # Draw the selected pose

    def jump(self): # Handles Jump and Dash/Boost
        if self.on_ground:
            self.velocity_y=PLAYER_JUMP_STRENGTH;self.on_ground=False;self.is_jumping=True;self.can_boost=True;self.has_boosted=False;self.is_dashing=False;self.dash_timer=0
        elif self.can_boost and not self.has_boosted: # Activate Dash/Boost
            self.velocity_y+=PLAYER_BOOST_STRENGTH;self.has_boosted=True;self.can_boost=False;self.is_jumping=True
            self.is_dashing=True; self.dash_timer=PLAYER_DASH_DURATION_FRAMES # Activate dash

    def stop_jump(self): self.is_jumping = False # For variable jump height

# --- Platform Class (Identical to v7) ---
class Platform(pygame.sprite.Sprite):
    def __init__(self, x, y, width):
        super().__init__(); self.width=width; self.height=PLATFORM_HEIGHT
        self.image=self._create_platform_surface(); self.rect=self.image.get_rect(topleft=(x,y))
    def _create_platform_surface(self):
        surf=pygame.Surface([self.width,self.height],pygame.SRCALPHA); rc=(110,100,90);gc=(0,150,0);gh=max(4,self.height//4)
        pygame.draw.rect(surf,rc,(0,gh,self.width,self.height-gh))
        for _ in range(int(self.width/10)): ly=random.randint(gh+2,self.height-3);sx=random.randint(0,self.width-5);ex=sx+random.randint(2,8);lcv=random.randint(-15,15);lc=tuple(max(0,min(255,c+lcv))for c in rc); pygame.draw.line(surf,lc,(sx,ly),(ex,ly),1)
        pygame.draw.rect(surf,gc,(0,0,self.width,gh))
        for _ in range(int(self.width/3)): bx=random.randint(0,self.width-1);bh=random.randint(3,7);bcg=random.randint(10,60);bcrb=random.randint(0,30);bc=(max(0,min(255,gc[0]+bcrb)),max(0,min(255,gc[1]+bcg)),max(0,min(255,gc[2]+bcrb))); pygame.draw.line(surf,bc,(bx,gh),(bx+random.randint(-1,1),gh-bh),random.choice([1,1,2]))
        return surf
    def update(self, current_speed): # <-- FIXED INDENTATION HERE
        self.rect.x -= current_speed
        if self.rect.right < 0:
            self.kill()

# --- Helper: Draw Sky (Identical to v7) ---
def draw_sky(screen): tc=(100,180,255);bc=(220,240,255);h=screen.get_height();w=screen.get_width(); [pygame.draw.line(screen,tuple(int(tc[c]*(1-(i/h))+bc[c]*(i/h)) for c in range(3)),(0,i),(w,i)) for i in range(h)]

# --- Helper: Calculate Max Air Time (Identical to v7) ---
def calculate_max_air_time():
    if PLAYER_GRAVITY<=0: return float('inf')
    biv=PLAYER_JUMP_STRENGTH+PLAYER_BOOST_STRENGTH; t_pb=-biv/PLAYER_GRAVITY if PLAYER_GRAVITY>0 else 0; t_pb=max(0,t_pb)
    mth=(biv*t_pb)+(0.5*PLAYER_GRAVITY*t_pb**2) if t_pb>0 else 0; fd=abs(mth)+PLATFORM_MAX_GAP_Y; fd=max(0,fd)
    t_f=math.sqrt(2*fd/PLAYER_GRAVITY) if PLAYER_GRAVITY>0 else 0; return (t_pb+t_f)*1.15

# --- Helper: Show Game Over Screen (Identical to v7) ---
def show_game_over_screen(screen, font, score):
    sw,sh=screen.get_size();ov=pygame.Surface((sw,sh),pygame.SRCALPHA);ov.fill((0,0,0,180));screen.blit(ov,(0,0))
    try:
        t=[font.render(txt,True,WHITE) for txt in ["GAME OVER!",f"Score: {score}","Press SPACE to Restart","Press ESCAPE to Quit"]]
        [screen.blit(t[i],(sw//2-t[i].get_width()//2,[sh//3,sh//2,sh*2//3,sh*2//3+40][i])) for i in range(4)]
    except Exception as e: print(f"Font error: {e}");pygame.draw.rect(screen,WHITE,(100,100,sw-200,sh-200),2)
    pygame.display.flip(); w=True
    while w:
        pygame.time.Clock().tick(15);
        for e in pygame.event.get():
            if e.type==pygame.QUIT: pygame.quit();sys.exit()
            if e.type==pygame.KEYDOWN:
                if e.key==pygame.K_SPACE: w=False
                if e.key==pygame.K_ESCAPE: pygame.quit();sys.exit()

# --- Helper: Unified Platform Generation (Using Robust v8 version) ---
def generate_next_platform(reference_platform, effective_speed, max_air_time):
    """Calculates position and size for the next reachable platform using effective speed."""
    if not reference_platform or not hasattr(reference_platform, 'rect'):
        print("Error: Invalid reference_platform passed to generate_next_platform.")
        return None
    try:
        max_physics_reach_x = max_air_time * effective_speed
        max_possible_gap_x = max(max_physics_reach_x, PLATFORM_MIN_GAP_X * 1.05)
        min_gap = PLATFORM_MIN_GAP_X; max_gap = min(PLATFORM_MAX_GAP_X, max_possible_gap_x)
        if min_gap > max_gap: max_gap = min_gap * 1.1
        actual_gap_x = random.uniform(min_gap, max_gap)
        time_cross = actual_gap_x / effective_speed if effective_speed > 0.001 else 0
        player_dy = (PLAYER_JUMP_STRENGTH*time_cross)+(0.5*PLAYER_GRAVITY*time_cross**2) if time_cross>0 else 0
        player_reach_y = reference_platform.rect.y + player_dy
        min_plat_top_y = player_reach_y + PLATFORM_REACH_MARGIN
        min_y_offset_physics = min_plat_top_y - reference_platform.rect.y
        max_y_offset_design = PLATFORM_MAX_GAP_Y; min_y_offset_design = PLATFORM_MIN_GAP_Y
        final_min_offset_y = max(min_y_offset_design, min_y_offset_physics)
        final_max_offset_y = max_y_offset_design
        if final_min_offset_y > final_max_offset_y:
            final_max_offset_y = final_min_offset_y + 40; final_max_offset_y = min(final_max_offset_y, PLATFORM_MAX_GAP_Y)
            if final_min_offset_y > final_max_offset_y: final_min_offset_y = 0; final_max_offset_y = 20
        actual_offset_y = random.uniform(final_min_offset_y, final_max_offset_y)
        next_plat_x = reference_platform.rect.right + actual_gap_x
        next_plat_y = reference_platform.rect.y + actual_offset_y
        next_plat_y = max(PLATFORM_HEIGHT*3, next_plat_y); next_plat_y = min(SCREEN_HEIGHT-PLATFORM_HEIGHT*4, next_plat_y)
        plat_width = random.randint(PLATFORM_MIN_WIDTH, PLATFORM_MAX_WIDTH)
        return next_plat_x, next_plat_y, plat_width
    except Exception as e:
        print(f"ERROR during platform generation calculation: {e}"); import traceback; traceback.print_exc()
        print(f"  Ref Rect: {reference_platform.rect if reference_platform else 'None'}"); print(f"  Speed: {effective_speed:.3f}"); print(f"  Air Time: {max_air_time:.3f}")
        return None

# --- Main Game Loop Function (Using v8 Logic) ---
def game_loop(screen, clock, font):
    MAX_ESTIMATED_AIR_TIME = calculate_max_air_time()
    all_sprites = pygame.sprite.Group()
    platforms = pygame.sprite.Group()
    player = Player()
    all_sprites.add(player)

    start_platform = Platform(player.rect.centerx - 75, PLAYER_START_Y, 150)
    all_sprites.add(start_platform); platforms.add(start_platform)
    last_platform_generated = start_platform
    initial_effective_speed = PLATFORM_START_SPEED
    while last_platform_generated.rect.right < SCREEN_WIDTH + PLATFORM_MAX_GAP_X:
        platform_data = generate_next_platform(last_platform_generated, initial_effective_speed, MAX_ESTIMATED_AIR_TIME)
        if platform_data: px, py, pw = platform_data; new_platform = Platform(px, py, pw); all_sprites.add(new_platform); platforms.add(new_platform); last_platform_generated = new_platform
        else: break

    current_base_speed = PLATFORM_START_SPEED
    score = 0; game_over = False; running = True

    while running:
        for event in pygame.event.get(): # Event handling
            if event.type == pygame.QUIT: running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE and not game_over: player.jump()
                if event.key == pygame.K_ESCAPE: running = False
            if event.type == pygame.KEYUP:
                 if event.key == pygame.K_SPACE and not game_over: player.stop_jump()

        if not running: break
        if game_over: show_game_over_screen(screen, font, score // 10); game_loop(screen, clock, font); return

        current_base_speed += PLATFORM_SPEED_INCREASE # Update speed
        effective_speed = current_base_speed + PLAYER_DASH_SPEED_BONUS if player.is_dashing else current_base_speed

        player.update(platforms) # Update player (handles dash timer, animation state)
        platforms.update(effective_speed) # Update platforms with current effective speed

        platform_count = len(platforms) # Dynamic spawning
        spawn_trigger_x = SCREEN_WIDTH - PLATFORM_MIN_GAP_X
        if last_platform_generated and last_platform_generated.rect.right < spawn_trigger_x and platform_count < 12:
             platform_data = generate_next_platform(last_platform_generated, effective_speed, MAX_ESTIMATED_AIR_TIME)
             if platform_data: px, py, pw = platform_data; new_platform = Platform(px, py, pw); all_sprites.add(new_platform); platforms.add(new_platform); last_platform_generated = new_platform

        score += 1 # Score and game over check
        if player.rect.top > SCREEN_HEIGHT + player.base_height: game_over = True

        draw_sky(screen) # Drawing
        all_sprites.draw(screen)
        try: score_display = font.render(f"Score: {score // 10}", True, BLACK); screen.blit(score_display, (10, 10))
        except Exception: pass

        pygame.display.flip() # Display update
        clock.tick(FPS) # Frame rate control

    pygame.quit(); sys.exit()

# --- Initialization and Game Start ---
if __name__ == '__main__':
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Rapid Runner Polygon v8.1")
    clock = pygame.time.Clock()
    if not pygame.font.get_init(): pygame.font.init()
    try: game_font = pygame.font.Font(None, 50)
    except OSError: game_font = pygame.font.SysFont(pygame.font.get_default_font(), 50)
    try: game_loop(screen, clock, game_font)
    except Exception as e: print(f"\nFATAL ERROR: {e}"); import traceback; traceback.print_exc()
    finally: pygame.quit(); sys.exit()