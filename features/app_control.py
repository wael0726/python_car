from sunfounder_controller import SunFounderController
from picarx import Picarx
from robot_hat import utils, Music
from vilib import Vilib
import os
from time import sleep

utils.reset_mcu()
sleep(0.2)

sc = SunFounderController()
sc.set_name('Picarx-001')
sc.set_type('Picarx')
sc.start()

# Init Picarx
px = Picarx()
speed = 0

current_line_state = None
last_line_state = "stop"
LINE_TRACK_SPEED = 10
LINE_TRACK_ANGLE_OFFSET = 21

AVOID_OBSTACLES_SPEED = 40
SafeDistance = 40 
DangerDistance = 20  

DETECT_COLOR = 'red' 

User = os.popen('echo ${SUDO_USER:-$LOGNAME}').readline().strip()
UserHome = os.popen('getent passwd %s | cut -d: -f 6' % User).readline().strip()

music = Music()
if os.geteuid() != 0:
    print('\033[33mPlay sound needs to be run with sudo.\033[m')

def horn(): 
    _status, _result = utils.run_command('sudo killall pulseaudio')
    music.sound_play_threading(f'{UserHome}/picar-x/sounds/car-double-horn.wav')

def avoid_obstacles():
    distance = px.get_distance()
    if distance >= SafeDistance:
        px.set_dir_servo_angle(0)
        px.backward(AVOID_OBSTACLES_SPEED)
    elif distance >= DangerDistance:
        px.set_dir_servo_angle(30)
        px.backward(AVOID_OBSTACLES_SPEED)
        sleep(0.1)
    else:
        px.set_dir_servo_angle(-30)
        px.forward(AVOID_OBSTACLES_SPEED)
        sleep(0.5) 

def get_status(val_list):
    _state = px.get_line_status(val_list)  # [bool, bool, bool]
    if _state == [0, 0, 0]:
        return 'stop'
    elif _state[1] == 1:
        return 'forward'
    elif _state[0] == 1:
        return 'right'
    elif _state[2] == 1:
        return 'left'

def outHandle():
    global last_line_state
    if last_line_state == 'left':
        px.set_dir_servo_angle(-30)
        px.backward(10)
    elif last_line_state == 'right':
        px.set_dir_servo_angle(90)
        px.forward(10)
    while True:
        gm_val_list = px.get_grayscale_data()
        gm_state = get_status(gm_val_list)
        current_state = gm_state
        if current_state != last_line_state:
            break
    sleep(0.001)

def line_track():
    global last_line_state
    gm_val_list = px.get_grayscale_data()
    gm_state = get_status(gm_val_list)

    if gm_state != "stop":
        last_line_state = gm_state

    if gm_state == 'forward':
        px.set_dir_servo_angle(0)
        px.backward(LINE_TRACK_SPEED) 
    elif gm_state == 'left':
        px.set_dir_servo_angle(LINE_TRACK_ANGLE_OFFSET)
        px.backward(LINE_TRACK_SPEED) 
    elif gm_state == 'right':
        # Réduisez l'angle pour tourner à droite
        adjusted_angle = -LINE_TRACK_ANGLE_OFFSET + 40  
        px.set_dir_servo_angle(adjusted_angle)
        px.backward(LINE_TRACK_SPEED) 
    else:
        outHandle()

def main():
    global speed

    ip = utils.get_ip()
    print('ip : %s' % ip)
    sc.set('video', 'http://' + ip + ':9000/mjpg')

    Vilib.camera_start(vflip=False, hflip=False)
    Vilib.display(local=False, web=True)
    speak = None
    while True:
        sc.set("A", speed)
        grayscale_data = px.get_grayscale_data()
        sc.set("D", grayscale_data)
        distance = px.get_distance()
        sc.set("F", distance)

        if sc.get('M'):
            horn()

        if sc.get('J') is not None:
            speak = sc.get('J')
            print(f'speaker: {speak}')
        if speak == "forward":
            px.backward(speed)
        elif speak == "backward":
            px.backward(speed)
        elif speak == "left":
            px.set_dir_servo_angle(-30)
            px.backward(60)
            sleep(1.2)
            px.set_dir_servo_angle(0)
            px.backward(speed)
        elif speak in ["right", "white", "rice"]:
            px.set_dir_servo_angle(30)
            px.backward(60)
            sleep(1.2)
            px.set_dir_servo_angle(0)
            px.backward(speed)
        elif speak == "stop":
            px.stop()

        line_track_switch = sc.get('I')
        avoid_obstacles_switch = sc.get('E')
        if line_track_switch:
            speed = LINE_TRACK_SPEED
            line_track()
        elif avoid_obstacles_switch:
            speed = AVOID_OBSTACLES_SPEED
            avoid_obstacles()
    
        if not line_track_switch and not avoid_obstacles_switch:
            Joystick_K_Val = sc.get('K')
            if Joystick_K_Val is not None:
                dir_angle = utils.mapping(Joystick_K_Val[0], -100, 100, -30, 30)
                
                if abs(Joystick_K_Val[0]) < 10:  # Ajuste la valeur pour la zone morte
                    dir_angle = 0  # Neutralise l'angle si dans la zone morte
                
                if dir_angle > 0:  # Si on tourne à droite
                    dir_angle += 10  # Ajuste pour un virage plus doux
                
                speed = Joystick_K_Val[1]

                print(f" Value: {Joystick_K_Val}, Direction: {dir_angle}, Speed: {speed}")  # Debug

                px.set_dir_servo_angle(dir_angle)
                
                if speed > 0:
                    px.backward(speed)
                elif speed < 0:
                    px.forward(-speed)
                else:
                    px.stop()

        Joystick_Q_Val = sc.get('Q')
        if Joystick_Q_Val is not None:
            pan = min(90, max(-90, Joystick_Q_Val[0]))
            tilt = min(120, max(-15, Joystick_Q_Val[1]))
            px.set_cam_pan_angle(pan)
            px.set_cam_tilt_angle(tilt)

        if sc.get('N'):
            Vilib.color_detect(DETECT_COLOR)
        else:
            Vilib.color_detect("close")

        if sc.get('O'):
            Vilib.face_detect_switch(True)  
        else:
            Vilib.face_detect_switch(False)  

        if sc.get('P'):
            Vilib.object_detect_switch(True) 
        else:
            Vilib.object_detect_switch(False)

if __name__ == "__main__":
    try:
        main()
    finally:
        print("stop and exit")
        px.stop()
        Vilib.camera_close()
