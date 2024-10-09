import pyaudio
import vosk
import os
import pygame
import cv2
import time
import re
from word2number import w2n
import concurrent.futures
from typing import Union, List


# Constants
WINDOW_WIDTH = 1000
WINDOW_HEIGHT = 600

pygame.init()
screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
pygame.display.set_caption('Speech to Sign Language')


class SpeechToSignLanguage:
    def __init__(self, screen_rect):
        self.screen_rect = screen_rect
        self.specific_signs = self.load_videos("assets/specific/")
        self.alphabet_signs = self.load_videos("assets/alphabets/")
        self.number_signs = self.load_videos("assets/numbers/")
        self.recorded_texts: List[str] = []
        self.recognizer = vosk.KaldiRecognizer(vosk.Model("./vosk-model-small-en-us-0.15/"), 16000)

    @staticmethod
    def decontract(phrase: str) -> str:
        contractions = {
            r"won\'t": "will not", r"can\'t": "can not", r"n\'t": " not",
            r"\'re": " are", r"\'s": " is", r"\'d": " would", r"\'ll": " will",
            r"\'t": " not", r"\'ve": " have", r"\'m": " am"
        }
        for contraction, expanded in contractions.items():
            phrase = re.sub(contraction, expanded, phrase)
        return phrase

    @staticmethod
    def convert_word_to_number(word: str) -> Union[int, float, None]:
        try:
            return w2n.word_to_num(word)
        except ValueError:
            return None

    @staticmethod
    def load_videos(folder_path: str) -> List[str]:
        return [os.path.splitext(file)[0] for file in os.listdir(folder_path)]

    def record_and_transcribe(self) -> Union[str, None]:
        try:
            mic = pyaudio.PyAudio()
            stream = mic.open(format=pyaudio.paInt16, channels=1, rate=16000, input=True, frames_per_buffer=8192)
            stream.start_stream()

            while True:
                data = stream.read(4096)
                if self.recognizer.AcceptWaveform(data):
                    input_text = self.recognizer.Result()[14:-3]
                    if input_text:
                        print(f"Speech: '{input_text}'")
                        return input_text

                for event in pygame.event.get():
                    if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.unicode == 'q'):
                        stream.stop_stream()
                        stream.close()
                        mic.terminate()
                        return None
        except Exception as e:
            print("Error occurred:", e)

    def play_video(self, video_file_path: str, word: str, completed_chars: List[str]):
        cap = cv2.VideoCapture(video_file_path)
        joined_chars = "".join(completed_chars)
        font = pygame.font.Font(None, 36)

        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            frame = cv2.resize(frame, (WINDOW_WIDTH, WINDOW_HEIGHT))
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame_surface = pygame.surfarray.make_surface(frame)
            screen.fill((0, 0, 0))
            screen.blit(pygame.transform.rotate(frame_surface, 270), (0, 0))
            screen.blit(font.render(word, True, (255, 255, 255)), (10, 30))
            screen.blit(font.render(joined_chars, True, (255, 0, 0)), (10, 70))
            pygame.display.flip()

        cap.release()

    def text_to_sign(self, text: str):
        words = text.split(" ")

        for word in words:
            if word in self.specific_signs:
                self.play_video(f'assets/specific/{word}.mp4', word, [word])
            else:
                completed_chars = []
                number = self.convert_word_to_number(word)
                if number is not None:
                    for char in str(number):
                        completed_chars.append(char)
                        self.play_video(f'assets/numbers/{char}.mp4', word, completed_chars)
                else:
                    for char in word:
                        if char in self.alphabet_signs:
                            completed_chars.append(char)
                            self.play_video(f'assets/alphabets/{char}.mp4', word, completed_chars)

    def display_message(self, message: str, font_size: int = 48):
        font = pygame.font.Font(None, font_size)
        text_surface = font.render(message, True, (255, 255, 255))
        text_rect = text_surface.get_rect(center=self.screen_rect.center)
        screen.fill((0, 0, 0))
        screen.blit(text_surface, text_rect)
        pygame.display.flip()

    def process_text(self):
        if self.recorded_texts:
            self.text_to_sign(self.recorded_texts.pop(0))

    def start(self):
        self.display_message("Say something")
        time.sleep(2)
        with concurrent.futures.ThreadPoolExecutor() as executor:
            while True:
                f1 = executor.submit(self.record_and_transcribe)
                f2 = executor.submit(self.process_text)

                recognized_text = f1.result()
                if recognized_text:
                    self.recorded_texts.append(recognized_text)

                f2.result()


if __name__ == "__main__":
    speech_to_sign_language = SpeechToSignLanguage(screen.get_rect())
    speech_to_sign_language.start()
