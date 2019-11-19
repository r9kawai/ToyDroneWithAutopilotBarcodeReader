# Toy drone with autopilot barcode reader

## Appendix
I confirmed that a software normary move on Ubuntu 19.10 on Oracle VirtualBox VM.
but, You should care network probrem about Python to Tello connection.
If you see a blackscreen on this applications camera moniter and can control Tello, You should try change setup VirtualBox network tab.
It change to type of "NAT" to "Bridge", then has possibile success a camera moniter.

## Introduction.
Task of barcode read automatically at flight. Anyone can experiment it with toy drone of "Tello - Ryze Tech" and Ubuntu on PC.
It use image processing of AR marker, camera process recognize position. Please replay below movie!

## Click below video.
[![](https://img.youtube.com/vi/t5xWGEUsbTc/0.jpg)](https://www.youtube.com/watch?v=t5xWGEUsbTc)

## System layer
<img width="670" alt="github_ToyDroneWithAutopilotBarcodeReader_Systemlayer.png" src="https://github.com/r9kawai/ToyDroneWithAutopilotBarcodeReader/blob/master/github_ToyDroneWithAutopilotBarcodeReader_Systemlayer.png">

## Future image
<img width="670" alt="github_ToyDroneWithAutopilotBarcodeReader" src="https://user-images.githubusercontent.com/47957215/56717350-697bc900-6777-11e9-8662-0a040f9596e9.png">

## What you need to play.
- toy drone of "Tello - Ryze Tech"
- PC on Ubuntu 18.10 (req WiFi

## Environmental configuration
The code is based on python2.7. and many import packages.
(You will little struggle to reproduce the environment.)
I wrote memorandum in ENVIRONMENT.TXT.
(If you reference on it, you can reproduce.)

## About "libh264decoder.so".
The "libh264decoder.so" is commited with binary.
but, It couldn't runnning on environment, frequently.
so, If you have trouble about "libh264decoder.so" with function call python.
You need build to "libh264decoder.so" of H.264 vide decoder.
There source is repositorie of below place, in "Tello-Python/Tello_Video/h264decoder/" dir.
https://github.com/dji-sdk/Tello-Python
You can build it, follow "Tello-Python/Tello_Video/h264decoder/CMakeLists.txt"

## Print out the AR marker and bigger barcode.
I prepared pdf file to print out with common A4 paper,
in "BarCodesAndMarkers_PrintSample.zip".
Stick it on the wall, please devise.

## Before automatically flight.
- Obtain drone, PC.
- You need try flight the drone, follow manual as normally toy play.(It is fun!
- (necessary firmware update, smart phone, and smart phone apli, and etc.)
- Make a run environment on PC. (follow ENVIRONMENT.TXT
- Make a git clone below.
https://github.com/r9kawai/ToyDroneWithAutopilotBarcodeReader.git
- Turn on drone, wait about 10sec,
- Connect wifi to drone as access point name of "TELLO_XXXX" from Ubuntu PC.
- Try below ping command. > ping 192.168.10.1
- If you take responce from drone, try run python code. > python main.py
- Boot application screen is like a above movie, it success.

## After take off.
- click "Take off".
(Please be careful about the safety of the surroundings.)
- You can controll drone as manual. cursol up, down, right, left,
(W)rise, (S)descent, (A)turn left, (D)turn right.
- If flight is stabillity, and indicate Battery [%] and Altitude [cm],
(It need brighter place, in many cases. because altitude sensor. and few seconds stay flight.)
click "Auto".
- Then drone is search up, and down, to AR marker in altitude 50 - 150cm.
- From there, please look at the source, and customize.

## Thanks
Thank you for the Tello development community.
In this space, Doing active development.
https://tellopilots.com/forums/tello-development.8/

## eof
