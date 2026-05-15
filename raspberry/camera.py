import cv2

class Camera:

    def __init__(self, mode="raspberry"):

        self.mode = mode

        if mode == "windows":
            self.cap = cv2.VideoCapture(0)

        else:
            try:
                from picamera2 import Picamera2

                self.picam2 = Picamera2()

                self.picam2.configure(
                    self.picam2.create_preview_configuration(
                        main={
                            "size": (2592, 1944)
                        }
                    )
                )

                self.picam2.start()

            except Exception as e:
                print("Picamera2 error:", e)
                self.cap = cv2.VideoCapture(0)
                self.mode = "windows"


    def read_frame(self):

        if self.mode == "windows":
            ret, frame = self.cap.read()
            return frame if ret else None

        frame = self.picam2.capture_array()

        return cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)


    def capture(self, path):

        if self.mode == "windows":
            ret, frame = self.cap.read()
            if ret:
                cv2.imwrite(path, frame)

        else:
            self.picam2.capture_file(path)