import os
import pygame
import cv2
import pyttsx3
from dotenv import load_dotenv
import speech_recognition as sr
from word2number import w2n
from typing import List, Union
import time

# Load environment variables
load_dotenv()

# Constants
WINDOW_WIDTH = 1000
WINDOW_HEIGHT = 600
BG_COLOR = (30, 30, 30)
BUTTON_COLOR = (70, 130, 180)
BUTTON_TEXT_COLOR = (255, 255, 255)

# Pygame setup
pygame.init()
screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
pygame.display.set_caption('Signa AI')


class SignaAI:
    def __init__(self, screen_rect):
        self.screen_rect = screen_rect
        self.input_text = ""
        self.transcribed_text = ""
        self.recording = False
        self.buttons = {}
        self.specific_signs = self.load_videos("assets/specific/")
        self.alphabet_signs = self.load_videos("assets/alphabets/")
        self.number_signs = self.load_videos("assets/numbers/")
        self.font = pygame.font.Font(None, 36)
        self.text_to_speech_engine = pyttsx3.init()
        self.r = sr.Recognizer()

    @staticmethod
    def convert_word_to_number(word: str) -> Union[int, float, None]:
        try:
            return w2n.word_to_num(word)
        except ValueError:
            return None

    @staticmethod
    def load_videos(folder_path: str) -> List[str]:
        return [os.path.splitext(file)[0] for file in os.listdir(folder_path) if file.endswith('.mp4')]

    def draw_button(self, label, rect):
        pygame.draw.rect(screen, BUTTON_COLOR, rect)
        text_surf = self.font.render(label, True, BUTTON_TEXT_COLOR)
        text_rect = text_surf.get_rect(center=rect.center)
        screen.blit(text_surf, text_rect)

    def draw_text(self, message, y_offset=0):
        text_surf = self.font.render(message, True, BUTTON_TEXT_COLOR)
        text_rect = text_surf.get_rect(
            center=(self.screen_rect.centerx, self.screen_rect.centery + y_offset))
        screen.blit(text_surf, text_rect)

    def display_message(self, message: str, y_offset=0):
        screen.fill(BG_COLOR)
        self.draw_text(message, y_offset)
        pygame.display.flip()

    def text_to_sign(self, text: str):
        # remove all special characters from text and remain with only alphabets and numbers
        text = ''.join(e for e in text if e.isalnum() or e.isspace())
        words = text.split(" ")

        for word in words:
            if word.lower() in self.specific_signs:
                self.play_video(f'assets/specific/{word}.mp4', word, [word])
            else:
                completed_chars = []
                number = self.convert_word_to_number(word)
                if number is not None:
                    for char in str(number):
                        completed_chars.append(char)
                        self.play_video(
                            f'assets/numbers/{char}.mp4', word, completed_chars)
                else:
                    for char in word:
                        if char.lower() in self.alphabet_signs:
                            completed_chars.append(char)   
                            self.play_video(
                                f'assets/alphabets/{char}.mp4', word, completed_chars)

    def ui_buttons(self, phase="input"):
        screen.fill(BG_COLOR)
        if phase == "input":
            self.buttons = {
                "Type Text": pygame.Rect(300, 500, 150, 50),
                "Record Audio": pygame.Rect(500, 500, 250, 50),
            }
        elif phase == "response":
            self.buttons = {
                "Show Signs": pygame.Rect(200, 500, 200, 50),
                "Read Aloud": pygame.Rect(450, 500, 200, 50),
                "Restart": pygame.Rect(700, 500, 150, 50),
            }

        if self.input_text and self.transcribed_text == "":
            self.draw_text(f"Input: {self.input_text}", y_offset=-150)

        if self.transcribed_text:
            self.draw_text(
                f"Transcribed: {self.transcribed_text}", y_offset=-100)

        for label, rect in self.buttons.items():
            self.draw_button(label, rect)

        pygame.display.flip()


    def play_video(self, video_file_path: str, word: str, completed_chars):
        cap = cv2.VideoCapture(video_file_path.lower(   ))
        joined_chars = "".join(completed_chars)

        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            frame = cv2.resize(frame, (WINDOW_WIDTH, WINDOW_HEIGHT))
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame_surface = pygame.surfarray.make_surface(frame)
            screen.fill((0, 0, 0))
            screen.blit(pygame.transform.rotate(frame_surface, 270), (0, 0))
            screen.blit(self.font.render(
                word, True, (255, 255, 255)), (10, 30))
            screen.blit(self.font.render(
                joined_chars, True, (255, 0, 0)), (10, 70))
            pygame.display.flip()
            time.sleep(0.015)
        cap.release()

    def handle_ui_events(self):
        self.ui_buttons()
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    return
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    pos = pygame.mouse.get_pos()
                    for label, rect in self.buttons.items():
                        if rect.collidepoint(pos):
                            if label == "Type Text":
                                self.input_text = self.get_user_text().strip()
                                if self.input_text == "":
                                    self.ui_buttons(phase="input")
                                else:
                                    self.ui_buttons("response")
                            elif label == "Record Audio":
                                self.display_message(
                                    "Recording... Press 'q' to stop")
                                self.recording = True
                                self.record_audio()
                                self.input_text = self.transcribed_text
                                self.ui_buttons(phase="response")
                            elif label == "Read Aloud":
                                self.read_aloud(self.input_text)
                                self.ui_buttons(phase="response")
                            elif label == "Show Signs":
                                self.text_to_sign(self.input_text)
                                self.ui_buttons(phase="response")
                            elif label == "Restart":
                                self.input_text = ""
                                self.transcribed_text = ""
                                self.ui_buttons(phase="input")
                            elif label == "Show Full Text":
                                self.display_message(self.input_text)
                                self.ui_buttons(phase="response")

    def get_user_text(self):
        user_text = ""
        active = True
        while active:
            screen.fill(BG_COLOR)
            self.draw_text(f"Type: {user_text}", y_offset=-50)
            self.draw_text("Press Enter to submit", y_offset=50)
            pygame.display.flip()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    return ""
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN:
                        active = False
                    elif event.key == pygame.K_BACKSPACE:
                        user_text = user_text[:-1]
                    else:
                        user_text += event.unicode
        return user_text

    def record_audio(self):
        with sr.Microphone() as source:
            while self.recording:
                try:
                    # self.r.adjust_for_ambient_noise(source, duration=0.2)
                    audio = self.r.listen(source)
                    for event in pygame.event.get():
                        if event.dict.get("key") == pygame.K_q:
                            self.display_message("Processing...")
                            text = self.r.recognize_google(audio)
                            self.transcribed_text = text
                            self.recording = False
                            return
                except sr.UnknownValueError:
                    pass

    def read_aloud(self, text):
        self.text_to_speech_engine.say(text)
        self.text_to_speech_engine.runAndWait()


if __name__ == "__main__":
    signa_ai = SignaAI(screen.get_rect())
    signa_ai.handle_ui_events()
