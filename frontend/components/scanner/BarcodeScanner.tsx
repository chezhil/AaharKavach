"use client";

import { useEffect, useRef, useState } from "react";
import { CameraOff, Loader2 } from "lucide-react";
import type { Html5Qrcode } from "html5-qrcode";

type Status = "starting" | "scanning" | "denied" | "unsupported";

/**
 * Live camera barcode scanner. html5-qrcode touches `navigator` and the DOM at
 * import time, so it is imported lazily inside the effect — that also keeps it
 * out of the bundle for everyone who never opens the scanner.
 */
export function BarcodeScanner({
  onDetected,
  onCaptureLabel,
}: {
  onDetected: (barcode: string) => void;
  onCaptureLabel?: (base64Image: string) => void;
}) {
  const [status, setStatus] = useState<Status>("starting");
  const instance = useRef<Html5Qrcode | null>(null);
  const done = useRef(false);
  const isCapturingRef = useRef(false);
  const containerRef = useRef<HTMLDivElement>(null);
  const streamRef = useRef<MediaStream | null>(null);

  const killAllTracks = () => {
    // 1. Kill from streamRef
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((t) => {
        t.stop();
        t.enabled = false;
      });
      streamRef.current = null;
    }

    // 2. Kill from any lingering video elements anywhere in the document
    if (typeof document !== "undefined") {
      document.querySelectorAll("video").forEach((v) => {
        v.onabort = null;
        v.onerror = null;
        try {
          v.pause();
        } catch (e) {}

        if (v.srcObject) {
          try {
            (v.srcObject as MediaStream).getTracks().forEach((t) => {
              t.stop();
              t.enabled = false;
            });
          } catch (e) {}
          v.srcObject = null;
        }
      });
    }
  };

  useEffect(() => {
    // html5-qrcode often drops unhandled AbortErrors if the component unmounts
    // while the camera is starting. Catch them so they don't crash Next.js.
    const handleUnhandledRejection = (event: PromiseRejectionEvent) => {
      if (
        event.reason?.name === "AbortError" ||
        event.reason?.message?.includes("play() request was interrupted") ||
        event.reason?.message?.includes("onabort() called") ||
        (typeof event.reason === "string" &&
          event.reason.includes("onabort() called"))
      ) {
        event.preventDefault();
      }
    };
    const handleError = (event: ErrorEvent) => {
      if (event.message?.includes("onabort() called")) {
        event.preventDefault();
      }
    };
    window.addEventListener("unhandledrejection", handleUnhandledRejection);
    window.addEventListener("error", handleError);
    return () => {
      window.removeEventListener(
        "unhandledrejection",
        handleUnhandledRejection,
      );
      window.removeEventListener("error", handleError);
      // Failsafe cleanup when component entirely unmounts
      killAllTracks();
    };
  }, []);

  useEffect(() => {
    let cancelled = false;
    // Captured now, not in the cleanup: React detaches DOM refs during unmount,
    // so reading containerRef.current from the teardown below can hand back
    // null and skip the track cleanup entirely -- which is the whole point of it.
    const container = containerRef.current;

    (async () => {
      if (
        typeof navigator === "undefined" ||
        !navigator.mediaDevices?.getUserMedia
      ) {
        setStatus("unsupported");
        return;
      }

      let scanner: Html5Qrcode | null = null;

      try {
        const { Html5Qrcode, Html5QrcodeSupportedFormats } =
          await import("html5-qrcode");
        if (cancelled) return;

        const created = new Html5Qrcode("scanner-region", {
          verbose: false,
          formatsToSupport: [
            Html5QrcodeSupportedFormats.EAN_13,
            Html5QrcodeSupportedFormats.EAN_8,
            Html5QrcodeSupportedFormats.UPC_A,
            Html5QrcodeSupportedFormats.UPC_E,
            Html5QrcodeSupportedFormats.CODE_128,
            Html5QrcodeSupportedFormats.CODE_39,
            Html5QrcodeSupportedFormats.QR_CODE,
          ],
        });
        scanner = created;

        const begin = (source: MediaTrackConstraints | string) =>
          created.start(
            source,
            // A wide, short box matches the shape of a barcode.
            { fps: 12, qrbox: { width: 260, height: 150 }, aspectRatio: 1.2 },
            (decoded) => {
              if (done.current || isCapturingRef.current) return;
              done.current = true;
              onDetected(decoded);
            },
            () => {
              // Per-frame decode misses are constant and expected — ignore them.
            },
          );

        try {
          await begin({ facingMode: "environment" });
        } catch {
          // A laptop has no rear camera, so the environment constraint can be
          // unsatisfiable — fall back to whatever device the machine does have.
          const cameras = await Html5Qrcode.getCameras();
          if (cameras.length === 0) throw new Error("no camera available");
          await begin(cameras[0].id);
        }

        // Tracked only once it is genuinely running: stop() throws on a
        // scanner that never started, so the cleanup path must never see one.
        instance.current = created;
        if (!cancelled) setStatus("scanning");

        // After starting, capture the streamRef for teardown.
        if (container) {
          const videoEl = container.querySelector("video");
          if (videoEl && videoEl.srcObject) {
            streamRef.current = videoEl.srcObject as MediaStream;
          }
        }
      } catch {
        try {
          if (scanner) scanner.clear();
        } catch {}
        if (!cancelled) setStatus("denied");
      }
    })();

    return () => {
      cancelled = true;
      const scanner = instance.current;
      instance.current = null;

      // Releasing the tracks is what actually turns the camera indicator off;
      // stop() alone does not always do it.
      killAllTracks();

      if (container) {
        const videoEl = container.querySelector(
          "video",
        ) as HTMLVideoElement | null;
        if (videoEl) {
          videoEl.onabort = null; // Prevent html5-qrcode from throwing "RenderedCameraImpl video surface onabort() called"
          videoEl.onerror = null;
          try {
            videoEl.pause();
          } catch (e) {}
          if (videoEl.srcObject) {
            try {
              const stream = videoEl.srcObject as MediaStream;
              stream.getTracks().forEach((t) => t.stop());
            } catch (e) {}
          }
          videoEl.srcObject = null;
        }
      }

      if (!scanner) {
        return;
      }
      // stop() rejects *and* can throw synchronously; both end in the same place.
      try {
        Promise.resolve(scanner.stop()).then(
          () => {
            try {
              scanner.clear();
            } catch {}
          },
          () => {
            try {
              scanner.clear();
            } catch {}
          },
        );
      } catch {
        try {
          scanner.clear();
        } catch {}
      }
    };
  }, [onDetected]);

  const [isCapturing, setIsCapturing] = useState(false);

  const handleCapture = () => {
    if (!onCaptureLabel || !containerRef.current || isCapturing) return;
    const video = containerRef.current.querySelector("video");
    // ReadyState 2 is HAVE_CURRENT_DATA. videoWidth must be > 0.
    if (!video || video.readyState < 2 || video.videoWidth === 0) return;

    setIsCapturing(true);
    isCapturingRef.current = true;
    const canvas = document.createElement("canvas");

    // Downscale to max 1600px width/height to avoid massive payloads
    let width = video.videoWidth;
    let height = video.videoHeight;
    const MAX_DIM = 1600;
    if (width > MAX_DIM || height > MAX_DIM) {
      if (width > height) {
        height = Math.floor((height * MAX_DIM) / width);
        width = MAX_DIM;
      } else {
        width = Math.floor((width * MAX_DIM) / height);
        height = MAX_DIM;
      }
    }

    canvas.width = width;
    canvas.height = height;
    const ctx = canvas.getContext("2d");
    if (ctx) {
      ctx.drawImage(video, 0, 0, width, height);
      const base64Image = canvas.toDataURL("image/jpeg", 0.85);
      // Clean up canvas
      canvas.width = 0;
      canvas.height = 0;
      onCaptureLabel(base64Image);
    }
  };

  if (status === "denied" || status === "unsupported") {
    return (
      <div className="flex aspect-[4/3] w-full flex-col items-center justify-center gap-3 rounded-2xl border border-border bg-surface text-center">
        <CameraOff
          className="text-fg-subtle opacity-50"
          size={32}
          aria-hidden
        />
        <p className="text-sm font-semibold">
          {status === "unsupported" ? "No camera available" : "Camera blocked"}
        </p>
        <p className="max-w-[30ch] text-xs text-fg-subtle">
          {status === "unsupported"
            ? "This browser can't open a camera. Type the barcode below instead."
            : "Allow camera access in your browser, or type the barcode below instead."}
        </p>
      </div>
    );
  }

  return (
    <div className="relative aspect-[4/3] w-full overflow-hidden rounded-2xl border border-border-strong bg-black">
      <div id="scanner-region" ref={containerRef} className="size-full" />

      {status === "starting" ? (
        <div className="absolute inset-0 grid place-items-center bg-bg/80 text-fg-subtle z-10">
          <span className="flex items-center gap-2 text-sm">
            <Loader2 size={16} className="animate-spin" aria-hidden />
            Waking the camera…
          </span>
        </div>
      ) : isCapturing ? (
        <div className="absolute inset-0 grid place-items-center bg-black/70 text-white z-10 backdrop-blur-sm">
          <div className="flex flex-col items-center gap-4 text-center">
            <Loader2
              size={32}
              className="animate-spin text-brand"
              aria-hidden
            />
            <span className="text-sm font-medium tracking-wide">
              Extracting ingredients with AWS Bedrock...
            </span>
          </div>
        </div>
      ) : (
        <>
          <div className="absolute top-0 inset-x-0 bg-gradient-to-b from-black/60 to-transparent p-4 text-center z-10">
            <p className="text-xs font-medium text-white/90 drop-shadow-md">
              Align Barcode or tap button below to photograph Ingredients
            </p>
          </div>
          <div className="pointer-events-none absolute inset-0 grid place-items-center z-0">
            <div className="relative h-[38%] w-[72%]">
              {/* Corner brackets — a viewfinder without hiding the frame. */}
              {(
                [
                  "left-0 top-0 border-l-2 border-t-2 rounded-tl-lg",
                  "right-0 top-0 border-r-2 border-t-2 rounded-tr-lg",
                  "left-0 bottom-0 border-l-2 border-b-2 rounded-bl-lg",
                  "right-0 bottom-0 border-r-2 border-b-2 rounded-br-lg",
                ] as const
              ).map((corner) => (
                <span
                  key={corner}
                  className={`absolute size-6 border-brand ${corner}`}
                />
              ))}
              <span className="animate-sweep absolute inset-x-2 top-1/2 h-0.5 rounded-full bg-brand shadow-[0_0_12px_2px_var(--brand)]" />
            </div>
          </div>
          {onCaptureLabel && (
            <div className="absolute bottom-4 inset-x-0 flex justify-center z-10">
              <button
                onClick={handleCapture}
                className="flex size-14 items-center justify-center rounded-full bg-white/20 backdrop-blur-md border-2 border-white/60 hover:bg-white/30 transition-all active:scale-95 shadow-lg"
                aria-label="Capture Ingredients"
              >
                <div className="size-10 rounded-full bg-white shadow-sm" />
              </button>
            </div>
          )}
        </>
      )}
    </div>
  );
}
