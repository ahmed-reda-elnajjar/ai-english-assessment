from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import os
import json
import base64
import io
from dotenv import load_dotenv
import asyncio
import threading
import time

# Optional imports with fallbacks
try:
    from groq import Groq
except ImportError:
    Groq = None
    print("Groq package not installed - assessment will be limited")

try:
    from azure.cognitiveservices.speech import SpeechConfig, SpeechRecognizer, AudioConfig
    from azure.cognitiveservices.speech.audio import AudioStreamFormat, PushAudioInputStream
except ImportError:
    SpeechConfig = SpeechRecognizer = AudioConfig = None
    AudioStreamFormat = PushAudioInputStream = None
    print("Azure Speech package not installed - Azure transcription disabled")

try:
    import google.cloud.speech as speech
except ImportError:
    speech = None
    print("Google Cloud Speech package not installed - Google transcription disabled")

try:
    from deepgram import Deepgram
except ImportError:
    Deepgram = None
    print("Deepgram package not installed - Deepgram transcription disabled")

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)

# API Keys (you'll need to set these in .env file)
GROQ_API_KEY = os.getenv('GROQ_API_KEY')
AZURE_SPEECH_KEY = os.getenv('AZURE_SPEECH_KEY')
AZURE_SPEECH_REGION = os.getenv('AZURE_SPEECH_REGION')
GOOGLE_CREDENTIALS_PATH = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
DEEPGRAM_API_KEY = os.getenv('DEEPGRAM_API_KEY')

# Initialize clients (with error handling)
try:
    groq_client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None
except Exception as e:
    print(f"Groq initialization error: {e}")
    groq_client = None

try:
    deepgram_client = Deepgram(DEEPGRAM_API_KEY) if DEEPGRAM_API_KEY else None
except Exception as e:
    print(f"Deepgram initialization error: {e}")
    deepgram_client = None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/assess', methods=['POST'])
def assess_speech():
    try:
        data = request.get_json()
        audio_data = data.get('audio')
        audio_format = data.get('format', 'webm')

        if not audio_data:
            return jsonify({'error': 'No audio data provided'}), 400

        # Decode base64 audio
        try:
            audio_bytes = base64.b64decode(audio_data.split(',')[1] if ',' in audio_data else audio_data)
        except Exception as e:
            return jsonify({'error': f'Invalid audio format: {str(e)}'}), 400

        if not audio_bytes:
            return jsonify({'error': 'Empty audio data'}), 400

        # Get transcriptions from all available providers
        transcriptions = {}

        # Azure Speech (Primary)
        if AZURE_SPEECH_KEY and SpeechConfig:
            azure_text = get_azure_transcription(audio_bytes, audio_format)
            if azure_text:
                transcriptions['azure'] = azure_text

        # Google Cloud Speech
        if GOOGLE_CREDENTIALS_PATH and speech:
            google_text = get_google_transcription(audio_bytes, audio_format)
            if google_text:
                transcriptions['google'] = google_text

        # Deepgram
        if deepgram_client:
            deepgram_text = get_deepgram_transcription(audio_bytes, audio_format)
            if deepgram_text:
                transcriptions['deepgram'] = deepgram_text

        # If no transcription providers available, return error
        if not transcriptions:
            return jsonify({'error': 'No speech-to-text providers configured. Please ensure at least one API key is set (Azure Speech, Google Cloud, or Deepgram)'}), 500

        # Combine transcriptions for best accuracy
        combined_text = combine_transcriptions(transcriptions)

        # Assess proficiency using AI
        assessment = assess_proficiency(combined_text)

        return jsonify({
            'transcriptions': transcriptions,
            'combined_text': combined_text,
            'assessment': assessment,
            'success': True
        })

    except Exception as e:
        import traceback
        print(f"Error in assess_speech: {traceback.format_exc()}")
        return jsonify({'error': f'Server error: {str(e)}'}), 500

def get_azure_transcription(audio_bytes, audio_format):
    """Get transcription from Azure Speech Services"""
    try:
        if not AZURE_SPEECH_KEY or not AZURE_SPEECH_REGION:
            return None

        speech_config = SpeechConfig(subscription=AZURE_SPEECH_KEY, region=AZURE_SPEECH_REGION)
        speech_config.speech_recognition_language = "en-US"

        # Create push stream
        push_stream = PushAudioInputStream()
        audio_config = AudioConfig(stream=push_stream)

        # Write audio data
        push_stream.write(audio_bytes)
        push_stream.close()

        speech_recognizer = SpeechRecognizer(speech_config=speech_config, audio_config=audio_config)

        result = speech_recognizer.recognize_once()
        if result.reason.name == 'RecognizedSpeech':
            return result.text
        return None

    except Exception as e:
        print(f"Azure Speech error: {e}")
        return None

def get_google_transcription(audio_bytes, audio_format):
    """Get transcription from Google Cloud Speech"""
    try:
        if not GOOGLE_CREDENTIALS_PATH:
            return None

        client = speech.SpeechClient()

        # Configure audio
        audio = speech.RecognitionAudio(content=audio_bytes)

        config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.WEBM_OPUS if audio_format == 'webm' else speech.RecognitionConfig.AudioEncoding.LINEAR16,
            sample_rate_hertz=16000,
            language_code="en-US",
            enable_automatic_punctuation=True,
            enable_word_time_offsets=False,
        )

        response = client.recognize(config=config, audio=audio)

        if response.results:
            return response.results[0].alternatives[0].transcript
        return None

    except Exception as e:
        print(f"Google Speech error: {e}")
        return None

def get_deepgram_transcription(audio_bytes, audio_format):
    """Get transcription from Deepgram"""
    try:
        if not deepgram_client:
            return None

        # Convert audio format if needed
        source = {'buffer': audio_bytes, 'mimetype': f'audio/{audio_format}'}

        response = deepgram_client.transcription.sync_prerecorded(source, {
            'punctuate': True,
            'model': 'nova-2',
            'language': 'en-US'
        })

        if response and 'results' in response and response['results']['channels'][0]['alternatives']:
            return response['results']['channels'][0]['alternatives'][0]['transcript']
        return None

    except Exception as e:
        print(f"Deepgram error: {e}")
        return None

def combine_transcriptions(transcriptions):
    """Combine transcriptions from multiple providers for higher accuracy"""
    if len(transcriptions) == 1:
        return list(transcriptions.values())[0]

    # Simple voting system - take the most common transcription
    texts = list(transcriptions.values())
    if len(set(texts)) == 1:
        return texts[0]

    # For now, return the longest transcription (often most complete)
    return max(texts, key=len)

def assess_proficiency(text):
    """Assess English proficiency using CEFR criteria"""
    if not groq_client or not text:
        return {
            'overall_level': 'Unable to assess',
            'pronunciation': 'N/A',
            'fluency': 'N/A',
            'grammar': 'N/A',
            'vocabulary': 'N/A',
            'feedback': 'AI assessment not available'
        }

    prompt = f"""
    Analyze the following English speech transcription and assess the speaker's proficiency level according to the CEFR framework (A1-C2).

    Transcription: "{text}"

    Please evaluate on these criteria:
    1. Pronunciation (clarity, accent, phonetics)
    2. Fluency (speech flow, hesitation, natural rhythm)
    3. Grammar (accuracy, complexity, error patterns)
    4. Vocabulary (range, appropriateness, sophistication)

    Provide:
    - Overall CEFR level (A1, A2, B1, B2, C1, C2)
    - Individual scores for each criterion (A1-C2)
    - Brief feedback for improvement

    Format your response as JSON with keys: overall_level, pronunciation, fluency, grammar, vocabulary, feedback
    """

    try:
        message = groq_client.chat.completions.create(
            model="llama3-8b-8192",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=500
        )

        result = message.choices[0].message.content.strip()

        # Try to parse as JSON
        try:
            assessment = json.loads(result)
            return assessment
        except:
            # Fallback if not valid JSON
            return {
                'overall_level': 'Assessment generated',
                'pronunciation': 'See feedback',
                'fluency': 'See feedback',
                'grammar': 'See feedback',
                'vocabulary': 'See feedback',
                'feedback': result
            }

    except Exception as e:
        return {
            'overall_level': 'Error',
            'pronunciation': 'N/A',
            'fluency': 'N/A',
            'grammar': 'N/A',
            'vocabulary': 'N/A',
            'feedback': f'Assessment failed: {str(e)}'
        }

@app.route('/api/upload', methods=['POST'])
def upload_file():
    """Handle file upload for pre-recorded audio"""
    try:
        if 'audio' not in request.files:
            return jsonify({'error': 'No file provided'}), 400

        file = request.files['audio']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400

        # Read file data
        audio_bytes = file.read()

        # Determine format from filename
        audio_format = file.filename.split('.')[-1].lower()
        if audio_format not in ['wav', 'mp3', 'webm', 'ogg']:
            audio_format = 'wav'  # default

        # Process the same way as recorded audio
        transcriptions = {}

        # Azure Speech
        azure_text = get_azure_transcription(audio_bytes, audio_format)
        if azure_text:
            transcriptions['azure'] = azure_text

        # Google Cloud Speech
        google_text = get_google_transcription(audio_bytes, audio_format)
        if google_text:
            transcriptions['google'] = google_text

        # Deepgram
        deepgram_text = get_deepgram_transcription(audio_bytes, audio_format)
        if deepgram_text:
            transcriptions['deepgram'] = deepgram_text

        if not transcriptions:
            return jsonify({'error': 'Failed to transcribe audio'}), 500

        combined_text = combine_transcriptions(transcriptions)
        assessment = assess_proficiency(combined_text)

        return jsonify({
            'transcriptions': transcriptions,
            'combined_text': combined_text,
            'assessment': assessment
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)