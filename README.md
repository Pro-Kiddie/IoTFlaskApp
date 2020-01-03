# IoT Flask Web Application on Raspberry Pi
An Flask web application developed for IoT devices setup on a Raspberry Pi. 

The web application allows user to visualise real-time and historical air quality (PM 2.5 & PM 10) data and send SMS alerts once the air quality passed a certain threshold. It also allows users to get real-time air quality readings and turn on/off an air quality warning buzzer via a Telegram bot.

The web application also supports live-streaming of door camera and captures an image when motion is sensed at door which is also sent to users via Telegram bot.

To establish access control to these IoT devices, the web application has implemented user login, account management and password reset. 

## Table of Contents
1. [Screenshots](#screenshots)
2. [Technologies Used](#technologies-used)
3. [Hardware Setup](#raspberry-pi-hardware-setup)
4. [Software Setup](#raspberry-pi-software-setup)


## ScreenShots
Air Quality Dashboard
![Air Quality Dashboard](/screenshots/aq_dashboard.png)

Door Camera Dashboard
![Door Camera Dashboard](/screenshots/door_camera_dashboard.png)

User Login System
![User Login System](/screenshots/user_login.png)

Password Reset
![Password Reset](/screenshots/password_reset1.png)
![Password Reset](/screenshots/password_reset2.png)

Custom Error Pages
![Custom Error Pages](/screenshots/custom_error_pages.png)

## Technologies Used
- Flask
- Flask-login
   - Flask login manager for access controls. 
- Flask-mail
   - Sending emails with email server and account details provided.
- TimedJSONWebSignatureSerializer
   - Generates one-time password reset URLs and able to store information such as user ID with the URL for verification purpose.
- SQLAlchemy
   - Object-Relation Mapper.
   - Access database in an object-oriented way.
- WTForms
   - Create forms as classes.
- Bcrypt
   - Generating cryptographically secure hash for user passwords.
- Jinja
   - HTML Template inheritance.
- Bootstrap

### Libraries Used
- Gpiozero
  - For different standard IoT devices; e.g. LED, Motion Sensor
- PiCamera
  - For camera module on the Raspoberry Pi. 
- Twilio API
  - For sending SMS alerts.
- Telepot API
  - For Telegram bot.
- ECharts
  - Visualization of air quality data as graphs.


## Raspberry Pi Hardware Setup

### Hardware Checklist
- 1 x SDS011 PM sensor
- 1 x LED
- 1 x 330 Ω resistor
- 1 x PIR Motion Sensor
- 1 x Buzzer
- 1 x LCD (2 x 16)
- 1 x RaspberryPi with Camera Module
  
![Hardware Setup](/screenshots/hardware_setup.png) 

### Fritzing Diagram
![Fritzing Diagram](/screenshots/fritizing.png)

### SDS011 Driver Installation
The SDS011 sensor connects to Raspberry Pi via USB. However, the Raspbian system does not have the driver for the specific USB device used by the sensor. 

To install the driver:

```bash
sudo apt-get install raspberrypi-kernel-headers # Install header files in order to compile/make the driver
git clone https://github.com/skyrocknroll/CH341SER_LINUX.git
cd CH341SER_LINUX
sudo make
modinfo ch341 # To confirm driver kernel module installed successfully.
dmesg | grep ‘ch341-uart converter now attached to ttyUSB0’ # To confirm Raspberry has attached SDS011 to ttyUSB0.
```

## Raspberry PI Software Setup

1)	First connect hardware as shown in [Fritzing diagram](#fritzing-diagram).
2)	Install USB driver for SDS011 PM sensor as described in [Hardware Setup](#sds011-driver-installation).
3) Ensure the `Camera` and `I2C` interface is enabled on Raspberry Pi via `sudo raspi-config`.
4) Install a database of your choice (e.g. MySQL). 
   - Create a schema and a new user. 
   - Grant the new user all privileges on the newly created schema.
5)	Install the  following libraries on Raspberry Pi:
    ```bash
    sudo apt-get install libopenjp2-7
    sudo apt install libtiff5
    ```
6) **Edit the `config.json` for Flask App configurations, API keys and admin account.**
   - To get `telegram_chat_id`, send a message to your bot in Telegram.
   - In Python interactive shell:
     ```python
     import telepot
     bot = telepot.Bot("TOKEN")
     bot.getUpdates()
     ```
7) Run the following commands:
   ```bash
   cd IoTFlaskApp

   # Setup Python virtual environment. (Assuming python -v >= 3.6)
   sudo apt-get install python3-venv
   python3 -m venv env
   source env/bin/activate

   # Install dependencies in virtual env
   pip install -r requirements.txt

   # To run Flask web server: 
   python3 run.py

   # To run PM Sensor, launch another shell
   source env/bin/activate # Activate the virutual environment
   python3 pm_sensor.py # Or you can run pm_sensor_random.py if you do not have a SDS011 sensor
   
   # To run Door Motion Capture with Telegram Bot, launch another shell
   source env/bin/activate # Activate the virutual environment
   python3 aq_door_telegram_bot.py
8)	Login with admin_email and admin_password.

