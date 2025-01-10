from pydoc import text
from vilib import Vilib
from time import sleep, time, strftime, localtime
import threading
import readchar
import os

flag_face = False
flag_color = False
qr_code_flag = False

manual = '''
Input key to call the function!
    q: Take photo
    1: Color detect : red
    2: Color detect : orange
    3: Color detect : yellow
    4: Color detect : green
    5: Color detect : blue
    6: Color detect : purple
    0: Switch off Color detect
    r: Scan the QR code
    f: Switch ON/OFF face detect
    s: Display detected object information
'''

color_list = ['close', 'red', 'orange', 'yellow',
        'green', 'blue', 'purple',
]

def face_detect(flag):
    print("Face Detect:", flag)
    if flag:
        print("Activation de la détection de visage.")
    else:
        print("Désactivation de la détection de visage.")
    Vilib.face_detect_switch(flag)

def qrcode_detect():
    global qr_code_flag
    if qr_code_flag:
        Vilib.qrcode_detect_switch(True)
        print("Waiting for QR code...")
    text = None
    while True:
        temp = Vilib.detect_obj_parameter['qr_data']
        if temp != "None" and temp != text:
            text = temp
            print('QR code detected: %s' % text)
        if not qr_code_flag:
            break
        sleep(0.5)
    Vilib.qrcode_detect_switch(False)

def take_photo():
    _time = strftime('%Y-%m-%d-%H-%M-%S', localtime(time()))
    name = f'photo_{_time}'
    username = os.getlogin()

    path = f"/home/{username}/Pictures/"
    print(f"Prise de photo, enregistrement à : {path}{name}.jpg")

    # Vérification des permissions
    if not os.access(path, os.W_OK):
        print(f"Erreur: Impossible d'écrire dans {path}. Vérifiez les permissions.")
        return

    Vilib.take_photo(name, path)
    print(f'Photo sauvegardée sous {path}{name}.jpg')

def object_show():
    global flag_color, flag_face

    print("Vérification de la détection d'objets...")

    if flag_color:
        print(f"Détection de couleur active : {Vilib.detect_obj_parameter['color_n']}")
        if Vilib.detect_obj_parameter['color_n'] == 0:
            print('Color Detect: Aucun objet détecté')
        else:
            color_coordinate = (Vilib.detect_obj_parameter['color_x'], Vilib.detect_obj_parameter['color_y'])
            color_size = (Vilib.detect_obj_parameter['color_w'], Vilib.detect_obj_parameter['color_h'])
            print("[Color Detect] ", "Coordonnée:", color_coordinate, "Taille", color_size)

    if flag_face:
        print(f"Détection de visage active : {Vilib.detect_obj_parameter['human_n']}")
        if Vilib.detect_obj_parameter['human_n'] == 0:
            print('Face Detect: Aucun visage détecté')
        else:
            human_coordinate = (Vilib.detect_obj_parameter['human_x'], Vilib.detect_obj_parameter['human_y'])
            human_size = (Vilib.detect_obj_parameter['human_w'], Vilib.detect_obj_parameter['human_h'])
            print("[Face Detect] ", "Coordonnée:", human_coordinate, "Taille", human_size)

def main():
    global flag_face, flag_color, qr_code_flag
    qrcode_thread = None

    print(manual)

    # Initialisation de la caméra
    print("Initialisation de la caméra...")
    Vilib.camera_start(vflip=False, hflip=False)
    Vilib.display(local=True, web=True)

    while True:
        # Lecture de la touche pressée
        key = readchar.readkey()
        key = key.lower()
        print(f"Touche pressée: {key}")

        # Prendre une photo
        if key == 'q':
            take_photo()

        # Détection de couleur
        elif key in ('0123456'):
            index = int(key)
            if index == 0:
                flag_color = False
                Vilib.color_detect('close')
            else:
                flag_color = True
                Vilib.color_detect(color_list[index])
            print(f'Détection de couleur : {color_list[index]}')

        # Détection de visage
        elif key == "f":
            flag_face = not flag_face
            face_detect(flag_face)

        # Détection de QR code
        elif key == "r":
            qr_code_flag = not qr_code_flag
            if qr_code_flag:
                if qrcode_thread is None or not qrcode_thread.is_alive():
                    qrcode_thread = threading.Thread(target=qrcode_detect)
                    qrcode_thread.daemon = True
                    qrcode_thread.start()
            else:
                if qrcode_thread is not None and qrcode_thread.is_alive():
                    qrcode_thread.join()
                    print('QRcode Detect: Fermé')

        # Afficher les informations détectées
        elif key == "s":
            object_show()

        sleep(0.5)

if __name__ == "__main__":
    main()
