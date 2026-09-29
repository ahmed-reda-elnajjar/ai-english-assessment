# English Proficiency Assessment App

An advanced AI-powered application that evaluates English speaking proficiency using multiple speech-to-text providers and CEFR-based assessment.

## Features

- **Multi-Provider Speech Recognition**: Combines Azure Speech, Google Cloud Speech, and Deepgram for maximum accuracy
- **CEFR Assessment**: Evaluates pronunciation, fluency, grammar, and vocabulary on A1-C2 scale
- **Browser Recording**: Real-time audio recording with WebRTC
- **File Upload**: Support for pre-recorded audio files
- **AI-Powered Analysis**: Uses OpenAI GPT-4 for sophisticated language assessment

## Prerequisites

### API Keys Required
1. **OpenAI API Key** - For AI assessment (required)
2. **Azure Speech Services** - Optional but recommended
3. **Google Cloud Speech** - Optional
4. **Deepgram API** - Optional

### System Requirements
- Python 3.8+
- Modern web browser with microphone access
- Internet connection for API calls

## Local Development Setup

1. **Clone and setup**:
   ```bash
   git clone <repository-url>
   cd english-proficiency-assessment
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Configure API keys**:
   Create a `.env` file in the root directory:
   ```env
   OPENAI_API_KEY=your_openai_api_key_here
   AZURE_SPEECH_KEY=your_azure_speech_key_here
   AZURE_SPEECH_REGION=eastus
   GOOGLE_APPLICATION_CREDENTIALS=path/to/google/credentials.json
   DEEPGRAM_API_KEY=your_deepgram_api_key_here
   ```

3. **Run the application**:
   ```bash
   python app.py
   ```
   Open http://localhost:5000 in your browser

## Azure Deployment

### Using Azure Developer CLI (Recommended)

1. **Install Azure Developer CLI**:
   ```bash
   # Windows
   winget install Microsoft.Azd

   # Or download from: https://learn.microsoft.com/en-us/azure/developer/azure-developer-cli/install-azd
   ```

2. **Login to Azure**:
   ```bash
   azd auth login
   ```

3. **Initialize and deploy**:
   ```bash
   azd init
   azd up
   ```

### Manual Azure App Service Deployment

1. **Create App Service**:
   ```bash
   az group create --name assessment-rg --location eastus
   az appservice plan create --name assessment-plan --resource-group assessment-rg --sku B1
   az webapp create --name english-assessment-app --resource-group assessment-rg --plan assessment-plan --runtime "PYTHON:3.9"
   ```

2. **Set environment variables**:
   ```bash
   az webapp config appsettings set --name english-assessment-app --resource-group assessment-rg --setting OPENAI_API_KEY="your_key"
   # Add other API keys as needed
   ```

3. **Deploy code**:
   ```bash
   az webapp up --name english-assessment-app --resource-group assessment-rg --location eastus
   ```

## API Setup Instructions

### OpenAI API (Required)
1. Go to [OpenAI Platform](https://platform.openai.com/)
2. Create an account and generate an API key
3. Add to environment variables

### Azure Speech Services (Optional)
1. Go to [Azure Portal](https://portal.azure.com/)
2. Create Cognitive Services resource
3. Get subscription key and region
4. Add to environment variables

### Google Cloud Speech (Optional)
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create project and enable Speech-to-Text API
3. Create service account and download credentials JSON
4. Set GOOGLE_APPLICATION_CREDENTIALS to JSON file path

### Deepgram API (Optional)
1. Go to [Deepgram Console](https://console.deepgram.com/)
2. Create account and get API key
3. Add to environment variables

## Usage

1. **Open the application** in your web browser
2. **Allow microphone access** when prompted
3. **Click "Start Recording"** and speak English (any duration)
4. **Click "Stop Recording"** when finished
5. **View your CEFR assessment** results

### Alternative: File Upload
- Click "Upload Audio File"
- Select a pre-recorded audio file (WAV, MP3, WebM, OGG) - any duration
- Get assessment results

## CEFR Levels

- **A1**: Beginner - Basic phrases and expressions
- **A2**: Elementary - Simple everyday communication
- **B1**: Intermediate - Independent communication
- **B2**: Upper Intermediate - Clear and detailed communication
- **C1**: Advanced - Fluent and well-structured communication
- **C2**: Proficient - Native-like fluency

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Web Browser   │    │   Flask API     │    │  Speech APIs    │
│                 │    │                 │    │                 │
│ • WebRTC        │◄──►│ • /api/assess   │◄──►│ • Azure Speech  │
│ • Audio Record  │    │ • /api/upload   │    │ • Google Cloud  │
│ • Visualization │    │ • CORS enabled  │    │ • Deepgram      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌─────────────────┐
                       │   OpenAI API    │
                       │                 │
                       │ • GPT-4         │
                       │ • CEFR Analysis │
                       └─────────────────┘
```

## Troubleshooting

### Common Issues

1. **Microphone not working**:
   - Ensure HTTPS in production (required for WebRTC)
   - Check browser permissions
   - Try different browser

2. **API errors**:
   - Verify API keys are set correctly
   - Check API quotas and limits
   - Ensure network connectivity

3. **Assessment fails**:
   - Ensure at least one speech provider is configured
   - Check OpenAI API key for assessment
   - Verify audio quality and length

### Development Tips

- Use browser developer tools to debug frontend issues
- Check Flask logs for backend errors
- Test with different audio formats and lengths
- Monitor API usage to avoid rate limits

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support and questions:
- Create an issue in the repository
- Check the troubleshooting section
- Review API documentation for integrated services