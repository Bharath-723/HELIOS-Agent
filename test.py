import speech_recognition as sr

r = sr.Recognizer()

# OPTIONAL: choose specific mic (better accuracy)
mic = sr.Microphone(device_index=1)  # change index if needed

with mic as source:
    print("🎤 Speak now...")
    r.adjust_for_ambient_noise(source, duration=1)
    audio = r.listen(source, timeout=5)

try:
    text = r.recognize_google(audio)
    print("You said:", text)
except sr.UnknownValueError:
    print("❌ Could not understand audio")
except sr.RequestError:
    print("❌ API error")