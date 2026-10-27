import { useState, useRef, useCallback, useEffect } from "react";
import type { ModalityStatus, VisionSignalResponse } from "../types";
import { api } from "../services/api";

export function useVision() {
  const [cameraStatus, setCameraStatus] = useState<ModalityStatus>({
    available: typeof navigator !== "undefined" && !!navigator.mediaDevices,
    active: false,
    permission: "prompt",
  });
  const [lastSignal, setLastSignal] = useState<VisionSignalResponse | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState<boolean>(false);

  const videoRef = useRef<HTMLVideoElement | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const intervalRef = useRef<any>(null);

  /**
   * Request webcam access explicitly
   */
  const requestPermission = useCallback(async (): Promise<boolean> => {
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      setCameraStatus({
        available: false,
        active: false,
        permission: "unsupported",
        error: "Camera access is not supported in this browser.",
      });
      return false;
    }

    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { width: { ideal: 320 }, height: { ideal: 240 }, frameRate: { max: 5 } },
      });
      streamRef.current = stream;

      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        videoRef.current.play().catch(() => {});
      }

      setCameraStatus({
        available: true,
        active: true,
        permission: "granted",
      });
      return true;
    } catch (err: any) {
      const isDenied = err.name === "NotAllowedError" || err.name === "PermissionDeniedError";
      setCameraStatus({
        available: true,
        active: false,
        permission: isDenied ? "denied" : "prompt",
        error: isDenied ? "Camera access denied by user." : err.message,
      });
      return false;
    }
  }, []);

  /**
   * Stop camera tracks cleanly
   */
  const stopCamera = useCallback(() => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => track.stop());
      streamRef.current = null;
    }
    if (videoRef.current) {
      videoRef.current.srcObject = null;
    }
    setCameraStatus((prev) => ({ ...prev, active: false }));
  }, []);

  /**
   * Capture single frame in-memory and extract anonymous facial signals
   */
  const captureAndAnalyze = useCallback(async () => {
    if (!videoRef.current || !streamRef.current || isAnalyzing) return;
    const video = videoRef.current;
    if (video.videoWidth === 0 || video.videoHeight === 0) return;

    setIsAnalyzing(true);
    try {
      const canvas = document.createElement("canvas");
      canvas.width = video.videoWidth;
      canvas.height = video.videoHeight;
      const ctx = canvas.getContext("2d");
      if (!ctx) return;

      ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

      // Convert to in-memory JPEG blob
      canvas.toBlob(
        async (blob) => {
          if (!blob) {
            setIsAnalyzing(false);
            return;
          }
          try {
            const signal = await api.analyzeFace(blob);
            setLastSignal(signal);
            setCameraStatus((prev) => ({
              ...prev,
              confidence: signal.confidence,
              lastSignalTimestamp: signal.timestamp,
            }));
          } catch (err) {
            console.warn("Vision signal extraction error:", err);
          } finally {
            setIsAnalyzing(false);
            // Explicit canvas cleanup
            canvas.width = 0;
            canvas.height = 0;
          }
        },
        "image/jpeg",
        0.75
      );
    } catch (e) {
      setIsAnalyzing(false);
    }
  }, [isAnalyzing]);

  /**
   * Toggle camera stream
   */
  const toggleCamera = useCallback(async () => {
    if (cameraStatus.active) {
      stopCamera();
    } else {
      const granted = await requestPermission();
      if (granted) {
        // Run periodic analysis every 4 seconds to conserve resources
        intervalRef.current = setInterval(captureAndAnalyze, 4000);
      }
    }
  }, [cameraStatus.active, stopCamera, requestPermission, captureAndAnalyze]);

  // Clean up stream on unmount
  useEffect(() => {
    return () => {
      stopCamera();
    };
  }, [stopCamera]);

  return {
    cameraStatus,
    videoRef,
    lastSignal,
    isAnalyzing,
    toggleCamera,
    stopCamera,
  };
}
