import streamlit as st
import boto3
import pyaudio
from io import BytesIO
import os
from tempfile import NamedTemporaryFile
import speech_recognition as sr

# AWS Credentials setup (directly within the code)
AWS_DEFAULT_REGION = os.getenv("AWS_DEFAULT_REGION", "us-west-2")
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_SESSION_TOKEN = os.getenv("AWS_SESSION_TOKEN")


# Initialize AWS Polly client
def initialize_polly_client():
    try:
        return boto3.client(
            'polly',
            region_name=AWS_DEFAULT_REGION,
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
            aws_session_token=AWS_SESSION_TOKEN
        )
    except Exception as e:
        st.error(f"Error initializing AWS Polly client: {e}")
        return None

# Session state initialization
if 'text' not in st.session_state:
    st.session_state['text'] = ''  # Store transcribed text
if 'run' not in st.session_state:
    st.session_state['run'] = False  # Recording status
if 'status' not in st.session_state:
    st.session_state['status'] = "Ready to start recording."  # Status message

# Start transcription function
def start_transcription():
    st.session_state['run'] = True
    st.session_state['text'] = ''  # Clear previous text
    st.session_state['status'] = "Recording started. Please speak clearly."

def stop_transcription():
    st.session_state['run'] = False
    st.session_state['status'] = "Recording stopped. Processing final text..."

# Function to convert text to speech using AWS Polly with an Indian accent
def text_to_speech(text, voice_id='Aditi'):
    polly = initialize_polly_client()
    if not polly:
        return None

    try:
        response = polly.synthesize_speech(Text=text, OutputFormat='mp3', VoiceId=voice_id)
        audio_file = NamedTemporaryFile(delete=False, suffix=".mp3")
        audio_file.write(response['AudioStream'].read())
        audio_file.close()
        return audio_file.name
    except Exception as e:
        st.error(f"Error converting text to speech: {e}")
        return None

# Function to listen to audio and transcribe it synchronously
def listen_and_transcribe():
    recognizer = sr.Recognizer()
    microphone = sr.Microphone()

    with microphone as source:
        # Adjust for ambient noise
        recognizer.adjust_for_ambient_noise(source)

        st.session_state['status'] = "Listening... Please speak."

        try:
            audio = recognizer.listen(source, timeout=5, phrase_time_limit=5)
            st.session_state['status'] = "Processing speech..."

            # Recognize the speech using Google Web Speech API
            transcribed_text = recognizer.recognize_google(audio)
            print(transcribed_text)
            st.session_state['text'] += " " + transcribed_text
            st.session_state['status'] = "Transcription successful!"
        except sr.UnknownValueError:
            st.warning("Could not understand the audio.")
            st.session_state['status'] = "Could not understand the audio."
        except sr.WaitTimeoutError:
            st.session_state['status'] = "Listening timed out, waiting for speech..."
        except sr.RequestError as e:
            st.error(f"Could not request results from Google Web Speech API; {e}")
            st.session_state['status'] = f"API request error: {e}"
        except Exception as e:
            st.error(f"Error occurred during transcription: {e}")
            st.session_state['status'] = f"Error occurred: {e}"

def main():
    # Set page configuration
    st.set_page_config(page_title="AccentFlow", page_icon="🎙️")

    # Custom CSS for centering and styling
    st.markdown("""
        <style>
        .center-content {
            display: flex;
            justify-content: center;
            align-items: center;
            flex-direction: column;
        }
        .title {
            font-size: 2.5em;
            color: #FFA500;
            text-align: center;
            font-weight: bold;
        }
        .subtitle {
            font-size: 1.5em;
            color: #666;
            text-align: center;
            margin-bottom: 1.5em;
        }
        .status-box {
            border: 2px solid #FFA500;
            padding: 10px;
            margin-top: 15px;
            border-radius: 8px;
            color: #FFA500;
            font-weight: bold;
            text-align: center;
        }
        .transcription-box {
            font-size: 1.2em;
            color: #333;
            border: 2px solid #ccc;
            border-radius: 8px;
            padding: 15px;
            margin-top: 10px;
            max-width: 600px;
        }
        .button-container {
            display: flex;
            justify-content: center;
            gap: 15px;
            margin-top: 20px;
        }
        </style>
    """, unsafe_allow_html=True)

    # Header Section
    st.markdown("<div class='center-content'><div class='title'>AccentFlow 🎙️</div>", unsafe_allow_html=True)
    st.markdown("<div class='subtitle'>Real-Time Accent Changer App</div></div>", unsafe_allow_html=True)

    # Status Message
    st.markdown(f"<div class='status-box'>{st.session_state['status']}</div>", unsafe_allow_html=True)

    # Start/Stop buttons for live transcription
    st.markdown("<div class='button-container'>", unsafe_allow_html=True)
    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("🎤 Start Listening"):
            start_transcription()
            listen_and_transcribe()  # Call the function synchronously after clicking start

    with col2:
        if st.button("⏹️ Stop Listening"):
            stop_transcription()
    st.markdown("</div>", unsafe_allow_html=True)

    # Display the live transcription with some styling
    st.subheader("Live Transcription:")
    st.markdown(f"<div class='transcription-box'>{st.session_state['text']}</div>", unsafe_allow_html=True)

    # Show conversion button only after recording is stopped and text is available
    if not st.session_state['run'] and st.session_state['text']:
        st.subheader("Convert to Speech with Indian Accent")
        if st.button("🗣️ Convert to Indian Accent"):
            accent_audio = text_to_speech(st.session_state['text'], voice_id='Aditi')
            if accent_audio:
                st.audio(accent_audio, format='audio/mp3', autoplay=True)

# Run the main function
if __name__ == '__main__':
    main()
