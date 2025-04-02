
document.addEventListener('DOMContentLoaded', () => {

    const canvas = document.getElementById('gameCanvas');
    const ctx = canvas.getContext('2d');

    // --- Constants ---
    const SCREEN_WIDTH = 800;
    const SCREEN_HEIGHT = 600;
    canvas.width = SCREEN_WIDTH;
    canvas.height = SCREEN_HEIGHT;

    // Player settings
    const PLAYER_WIDTH = 30;  // Collision width
    const PLAYER_HEIGHT = 45; // Collision height
    const PLAYER_DRAW_WIDTH_PADDING = 10; // Extra width for drawing surface
    const PLAYER_DRAW_HEIGHT_PADDING = 10; // Extra height for drawing surface
    const PLAYER_GRAVITY = 0.6;
    const PLAYER_JUMP_STRENGTH = -14; // Adjusted slightly
    const PLAYER_JUMP_CUTOFF_MULTIPLIER = 3; // How much gravity increases when jump key released early
    const PLAYER_BOOST_STRENGTH = -7; // Vertical boost on double jump/dash
    const PLAYER_MAX_FALL_SPEED = 18;
    const PLAYER_ANIM_SPEED = 5; // Frames per animation change (faster)
    const PLAYER_START_X = 150; // Start further in
    const PLAYER_START_Y = SCREEN_HEIGHT / 2;

    // Dash Constants
    const PLAYER_DASH_DURATION_FRAMES = 20; // Shorter dash
    const PLAYER_DASH_SPEED_BONUS = 5.0;  // Faster dash

    // Platform settings
    const PLATFORM_HEIGHT = 25;
    const PLATFORM_MIN_WIDTH = 90;
    const PLATFORM_MAX_WIDTH = 160;
    const PLATFORM_START_SPEED = 4.0;
    const PLATFORM_SPEED_INCREASE = 0.0015; // Slower increase
    const PLATFORM_MIN_GAP_X = 85; // Slightly larger min gap
    const PLATFORM_MAX_GAP_X = 220; // Slightly larger max gap
    const PLATFORM_MIN_GAP_Y = -135; // Relative to previous platform's top
    const PLATFORM_MAX_GAP_Y = 120;  // Relative to previous platform's top
    const PLATFORM_REACH_MARGIN = 35; // Increased margin for safety
    const MAX_PLATFORMS_ON_SCREEN = 12; // Limit active platforms

    // Colors
    const WHITE = 'rgb(255, 255, 255)';
    const BLACK = 'rgb(0, 0, 0)';
    // Adjusted colors slightly for better visibility if needed
    const PLAYER_COLORS = {
        skin: "rgb(255, 210, 170)", // Slightly less pale
        shirt: "rgb(50, 100, 220)", // Brighter blue
        pants: "rgb(60, 60, 70)",   // Slightly lighter pants
        shoes: "rgb(120, 90, 70)",   // Slightly lighter shoes
        dash_trail: "rgba(210, 210, 255, 0.5)", // Adjusted alpha/color
        // Add keys for specific parts if needed (e.g., leg, arm, head) for easier mapping
        leg: "rgb(60, 60, 70)",     // Same as pants
        arm: "rgb(50, 100, 220)",    // Same as shirt
        head: "rgb(255, 210, 170)",  // Same as skin
        shoe: "rgb(120, 90, 70)",   // Same as shoes
    };
    const PLATFORM_COLORS = {
        rock: "rgb(110, 100, 90)", grass: "rgb(0, 150, 0)"
    };
    const SKY_COLORS = { top: "rgb(100, 180, 255)", bottom: "rgb(220, 240, 255)" };


    // --- Game State ---
    let score = 0;
    let gameOver = false;
    let gameRunning = false; // Start paused until space pressed
    let currentBaseSpeed = PLATFORM_START_SPEED;
    let effectiveSpeed = PLATFORM_START_SPEED;
    let platforms = [];
    let lastPlatformGenerated = null;
    let player = null; // Will be initialized in resetGame
    let keys = {}; // To track key states
    let maxEstimatedAirTime = 0; // Will be calculated
    let spaceWasPressed = false; // To detect jump release

    // --- Input Handling ---
    document.addEventListener('keydown', (e) => {
        if (e.code === 'Space') keys.space = true;
        if (e.code === 'Escape') { // Allow Escape to restart if game over
            if (gameOver) resetGame();
        }
        // Prevent space bar from scrolling the page
        if (e.code === 'Space' && (gameRunning || gameOver || !gameRunning)) {
            e.preventDefault();
        }
    });
    document.addEventListener('keyup', (e) => {
        if (e.code === 'Space') {
            keys.space = false;
            spaceWasPressed = false; // Reset on key up
        }
    });

    // --- Player Class ---
    class Player {
        constructor() {
            this.collisionWidth = PLAYER_WIDTH;
            this.collisionHeight = PLAYER_HEIGHT;
            // Drawing surface is larger to contain animations
            this.drawWidth = this.collisionWidth + PLAYER_DRAW_WIDTH_PADDING;
            this.drawHeight = this.collisionHeight + PLAYER_DRAW_HEIGHT_PADDING;
            // X, Y represent the top-left of the *collision box*
            this.x = PLAYER_START_X;
            this.y = PLAYER_START_Y - this.collisionHeight; // Initial placement adjustment needed in resetGame

            // Calculate drawing offsets relative to the collision box's top-left (this.x, this.y)
            this.drawOffsetX = -PLAYER_DRAW_WIDTH_PADDING / 2;
            this.drawOffsetY = -PLAYER_DRAW_HEIGHT_PADDING / 2;

            this.velocityY = 0;
            this.onGround = false;
            this.isHoldingJump = false; // Track if space is held *during* a jump
            this.canBoost = false;      // Allowed to double jump/dash
            this.hasBoosted = false;    // Already used the boost in the current airtime
            this.isDashing = false;
            this.dashTimer = 0;

            this.animFrame = 0;
            this.animTimer = 0;
            this.poses = {};
            this.currentPoseData = {}; // Polygon points for current frame
            this.defineAnimFrames(); // Define all animation frames
            this.setPose("run", 0); // Set initial pose
        }

            // --- Animation Definition (Uses drawing surface dimensions) ---
        defineAnimFrames() {
            this.poses = {"run": [], "jump_ascend": [], "jump_descend": [], "dash": []};
            // w, h are the collision box dimensions, dw, dh are drawing surface dimensions
            const w = this.collisionWidth, h = this.collisionHeight;
            const dw = this.drawWidth, dh = this.drawHeight;
            // cx, cy are the center of the *drawing surface*
            const cx = dw / 2, cy = dh / 2;

            const head_r=w*0.18, torso_w=w*0.4, torso_h=h*0.45, limb_w=w*0.15;
            const up_limb_h=h*0.25, lo_limb_h=h*0.30, shoe_h=h*0.1, shoe_w_f=limb_w*1.5, shoe_w_b=limb_w*0.8;
            const neck_y=cy-torso_h*0.45, shoulder_y=cy-torso_h*0.4, shoulder_x_off=torso_w*0.55;
            const hip_y=cy+torso_h*0.45, hip_x_off=torso_w*0.45, knee_off_y=up_limb_h*1.1;

            // --- Generate Polygons (relative to drawing surface top-left 0,0) ---
            // Run Frames
                for (let i = 0; i < 4; i++) {
                let pose_data={}; const angle1=Math.sin(i*Math.PI/2), angle2=Math.sin((i+2)*Math.PI/2), bob=Math.abs(Math.cos(i*Math.PI/2))*3;
                const t_cx=cx+angle1*2, t_cy=cy+bob;
                pose_data["torso"]=[{x:t_cx-torso_w/2,y:t_cy-torso_h/2},{x:t_cx+torso_w/2,y:t_cy-torso_h/2},{x:t_cx+torso_w/2*0.8,y:t_cy+torso_h/2},{x:t_cx-torso_w/2*0.8,y:t_cy+torso_h/2}];
                pose_data["head"]=[{x:t_cx,y:neck_y+bob-head_r*1.5},{x:t_cx+head_r,y:neck_y+bob-head_r*0.5},{x:t_cx,y:neck_y+bob+head_r*0.5},{x:t_cx-head_r,y:neck_y+bob-head_r*0.5}];
                const sh_l={x:t_cx-shoulder_x_off,y:shoulder_y+bob}, elb_l={x:sh_l.x+Math.cos(angle1*0.8+Math.PI/2)*up_limb_h,y:sh_l.y+Math.sin(angle1*0.8+Math.PI/2)*up_limb_h}, hnd_l={x:elb_l.x+Math.cos(angle1*0.6+Math.PI/2)*lo_limb_h,y:elb_l.y+Math.sin(angle1*0.6+Math.PI/2)*lo_limb_h};
                pose_data["arm_upper_L"]=this.makeLimbPoly(sh_l,elb_l,limb_w); pose_data["arm_lower_L"]=this.makeLimbPoly(elb_l,hnd_l,limb_w*0.9);
                const sh_r={x:t_cx+shoulder_x_off,y:shoulder_y+bob}, elb_r={x:sh_r.x+Math.cos(angle2*0.8+Math.PI/2)*up_limb_h,y:sh_r.y+Math.sin(angle2*0.8+Math.PI/2)*up_limb_h}, hnd_r={x:elb_r.x+Math.cos(angle2*0.6+Math.PI/2)*lo_limb_h,y:elb_r.y+Math.sin(angle2*0.6+Math.PI/2)*lo_limb_h};
                pose_data["arm_upper_R"]=this.makeLimbPoly(sh_r,elb_r,limb_w); pose_data["arm_lower_R"]=this.makeLimbPoly(elb_r,hnd_r,limb_w*0.9);
                const hp_l={x:t_cx-hip_x_off,y:hip_y+bob}, kn_l={x:hp_l.x+Math.cos(angle2*0.9-Math.PI/2)*knee_off_y,y:hp_l.y+Math.sin(angle2*0.9-Math.PI/2)*knee_off_y}, ft_l={x:kn_l.x+Math.cos(angle2*0.7-Math.PI/2)*lo_limb_h,y:kn_l.y+Math.sin(angle2*0.7-Math.PI/2)*lo_limb_h};
                pose_data["leg_upper_L"]=this.makeLimbPoly(hp_l,kn_l,limb_w*1.1); pose_data["leg_lower_L"]=this.makeLimbPoly(kn_l,ft_l,limb_w); pose_data["shoe_L"]=[{x:ft_l.x-shoe_w_b,y:ft_l.y-shoe_h/2},{x:ft_l.x+shoe_w_f,y:ft_l.y-shoe_h/3},{x:ft_l.x+shoe_w_f*0.8,y:ft_l.y+shoe_h/2},{x:ft_l.x-shoe_w_b,y:ft_l.y+shoe_h/2}];
                const hp_r={x:t_cx+hip_x_off,y:hip_y+bob}, kn_r={x:hp_r.x+Math.cos(angle1*0.9-Math.PI/2)*knee_off_y,y:hp_r.y+Math.sin(angle1*0.9-Math.PI/2)*knee_off_y}, ft_r={x:kn_r.x+Math.cos(angle1*0.7-Math.PI/2)*lo_limb_h,y:kn_r.y+Math.sin(angle1*0.7-Math.PI/2)*lo_limb_h};
                pose_data["leg_upper_R"]=this.makeLimbPoly(hp_r,kn_r,limb_w*1.1); pose_data["leg_lower_R"]=this.makeLimbPoly(kn_r,ft_r,limb_w); pose_data["shoe_R"]=[{x:ft_r.x-shoe_w_b,y:ft_r.y-shoe_h/2},{x:ft_r.x+shoe_w_f,y:ft_r.y-shoe_h/3},{x:ft_r.x+shoe_w_f*0.8,y:ft_r.y+shoe_h/2},{x:ft_r.x-shoe_w_b,y:ft_r.y+shoe_h/2}];
                this.poses.run.push(pose_data);
            }
            // Jump Ascend Frame
            let ja_pose={}; let ja_t_cx=cx, ja_t_cy=cy-5;
            ja_pose["torso"]=[{x:ja_t_cx-torso_w/2,y:ja_t_cy-torso_h/2},{x:ja_t_cx+torso_w/2,y:ja_t_cy-torso_h/2},{x:ja_t_cx+torso_w/2*0.8,y:ja_t_cy+torso_h/2},{x:ja_t_cx-torso_w/2*0.8,y:ja_t_cy+torso_h/2}]; ja_pose["head"]=[{x:ja_t_cx,y:neck_y-5-head_r*1.5},{x:ja_t_cx+head_r,y:neck_y-5-head_r*0.5},{x:ja_t_cx,y:neck_y-5+head_r*0.5},{x:ja_t_cx-head_r,y:neck_y-5-head_r*0.5}];
            const ja_sh_l={x:ja_t_cx-shoulder_x_off,y:shoulder_y-5}, ja_sh_r={x:ja_t_cx+shoulder_x_off,y:shoulder_y-5}; const ja_elb_l={x:ja_sh_l.x-limb_w,y:ja_sh_l.y-up_limb_h}, ja_elb_r={x:ja_sh_r.x+limb_w,y:ja_sh_r.y-up_limb_h}; const ja_hnd_l={x:ja_elb_l.x,y:ja_elb_l.y-lo_limb_h}, ja_hnd_r={x:ja_elb_r.x,y:ja_elb_r.y-lo_limb_h};
            ja_pose["arm_upper_L"]=this.makeLimbPoly(ja_sh_l,ja_elb_l,limb_w); ja_pose["arm_lower_L"]=this.makeLimbPoly(ja_elb_l,ja_hnd_l,limb_w*0.9); ja_pose["arm_upper_R"]=this.makeLimbPoly(ja_sh_r,ja_elb_r,limb_w); ja_pose["arm_lower_R"]=this.makeLimbPoly(ja_elb_r,ja_hnd_r,limb_w*0.9);
            const ja_hp_l={x:ja_t_cx-hip_x_off,y:hip_y-5}, ja_hp_r={x:ja_t_cx+hip_x_off,y:hip_y-5}; const ja_kn_l={x:ja_hp_l.x+limb_w*0.5,y:ja_hp_l.y-knee_off_y*0.3}, ja_kn_r={x:ja_hp_r.x-limb_w*0.5,y:ja_hp_r.y-knee_off_y*0.3}; const ja_ft_l={x:ja_kn_l.x+limb_w,y:ja_kn_l.y+lo_limb_h*0.6}, ja_ft_r={x:ja_kn_r.x-limb_w,y:ja_kn_r.y+lo_limb_h*0.6};
            ja_pose["leg_upper_L"]=this.makeLimbPoly(ja_hp_l,ja_kn_l,limb_w*1.1); ja_pose["leg_lower_L"]=this.makeLimbPoly(ja_kn_l,ja_ft_l,limb_w); ja_pose["shoe_L"]=[{x:ja_ft_l.x-shoe_w_b,y:ja_ft_l.y-shoe_h/2},{x:ja_ft_l.x+shoe_w_f,y:ja_ft_l.y-shoe_h/3},{x:ja_ft_l.x+shoe_w_f*0.8,y:ja_ft_l.y+shoe_h/2},{x:ja_ft_l.x-shoe_w_b,y:ja_ft_l.y+shoe_h/2}];
            ja_pose["leg_upper_R"]=this.makeLimbPoly(ja_hp_r,ja_kn_r,limb_w*1.1); ja_pose["leg_lower_R"]=this.makeLimbPoly(ja_kn_r,ja_ft_r,limb_w); ja_pose["shoe_R"]=[{x:ja_ft_r.x-shoe_w_b,y:ja_ft_r.y-shoe_h/2},{x:ja_ft_r.x+shoe_w_f,y:ja_ft_r.y-shoe_h/3},{x:ja_ft_r.x+shoe_w_f*0.8,y:ja_ft_r.y+shoe_h/2},{x:ja_ft_r.x-shoe_w_b,y:ja_ft_r.y+shoe_h/2}];
            this.poses.jump_ascend.push(ja_pose);
            // Jump Descend Frame
            let jd_pose={}; let jd_t_cx=cx, jd_t_cy=cy;
            jd_pose["torso"]=[{x:jd_t_cx-torso_w/2,y:jd_t_cy-torso_h/2},{x:jd_t_cx+torso_w/2,y:jd_t_cy-torso_h/2},{x:jd_t_cx+torso_w/2*0.8,y:jd_t_cy+torso_h/2},{x:jd_t_cx-torso_w/2*0.8,y:jd_t_cy+torso_h/2}]; jd_pose["head"]=[{x:jd_t_cx,y:neck_y-head_r*1.5},{x:jd_t_cx+head_r,y:neck_y-head_r*0.5},{x:jd_t_cx,y:neck_y+head_r*0.5},{x:jd_t_cx-head_r,y:neck_y-head_r*0.5}];
            const jd_sh_l={x:jd_t_cx-shoulder_x_off,y:shoulder_y}, jd_sh_r={x:jd_t_cx+shoulder_x_off,y:shoulder_y}; const jd_elb_l={x:jd_sh_l.x+limb_w*0.5,y:jd_sh_l.y+up_limb_h*0.8}, jd_elb_r={x:jd_sh_r.x-limb_w*0.5,y:jd_sh_r.y+up_limb_h*0.8}; const jd_hnd_l={x:jd_elb_l.x,y:jd_elb_l.y+lo_limb_h}, jd_hnd_r={x:jd_elb_r.x,y:jd_elb_r.y+lo_limb_h};
            jd_pose["arm_upper_L"]=this.makeLimbPoly(jd_sh_l,jd_elb_l,limb_w); jd_pose["arm_lower_L"]=this.makeLimbPoly(jd_elb_l,jd_hnd_l,limb_w*0.9); jd_pose["arm_upper_R"]=this.makeLimbPoly(jd_sh_r,jd_elb_r,limb_w); jd_pose["arm_lower_R"]=this.makeLimbPoly(jd_elb_r,jd_hnd_r,limb_w*0.9);
            const jd_hp_l={x:jd_t_cx-hip_x_off,y:hip_y}, jd_hp_r={x:jd_t_cx+hip_x_off,y:hip_y}; const jd_kn_l={x:jd_hp_l.x-limb_w*0.2,y:jd_hp_l.y+knee_off_y*0.9}, jd_kn_r={x:jd_hp_r.x+limb_w*0.2,y:jd_hp_r.y+knee_off_y*0.9}; const jd_ft_l={x:jd_kn_l.x-limb_w*0.5,y:jd_kn_l.y+lo_limb_h}, jd_ft_r={x:jd_kn_r.x+limb_w*0.5,y:jd_kn_r.y+lo_limb_h};
            jd_pose["leg_upper_L"]=this.makeLimbPoly(jd_hp_l,jd_kn_l,limb_w*1.1); jd_pose["leg_lower_L"]=this.makeLimbPoly(jd_kn_l,jd_ft_l,limb_w); jd_pose["shoe_L"]=[{x:jd_ft_l.x-shoe_w_b,y:jd_ft_l.y-shoe_h/2},{x:jd_ft_l.x+shoe_w_f*0.8,y:jd_ft_l.y-shoe_h/3},{x:jd_ft_l.x+shoe_w_f*0.6,y:jd_ft_l.y+shoe_h/2},{x:jd_ft_l.x-shoe_w_b,y:jd_ft_l.y+shoe_h/2}];
            jd_pose["leg_upper_R"]=this.makeLimbPoly(jd_hp_r,jd_kn_r,limb_w*1.1); jd_pose["leg_lower_R"]=this.makeLimbPoly(jd_kn_r,jd_ft_r,limb_w); jd_pose["shoe_R"]=[{x:jd_ft_r.x-shoe_w_b,y:jd_ft_r.y-shoe_h/2},{x:jd_ft_r.x+shoe_w_f*0.8,y:jd_ft_r.y-shoe_h/3},{x:jd_ft_r.x+shoe_w_f*0.6,y:jd_ft_r.y+shoe_h/2},{x:jd_ft_r.x-shoe_w_b,y:jd_ft_r.y+shoe_h/2}];
            this.poses.jump_descend.push(jd_pose);
            // Dash Frame
            let d_pose={}; let d_t_cx=cx+5, d_t_cy=cy; const lean_angle=-Math.PI/10;
            d_pose["torso"]=this.rotatePoly([{x:d_t_cx-torso_w/2,y:d_t_cy-torso_h/2},{x:d_t_cx+torso_w/2,y:d_t_cy-torso_h/2},{x:d_t_cx+torso_w/2*0.8,y:d_t_cy+torso_h/2},{x:d_t_cx-torso_w/2*0.8,y:d_t_cy+torso_h/2}],{x:d_t_cx,y:d_t_cy},lean_angle); d_pose["head"]=this.rotatePoly([{x:d_t_cx,y:neck_y-head_r*1.5},{x:d_t_cx+head_r,y:neck_y-head_r*0.5},{x:d_t_cx,y:neck_y+head_r*0.5},{x:d_t_cx-head_r,y:neck_y-head_r*0.5}],{x:d_t_cx,y:d_t_cy},lean_angle);
            let d_sh_l={x:d_t_cx-shoulder_x_off,y:shoulder_y}, d_sh_r={x:d_t_cx+shoulder_x_off,y:shoulder_y}; d_sh_l=this.rotatePoint(d_sh_l,{x:d_t_cx,y:d_t_cy},lean_angle); d_sh_r=this.rotatePoint(d_sh_r,{x:d_t_cx,y:d_t_cy},lean_angle); const d_elb_l={x:d_sh_l.x-limb_w*0.5,y:d_sh_l.y+up_limb_h*0.5}, d_elb_r={x:d_sh_r.x-limb_w*0.5,y:d_sh_r.y+up_limb_h*0.5}; const d_hnd_l={x:d_elb_l.x-lo_limb_h,y:d_elb_l.y}, d_hnd_r={x:d_elb_r.x-lo_limb_h,y:d_elb_r.y};
            d_pose["arm_upper_L"]=this.makeLimbPoly(d_sh_l,d_elb_l,limb_w); d_pose["arm_lower_L"]=this.makeLimbPoly(d_elb_l,d_hnd_l,limb_w*0.9); d_pose["arm_upper_R"]=this.makeLimbPoly(d_sh_r,d_elb_r,limb_w); d_pose["arm_lower_R"]=this.makeLimbPoly(d_elb_r,d_hnd_r,limb_w*0.9);
            let d_hp_l={x:d_t_cx-hip_x_off,y:hip_y}, d_hp_r={x:d_t_cx+hip_x_off,y:hip_y}; d_hp_l=this.rotatePoint(d_hp_l,{x:d_t_cx,y:d_t_cy},lean_angle); d_hp_r=this.rotatePoint(d_hp_r,{x:d_t_cx,y:d_t_cy},lean_angle); const d_kn_l={x:d_hp_l.x-knee_off_y*0.7,y:d_hp_l.y+limb_w*0.3}, d_kn_r={x:d_hp_r.x-knee_off_y*0.6,y:d_hp_r.y-limb_w*0.2}; const d_ft_l={x:d_kn_l.x-lo_limb_h,y:d_kn_l.y}, d_ft_r={x:d_kn_r.x-lo_limb_h*0.9,y:d_kn_r.y};
            d_pose["leg_upper_L"]=this.makeLimbPoly(d_hp_l,d_kn_l,limb_w*1.1); d_pose["leg_lower_L"]=this.makeLimbPoly(d_kn_l,d_ft_l,limb_w); d_pose["shoe_L"]=[{x:d_ft_l.x-shoe_w_f,y:d_ft_l.y-shoe_h/2},{x:d_ft_l.x+shoe_w_b,y:d_ft_l.y-shoe_h/3},{x:d_ft_l.x+shoe_w_b*0.8,y:d_ft_l.y+shoe_h/2},{x:d_ft_l.x-shoe_w_f,y:d_ft_l.y+shoe_h/2}];
            d_pose["leg_upper_R"]=this.makeLimbPoly(d_hp_r,d_kn_r,limb_w*1.1); d_pose["leg_lower_R"]=this.makeLimbPoly(d_kn_r,d_ft_r,limb_w); d_pose["shoe_R"]=[{x:d_ft_r.x-shoe_w_f,y:d_ft_r.y-shoe_h/2},{x:d_ft_r.x+shoe_w_b,y:d_ft_r.y-shoe_h/3},{x:d_ft_r.x+shoe_w_b*0.8,y:d_ft_r.y+shoe_h/2},{x:d_ft_r.x-shoe_w_f,y:d_ft_r.y+shoe_h/2}];
            this.poses.dash.push(d_pose);
        }

        makeLimbPoly(startPos, endPos, width) {
            const angle=Math.atan2(endPos.y-startPos.y,endPos.x-startPos.x), pAngle=angle+Math.PI/2, w2=width/2;
            const p1={x:startPos.x+Math.cos(pAngle)*w2,y:startPos.y+Math.sin(pAngle)*w2}, p2={x:startPos.x-Math.cos(pAngle)*w2,y:startPos.y-Math.sin(pAngle)*w2};
            const p3={x:endPos.x-Math.cos(pAngle)*w2,y:endPos.y-Math.sin(pAngle)*w2}, p4={x:endPos.x+Math.cos(pAngle)*w2,y:endPos.y+Math.sin(pAngle)*w2};
            return [p1, p2, p3, p4];
        }
        rotatePoint(point, center, angleRad) {
            const {x,y}=point, {x:cx,y:cy}=center, cosA=Math.cos(angleRad), sinA=Math.sin(angleRad);
            const nx=cosA*(x-cx)-sinA*(y-cy)+cx, ny=sinA*(x-cx)+cosA*(y-cy)+cy; return {x:nx,y:ny};
        }
        rotatePoly(poly, center, angleRad) { return poly.map(p => this.rotatePoint(p, center, angleRad)); }

        setPose(poseName, frameIndex) {
            try { this.currentPoseData = this.poses[poseName][frameIndex]; }
            catch { this.currentPoseData = this.poses["run"][0]; } // Fallback
        }

        update(platforms) {
            // Dash Timer
            if (this.isDashing) {
                this.dashTimer--;
                if (this.dashTimer <= 0) this.isDashing = false;
            }

            // Gravity: Apply more gravity if jump key is released early
            const effectiveGravity = PLAYER_GRAVITY * ( (!this.isHoldingJump && this.velocityY < 0) ? PLAYER_JUMP_CUTOFF_MULTIPLIER : 1);
            this.velocityY += effectiveGravity;
            this.velocityY = Math.min(this.velocityY, PLAYER_MAX_FALL_SPEED); // Clamp fall speed

            // Vertical Movement
            this.y += this.velocityY;

            // Collision Check
            this.onGround = false; // Assume not on ground until collision confirmed
            platforms.forEach(platform => {
                // Basic BBox check first (using collision dimensions)
                if (this.x < platform.x + platform.width &&
                    this.x + this.collisionWidth > platform.x &&
                    this.y < platform.y + platform.height && // Check top collision slightly before actual position
                    this.y + this.collisionHeight > platform.y) // Check bottom collision
                {
                    // Landing check: Player moving down, and was previously above the platform top
                    if (this.velocityY >= 0 && (this.y + this.collisionHeight - this.velocityY) <= platform.y + 1 ) { // Check previous bottom pos
                        this.y = platform.y - this.collisionHeight; // Adjust position precisely onto the platform
                        this.velocityY = 0;
                        this.onGround = true;
                        this.hasBoosted = false; // Reset boost/dash on landing
                        this.canBoost = true;    // Allow boost again
                        this.isHoldingJump = false; // Reset jump hold state
                        this.isDashing = false;   // Stop dashing on landing
                        this.dashTimer = 0;
                    }
                    // Head bonk check: Player moving up, and was previously below the platform bottom
                    else if (this.velocityY < 0 && (this.y - this.velocityY) >= platform.y + platform.height - 1) {
                            this.y = platform.y + platform.height; // Adjust position to be just below
                            this.velocityY = 0; // Stop upward movement
                            this.isHoldingJump = false; // Force stop holding jump on bonk
                    }
                }
            });

            // Update Animation State
            if (this.isDashing) { this.setPose("dash", 0); }
            else if (!this.onGround) { this.setPose(this.velocityY < 0 ? "jump_ascend" : "jump_descend", 0); }
            else { // On ground
                this.animTimer++;
                if (this.animTimer >= PLAYER_ANIM_SPEED) {
                    this.animTimer = 0;
                    this.animFrame = (this.animFrame + 1) % this.poses.run.length;
                }
                this.setPose("run", this.animFrame);
            }
        }

        jump() {
            if (this.onGround) {
                this.velocityY = PLAYER_JUMP_STRENGTH;
                this.onGround = false;
                this.isHoldingJump = true; // Player is holding jump key
                this.canBoost = true;      // Can boost after this jump
                this.hasBoosted = false;
                this.isDashing = false;
                this.dashTimer = 0;
            } else if (this.canBoost && !this.hasBoosted) { // Mid-air boost/dash
                this.velocityY = PLAYER_BOOST_STRENGTH; // Give vertical boost
                this.hasBoosted = true;
                this.canBoost = false;    // Cannot boost again until landing
                this.isHoldingJump = true; // Treat boost as holding jump briefly
                // Activate Dash
                this.isDashing = true;
                this.dashTimer = PLAYER_DASH_DURATION_FRAMES;
            }
        }

        stopHoldingJump() { // Called when space key is released
                this.isHoldingJump = false;
        }

        draw(ctx) {
            if (!this.currentPoseData) return;

            // Get the top-left corner for drawing the *entire* animation surface
            const drawSurfaceX = this.x + this.drawOffsetX;
            const drawSurfaceY = this.y + this.drawOffsetY;

            // Define draw order (background to foreground)
            const drawOrder=["leg_upper_R","leg_lower_R","shoe_R","arm_upper_R","arm_lower_R","torso","leg_upper_L","leg_lower_L","shoe_L","arm_upper_L","arm_lower_L","head"];

            // Draw dash trail (behind the player)
            if (this.isDashing) {
                const trailOffset=10; // Increased offset
                const trailParts=["torso","leg_upper_L","leg_lower_L","leg_upper_R","leg_lower_R", "head"]; // Include more parts
                ctx.fillStyle = PLAYER_COLORS.dash_trail;
                trailParts.forEach(partName => {
                    if (this.currentPoseData[partName]) {
                        const poly = this.currentPoseData[partName];
                        if (poly.length < 3) return;
                        ctx.beginPath();
                        // Draw polygon points relative to the drawing surface's top-left, offset for trail
                        ctx.moveTo(drawSurfaceX + poly[0].x - trailOffset, drawSurfaceY + poly[0].y);
                        for (let i = 1; i < poly.length; i++) { ctx.lineTo(drawSurfaceX + poly[i].x - trailOffset, drawSurfaceY + poly[i].y); }
                        ctx.closePath();
                        ctx.fill();
                    }
                });
            }

            // Draw main body parts
            drawOrder.forEach(partName => {
                    const basePartName = partName.split('_')[0].toLowerCase(); // e.g., "leg" from "leg_upper_R"
                    const color = PLAYER_COLORS[basePartName] || PLAYER_COLORS.shirt; // Use base part name for color lookup

                    if (this.currentPoseData[partName]) {
                    const poly = this.currentPoseData[partName];
                    if (poly.length < 3) return; // Skip if not enough points

                    ctx.fillStyle = color;
                    ctx.beginPath();
                    // Draw polygon points relative to the drawing surface's top-left
                    ctx.moveTo(drawSurfaceX + poly[0].x, drawSurfaceY + poly[0].y);
                    for (let i = 1; i < poly.length; i++) {
                        ctx.lineTo(drawSurfaceX + poly[i].x, drawSurfaceY + poly[i].y);
                    }
                    ctx.closePath();
                    ctx.fill();
                    // Optional Outline (can make character clearer):
                    // ctx.strokeStyle = BLACK;
                    // ctx.lineWidth = 0.5;
                    // ctx.stroke();
                    }
            });

            // --- Debug Drawing (Optional) ---
            // ctx.strokeStyle = 'red';
            // ctx.lineWidth = 1;
            // ctx.strokeRect(this.x, this.y, this.collisionWidth, this.collisionHeight); // Collision box
            // ctx.strokeStyle = 'blue';
            // ctx.strokeRect(drawSurfaceX, drawSurfaceY, this.drawWidth, this.drawHeight); // Drawing surface
            // --- End Debug Drawing ---
        }

        // --- Getters for collision bounding box ---
        get left() { return this.x; }
        get right() { return this.x + this.collisionWidth; }
        get top() { return this.y; }
        get bottom() { return this.y + this.collisionHeight; }
    }

    // --- Platform Class ---
    class Platform {
        constructor(x, y, width) {
            this.x = x;
            this.y = y;
            this.width = width;
            this.height = PLATFORM_HEIGHT;
            this.shouldRemove = false; // Flag for removal
            this.grassHeight = Math.max(5, this.height / 4); // Consistent grass height

            // Pre-calculate some random details for appearance (optional)
            this.rockLines = [];
            for (let i = 0; i < Math.floor(this.width / 12); i++) { // Fewer lines
                const lineY = Math.random() * (this.height - this.grassHeight - 5) + this.grassHeight + 3; // Ensure within rock part
                const startX = Math.random() * (this.width - 10);
                const endX = startX + Math.random() * 8 + 2;
                const shade = Math.floor(Math.random() * 31) - 15; // +/- 15 shade variation
                this.rockLines.push({ y: lineY, x1: startX, x2: endX, color: `rgb(${110+shade}, ${100+shade}, ${90+shade})` });
            }
            this.grassBlades = [];
            for (let i = 0; i < Math.floor(this.width / 4); i++) { // Fewer blades
                    const bladeX = Math.random() * this.width;
                    const bladeH = Math.random() * 5 + 3; // Slightly taller range
                    const bladeDX = Math.random() * 2 - 1; // Angle variation
                    const shadeG = Math.floor(Math.random() * 41) - 20; // +/- 20 green shade
                    const shadeRB = Math.floor(Math.random() * 21) - 10; // +/- 10 red/blue tint
                    this.grassBlades.push({x:bladeX, h:bladeH, dx: bladeDX, color:`rgb(${0+shadeRB}, ${150+shadeG}, ${0+shadeRB})`});
            }
        }

        update(speed) {
            this.x -= speed;
            if (this.x + this.width < 0) { // Remove when fully off-screen left
                this.shouldRemove = true;
            }
        }

        draw(ctx) {
            // Rock base
            ctx.fillStyle = PLATFORM_COLORS.rock;
            ctx.fillRect(this.x, this.y + this.grassHeight, this.width, this.height - this.grassHeight);

            // Rock lines
            ctx.lineWidth = 1;
            this.rockLines.forEach(line => {
                ctx.strokeStyle = line.color;
                ctx.beginPath();
                ctx.moveTo(this.x + line.x1, this.y + line.y);
                ctx.lineTo(this.x + line.x2, this.y + line.y);
                ctx.stroke();
            });

            // Grass top
            ctx.fillStyle = PLATFORM_COLORS.grass;
            ctx.fillRect(this.x, this.y, this.width, this.grassHeight);

            // Grass blades
            ctx.lineWidth = 1; // Ensure consistent line width
            this.grassBlades.forEach(blade => {
                    ctx.strokeStyle = blade.color;
                    ctx.beginPath();
                    ctx.moveTo(this.x + blade.x, this.y + this.grassHeight); // Start at grass top edge
                    ctx.lineTo(this.x + blade.x + blade.dx, this.y + this.grassHeight - blade.h); // End above edge
                    ctx.stroke();
            });
        }
    }

    // --- Helper: Draw Sky ---
    function drawSky(ctx) {
        const gradient = ctx.createLinearGradient(0, 0, 0, SCREEN_HEIGHT);
        gradient.addColorStop(0, SKY_COLORS.top);
        gradient.addColorStop(1, SKY_COLORS.bottom);
        ctx.fillStyle = gradient;
        ctx.fillRect(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT);
    }

    // --- Helper: Calculate Max Air Time (Approximation) ---
    function calculateMaxAirTime() {
        // Simulate a jump and boost to find approx max height and air time
        // This is complex to get perfect due to variable jump height and cut-off multiplier
        // Let's use a simplified estimate based on full jump + boost peak
            if (PLAYER_GRAVITY <= 0) return Infinity;

        // Time to peak of initial jump (if held)
        let v = PLAYER_JUMP_STRENGTH;
        let y = 0;
        let t = 0;
        while(v < 0){
            v += PLAYER_GRAVITY;
            y += v;
            t++;
        }
        const initialJumpPeakTime = t / 60; // Approx time in seconds (assuming 60fps)

        // Simulate boost applied at peak (simplification)
        v = PLAYER_BOOST_STRENGTH;
        let t_boost = 0;
            while(v < 0){
            v += PLAYER_GRAVITY;
            t_boost++;
            }
            const boostPeakTime = t_boost / 60;

            // Max height estimate (very rough)
            const maxEstHeight = Math.abs(PLAYER_JUMP_STRENGTH*initialJumpPeakTime + 0.5*PLAYER_GRAVITY*(initialJumpPeakTime**2))
                                + Math.abs(PLAYER_BOOST_STRENGTH*boostPeakTime + 0.5*PLAYER_GRAVITY*(boostPeakTime**2));

            // Time to fall from max height + max downward gap
            const fallDistance = maxEstHeight + Math.abs(PLATFORM_MIN_GAP_Y) + PLATFORM_HEIGHT; // Consider lowest possible next plat
            const timeToFall = Math.sqrt(2 * fallDistance / PLAYER_GRAVITY);

            // Total estimated time
            const totalTime = initialJumpPeakTime + boostPeakTime + timeToFall;

            return totalTime * 0.9; // Return time in seconds, maybe with slight reduction factor
    }


        // --- Helper: Generate Next Platform ---
    function generateNextPlatform(referencePlatform, currentEffSpeed, maxAirSeconds) {
        if (!referencePlatform) return null;

        try {
            // Max distance reachable *theoretically* during max air time
            const maxReachX = maxAirSeconds * currentEffSpeed * 60; // Convert air time (seconds) to frames * speed

            // Clamp X gap using constants and reachability
            let minGapX = PLATFORM_MIN_GAP_X;
            let maxGapX = Math.min(PLATFORM_MAX_GAP_X, maxReachX * 1.1); // Allow slightly exceeding theoretical max
            if (maxGapX < minGapX) {
                maxGapX = minGapX * 1.2; // Ensure max is always > min
            }
            const actualGapX = Math.random() * (maxGapX - minGapX) + minGapX;

            // Estimate Y position based on a standard jump trajectory over the chosen gap X
            const timeToCrossGapFrames = (currentEffSpeed > 0.01) ? actualGapX / currentEffSpeed : 0;
            const playerDeltaY = (PLAYER_JUMP_STRENGTH * (timeToCrossGapFrames/60.0)) + (0.5 * PLAYER_GRAVITY * (timeToCrossGapFrames/60.0)**2 * 60.0); // Simplified physics
            // Player's approximate Y position relative to the start platform's Y when crossing the gap
            const estimatedPlayerY = referencePlatform.y + playerDeltaY;

            // Determine valid Y range for the next platform top
            // Lower bound: Player must be able to land on it after standard jump, plus margin
            const minYBasedOnReach = estimatedPlayerY + PLATFORM_REACH_MARGIN;
            // Upper bound: Player must be able to jump *up* to it
            const maxYBasedOnReach = referencePlatform.y + PLATFORM_MIN_GAP_Y; // Highest relative jump allowed by constants

            // Combine reachability bounds with design bounds
            let finalMinY = Math.max(referencePlatform.y + PLATFORM_MIN_GAP_Y, minYBasedOnReach);
            let finalMaxY = Math.min(referencePlatform.y + PLATFORM_MAX_GAP_Y, maxYBasedOnReach + PLATFORM_MAX_WIDTH*2); // Give more upper leeway?

            // Clamp Y within screen limits and ensure min <= max
            finalMinY = Math.max(PLATFORM_HEIGHT * 2, finalMinY); // Keep away from screen top
            finalMaxY = Math.min(SCREEN_HEIGHT - PLATFORM_HEIGHT * 3, finalMaxY); // Keep away from screen bottom

            if (finalMinY > finalMaxY) {
                // If calculations lead to impossible range, create a relatively safe platform
                finalMinY = referencePlatform.y - 30;
                finalMaxY = referencePlatform.y + 30;
                    // Re-clamp
                finalMinY = Math.max(PLATFORM_HEIGHT * 2, finalMinY);
                finalMaxY = Math.min(SCREEN_HEIGHT - PLATFORM_HEIGHT * 3, finalMaxY);
                if (finalMinY > finalMaxY) { // Last resort
                        finalMinY = SCREEN_HEIGHT / 2 - 50;
                        finalMaxY = SCREEN_HEIGHT / 2 + 50;
                }
            }

            const actualOffsetY = Math.random() * (finalMaxY - finalMinY) + finalMinY - referencePlatform.y;
            const nextPlatX = referencePlatform.x + referencePlatform.width + actualGapX;
            const nextPlatY = referencePlatform.y + actualOffsetY;
            const platWidth = Math.random() * (PLATFORM_MAX_WIDTH - PLATFORM_MIN_WIDTH) + PLATFORM_MIN_WIDTH;

            // Ensure Y is valid before returning
            const clampedY = Math.max(PLATFORM_HEIGHT * 2, Math.min(SCREEN_HEIGHT - PLATFORM_HEIGHT * 3, nextPlatY));

            return { x: nextPlatX, y: clampedY, width: platWidth };

        } catch (e) {
            console.error("Error during platform generation:", e);
            // Fallback: create a safe platform near the last one
            const fallbackX = (referencePlatform.x + referencePlatform.width + PLATFORM_MIN_GAP_X + 20);
            const fallbackY = Math.max(PLATFORM_HEIGHT * 2, Math.min(SCREEN_HEIGHT - PLATFORM_HEIGHT*3, referencePlatform.y));
            const fallbackW = PLATFORM_MIN_WIDTH + 20;
            return { x: fallbackX, y: fallbackY, width: fallbackW };
        }
    }


    // --- Helper: Draw Score ---
    function drawScore(ctx) {
        ctx.fillStyle = BLACK;
        ctx.font = 'bold 28px Arial'; // Slightly smaller, bold
        ctx.textAlign = 'left';
        ctx.textBaseline = 'top';
        ctx.fillText(`Score: ${Math.floor(score / 10)}`, 15, 15); // Padding
    }

        // --- Helper: Draw Start/Game Over Screen ---
    function drawOverlay(ctx, title, scoreText, instruction) {
        // Semi-transparent background
        ctx.fillStyle = 'rgba(0, 0, 0, 0.7)'; // Darker overlay
        ctx.fillRect(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT);

        // Text styling
        ctx.fillStyle = WHITE;
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';

        // Title
        ctx.font = 'bold 70px Arial';
        ctx.fillText(title, SCREEN_WIDTH / 2, SCREEN_HEIGHT / 3);

        // Score (if provided)
        if (scoreText) {
            ctx.font = '45px Arial';
            ctx.fillText(scoreText, SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 + 10); // Adjust vertical pos
        }

        // Instruction
        ctx.font = '35px Arial'; // Larger instruction
        ctx.fillText(instruction, SCREEN_WIDTH / 2, SCREEN_HEIGHT * 2 / 3 + 20); // Adjust vertical pos
    }


    // --- Reset Game ---
    function resetGame() {
        console.log("Resetting game...");
        score = 0;
        gameOver = false;
        gameRunning = true; // Game is active now
        currentBaseSpeed = PLATFORM_START_SPEED;
        effectiveSpeed = PLATFORM_START_SPEED;
        platforms = [];
        player = new Player(); // Create new player instance

        // Create starting platform
        const startPlatformWidth = 200; // Wider start platform
        const startX = player.x + player.collisionWidth / 2 - startPlatformWidth / 2; // Center under player start
        const startY = PLAYER_START_Y + 20; // Place slightly below player's logical start Y
        const startPlatform = new Platform(startX, startY, startPlatformWidth);
        platforms.push(startPlatform);
        lastPlatformGenerated = startPlatform;

        // Correct player's initial Y position to be on the start platform
        player.y = startPlatform.y - player.collisionHeight;
        player.onGround = true;
        player.velocityY = 0; // Ensure no initial velocity


        // Initial Screen Population
            maxEstimatedAirTime = calculateMaxAirTime(); // Calculate based on constants (result in seconds)
            console.log("Max Est Air Time (s):", maxEstimatedAirTime);

        while (lastPlatformGenerated.x + lastPlatformGenerated.width < SCREEN_WIDTH + PLATFORM_MAX_GAP_X * 1.5) { // Generate further out
            const platformData = generateNextPlatform(lastPlatformGenerated, PLATFORM_START_SPEED, maxEstimatedAirTime);
            if (platformData && platformData.x > lastPlatformGenerated.x + lastPlatformGenerated.width + PLATFORM_MIN_GAP_X/2) { // Basic sanity check on X pos
                const newPlatform = new Platform(platformData.x, platformData.y, platformData.width);
                platforms.push(newPlatform);
                lastPlatformGenerated = newPlatform;
            } else {
                console.warn("Failed to generate a valid initial platform or too close, stopping population early.");
                // Try generating one more safe platform if list is short
                if (platforms.length < 3) {
                        const safeX = lastPlatformGenerated.x + lastPlatformGenerated.width + PLATFORM_MIN_GAP_X + 50;
                        const safeY = Math.max(PLATFORM_HEIGHT * 2, Math.min(SCREEN_HEIGHT - PLATFORM_HEIGHT*3, lastPlatformGenerated.y));
                        const safeW = PLATFORM_MIN_WIDTH + 30;
                        const safePlat = new Platform(safeX, safeY, safeW);
                        platforms.push(safePlat);
                        lastPlatformGenerated = safePlat;
                        console.log("Added a fallback safe platform.");
                } else {
                    break; // Stop if generation fails consistently
                }
            }
                if (platforms.length > MAX_PLATFORMS_ON_SCREEN + 5) break; // Prevent infinite loop
        }
        console.log("Initial platforms generated:", platforms.length);


        // Clear any lingering key presses
        keys = {};
        spaceWasPressed = false;

        // Loop is already running via requestAnimationFrame
    }

    // --- Game Loop ---
    let lastTime = 0;
    let frameCount = 0; // For delta time calculation

    function gameLoop(timestamp) {
        // Calculate delta time (in seconds)
        const deltaTime = (timestamp - lastTime) / 1000;
        lastTime = timestamp;
        // Cap delta time to prevent large jumps if tab loses focus
        const cappedDeltaTime = Math.min(deltaTime, 1 / 30); // Max delta = 1/30th second

        // --- State Handling ---
        if (!gameRunning && !gameOver) {
            // Title Screen
            drawSky(ctx); // Draw background for title
            drawOverlay(ctx, "Rapid Runner", null, "Press SPACE to Start");
            if (keys.space) {
                    resetGame(); // This sets gameRunning = true
                    keys.space = false; // Consume the key press
                    spaceWasPressed = true;
            }
            requestAnimationFrame(gameLoop); // Keep checking for start input
            return;
        }

            if (gameOver) {
                // Game Over Screen
                drawOverlay(ctx, "GAME OVER!", `Score: ${Math.floor(score / 10)}`, "Press SPACE to Restart");
                if (keys.space) {
                    resetGame();
                    keys.space = false; // Consume key press
                    spaceWasPressed = true;
                }
                requestAnimationFrame(gameLoop); // Keep checking for restart input
                return;
        }

        // --- Input Checks (Inside Active Game) ---
        // Handle jump/dash press (only process press once)
        if (keys.space && !spaceWasPressed) {
            player.jump(); // Attempts jump or boost/dash
            spaceWasPressed = true; // Mark that the press has been handled for this hold
        }
        // Handle jump release (for variable height)
        if (!keys.space && player.isHoldingJump) { // If key released while player thinks they are holding jump
                player.stopHoldingJump();
        }


        // --- Updates (Use cappedDeltaTime for physics/speed) ---
            const speedIncrementFactor = 60; // Assuming base constants balanced for 60fps
            currentBaseSpeed += PLATFORM_SPEED_INCREASE * cappedDeltaTime * speedIncrementFactor;
            effectiveSpeed = currentBaseSpeed + (player.isDashing ? PLAYER_DASH_SPEED_BONUS : 0);

        player.update(platforms); // Update player physics, animation, dash timer
        platforms.forEach(platform => platform.update(effectiveSpeed)); // Update platform positions

        // Remove off-screen platforms
        platforms = platforms.filter(platform => !platform.shouldRemove);

        // Dynamic Platform Spawning
        const platformCount = platforms.length;
        const spawnTriggerX = SCREEN_WIDTH + PLATFORM_MAX_GAP_X; // Spawn when last platform's *start* is further out
        if (lastPlatformGenerated && lastPlatformGenerated.x < spawnTriggerX && platformCount < MAX_PLATFORMS_ON_SCREEN)
        {
            // Recalculate air time estimate occasionally if needed, or use initial estimate
            // maxEstimatedAirTime = calculateMaxAirTime();
            const platformData = generateNextPlatform(lastPlatformGenerated, effectiveSpeed, maxEstimatedAirTime);
            if (platformData && platformData.x > lastPlatformGenerated.x + lastPlatformGenerated.width + PLATFORM_MIN_GAP_X / 2) { // Check X again
                const newPlatform = new Platform(platformData.x, platformData.y, platformData.width);
                platforms.push(newPlatform);
                lastPlatformGenerated = newPlatform; // Update reference *only* if successfully generated
            } else if (platformData) {
                // console.log("Skipped generating platform too close or invalid:", platformData.x, lastPlatformGenerated.x + lastPlatformGenerated.width);
            }
        }

            // --- Score & Game Over Check ---
            score++; // Simple frame-based score increment
            if (player.top > SCREEN_HEIGHT + player.collisionHeight) { // Player fell off bottom (give buffer)
            gameOver = true;
            gameRunning = false;
            }


        // --- Drawing ---
        drawSky(ctx); // Background first
        platforms.forEach(platform => platform.draw(ctx));
        player.draw(ctx);
        drawScore(ctx); // UI on top


        // --- Next Frame ---
        requestAnimationFrame(gameLoop);
    }

    // --- Initial Start ---
    // Don't reset immediately, show title screen first by starting the loop
    requestAnimationFrame(gameLoop);

}); // End DOMContentLoaded