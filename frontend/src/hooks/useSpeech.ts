import { useState, useRef, useCallback } from "react";
import type { ModalityStatus } from "../types";
import { api } from "../services/api";

export function useSpeech(language: string = "en") {
  const [micStatus, setMicStatus] = useState<ModalityStatus>({
    available: typeof navigator !== "undefined" && !!navigator.mediaDevices,
    active: false,
    permission: "prompt",
  });
  const [isRecording, setIsRecording] = useState<boolean>(false);
  const [isSpeaking, setIsSpeaking] = useState<boolean>(false);
  const [speechError, setSpeechError] = useState<string | null>(null);

  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const currentAudioRef = useRef<HTMLAudioElement | null>(null);

  /**
   * Request microphone permission explicitly
   */
  const requestPermission = useCallback(async (): Promise<boolean> => {
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      setMicStatus({
        available: false,
        active: false,
        permission: "unsupported",
        error: "Microphone recording is not supported in this browser.",
      });
      return false;
    }

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      // Release stream immediately after verification
      stream.getTracks().forEach((track) => track.stop());

      setMicStatus({
        available: true,
        active: false,
        permission: "granted",
      });
      setSpeechError(null);
      return true;
    } catch (err: any) {
      const isDenied = err.name === "NotAllowedError" || err.name === "PermissionDeniedError";
      setMicStatus({
        available: true,
        active: false,
        permission: isDenied ? "denied" : "prompt",
        error: isDenied ? "Microphone access denied by user." : err.message,
      });
      return false;
    }
  }, []);

  /**
   * Start voice capture
   */
  const startRecording = useCallback(
    async (onTranscribe: (text: string) => void) => {
      setSpeechError(null);

      // Check permission first
      if (micStatus.permission !== "granted") {
        const granted = await requestPermission();
        if (!granted) return;
      }

      try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        audioChunksRef.current = [];

        const mediaRecorder = new MediaRecorder(stream);
        mediaRecorderRef.current = mediaRecorder;

        mediaRecorder.ondataavailable = (event) => {
          if (event.data.size > 0) {
            audioChunksRef.current.push(event.data);
          }
        };

        mediaRecorder.onstop = async () => {
          // Stop all stream tracks
          stream.getTracks().forEach((track) => track.stop());
          setIsRecording(false);
          setMicStatus((prev) => ({ ...prev, active: false }));

          if (audioChunksRef.current.length === 0) return;

          const audioBlob = new Blob(audioChunksRef.current, {
            type: mediaRecorder.mimeType || "audio/wav",
          });

          try {
            // Transcribe using backend API
            const transcribedText = await api.transcribeAudio(audioBlob);
            if (transcribedText) {
              onTranscribe(transcribedText);
            }
          } catch (err: any) {
            console.warn("Backend STT error, trying browser fallback recognition:", err);
            setSpeechError("Voice transcription failed. You can continue typing in text mode.");
          }
        };

        mediaRecorder.start();
        setIsRecording(true);
        setMicStatus((prev) => ({ ...prev, active: true }));
      } catch (err: any) {
        console.error("Recording error:", err);
        setSpeechError("Failed to access microphone. Text fallback is active.");
        setIsRecording(false);
      }
    },
    [micStatus.permission, requestPermission]
  );

  /**
   * Stop voice capture
   */
  const stopRecording = useCallback(() => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state === "recording") {
      mediaRecorderRef.current.stop();
    }
  }, []);

  /**
   * Speak text out loud via TTS
   */
  const speakText = useCallback(
    async (text: string) => {
      // Stop any existing playback
      if (currentAudioRef.current) {
        currentAudioRef.current.pause();
        currentAudioRef.current = null;
      }
      if (window.speechSynthesis) {
        window.speechSynthesis.cancel();
      }

      setIsSpeaking(true);

      // 1. Try backend TTS synthesis endpoint
      try {
        const audioBlob = await api.synthesizeSpeech(text, language);
        const audioUrl = URL.createObjectURL(audioBlob);
        const audio = new Audio(audioUrl);
        currentAudioRef.current = audio;

        audio.onended = () => {
          setIsSpeaking(false);
          URL.revokeObjectURL(audioUrl);
        };
        audio.onerror = () => {
          // Fallback to browser synthesis
          fallbackBrowserSpeak(text);
        };

        await audio.play();
        return;
      } catch (err) {
        console.warn("Backend TTS failed, falling back to browser Web Speech API:", err);
        fallbackBrowserSpeak(text);
      }
    },
    [language]
  );

  const fallbackBrowserSpeak = (text: string) => {
    if (typeof window !== "undefined" && "speechSynthesis" in window) {
      const utterance = new SpeechSynthesisUtterance(text);
      utterance.lang = language;
      utterance.rate = 1.0;
      utterance.onend = () => setIsSpeaking(false);
      utterance.onerror = () => setIsSpeaking(false);
      window.speechSynthesis.speak(utterance);
    } else {
      setIsSpeaking(false);
    }
  };

  const stopSpeaking = useCallback(() => {
    if (currentAudioRef.current) {
      currentAudioRef.current.pause();
      currentAudioRef.current = null;
    }
    if (typeof window !== "undefined" && "speechSynthesis" in window) {
      window.speechSynthesis.cancel();
    }
    setIsSpeaking(false);
  }, []);

  return {
    micStatus,
    isRecording,
    isSpeaking,
    speechError,
    requestPermission,
    startRecording,
    stopRecording,
    speakText,
    stopSpeaking,
  };
}
