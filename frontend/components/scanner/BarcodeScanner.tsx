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
/** Tear a scanner down without letting its own errors escape. */
function wipe(scanner: Html5Qrcode | null) {
  if (!scanner) return;
  try {
    scanner.clear();
  } catch {
    // Already unmounted — nothing to clean up.
  }
}

export function BarcodeScanner({ onDetected }: { onDetected: (barcode: string) => void }) {
  const [status, setStatus] = useState<Status>("starting");
  const instance = useRef<Html5Qrcode | null>(null);
  const done = useRef(false);

  useEffect(() => {
    let cancelled = false;

    (async () => {
      if (typeof navigator === "undefined" || !navigator.mediaDevices?.getUserMedia) {
        setStatus("unsupported");
        return;
      }

      let scanner: Html5Qrcode | null = null;

      try {
        const { Html5Qrcode, Html5QrcodeSupportedFormats } = await import("html5-qrcode");
        if (cancelled) return;

        scanner = new Html5Qrcode("scanner-region", {
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

        await scanner.start(
          { facingMode: "environment" },
          // A wide, short box matches the shape of a barcode.
          { fps: 12, qrbox: { width: 260, height: 150 }, aspectRatio: 1.2 },
          (decoded) => {
            if (done.current) return;
            done.current = true;
            onDetected(decoded);
          },
          () => {
            // Per-frame decode misses are constant and expected — ignore them.
          },
        );

        // Tracked only once it is genuinely running: stop() throws on a
        // scanner that never started, so the cleanup path must never see one.
        instance.current = scanner;
        if (!cancelled) setStatus("scanning");
      } catch {
        wipe(scanner);
        if (!cancelled) setStatus("denied");
      }
    })();

    return () => {
      cancelled = true;
      const scanner = instance.current;
      instance.current = null;
      if (!scanner) return;
      // stop() rejects *and* can throw synchronously; both end in the same place.
      try {
        Promise.resolve(scanner.stop()).then(
          () => wipe(scanner),
          () => wipe(scanner),
        );
      } catch {
        wipe(scanner);
      }
    };
  }, [onDetected]);

  if (status === "denied" || status === "unsupported") {
    return (
      <div className="flex flex-col items-center gap-2 rounded-2xl border border-dashed border-border-strong px-5 py-8 text-center">
        <CameraOff size={22} className="text-fg-subtle" aria-hidden />
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
      <div id="scanner-region" className="size-full" />

      {status === "starting" ? (
        <div className="absolute inset-0 grid place-items-center bg-bg/80 text-fg-subtle">
          <span className="flex items-center gap-2 text-sm">
            <Loader2 size={16} className="animate-spin" aria-hidden />
            Waking the camera…
          </span>
        </div>
      ) : (
        <div className="pointer-events-none absolute inset-0 grid place-items-center">
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
              <span key={corner} className={`absolute size-6 border-brand ${corner}`} />
            ))}
            <span className="animate-sweep absolute inset-x-2 top-1/2 h-0.5 rounded-full bg-brand shadow-[0_0_12px_2px_var(--brand)]" />
          </div>
        </div>
      )}
    </div>
  );
}
