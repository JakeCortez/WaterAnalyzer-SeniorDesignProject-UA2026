# WaterAnalyzer-SeniorDesignProject-UA2026
This Page is a deliverable as part a senior design project I was a member of at the University of Arizona

The main organization are the two folders:

Please look at the readme for each subfolder.

The flutter-build is what is needed to re-create the application to control and download data from the device.

Raspberry-pi-files contains all the python scripts and some test data to run the program.

All the GUI does is display some basic information and sends commands to the raspberry pi. The raspberry pi needs to be connected to the phone via hotspot for the communication to work.

I've included all the dependencies in the requirements.txt file for python.

There is also a service file, I added this needs to be added to the raspberry pi so that on boot the device will start listening for commands from the phone.

Steps to enable service on boot:

1) sudo nano /lib/systemd/system/await-command.service

2) paste the contents of the service file

3) sudo systemctl daemon-reload

4) sudo systemctl enable await-command.service
