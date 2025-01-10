from picarx import Picarx
import time

POWER = 50
SafeDistance = 40   
DangerDistance = 20 
                   

def main():
    try:
        px = Picarx()
        while True:
            distance = round(px.ultrasonic.read(), 2)
            print("distance: ", distance)
            
            if distance >= SafeDistance:
                # Si la distance est suffisamment grande, avance
                px.set_dir_servo_angle(0)  # Diriger tout droit
                px.backward(POWER)  # Avancer à une certaine puissance
            elif distance >= DangerDistance:
                # Si la distance est dans la zone de danger (entre 20 et 40 cm), tourner légèrement
                px.set_dir_servo_angle(30)  # Tourner légèrement
                px.backward(POWER)
                time.sleep(0.1)
            else:
                # Si la distance est trop proche (moins de 20 cm), reculer
                px.set_dir_servo_angle(-30)  # Tourner dans l'autre sens
                px.forward(POWER)  # Reculer
                time.sleep(0.5)
                

    finally:
        px.forward(0)

if __name__ == "__main__":
    main()
