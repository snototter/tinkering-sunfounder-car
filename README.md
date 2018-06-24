# Tinkering with RaspberryPi
TODO add temperature sensor scripts (lrs)

TODO cloc --exclude-dir=third_party,.venv,sunfounder-patched .

## Sunfounder's "Smart Video Car" Kit

* Control the car with a gamepad: `car-ctrl-gamepad`

* Receive and view the webcam stream from the car's bluetooth server: `car-bluetooth-image-client`

### car-ctrl-gamepad

TODO visualize current button mapping
TODO checkout https://github.com/raspberrypi/linux/issues/1402 - need to disable wifi for decent bluetooth speeds (needed `ifconfig wlan0 down`, instead of `ifdown`)
Check pi_gamepad_ctrl.sh for params
![Controller Layout](car-ctrl-gamepad/figures/gamepad-schematic.png)

Enable service, see [unit files](https://access.redhat.com/documentation/en-us/red_hat_enterprise_linux/7/html/system_administrators_guide/sect-managing_services_with_systemd-unit_files):
```bash
  $> sudo vi /lib/systemd/system/car-ctrl-gamepad.service

[Unit]
Description=Gamepad car controller service
After=bluetooth.target

[Service]
Type=simple
ExecStart=/home/pi/tinkering-pi/car-ctrl-gamepad/pi_gamepad_ctrl.sh
WorkingDirectory=/home/pi/tinkering-pi/car-ctrl-gamepad

[Install]
WantedBy=multi-user.target

  $> sudo chmod 644 /lib/systemd/system/car-ctrl-gamepad.service
  $> sudo systemctl daemon-reload
  $> sudo systemctl enable car-ctrl-gamepad.service
```

### car-bluetooth-image-client
Connects to the server running on the pi-car (if you started `car-ctrl-gamepad`) and views the webcam stream


