import telepot, json, re
from datetime import datetime
from models import Device, AirQuality, Status
from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTClient
from telepot.loop import MessageLoop
from time import sleep

class TelegramBot():

    def __init__(self):
        with open("config_mine.json", "r") as config_file:
            self.config = json.load(config_file)

        # Retrieve all the devices from database
        self.devices = [device.device_id for device in Device.scan()] # everytime there is new device added (not so freq) need to restart bot to retrieve all devices

        self.telegram_bot = telepot.Bot(self.config["telegram_bot_token"])

        # MQTT client to publish messages
        self.mqtt_client = AWSIoTMQTTClient(self.config["mqtt_client_name"])
        self.mqtt_client.configureEndpoint(self.config["aws_host"], 8883)
        self.mqtt_client.configureCredentials(self.config["aws_root_ca"], self.config["aws_private_key"], self.config["aws_certificate"])
        self.mqtt_client.configureOfflinePublishQueueing(-1)  # Infinite offline Publish queueing
        self.mqtt_client.configureDrainingFrequency(2)  # Draining: 2 Hz
        self.mqtt_client.configureConnectDisconnectTimeout(10)  # 10 sec
        self.mqtt_client.configureMQTTOperationTimeout(5)  # 5 sec
        if not self.mqtt_client.connect():
            raise Exception("Unable to connect to AWS MQTT broke.")

    def _telegram_respond(self, msg):
            telegram_chat_id = msg["chat"]["id"]
            command = msg["text"].lower()
            now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print("Telegram Bot Thread \t\t {}\t Received command: {}".format(now_str, command))

            try:
                result = re.compile(r"\b(all|[a-z]+) (on|off) (sound|buzzer|warning)", re.IGNORECASE).search(command)
                if (result != None) and (None not in result.groups()):
                    device_id = result.group(1)
                    status = result.group(2)
                    # Turn on/off buzzer for all devices
                    if device_id == "all":
                        for device in self.devices:
                            hash_key = device + "_" + "buzzer"
                            new_status = Status(hash_key)
                            new_status.update(actions=[Status.status.set(status)])
                            # payload = {"device_comp" : "{}_{}".format(device, "buzzer"),
                            #            "status" : status}
                            # mqtt_client.publish("status/{}".format(device), json.dumps(payload), 1)
                            sleep(1)
                        self.telegram_bot.sendMessage(telegram_chat_id, "Device ID: {}\nUnhealthy Air Quality Warning Sound Has Been Turned {}!".format("ALL", status))
                        print("Telegram Bot Thread \t\t {}\t Device ID:{} - Turned {} Buzzer.".format(now_str, "ALL", status))
                    # Turn on/off buzzer for the device id specified
                    else:
                        if device_id in self.devices:
                            hash_key = device_id + "_" + "buzzer"
                            new_status = Status(hash_key)
                            new_status.update(actions=[Status.status.set(status)])
                            self.telegram_bot.sendMessage(telegram_chat_id, "Device ID: {}\nUnhealthy Air Quality Warning Sound Has Been Turned {}!".format(device_id, status))
                            print("Telegram Bot Thread \t\t {}\t Device ID:{} - Turned {} Buzzer.".format(now_str, device_id, status))
                        else:
                            self.telegram_bot.sendMessage(telegram_chat_id, "Invalid Device ID: {}".format(device_id))
                    return

                result = re.compile(r"\b(all|[a-z]+) get (aq|air quality)\b", re.IGNORECASE).search(command)
                if (result != None) and (None not in result.groups()):
                    device_id = result.group(1)
                    if device_id == "all":
                        for device in self.devices:
                            last_reading = AirQuality.query(device, scan_index_forward=False, limit=1).next()
                            reply = "Device ID: {}\nCurrent Air Quality:\nPM 2.5: {:.1f}\nPM 10: {:.1f}".format(device, last_reading.pm_25, last_reading.pm_10)
                            self.telegram_bot.sendMessage(telegram_chat_id, reply)
                        print("Telegram Bot Thread \t\t {}\t Device ID:{} - Retrieved Air Quality.".format(now_str, "ALL"))
                    else:
                        if device_id in self.devices:
                            last_reading = AirQuality.query(device_id, scan_index_forward=False, limit=1).next()
                            reply = "Device ID: {}\nCurrent Air Quality:\nPM 2.5: {:.1f}\nPM 10: {:.1f}".format(device_id, last_reading.pm_25, last_reading.pm_10)
                            self.telegram_bot.sendMessage(telegram_chat_id, reply)
                        else:
                            self.telegram_bot.sendMessage(telegram_chat_id, "Invalid Device ID: {}".format(device_id))
                    return 

                result = re.compile(r"\b(all|[a-z]+) take (photo|image|img|pic|picture)\b", re.IGNORECASE).search(command)
                if (result != None) and (None not in result.groups()):
                    device_id = result.group(1)
                    if device_id == "all":
                        for device in self.devices:
                            self.mqtt_client.publish("status/{}/takephoto".format(device), json.dumps({"comp" : "camera", "status" : "take"}), 1)
                            sleep(1)
                        print("Telegram Bot Thread \t\t {}\t Device ID:{} - Taking Image.".format(now_str, "ALL"))
                    else:
                        if device_id in self.devices:
                            self.mqtt_client.publish("status/{}/takephoto".format(device_id), json.dumps({"comp" : "camera", "status" : "take"}), 1)
                            print("Telegram Bot Thread \t\t {}\t Device ID:{} - Taking Image.".format(now_str, device_id))
                        else:
                            self.telegram_bot.sendMessage(telegram_chat_id, "Invalid Device ID: {}".format(device_id))
                    return

                result = re.compile(r"get (id|device)s?", re.IGNORECASE).search(command)
                if result != None:
                    reply = "All Device IDs:\n"
                    for device in self.devices:
                        reply += (device + "\n")
                    self.telegram_bot.sendMessage(telegram_chat_id, reply)
                    print("Telegram Bot Thread \t\t {}\t Retrieved All Device IDs.".format(now_str))
                    return

                # Catch all reply:
                reply = '''Sorry! Invalid Command.\n
"get devices" - Get all the device IDs.
"<all|device_id> get AQ" - Get real-time PM2.5 and PM10 reading from all devices or the device with device ID specified.
"<all|device_id> <on|off> buzzer" - On/Off the warning buzzer for the factory monitored by the device specified. 
"<all|device_id> take photo" - Take a photo on the device specified.'''
                self.telegram_bot.sendMessage(telegram_chat_id, reply)
                print("Telegram Bot Thread \t\t {}\t Unknown Command: {}.".format(now_str, command))

            except Exception as e:
                print(e)
                print("Telegram Bot Thread - Exception. Recovering ...")

    def run(self):
        # Keep the calling program running after calling this method
        MessageLoop(self.telegram_bot, self._telegram_respond).run_as_thread()
        print("***********************************************************\n")
        print("           Telegram Bot Listening for Commands             ")
        print("***********************************************************\n")

