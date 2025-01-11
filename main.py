import os
import pygame
import cv2
import threading
import pyttsx3
from dotenv import load_dotenv
from word2number import w2n
from openai import OpenAI
from typing import List, Union

# Load environment variables
load_dotenv()

# Initialize OpenAI Client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Constants
WINDOW_WIDTH = 1000
WINDOW_HEIGHT = 600
BG_COLOR = (30, 30, 30)
BUTTON_COLOR = (70, 130, 180)
BUTTON_TEXT_COLOR = (255, 255, 255)

# Pygame setup
pygame.init()
screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
pygame.display.set_caption('Speech to Sign Language with OpenAI')


class SpeechToSignLanguage:
    def __init__(self, screen_rect):
        self.screen_rect = screen_rect
        self.input_text = ""
        self.response_text = ""
        self.recording = False
        self.transcribed_text = ""
        self.buttons = {}
        self.specific_signs = self.load_videos("assets/specific/")
        self.alphabet_signs = self.load_videos("assets/alphabets/")
        self.number_signs = self.load_videos("assets/numbers/")
        self.font = pygame.font.Font(None, 36)
        self.text_to_speech_engine = pyttsx3.init()

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
        text_rect = text_surf.get_rect(center=(self.screen_rect.centerx, self.screen_rect.centery + y_offset))
        screen.blit(text_surf, text_rect)

    def display_message(self, message: str, y_offset=0):
        screen.fill(BG_COLOR)
        self.draw_text(message, y_offset)
        pygame.display.flip()

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

    def ui_buttons(self, phase="input"):
        screen.fill(BG_COLOR)
        if phase == "input":
            self.buttons = {
                "Type Text": pygame.Rect(100, 500, 150, 50),
                "Record Audio": pygame.Rect(300, 500, 150, 50),
                "Send": pygame.Rect(500, 500, 150, 50),
            }
        elif phase == "response":
            self.display_message(self.response_text, y_offset=-100)
            self.buttons = {
                "Show Signs": pygame.Rect(300, 500, 150, 50),
                "Read Aloud": pygame.Rect(500, 500, 150, 50),
                "Restart": pygame.Rect(700, 500, 150, 50),
            }
        elif phase == "sign_language":
            self.buttons = {
                "Show Full Text": pygame.Rect(300, 500, 150, 50),
                "Restart": pygame.Rect(500, 500, 150, 50),
            }

        if self.input_text:
            self.draw_text(f"Input: {self.input_text}", y_offset=-150)

        if self.transcribed_text:
            self.draw_text(f"Transcribed: {self.transcribed_text}", y_offset=-100)

        for label, rect in self.buttons.items():
            self.draw_button(label, rect)

        pygame.display.flip()

    def handle_openai_response(self, user_input):
        try:
            # Call OpenAI for a response
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": user_input}]
            )
            self.response_text = response.choices[0].message.content
        except Exception as e:
            self.response_text = f"Error: {str(e)}"

    def play_video(self, video_file_path: str, word: str, completed_chars):
        cap = cv2.VideoCapture(video_file_path)
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
            screen.blit(self.font.render(word, True, (255, 255, 255)), (10, 30))
            screen.blit(self.font.render(joined_chars, True, (255, 0, 0)), (10, 70))
            pygame.display.flip()

        cap.release()

    def handle_ui_events(self):
        self.ui_buttons(phase="input")
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
                                self.input_text = self.get_user_text()
                                self.ui_buttons()
                            elif label == "Record Audio":
                                self.display_message("Recording... Press 'q' to stop")
                                self.recording = True
                                threading.Thread(target=self.record_audio).start()
                            elif label == "Send":
                                if self.input_text or self.recording:
                                    self.display_message("Processing...")
                                    self.handle_openai_response(self.input_text or "Audio recorded")                              
                                    self.ui_buttons(phase="response")
                            elif label == "Read Aloud":
                                self.read_aloud(self.response_text)
                            elif label == "Show Signs":
                                self.text_to_sign(self.response_text)
                                self.ui_buttons(phase="sign_language")
                            elif label == "Restart":
                                self.input_text = ""
                                self.response_text = ""
                                self.ui_buttons(phase="input")
                            elif label == "Show Full Text":
                                self.display_message(self.response_text)
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
        # Record audio and transcribe using speech-to-text
        # Placeholder for actual audio recording and transcription logic
        self.transcribed_text = "Transcribed audio text will appear here."
        self.recording = False
        self.display_message("Audio Transcribed", y_offset=50)
        self.ui_buttons()

    def read_aloud(self, text):
        self.text_to_speech_engine.say(text)
        self.text_to_speech_engine.runAndWait()


if __name__ == "__main__":
    speech_to_sign_language = SpeechToSignLanguage(screen.get_rect())
    speech_to_sign_language.handle_ui_events()
