# Voice and language matrix

Text language support and voice support are intentionally separate capabilities.

The application currently exposes language choices for English, Hindi, Telugu, Tamil, Bengali, Marathi, Gujarati, Punjabi, Urdu, Kannada, Malayalam, Spanish, French, German, Arabic, Italian, Portuguese, Japanese and Simplified Chinese.

Browser STT uses the selected speech locale. Browser TTS uses the same locale and then lets the operating system/browser select an installed voice.

Amazon Transcribe currently supports streaming for many of these languages, including Hindi, Bengali, Tamil, Telugu and Kannada. Amazon Polly supports a broad set of languages, including Hindi, English, Spanish, French, German, Italian, Portuguese, Japanese, Chinese and Arabic, but coverage is not identical to Transcribe or Translate.

Cloud voice selection is therefore provider-aware. The production implementation must use provider capability discovery rather than assuming a hard-coded voice is available in every AWS region.
