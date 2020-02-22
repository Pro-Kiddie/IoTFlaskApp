import io
import time
import picamera
from flask_iot_app.iot.base_camera import BaseCamera


class Camera(BaseCamera):

    @staticmethod
    def frames():
        while True:
            camera = None
            try:
                camera = picamera.PiCamera()
                # let camera warm up
                time.sleep(4)

                # Byte stream to store the captured image
                stream = io.BytesIO()
                for _ in camera.capture_continuous(stream, 'jpeg',
                                                use_video_port=True):
                    # return current frame
                    stream.seek(0)  # Seek to starting of the stream
                    yield stream.read()

                    # reset stream for next frame
                    stream.seek(0)
                    stream.truncate()  # resize the stream to current cursor position which is at start of stream
            except GeneratorExit:
                break
            except:
                print("*** PICAMERA IS BUSY! USER IS VIEWING LIVE STREAMING. WILL DETECTION RESUME ONCE USER STOPS. ***")
                time.sleep(10)
            else:
                break
            finally:
                if camera is not None:
                    camera.close()
