export interface VoiceCommand {
  pattern: string | RegExp;
  action: (args: Record<string, string>) => void;
  description: string;
  category: string;
}

export interface VoiceConfig {
  enabled: boolean;
  language: string;
  continuous: boolean;
  interimResults: boolean;
  confidenceThreshold: number;
}

export interface VoiceEngine {
  start(): Promise<void>;
  stop(): void;
  registerCommand(command: VoiceCommand): void;
  unregisterCommand(pattern: string): void;
  getRegisteredCommands(): VoiceCommand[];
  isListening(): boolean;
  onResult(callback: (result: VoiceResult) => void): () => void;
  onError(callback: (error: VoiceError) => void): () => void;
}

export interface VoiceResult {
  transcript: string;
  confidence: number;
  command?: VoiceCommand;
  args?: Record<string, string>;
}

export interface VoiceError {
  code: string;
  message: string;
}

export function createVoiceEngine(config: VoiceConfig): VoiceEngine {
  let recognition: SpeechRecognition | null = null;
  const commands: VoiceCommand[] = [];
  const resultCallbacks = new Set<(result: VoiceResult) => void>();
  const errorCallbacks = new Set<(error: VoiceError) => void>();
  let listening = false;

  function initRecognition(): void {
    if (typeof window === 'undefined') return;

    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      errorCallbacks.forEach((cb) => cb({ code: 'NOT_SUPPORTED', message: 'Speech recognition not supported' }));
      return;
    }

    recognition = new SpeechRecognition();
    recognition.lang = config.language;
    recognition.continuous = config.continuous;
    recognition.interimResults = config.interimResults;

    recognition.onresult = (event: SpeechRecognitionEvent) => {
      for (let i = event.resultIndex; i < event.results.length; i++) {
        const result = event.results[i];
        if (!result.isFinal) continue;

        const transcript = result[0].transcript.toLowerCase().trim();
        const confidence = result[0].confidence;

        if (confidence < config.confidenceThreshold) continue;

        const matchedCommand = matchCommand(transcript);
        const voiceResult: VoiceResult = {
          transcript,
          confidence,
          command: matchedCommand?.command,
          args: matchedCommand?.args,
        };

        resultCallbacks.forEach((cb) => cb(voiceResult));

        if (matchedCommand) {
          matchedCommand.command.action(matchedCommand.args);
        }
      }
    };

    recognition.onerror = (event: SpeechRecognitionErrorEvent) => {
      errorCallbacks.forEach((cb) => cb({ code: event.error, message: event.error }));
    };

    recognition.onend = () => {
      if (config.continuous && listening) {
        recognition?.start();
      } else {
        listening = false;
      }
    };
  }

  function matchCommand(transcript: string): { command: VoiceCommand; args: Record<string, string> } | null {
    for (const command of commands) {
      if (command.pattern instanceof RegExp) {
        const match = transcript.match(command.pattern);
        if (match) {
          const args: Record<string, string> = {};
          match.forEach((value, index) => {
            if (index > 0) args[`group${index}`] = value;
          });
          return { command, args };
        }
      } else {
        if (transcript.includes(command.pattern.toLowerCase())) {
          return { command, args: {} };
        }
      }
    }
    return null;
  }

  return {
    async start() {
      if (listening) return;
      if (!recognition) initRecognition();
      if (!recognition) return;

      try {
        recognition.start();
        listening = true;
      } catch (e) {
        errorCallbacks.forEach((cb) => cb({ code: 'START_FAILED', message: String(e) }));
      }
    },
    stop() {
      recognition?.stop();
      listening = false;
    },
    registerCommand(command) {
      commands.push(command);
    },
    unregisterCommand(pattern) {
      const idx = commands.findIndex((c) => {
        if (c.pattern instanceof RegExp) return c.pattern.source === pattern;
        return c.pattern === pattern;
      });
      if (idx !== -1) commands.splice(idx, 1);
    },
    getRegisteredCommands: () => [...commands],
    isListening: () => listening,
    onResult(callback) {
      resultCallbacks.add(callback);
      return () => resultCallbacks.delete(callback);
    },
    onError(callback) {
      errorCallbacks.add(callback);
      return () => errorCallbacks.delete(callback);
    },
  };
}

export function createVoiceCommands(): VoiceCommand[] {
  return [
    { pattern: /open\s+(.+)/i, action: (args) => console.log('Opening:', args.group1), description: 'Open a panel or feature', category: 'navigation' },
    { pattern: /close\s+(.+)/i, action: (args) => console.log('Closing:', args.group1), description: 'Close a panel or feature', category: 'navigation' },
    { pattern: /scroll\s+(up|down|left|right)/i, action: (args) => console.log('Scrolling:', args.group1), description: 'Scroll in a direction', category: 'navigation' },
    { pattern: /zoom\s+(in|out)/i, action: (args) => console.log('Zooming:', args.group1), description: 'Zoom in or out', category: 'view' },
    { pattern: /save/i, action: () => console.log('Saving'), description: 'Save current state', category: 'action' },
    { pattern: /undo/i, action: () => console.log('Undoing'), description: 'Undo last action', category: 'action' },
    { pattern: /redo/i, action: () => console.log('Redoing'), description: 'Redo last action', category: 'action' },
  ];
}
