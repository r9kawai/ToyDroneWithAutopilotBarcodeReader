# This source code is only create instance, start.

import tello
from drone_control_ui import DroneUI

def main():
    drone = tello.Tello('', 8889)  
    ui = DroneUI(drone,"./img/")
    ui.root.mainloop() 

if __name__ == "__main__":
    main()

#eof

