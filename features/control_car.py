from inputs import get_gamepad
from picarx import Picarx
import time

px = Picarx()
speed = 0

while True:
    events = get_gamepad()
    for event in events:
        print(event.ev_type, event.code, event.state)
        if event.ev_type == 'Key':
            if event.code == 'R2' and event.state > 0:  # Avancer
                speed = 50  # Ajuste la vitesse
                px.forward(speed)
            elif event.code == 'L2' and event.state > 0:  # Reculer
                speed = 50
                px.backward(speed)
            elif event.code == 'cross':  # Arrêter
                px.stop()
        elif event.ev_type == 'Absolute':
            if event.code == 'ABS_X':  # Joystick gauche pour direction
                angle = event.state / 32767 * 30  # Ajuste l'angle
                px.set_dir_servo_angle(angle)

            elif event.code == 'ABS_Y':  # Joystick droit pour caméra (optionnel)
                tilt = event.state / 32767 * 30  # Ajuste l'angle de la caméra
                px.set_cam_tilt_angle(tilt)

    time.sleep(0.1)
