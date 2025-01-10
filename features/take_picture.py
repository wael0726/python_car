#!/usr/bin/env python3

from robot_hat.utils import reset_mcu
from picarx import Picarx
from vilib import Vilib
from time import sleep, time, strftime, localtime
import readchar
import os

user = os.getlogin()
user_home = os.path.expanduser(f'~{user}')

reset_mcu()
sleep(0.2)

manual = '''
Press key to call the function (non-case sensitive):

    O: speed up
    P: speed down
    W: forward
    S: backward
    A: turn left
    D: turn right
    F: stop
    T: take photo

    Ctrl+C: quit
'''

px = Picarx()
def take_photo():
    _time = strftime('%Y-%m-%d-%H-%M-%S', localtime(time()))
    name = 'photo_%s' % _time
    path = f"{user_home}/Pictures/picar-x/"
    Vilib.take_photo(name, path)
    print('\nPhoto saved as %s%s.jpg' % (path, name))

def move(operate: str, speed):
    if operate == 'stop':
        px.stop()
    else:
        if operate == 'forward':
            px.set_dir_servo_angle(0)
            px.forward(speed)
        elif operate == 'backward':
            px.set_dir_servo_angle(0)
            px.backward(speed)
        elif operate == 'turn left':
            px.set_dir_servo_angle(-30)  # Tourner légèrement à gauche
            px.forward(speed)  # Avancer vers la gauche
        elif operate == 'turn right':
            px.set_dir_servo_angle(30)  # Tourner légèrement à droite
            px.forward(speed)  # Avancer vers la droite

# Fonction principale
def main():
    speed = 0
    status = 'stop'

    # Démarrer la caméra et l'affichage
    Vilib.camera_start(vflip=False, hflip=False)
    Vilib.display(local=True, web=True)
    sleep(2)  # Attendre le démarrage
    print(manual)

    while True:
        # Afficher le statut et la vitesse
        print("\rStatus: %s , Speed: %s    " % (status, speed), end='', flush=True)

        # Lire une touche
        key = readchar.readkey().lower()

        # Traiter les actions selon la touche appuyée
        if key in ('wsadfop'):
            # Accélérer ou ralentir
            if key == 'o':
                if speed <= 90:
                    speed += 10
            elif key == 'p':
                if speed >= 10:
                    speed -= 10
                if speed == 0:
                    status = 'stop'
            # Direction (avant, arrière, gauche, droite)
            elif key in ('wsad'):
                if speed == 0:
                    speed = 10
                if key == 'w':
                    if status != 'backward' and speed > 60:  
                        speed = 60
                    status = 'backward'
                elif key == 'a':
                    status = 'turn left'  # Tourner à gauche tout en avançant
                elif key == 's':
                    if status != 'forward' and speed > 60: 
                        speed = 60
                    status = 'forward'
                elif key == 'd':
                    status = 'backward'  
            elif key == 'f':
                status = 'stop'
            move(status, speed)

        # Prendre une photo
        elif key == 't':
            take_photo()

        # Quitter
        elif key == readchar.key.CTRL_C:
            print('\nQuit...')
            px.stop()
            Vilib.camera_close()
            break

        sleep(0.1)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print("Error: %s" % e)
    finally:
        px.stop()
        Vilib.camera_close()