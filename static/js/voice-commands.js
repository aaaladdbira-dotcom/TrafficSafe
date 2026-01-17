"""
Voice Commands Support
======================
JavaScript helper for Web Speech API voice command integration
Include this in accident reporting forms
"""

// Voice Commands Handler
class VoiceCommandsHandler {
  constructor(options = {}) {
    this.recognition = null;
    this.isListening = false;
    this.transcript = '';
    this.isFinal = false;
    
    // Get browser's SpeechRecognition API
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      console.warn('Speech Recognition API not supported in this browser');
      return;
    }
    
    this.recognition = new SpeechRecognition();
    this.setupRecognition(options);
  }
  
  setupRecognition(options) {
    const lang = options.language || 'en-US';
    const interimResults = options.interimResults !== false;
    const maxAlternatives = options.maxAlternatives || 1;
    
    this.recognition.continuous = options.continuous || false;
    this.recognition.interimResults = interimResults;
    this.recognition.maxAlternatives = maxAlternatives;
    this.recognition.lang = lang;
    
    // Start listening
    this.recognition.onstart = () => {
      this.isListening = true;
      this.transcript = '';
      console.log('Voice recognition started');
    };
    
    // Get results
    this.recognition.onresult = (event) => {
      this.transcript = '';
      
      for (let i = event.resultIndex; i < event.results.length; i++) {
        const transcript = event.results[i][0].transcript;
        this.transcript += transcript + ' ';
        
        if (event.results[i].isFinal) {
          this.isFinal = true;
        }
      }
      
      // Emit event with results
      window.dispatchEvent(new CustomEvent('voiceResult', {
        detail: {
          transcript: this.transcript.trim(),
          isFinal: this.isFinal,
          confidence: this.getConfidence(event)
        }
      }));
    };
    
    // Handle errors
    this.recognition.onerror = (event) => {
      console.error('Voice recognition error:', event.error);
      window.dispatchEvent(new CustomEvent('voiceError', {
        detail: { error: event.error }
      }));
    };
    
    // Stop listening
    this.recognition.onend = () => {
      this.isListening = false;
      console.log('Voice recognition ended');
      window.dispatchEvent(new CustomEvent('voiceEnd', {
        detail: { transcript: this.transcript }
      }));
    };
  }
  
  start() {
    if (!this.recognition) {
      console.error('Speech Recognition not supported');
      return false;
    }
    this.recognition.start();
    return true;
  }
  
  stop() {
    if (this.recognition) {
      this.recognition.stop();
    }
  }
  
  abort() {
    if (this.recognition) {
      this.recognition.abort();
    }
  }
  
  getConfidence(event) {
    if (event.results.length === 0) return 0;
    return event.results[event.results.length - 1][0].confidence;
  }
  
  isSupported() {
    return this.recognition !== null;
  }
}


// Usage in accident form
document.addEventListener('DOMContentLoaded', () => {
  const voiceBtn = document.getElementById('voiceCommandBtn');
  const descriptionInput = document.getElementById('description');
  
  if (!voiceBtn) return;
  
  // Check browser support
  const voiceHandler = new VoiceCommandsHandler({ language: 'en-US' });
  
  if (!voiceHandler.isSupported()) {
    voiceBtn.disabled = true;
    voiceBtn.title = 'Speech Recognition not supported in your browser';
  }
  
  // Toggle listening
  voiceBtn.addEventListener('click', () => {
    if (voiceHandler.isListening) {
      voiceHandler.stop();
      voiceBtn.classList.remove('listening');
      voiceBtn.textContent = '🎤 Speak';
    } else {
      voiceHandler.start();
      voiceBtn.classList.add('listening');
      voiceBtn.textContent = '⏹️ Stop';
    }
  });
  
  // Handle voice results
  window.addEventListener('voiceResult', (e) => {
    const { transcript, isFinal } = e.detail;
    
    if (isFinal) {
      // Append to textarea
      if (descriptionInput.value) {
        descriptionInput.value += ' ' + transcript;
      } else {
        descriptionInput.value = transcript;
      }
      
      // Show toast notification
      if (window.Toast) {
        Toast.success(`Voice captured: "${transcript}"`);
      }
    } else {
      // Show interim results
      console.log('Interim:', transcript);
    }
  });
  
  // Handle errors
  window.addEventListener('voiceError', (e) => {
    const { error } = e.detail;
    voiceBtn.classList.remove('listening');
    voiceBtn.textContent = '🎤 Speak';
    
    if (window.Toast) {
      Toast.error(`Voice error: ${error}`);
    }
  });
});
