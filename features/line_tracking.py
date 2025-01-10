from picarx import Picarx
from time import sleep

px = Picarx()

current_state = None
px_power = 6
offset = 30
last_state = "stop"

def outHandle():
    global last_state, current_state
    if last_state == 'left':
        px.set_dir_servo_angle(-30)
        px.forward(10)
    elif last_state == 'right':
        px.set_dir_servo_angle(30)
        px.forward(10)
    while True:
        gm_val_list = px.get_grayscale_data()
        gm_state = get_status(gm_val_list)
        print("outHandle gm_val_list: %s, %s"%(gm_val_list, gm_state))
        currentSta = gm_state
        if currentSta != last_state:
            break
    sleep(0.001)

def get_status(val_list):
    _state = px.get_line_status(val_list)  
    if _state == [0, 0, 0]:
        print(_state)
        return 'stop'
    elif _state[1] == 1:
        return 'forward'
    elif _state[2] == 1:
        return 'right'
    elif _state[0] == 1:
        return 'left'

if __name__ == '__main__':
    try:
        while True:
            gm_val_list = px.get_grayscale_data()
            gm_state = get_status(gm_val_list)
            print(f"gm_val_list: {gm_val_list}, gm_state: {gm_state}, last_state: {last_state}")

            if gm_state != "stop":
                last_state = gm_state

            if gm_state == 'forward':
                px.set_dir_servo_angle(0)
                px.backward(px_power)
            elif gm_state == 'left':
                px.set_dir_servo_angle(-offset)
                px.backward(px_power)
            elif gm_state == 'right':
                px.set_dir_servo_angle(offset)
                px.backward(px_power)
            else:
                outHandle()
    finally:
        px.stop()
        print("stop and exit")
        sleep(0.1)
