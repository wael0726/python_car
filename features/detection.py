from picarx import Picarx
from time import sleep
from robot_hat import TTS
from vilib import Vilib 

tts = TTS()
tts.lang("en-US")
px = Picarx()

# Activation des détections de couleur et de visage
flag_face = True
flag_color = True

# Détection de la couleur rouge
def color_detect():
    global flag_color
    if flag_color:
        Vilib.color_detect('red')  # Activer la détection de couleur rouge
    else:
        Vilib.color_detect('close')  # Désactiver la détection de couleur

# Détection du visage
def face_detect():
    global flag_face
    if flag_face:
        Vilib.face_detect_switch(True)  # Activer la détection de visage
    else:
        Vilib.face_detect_switch(False)  # Désactiver la détection de visage

# Fonction pour faire avancer la voiture
def move_forward():
    print("La voiture avance.")
    px.set_dir_servo_angle(15)  # Ajuste l'angle du servo pour tourner légèrement à droite
    px.backward(10)  

# Fonction pour arrêter la voiture pendant 3 secondes
def stop_and_wait():
    print("Arrêt du véhicule pendant 3 secondes.")
    px.stop()  # Arrêter la voiture
    sleep(3)    # Attente de 3 secondes
    move_forward()  # Reprendre le mouvement en avant

# Fonction pour vérifier la détection d'objet
def object_show():
    if Vilib.detect_obj_parameter['color_n'] > 0:
        print("Couleur rouge détectée!")
        stop_and_wait()  # Si la couleur rouge est détectée, arrêter et attendre

    if Vilib.detect_obj_parameter['human_n'] > 0:
        print("Visage détecté!")
        stop_and_wait()  # Si un visage est détecté, arrêter et attendre

def main():
    # Initialisation de la caméra
    print("Initialisation de la caméra...")
    Vilib.camera_start(vflip=False, hflip=False)  # Démarrer la caméra avec options de miroir si nécessaire
    Vilib.display(local=True, web=True)  # Affichage local et web du flux caméra

    # Initialisation des détections
    print("Initialisation des détections...")
    color_detect()  # Activation de la détection de couleur
    face_detect()   # Activation de la détection de visage

    # Commence à avancer
    move_forward()

    while True:
        object_show()  # Vérifie si une couleur ou un visage est détecté
        sleep(0.5)  # Pause avant la prochaine vérification

if __name__ == "__main__":
    main()
