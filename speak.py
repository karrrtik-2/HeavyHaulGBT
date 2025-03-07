import os
import asyncio
import pygame
import edge_tts
import shutil
import speech_recognition as sr
import time
import threading
from dotenv import load_dotenv
from queue import Queue

recognizer = sr.Recognizer()
recognizer.energy_threshold = 1000
recognizer.dynamic_energy_threshold = False
recognizer.pause_threshold = 1
recognizer.phrase_threshold = 0.5
recognizer.non_speaking_duration = 0.6

load_dotenv()
os.makedirs("ASSETS/STREAM_AUDIOS", exist_ok=True)

class WakeWordDetector:
    def __init__(self):
        self.wake_word = "pixel"
        self.should_stop = False
        self.is_speaking = False
        self.recognizer = sr.Recognizer()
        self.recognizer.energy_threshold = 1000
        self.recognizer.dynamic_energy_threshold = False

    async def listen_for_wake_word(self):
        try:
            with sr.Microphone() as source:
                print("Listening for wake word...")
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=5)
                try:
                    text = self.recognizer.recognize_google(audio).lower()
                    return text
                except sr.UnknownValueError:
                    return ""
                except sr.RequestError:
                    return ""
        except Exception as e:
            print(f"Error in wake word detection: {e}")
            return ""

    async def background_listener(self):
        while not self.should_stop:
            try:
                with sr.Microphone() as source:
                    audio = self.recognizer.listen(source, timeout=1, phrase_time_limit=1)
                    try:
                        text = self.recognizer.recognize_google(audio).lower()
                        if text == "stop" and self.is_speaking:
                            pygame.mixer.music.stop()
                            self.is_speaking = False
                    except sr.UnknownValueError:
                        pass
                    except sr.RequestError:
                        pass
            except Exception:
                pass
            await asyncio.sleep(0.1)

async def continuous_listen():
    try:
        import speech_recognition as sr
        recognizer = sr.Recognizer()
        
        with sr.Microphone() as source:
            print("Listening...")
            recognizer.adjust_for_ambient_noise(source, duration=0.5)
            audio = recognizer.listen(source)
            
            try:
                text = recognizer.recognize_google(audio)
                return text
            except sr.UnknownValueError:
                return "none"
            except sr.RequestError:
                return "none"
    except Exception as e:
        print(f"Error in speech recognition: {e}")
        return "none"

async def take_command():
    try:
        with sr.Microphone() as source:
            print("\nListening...")
            audio = recognizer.listen(source, timeout=5, phrase_time_limit=5)
            
            try:
                print("Recognizing...")
                query = recognizer.recognize_google(audio, language='en-US')
                print(f"You said: {query}")
                return query.lower()
            except sr.UnknownValueError:
                return "none"
            except sr.RequestError as e:
                print(f"Could not request results; {e}")
                return "none"
            
    except Exception as e:
        print(f"Error in speech recognition: {e}")
        return "none"

def delete_stream_audio_files(folder_path='ASSETS/STREAM_AUDIOS') -> None:
    if os.path.exists(folder_path):
        for filename in os.listdir(folder_path):
            file_path = os.path.join(folder_path, filename)
            try:
                if os.path.isfile(file_path):
                    try:
                        os.remove(file_path)
                    except PermissionError:
                        pygame.mixer.music.unload()
                        time.sleep(0.1)
                        os.remove(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
            except Exception as e:
                print(f"Error deleting {file_path}: {e}")

class ContinuousListener:
    def __init__(self):
        self.wake_word = "pixel"
        self.should_stop = False
        self.is_speaking = False
        self.recognizer = sr.Recognizer()
        self.recognizer.energy_threshold = 500
        self.recognizer.dynamic_energy_threshold = False
        self.recognizer.pause_threshold = 1
        self.recognizer.phrase_threshold = 0.5
        self.recognizer.non_speaking_duration = 0.6
        self.stop_listener_thread = None
        
    def start_stop_listener(self):
        self.stop_listener_thread = threading.Thread(target=self._stop_listener_worker)
        self.stop_listener_thread.daemon = True
        self.stop_listener_thread.start()

    def _stop_listener_worker(self):
        with sr.Microphone() as source:
            while not self.should_stop:
                try:
                    audio = self.recognizer.listen(source, timeout=1, phrase_time_limit=1)
                    try:
                        text = self.recognizer.recognize_google(audio).lower()
                        if "stop" in text and self.is_speaking:
                            print("Stop command detected!")
                            pygame.mixer.music.stop()
                            self.is_speaking = False
                    except sr.UnknownValueError:
                        pass
                    except sr.RequestError:
                        pass
                except Exception:
                    pass
                time.sleep(0.1)

    async def background_listen(self):
        print("\nStarting background listener...")
        with sr.Microphone() as source:
            print(f"Energy threshold set to {self.recognizer.energy_threshold}")
            
            while not self.should_stop:
                print("\nListening...")
                try:
                    audio = self.recognizer.listen(source, timeout=None, phrase_time_limit=None)
                    print("Audio captured, recognizing...")
                    
                    try:
                        text = self.recognizer.recognize_google(audio).lower()
                        #print(f"Recognized text: {text}")
                        
                        if self.wake_word in text:
                            query = text.replace(self.wake_word, "", 1).strip()
                            if query:
                                print(f"Wake word detected!")
                                return query
                    except sr.UnknownValueError:
                        print("Could not understand audio")
                        continue
                    except sr.RequestError as e:
                        print(f"Could not request results; {e}")
                        continue
                except Exception as e:
                    print(f"Error in listening: {e}")
                    continue
                
                await asyncio.sleep(0.1)
        return "exit"
    
class SpeechSynthesizer:
    def __init__(self, continuous_listener=None):
        print("Initializing Speech Synthesizer...")
        self.voice = "en-US-JennyNeural"
        self.stream_folder = "ASSETS/STREAM_AUDIOS"
        self.audio_queue = Queue()
        self.continuous_listener = continuous_listener
        os.makedirs(self.stream_folder, exist_ok=True)
        
        try:
            pygame.mixer.init(frequency=24000)
            pygame.mixer.init()
            print("Audio system initialized")
        except pygame.error as e:
            print(f"Failed to initialize pygame mixer: {e}")
            raise

        self.playback_thread = threading.Thread(target=self._audio_playback_handler, args=(self.audio_queue,))
        self.playback_thread.daemon = True
        self.playback_thread.start()
        print("Speech Synthesizer ready")

    async def text_to_speech(self, text):
        if not text:
            return
        try:
            print("Starting text-to-speech conversion...")
            if self.continuous_listener:
                self.continuous_listener.is_speaking = True
                print("Speaking state set to True")
            
            temp_file = os.path.join(
                self.stream_folder, 
                f"temp_{str(hash(text + str(time.time())))}.mp3"
            )
            print("Converting text to speech...")
            communicate = edge_tts.Communicate(text, self.voice)
            await communicate.save(temp_file)
            print("Speech file created")
            
            try:
                if not pygame.mixer.get_init():
                    pygame.mixer.init(frequency=24000)
                
                print("Playing audio...")
                pygame.mixer.music.load(temp_file)
                pygame.mixer.music.play()
                
                while pygame.mixer.music.get_busy():
                    if not self.continuous_listener or not self.continuous_listener.is_speaking:
                        print("Speech interrupted")
                        pygame.mixer.music.stop()
                        break
                    await asyncio.sleep(0.1)
                
                pygame.mixer.music.unload()
                print("Audio playback complete")
                
            finally:
                if self.continuous_listener:
                    self.continuous_listener.is_speaking = False
                    print("Speaking state set to False")
                if os.path.exists(temp_file):
                    os.remove(temp_file)
                    print("Temporary audio file cleaned up")
                    
        except Exception as e:
            print(f"Error in text_to_speech: {e}")
            if self.continuous_listener:
                self.continuous_listener.is_speaking = False

    def queue_audio(self, filename: str):
        self.audio_queue.put(filename)
    
    def wait_for_playback_completion(self):
        self.audio_queue.join()

    def _audio_playback_handler(self, audio_queue: Queue):
        while True:
            filename = audio_queue.get()
            if filename is None:  
                break
            
            if not os.path.exists(filename):
                print(f"File not found: {filename}")
                audio_queue.task_done()
                continue

            try:
                pygame.mixer.music.load(filename)
                pygame.mixer.music.play()
                while pygame.mixer.music.get_busy():
                    pygame.time.Clock().tick(10)  # Reduce CPU usage
                
                pygame.mixer.music.unload()
                time.sleep(0.01)
                
                if os.path.exists(filename):
                    try:
                        os.remove(filename)
                    except PermissionError:
                        print(f"Permission denied while deleting: {filename}")
                    except Exception as e:
                        print(f"Error deleting file {filename}: {e}")
                
            except Exception as e:
                print(f"Error during playback of {filename}: {e}")
            finally:
                audio_queue.task_done()
                try:
                    if os.path.exists(filename):
                        os.remove(filename)
                except Exception:
                    pass
                
def initialize_speech():
    try:
        pygame.mixer.init(frequency=24000)
        print("Speech system initialized successfully")
    except pygame.error as e:
        print(f"Failed to initialize pygame mixer: {e}")
        raise
    
class VoiceAssistant:
    def __init__(self, continuous_listener=None):     
        try:
            pygame.mixer.init(frequency=24000)
        except pygame.error as e:
            print(f"Failed to initialize pygame mixer: {e}")
            raise
        
        self.voice = "en-US-ChristopherNeural"  
        self.response_text = ""
        self.is_processing = False
        self.speech_synthesizer = SpeechSynthesizer(continuous_listener)
        
    async def process_stream(self, stream):
        try:
            self.response_text = ""
            buffer = ""  
            for chunk in stream:
                if hasattr(chunk.choices[0].delta, 'content'):
                    content = chunk.choices[0].delta.content
                    if content is None:
                        continue
                    print(content, end='', flush=True)
                    self.response_text += content
                    buffer += content

            # Process the entire buffer as a single piece of text
            if buffer.strip():
                await self.speech_synthesizer.text_to_speech(buffer)
                        
            self.speech_synthesizer.wait_for_playback_completion()
                    
        except Exception as e:
            print(f"\nStream processing error: {str(e)}")