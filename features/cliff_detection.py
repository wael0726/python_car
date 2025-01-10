from picarx import Picarx
from time import sleep
from robot_hat import TTS

tts = TTS()
tts.lang("en-US")

px = Picarx()
px.set_cliff_reference([200, 200, 200])

current_state = None
px_power = 10
offset = 20
last_state = "safe"

backward_speed = 50

if __name__=='__main__':
    try:
        px.backward(backward_speed) 
        while True:
            gm_val_list = px.get_grayscale_data()
            gm_state = px.get_cliff_status(gm_val_list)

            if gm_state is False:
                state = "safe"
                px.backward(backward_speed)
            else:
                state = "danger"
                px.forward(80)  # Move backward if danger is detected
                if last_state == "safe":
                    tts.say("danger")
                    sleep(0.1)
            last_state = state

    finally:
        px.stop()
        print("stop and exit")
        sleep(0.1)



                
