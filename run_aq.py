from aq_monitoring.main_app import MainApp

if __name__ == "__main__":
    app = MainApp(config_file="config.json")
    app.run_pm_sensor()
    app.run_update_pm_threshold()
    app.run_update_buzzer()
    app.run_telegram_bot()
    try:
        while True: # Keep the main thread running
            for t in MainApp.iot_threads: # Loop through the different threads
                if not t.isAlive(): # If any is not alive, try to restart the thread
                    if t.getName() == "pm_sensor":
                        app.run_pm_sensor()
                    elif t.getName() == "update_pm_threshold":
                        app.run_update_pm_threshold()
                    elif t.getName() == "update_buzzer":
                        app.run_update_buzzer()
                    MainApp.iot_threads.remove(t)
                t.join(5)
    except KeyboardInterrupt:
        print("Ending IoT Component of this IoT Flask Web Application")
            