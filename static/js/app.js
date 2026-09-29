// English Proficiency Assessment JavaScript

class SpeechAssessmentApp {
    constructor() {
        this.mediaRecorder = null;
        this.audioChunks = [];
        this.isRecording = false;
        this.startTime = null;
        this.timerInterval = null;
        this.stream = null;
        this.audioContext = null;
        this.analyser = null;
        this.canvas = null;
        this.canvasContext = null;

        this.initializeElements();
        this.setupEventListeners();
        this.initializeCanvas();
    }

    initializeElements() {
        this.recordBtn = document.getElementById('recordBtn');
        this.stopBtn = document.getElementById('stopBtn');
        this.uploadBtn = document.getElementById('uploadBtn');
        this.fileInput = document.getElementById('fileInput');
        this.statusDiv = document.getElementById('status');
        this.timerDiv = document.getElementById('timer');
        this.resultsSection = document.getElementById('resultsSection');
        this.loadingDiv = document.getElementById('loading');
        this.waveformCanvas = document.getElementById('waveform');
    }

    setupEventListeners() {
        this.recordBtn.addEventListener('click', () => this.startRecording());
        this.stopBtn.addEventListener('click', () => this.stopRecording());
        this.uploadBtn.addEventListener('click', () => this.fileInput.click());
        this.fileInput.addEventListener('change', (e) => this.handleFileUpload(e));
    }

    initializeCanvas() {
        this.canvas = this.waveformCanvas;
        this.canvasContext = this.canvas.getContext('2d');
        this.canvasContext.fillStyle = '#f5f5f5';
        this.canvasContext.fillRect(0, 0, this.canvas.width, this.canvas.height);
    }

    async startRecording() {
        try {
            this.stream = await navigator.mediaDevices.getUserMedia({
                audio: {
                    sampleRate: 16000,
                    channelCount: 1,
                    echoCancellation: true,
                    noiseSuppression: true
                }
            });

            this.mediaRecorder = new MediaRecorder(this.stream, {
                mimeType: 'audio/webm;codecs=opus'
            });

            this.audioChunks = [];
            this.mediaRecorder.ondataavailable = (event) => {
                this.audioChunks.push(event.data);
            };

            this.mediaRecorder.onstop = () => this.processRecording();

            // Setup audio visualization
            this.setupAudioVisualization();

            this.mediaRecorder.start(100); // Collect data every 100ms
            this.isRecording = true;
            this.startTime = Date.now();

            this.updateUIForRecording();
            this.startTimer();

        } catch (error) {
            console.error('Error starting recording:', error);
            this.showError('Could not access microphone. Please check permissions.');
        }
    }

    stopRecording() {
        if (this.mediaRecorder && this.isRecording) {
            this.mediaRecorder.stop();
            this.stream.getTracks().forEach(track => track.stop());
            this.isRecording = false;
            this.stopTimer();
            this.updateUIForStopped();
        }
    }

    updateUIForRecording() {
        this.recordBtn.disabled = true;
        this.stopBtn.disabled = false;
        this.uploadBtn.disabled = true;
        this.statusDiv.textContent = 'Recording... Speak English (any duration)';
        this.statusDiv.style.color = '#4CAF50';
    }

    updateUIForStopped() {
        this.recordBtn.disabled = false;
        this.stopBtn.disabled = true;
        this.uploadBtn.disabled = false;
        this.statusDiv.textContent = 'Processing your speech...';
        this.statusDiv.style.color = '#2196F3';
    }

    startTimer() {
        this.timerInterval = setInterval(() => {
            const elapsed = Math.floor((Date.now() - this.startTime) / 1000);
            const minutes = Math.floor(elapsed / 60);
            const seconds = elapsed % 60;
            this.timerDiv.textContent = `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
        }, 1000);
    }

    stopTimer() {
        if (this.timerInterval) {
            clearInterval(this.timerInterval);
            this.timerInterval = null;
        }
    }

    setupAudioVisualization() {
        this.audioContext = new (window.AudioContext || window.webkitAudioContext)();
        this.analyser = this.audioContext.createAnalyser();
        this.analyser.fftSize = 256;

        const source = this.audioContext.createMediaStreamSource(this.stream);
        source.connect(this.analyser);

        this.drawWaveform();
    }

    drawWaveform() {
        if (!this.isRecording) return;

        const bufferLength = this.analyser.frequencyBinCount;
        const dataArray = new Uint8Array(bufferLength);

        const draw = () => {
            if (!this.isRecording) return;

            this.analyser.getByteFrequencyData(dataArray);

            this.canvasContext.fillStyle = '#f5f5f5';
            this.canvasContext.fillRect(0, 0, this.canvas.width, this.canvas.height);

            this.canvasContext.fillStyle = '#4CAF50';
            this.canvasContext.strokeStyle = '#4CAF50';

            const barWidth = (this.canvas.width / bufferLength) * 2.5;
            let barHeight;
            let x = 0;

            for (let i = 0; i < bufferLength; i++) {
                barHeight = (dataArray[i] / 255) * this.canvas.height;

                this.canvasContext.fillRect(x, this.canvas.height - barHeight, barWidth, barHeight);
                x += barWidth + 1;
            }

            requestAnimationFrame(draw);
        };

        draw();
    }

    async processRecording() {
        if (this.audioChunks.length === 0) {
            this.showError('No audio recorded. Please try again.');
            return;
        }

        this.showLoading();

        try {
            const audioBlob = new Blob(this.audioChunks, { type: 'audio/webm' });
            const audioData = await this.blobToBase64(audioBlob);

            const response = await fetch('/api/assess', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    audio: audioData,
                    format: 'webm'
                })
            });

            const result = await response.json();

            if (response.ok) {
                this.displayResults(result);
            } else {
                this.showError(result.error || 'Assessment failed');
            }

        } catch (error) {
            console.error('Error processing recording:', error);
            this.showError('Failed to process recording: ' + error.message);
        } finally {
            this.hideLoading();
        }
    }

    async handleFileUpload(event) {
        const file = event.target.files[0];
        if (!file) return;

        this.showLoading();

        try {
            const formData = new FormData();
            formData.append('audio', file);

            const response = await fetch('/api/upload', {
                method: 'POST',
                body: formData
            });

            const result = await response.json();

            if (response.ok) {
                this.displayResults(result);
            } else {
                this.showError(result.error || 'Upload failed');
            }

        } catch (error) {
            console.error('Error uploading file:', error);
            this.showError('Failed to upload file');
        } finally {
            this.hideLoading();
        }
    }

    blobToBase64(blob) {
        return new Promise((resolve, reject) => {
            const reader = new FileReader();
            reader.onload = () => resolve(reader.result);
            reader.onerror = reject;
            reader.readAsDataURL(blob);
        });
    }

    displayResults(result) {
        // Display transcriptions
        const transcriptionDiv = document.getElementById('transcriptionResults');
        transcriptionDiv.innerHTML = '';

        if (result.transcriptions) {
            Object.entries(result.transcriptions).forEach(([provider, text]) => {
                const div = document.createElement('div');
                div.className = 'transcription-item';
                div.innerHTML = `<strong>${provider.toUpperCase()}:</strong> ${text}`;
                transcriptionDiv.appendChild(div);
            });
        }

        // Display assessment
        if (result.assessment) {
            document.getElementById('overallLevel').textContent = result.assessment.overall_level || 'N/A';
            document.getElementById('overallLevel').className = `cefr-${(result.assessment.overall_level || '').toLowerCase()}`;

            document.getElementById('pronunciationScore').textContent = result.assessment.pronunciation || 'N/A';
            document.getElementById('pronunciationScore').className = `cefr-${(result.assessment.pronunciation || '').toLowerCase()}`;

            document.getElementById('fluencyScore').textContent = result.assessment.fluency || 'N/A';
            document.getElementById('fluencyScore').className = `cefr-${(result.assessment.fluency || '').toLowerCase()}`;

            document.getElementById('grammarScore').textContent = result.assessment.grammar || 'N/A';
            document.getElementById('grammarScore').className = `cefr-${(result.assessment.grammar || '').toLowerCase()}`;

            document.getElementById('vocabularyScore').textContent = result.assessment.vocabulary || 'N/A';
            document.getElementById('vocabularyScore').className = `cefr-${(result.assessment.vocabulary || '').toLowerCase()}`;

            document.getElementById('feedbackText').textContent = result.assessment.feedback || 'No feedback available';
        }

        this.resultsSection.style.display = 'block';
        this.statusDiv.textContent = 'Assessment complete!';
        this.statusDiv.style.color = '#28a745';
    }

    showLoading() {
        this.loadingDiv.style.display = 'block';
        this.resultsSection.style.display = 'none';
    }

    hideLoading() {
        this.loadingDiv.style.display = 'none';
    }

    showError(message) {
        this.statusDiv.textContent = `Error: ${message}`;
        this.statusDiv.style.color = '#dc3545';
        this.hideLoading();
    }
}

// Initialize the app when the page loads
document.addEventListener('DOMContentLoaded', () => {
    new SpeechAssessmentApp();
});