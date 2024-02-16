import os
import cv2

DATA_DIR = './data'
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)


class Record:
    def get_values(self, folder_path) -> list[str]:
        file_names = os.listdir(folder_path)
        file_names = [file_name.split(".")[0] for file_name in file_names]
        return file_names

    def collect_values(self):
        alphabets = self.get_values("assets/alphabets/")
        numbers = self.get_values("assets/numbers/")
        specifics = self.get_values("assets/specific/")

        return alphabets, numbers, specifics

    def record(self):
        video_capture = cv2.VideoCapture(0)

        alphabets, numbers, specifics = self.collect_values()

        for category, values in zip(["alphabets", "numbers", "specifics"], [alphabets, numbers, specifics]):
            category_dir = os.path.join(DATA_DIR, category)
            if not os.path.exists(category_dir):
                os.makedirs(category_dir)

            for value in values:
                value_dir = os.path.join(category_dir, value)
                exists = os.path.exists(value_dir)
                if not exists:
                    os.makedirs(value_dir)

                has_images = len(os.listdir(value_dir)) > 0

                if has_images:
                    continue

                print(f"Collecting {value}:")
                while True:
                    ret, frame = video_capture.read()

                    cv2.putText(frame, 'Ready? Press "Q" ! :)', (100, 50), cv2.FONT_HERSHEY_SIMPLEX, 1.3,
                                (0, 255, 0), 3, cv2.LINE_AA)
                    cv2.imshow('frame', frame)

                    if cv2.waitKey(25) == ord('q'):
                        break

                counter = 0
                while counter < 100:
                    ret, frame = video_capture.read()
                    frame = cv2.resize(frame, (640, 480))
                    cv2.imshow('frame', frame)
                    cv2.waitKey(25)
                    cv2.imwrite(os.path.join(
                        value_dir, f'{value}_{counter}.jpg'), frame)
                    counter += 1

        video_capture.release()
        cv2.destroyAllWindows()


record = Record()

record.record()
