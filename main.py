# 1234567
import pyaudio
import speech_recognition as sr
import vosk
import os
import pygame
import cv2
import time
import re
from word2number import w2n
import concurrent.futures

# Constants
WINDOW_WIDTH = 600
WINDOW_HEIGHT = 400

pygame.init()
screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
pygame.display.set_caption('Speech to Sign Language')


class SpeechToSignLanguage:
    def __init__(self, screen_rect):
        self.screen_rect = screen_rect
        self.r = sr.Recognizer()
        self.specifics = self.get_videos("assets/specific/")
        self.alphabets = self.get_videos("assets/alphabets/")
        self.numbers = self.get_videos("assets/numbers/")
        self.recorded_texts: list[str] = []

        model_path = "C:/Users/PC/Downloads/Compressed/vosk-model-small-en-us-0.15/vosk-model-small-en-us-0.15"
        self.recognizer = vosk.KaldiRecognizer(vosk.Model(model_path), 16000)

    def decontracted(self, phrase):
        # specific
        phrase = re.sub(r"won\'t", "will not", phrase)
        phrase = re.sub(r"can\'t", "can not", phrase)

        # general
        phrase = re.sub(r"n\'t", " not", phrase)
        phrase = re.sub(r"\'re", " are", phrase)
        phrase = re.sub(r"\'s", " is", phrase)
        phrase = re.sub(r"\'d", " would", phrase)
        phrase = re.sub(r"\'ll", " will", phrase)
        phrase = re.sub(r"\'t", " not", phrase)
        phrase = re.sub(r"\'ve", " have", phrase)
        phrase = re.sub(r"\'m", " am", phrase)
        return phrase

    def convert_word_number_to_number(self, word: str) -> int | float | None:
        try:
            number = w2n.word_to_num(word)
            return number
        except:
            return None

    def get_videos(self, folder_path) -> list[str]:
        file_names = os.listdir(folder_path)
        file_names = [file_name.split(".")[0] for file_name in file_names]
        return file_names

    def record_transcribe(self):
        try:
            mic = pyaudio.PyAudio()
            stream = mic.open(format=pyaudio.paInt16, channels=1, rate=16000, input=True, frames_per_buffer=8192)
            stream.start_stream()

            while True:
                data = stream.read(4096)
                recognizer = self.recognizer
                if recognizer.AcceptWaveform(data):
                    recognized_text = recognizer.Result()
                    print(f"Recognized: '{recognized_text[14:-3]}'")
                    return recognized_text[14:-3]
                pygame.event.pump()  # Process Pygame events
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        stream.stop_stream()
                        stream.close()
                        mic.terminate()
                        break
                    if event.type == pygame.KEYDOWN:
                        if event.unicode == 'q':
                            return None  # Return None if the 'q' key is pressed
        except Exception as e:
            print("Error occurred")
            print(e)

    def play_video(self, video_file_path: str, word: str, finished_chars: list[str]):
        cap = cv2.VideoCapture(video_file_path)
        joined_finished_chars = "".join(finished_chars)
        while cap.isOpened():
            ret, frame = cap.read()
            if ret:
                frame = cv2.resize(frame, (WINDOW_WIDTH, WINDOW_HEIGHT))
                frame = cv2.rotate(frame, cv2.ROTATE_90_COUNTERCLOCKWISE)
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

                cv2.putText(frame, word, (10, 30), cv2.FONT_HERSHEY_SIMPLEX,
                            1, (255, 255, 255), 2, cv2.LINE_AA, True)

                cv2.putText(frame, joined_finished_chars, (10, 70), cv2.FONT_HERSHEY_SIMPLEX,
                            1, (255, 0, 0), 2, cv2.LINE_AA, True)

                frame = pygame.surfarray.make_surface(frame)
                screen.blit(frame, (0, 0))
                pygame.display.flip()
                time.sleep(1/75)
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        cap.release()
                        pygame.quit()
                        exit()
            else:
                break
        cap.release()

    def text_to_sign(self, text: str):

        splitted_text = text.split(" ")

        for word in splitted_text:
            if word in self.specifics:
                print(word)
                self.play_video(
                    f'assets/specific/{word}.mp4', word, [word])
            else:
                finished_chars = []
                # check if it is a number in disguise(like ten million, twenty)
                number = self.convert_word_number_to_number(word)
                if number is not None:
                    number = str(number)
                    for char in number:
                        print(char)
                        finished_chars.append(char)
                        self.play_video(
                            f'assets/numbers/{char}.mp4', word, finished_chars)
                else:
                    for char in word:
                        if char in self.alphabets:
                            print(char)
                            finished_chars.append(char)
                            self.play_video(
                                f'assets/alphabets/{char}.mp4', word, finished_chars)
                        else:
                            print("Not found")
                            continue

    def perform(self):
        if len(self.recorded_texts) > 0:
            text = self.recorded_texts[0]
            self.recorded_texts = self.recorded_texts[1:]
            self.text_to_sign(text)

    def start(self):
        with concurrent.futures.ThreadPoolExecutor() as executor:
            while True:
                f1 = executor.submit(self.record_transcribe)
                f2 = executor.submit(self.perform)

                recognized_text = f1.result()  # Capture the recognized text
                if recognized_text is not None:
                    self.recorded_texts.append(recognized_text)  # Add to recorded_texts if not None

                f2.result()


speech_to_sign_language = SpeechToSignLanguage(screen.get_rect())
speech_to_sign_language.start()
