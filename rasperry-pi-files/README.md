# This contains some general setup to make the program work nicely.

You need to create a environment named spectrometer_env inside the directory that contains all the python files

$python3 -m venv spectrometer_env

then install all of the dependencies

$./spectrometer_env/bin/python3 -m pip install seabreeze, opencv, ...

In addition to this you need follow the guidelines provided by arducam to get the camera up and running.

If you are using an official raspberry pi camera you can ignore this setup: [Arducam quick guide](https://docs.arducam.com/Raspberry-Pi-Camera/Native-camera/Quick-Start-Guide/)
