// Owner: Keshav
// Packaged Commodity Label Scanner UI styled in the luxury minimalist porcelain & stark-white design system.
// Conforms strictly to docs/API_CONTRACT.md and Legal Metrology (Packaged Commodities) Rules, 2011 (LMPC-2011-v1.1)

import React, { useState, useRef, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { scanLabel } from "../api/client";

export default function Upload() {
  const [file, setFile] = useState(null);
  const [previewUrl, setPreviewUrl] = useState("/kohaku_bottle.jpg");
  const [productTitle, setProductTitle] = useState("Organic Kohaku Water 500mL (Sample)");
  const [calibrationMethod, setCalibrationMethod] = useState("aruco");
  const [knownObjectSizeMm, setKnownObjectSizeMm] = useState(24.0);
  const [productCategory, setProductCategory] = useState("standard_retail");
  const [loading, setLoading] = useState(false);
  const [scanStage, setScanStage] = useState(0);
  const [error, setError] = useState(null);
  const [isDragOver, setIsDragOver] = useState(false);

  // Camera capture states
  const [isCameraOpen, setIsCameraOpen] = useState(false);
  const [cameraStream, setCameraStream] = useState(null);
  const [cameraError, setCameraError] = useState(null);
  const [facingMode, setFacingMode] = useState("environment"); // back camera by default

  const fileInputRef = useRef(null);
  const videoRef = useRef(null);
  const navigate = useNavigate();

  const scanStages = [
    "Locking Principal Display Panel (YOLOv8 Mesh)...",
    "Running OCR Token Extraction & Spatial Projection...",
    "Fuzzy Matching Mandatory Declarations (RapidFuzz)...",
    "Calibrating Scale & Measuring Character Height...",
    "Validating Against Legal Metrology Rules, 2011...",
  ];

  const handleFileSelect = (selectedFile) => {
    if (!selectedFile) return;
    setFile(selectedFile);
    setError(null);
    const cleanName = selectedFile.name.replace(/\.[^/.]+$/, "").replace(/[-_]/g, " ");
    setProductTitle(cleanName.charAt(0).toUpperCase() + cleanName.slice(1));
    const url = URL.createObjectURL(selectedFile);
    setPreviewUrl(url);
  };

  const handleResetToDefault = (e) => {
    e.stopPropagation();
    setFile(null);
    setPreviewUrl("/kohaku_bottle.jpg");
    setProductTitle("Organic Kohaku Water 500mL (Sample)");
    setError(null);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragOver(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileSelect(e.dataTransfer.files[0]);
    }
  };

  // Open Camera Stream
  const handleStartCamera = async () => {
    setCameraError(null);
    setIsCameraOpen(true);
    try {
      if (cameraStream) {
        cameraStream.getTracks().forEach((track) => track.stop());
      }
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode, width: { ideal: 1280 }, height: { ideal: 720 } },
      });
      setCameraStream(stream);
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
      }
    } catch (err) {
      console.error("Camera access error:", err);
      setCameraError("Unable to access camera. Check device permissions or upload an image file.");
    }
  };

  // Close Camera Stream
  const handleStopCamera = () => {
    if (cameraStream) {
      cameraStream.getTracks().forEach((track) => track.stop());
      setCameraStream(null);
    }
    setIsCameraOpen(false);
    setCameraError(null);
  };

  // Ensure video element receives stream when ready
  useEffect(() => {
    if (isCameraOpen && videoRef.current && cameraStream) {
      videoRef.current.srcObject = cameraStream;
    }
    return () => {
      if (cameraStream) {
        cameraStream.getTracks().forEach((track) => track.stop());
      }
    };
  }, [isCameraOpen, cameraStream]);

  // Capture Photo from Camera Viewfinder
  const handleCapturePhoto = () => {
    if (!videoRef.current) return;
    const video = videoRef.current;
    const canvas = document.createElement("canvas");
    canvas.width = video.videoWidth || 1280;
    canvas.height = video.videoHeight || 720;
    const ctx = canvas.getContext("2d");
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

    canvas.toBlob(
      (blob) => {
        if (!blob) return;
        const capturedFile = new File([blob], `label_capture_${Date.now()}.jpg`, {
          type: "image/jpeg",
        });
        handleFileSelect(capturedFile);
        handleStopCamera();
      },
      "image/jpeg",
      0.92
    );
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    setLoading(true);
    setError(null);
    setScanStage(0);

    const interval = setInterval(() => {
      setScanStage((prev) => (prev < scanStages.length - 1 ? prev + 1 : prev));
    }, 1200);

    try {
      const sizeParam = Number(knownObjectSizeMm) || (calibrationMethod === "aruco" ? 24.0 : 25.0);
      let targetFile = file;

      // If user hasn't uploaded a custom photo, fetch default sample as real Blob
      if (!targetFile) {
        try {
          const res = await fetch("/kohaku_bottle.jpg");
          const blob = await res.blob();
          targetFile = new File([blob], "kohaku_bottle.jpg", { type: "image/jpeg" });
        } catch {
          targetFile = new File(["sample_label"], "label.jpg", { type: "image/jpeg" });
        }
      }

      const scanResult = await scanLabel(
        targetFile,
        calibrationMethod,
        sizeParam,
        productCategory
      );
      clearInterval(interval);
      navigate(`/results/${scanResult.scan_id}`, { state: { scanResult, previewUrl } });
    } catch (err) {
      clearInterval(interval);
      setError(err.message || "Scan processing encountered an error.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-6xl mx-auto space-y-8">
      {/* HEADER SECTION — Luxury Minimalist Typography */}
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-4 pb-5 border-b border-[#E5E7EB]">
        <div>
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-white border border-[#E5E7EB] shadow-xs mb-2.5">
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
            <span className="text-[10px] font-mono tracking-widest uppercase text-neutral-600 font-semibold">
              Spatial Computer Vision • Rule 6 & 7 Engine
            </span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-neutral-900">
            Packaged Commodity Label Scanner
          </h1>
          <p className="mt-1 text-xs sm:text-sm text-neutral-500 max-w-2xl leading-relaxed">
            Automated statutory compliance audit against the{" "}
            <strong className="text-neutral-800">Legal Metrology (Packaged Commodities) Rules, 2011</strong> with
            real-time laser scanning analysis.
          </p>
        </div>

        <div className="flex items-center gap-2 text-xs font-mono text-neutral-500 bg-white px-3.5 py-2 rounded-xl border border-[#E5E7EB] shadow-xs shrink-0">
          <span>Framework:</span>
          <span className="text-neutral-900 font-bold">LMPC-2011-v1.1</span>
        </div>
      </div>

      {/* MAIN TWO-COLUMN WORKSPACE: PACKAGING DISPLAY & CONTROLS */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
        {/* LEFT/CENTER: PRODUCT DISPLAY WITH LASER SWEEP */}
        <div className="lg:col-span-7 flex flex-col items-center justify-center bg-white rounded-2xl border border-[#E5E7EB] p-8 sm:p-10 shadow-sm relative min-h-[520px]">
          <div className="relative w-full max-w-sm aspect-[4/5] flex items-center justify-center">
            {/* Product Box Container */}
            <div className="relative z-10 w-full h-full rounded-2xl bg-neutral-900 border border-neutral-300 p-4 shadow-2xl flex flex-col items-center justify-between overflow-hidden group">
              {/* Vertical Laser Scan Beam */}
              <div className="absolute left-0 right-0 h-[2px] bg-white shadow-[0_0_12px_rgba(255,255,255,1),0_0_24px_rgba(255,255,255,0.8)] pointer-events-none z-20 animate-laser-sweep" />

              {/* Top HUD Telemetry Bar */}
              <div className="w-full flex items-center justify-between text-[10px] font-mono text-neutral-300 border-b border-neutral-700/60 pb-1.5 z-10">
                <span className="text-emerald-400 font-bold flex items-center gap-1.5">
                  <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping" />
                  ANALYSIS ACTIVE
                </span>
                <span className="text-neutral-400">PDP: LOCK READY</span>
              </div>

              {/* Product Image Viewport */}
              <div className="relative flex-1 w-full flex items-center justify-center overflow-hidden my-2">
                {previewUrl ? (
                  <img
                    src={previewUrl}
                    alt={productTitle}
                    className="max-h-[300px] w-auto object-contain drop-shadow-2xl group-hover:scale-105 transition-transform duration-500"
                  />
                ) : (
                  <div className="text-center space-y-2 py-16">
                    <div className="w-16 h-16 rounded-2xl bg-neutral-800 border border-neutral-700 flex items-center justify-center text-3xl mx-auto shadow-inner">
                      📦
                    </div>
                    <p className="text-xs font-semibold text-white">No Image Selected</p>
                    <p className="text-[10px] text-neutral-400 font-mono">Upload a packaging photo</p>
                  </div>
                )}
              </div>

              {/* Bottom Label Bar */}
              <div className="w-full bg-neutral-850 rounded-xl p-2.5 border border-neutral-700/60 text-center z-10">
                <div className="text-[11px] font-bold text-white truncate">{productTitle}</div>
                <div className="text-[9px] font-mono text-neutral-400 flex items-center justify-center gap-2 mt-0.5">
                  <span>CALIBRATION: {calibrationMethod.toUpperCase()}</span>
                  <span>•</span>
                  <span>CAT: {productCategory.toUpperCase()}</span>
                </div>
              </div>
            </div>
          </div>

          {/* Quick toggle link below canvas */}
          {file && (
            <div className="mt-4 text-xs font-mono text-neutral-500">
              Custom photo uploaded •{" "}
              <button
                onClick={handleResetToDefault}
                className="text-black underline font-semibold hover:text-neutral-700"
              >
                Reset to Sample Bottle
              </button>
            </div>
          )}
        </div>

        {/* RIGHT: CONTROLS, CALIBRATION & RUN SCAN BUTTON */}
        <div className="lg:col-span-5 space-y-5">
          {/* Action Dual-Buttons: Upload File or Camera */}
          <div className="grid grid-cols-2 gap-3">
            <button
              type="button"
              onClick={() => fileInputRef.current?.click()}
              className="p-4 rounded-xl border border-[#D1D5DB] hover:border-black bg-white hover:bg-neutral-50 transition-all text-center flex flex-col items-center justify-center space-y-1.5 shadow-xs"
            >
              <div className="w-8 h-8 rounded-full bg-neutral-100 flex items-center justify-center text-base">
                📁
              </div>
              <div className="text-xs font-bold text-neutral-900 uppercase tracking-wider">Choose File</div>
              <div className="text-[10px] text-neutral-500">JPEG, PNG, WEBP</div>
            </button>

            <button
              type="button"
              onClick={handleStartCamera}
              className="p-4 rounded-xl border border-[#D1D5DB] hover:border-black bg-white hover:bg-neutral-50 transition-all text-center flex flex-col items-center justify-center space-y-1.5 shadow-xs"
            >
              <div className="w-8 h-8 rounded-full bg-neutral-100 flex items-center justify-center text-base">
                📸
              </div>
              <div className="text-xs font-bold text-neutral-900 uppercase tracking-wider">Use Camera</div>
              <div className="text-[10px] text-neutral-500">Live Device Capture</div>
            </button>
          </div>

          {/* Custom Upload Dropzone */}
          <div
            onDragOver={(e) => {
              e.preventDefault();
              setIsDragOver(true);
            }}
            onDragLeave={() => setIsDragOver(false)}
            onDrop={handleDrop}
            onClick={() => fileInputRef.current?.click()}
            className={`p-6 rounded-2xl border-2 border-dashed transition-all cursor-pointer text-center bg-white ${
              isDragOver
                ? "border-black bg-neutral-50 shadow-sm"
                : "border-[#D1D5DB] hover:border-black hover:bg-neutral-50/50"
            }`}
          >
            <input
              ref={fileInputRef}
              type="file"
              accept="image/jpeg,image/png,image/webp"
              onChange={(e) => handleFileSelect(e.target.files?.[0])}
              className="hidden"
            />
            <div className="text-xs font-bold text-neutral-900 uppercase tracking-wider">
              {file ? file.name : "Drag & Drop Image Here"}
            </div>
            <p className="text-[11px] text-neutral-500 mt-1 max-w-xs mx-auto">
              Front-facing commodity label photo with clear declarations & Principal Display Panel
            </p>
          </div>

          {/* Statutory Category Exceptions Selector */}
          <div className="bg-white rounded-2xl border border-[#E5E7EB] p-4 shadow-sm space-y-2">
            <div className="flex items-center justify-between border-b border-[#F0F2F5] pb-2">
              <span className="text-xs font-bold uppercase tracking-widest text-neutral-900">
                Commodity Category
              </span>
              <span className="text-[10px] font-mono text-neutral-400">Rule Exceptions</span>
            </div>
            <select
              value={productCategory}
              onChange={(e) => setProductCategory(e.target.value)}
              className="w-full px-3 py-2 text-xs rounded-lg bg-neutral-50 border border-[#D1D5DB] text-neutral-900 font-semibold focus:outline-none focus:border-black"
            >
              <option value="standard_retail">Standard Retail Commodity (Full Rule 6 & 7)</option>
              <option value="food_expiry">Food Item (Mandates PKD Date & Best-Before/Expiry)</option>
              <option value="medical_device">Medical Device (Standard Exemptions Apply)</option>
              <option value="bulk_exempt">Bulk Package (&gt; 25kg/25L Exemption Audit)</option>
            </select>
          </div>

          {/* Physical Calibration Configuration */}
          <div className="bg-white rounded-2xl border border-[#E5E7EB] p-4 shadow-sm space-y-3">
            <div className="flex items-center justify-between border-b border-[#F0F2F5] pb-2">
              <span className="text-xs font-bold uppercase tracking-widest text-neutral-900">
                Visual Scale Calibration
              </span>
              <span className="text-[10px] font-mono text-neutral-400">Rule 7 Table-I</span>
            </div>

            <div className="grid grid-cols-2 gap-2.5">
              <button
                type="button"
                onClick={() => setCalibrationMethod("aruco")}
                className={`p-3 rounded-xl border text-left transition-all ${
                  calibrationMethod === "aruco"
                    ? "bg-neutral-900 text-white border-black shadow-sm"
                    : "bg-white text-neutral-700 border-[#E5E7EB] hover:bg-neutral-50"
                }`}
              >
                <div className="text-xs font-bold">ArUco Marker</div>
                <div
                  className={`text-[10px] mt-0.5 ${
                    calibrationMethod === "aruco" ? "text-neutral-300" : "text-neutral-500"
                  }`}
                >
                  Primary reference fiducial
                </div>
              </button>

              <button
                type="button"
                onClick={() => setCalibrationMethod("known_object")}
                className={`p-3 rounded-xl border text-left transition-all ${
                  calibrationMethod === "known_object"
                    ? "bg-neutral-900 text-white border-black shadow-sm"
                    : "bg-white text-neutral-700 border-[#E5E7EB] hover:bg-neutral-50"
                }`}
              >
                <div className="text-xs font-bold">Known Object</div>
                <div
                  className={`text-[10px] mt-0.5 ${
                    calibrationMethod === "known_object" ? "text-neutral-300" : "text-neutral-500"
                  }`}
                >
                  Reference scale object
                </div>
              </button>
            </div>

            {/* Input for Marker or Known Object Size */}
            <div className="pt-1">
              <label className="block text-[11px] font-semibold text-neutral-700 mb-1">
                {calibrationMethod === "aruco"
                  ? "ArUco Marker Outer Black Square (mm):"
                  : "Reference Object Dimension (mm):"}
              </label>
              <input
                type="number"
                step="0.1"
                value={knownObjectSizeMm}
                onChange={(e) => setKnownObjectSizeMm(e.target.value)}
                className="w-full px-3 py-2 text-xs rounded-lg bg-neutral-50 border border-[#D1D5DB] text-neutral-900 focus:outline-none focus:border-black font-mono"
                placeholder={calibrationMethod === "aruco" ? "e.g. 24.0 or 30.0" : "e.g. 25.0"}
              />
              <span className="text-[10px] text-neutral-400 mt-0.5 block">
                {calibrationMethod === "aruco"
                  ? "Default is 24.0 mm for standard cutout test markers"
                  : "Physical dimension of known coin or reference token"}
              </span>
            </div>
          </div>

          {/* Error Message */}
          {error && (
            <div className="p-3.5 rounded-xl bg-rose-50 border border-rose-200 text-rose-700 text-xs font-medium">
              ⚠️ {error}
            </div>
          )}

          {/* SUBMIT ACTION BUTTON */}
          <button
            type="button"
            disabled={loading}
            onClick={handleSubmit}
            className="w-full py-4 rounded-xl bg-black text-white text-xs font-bold uppercase tracking-widest hover:bg-neutral-900 active:scale-[0.99] transition-all shadow-md disabled:opacity-60 flex items-center justify-center space-x-2"
          >
            {loading ? (
              <>
                <div className="w-4 h-4 border-2 border-white/40 border-t-white rounded-full animate-spin" />
                <span>{scanStages[scanStage]}</span>
              </>
            ) : (
              <span>Analyze Packaged Commodity →</span>
            )}
          </button>
        </div>
      </div>

      {/* LIVE CAMERA VIEWFINDER MODAL */}
      {isCameraOpen && (
        <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-md flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-lg w-full overflow-hidden shadow-2xl border border-neutral-200 flex flex-col">
            <div className="p-4 border-b border-[#F0F2F5] flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <span className="w-2.5 h-2.5 rounded-full bg-rose-500 animate-ping" />
                <h3 className="text-xs font-bold uppercase tracking-wider text-neutral-900">
                  Live Viewfinder • Package Capture
                </h3>
              </div>
              <button
                onClick={handleStopCamera}
                className="text-neutral-400 hover:text-black text-sm font-bold"
              >
                ✕
              </button>
            </div>

            <div className="relative bg-black aspect-[4/3] flex items-center justify-center overflow-hidden">
              <video
                ref={videoRef}
                autoPlay
                playsInline
                muted
                className="w-full h-full object-cover"
              />

              {/* Viewfinder Target Guidelines */}
              <div className="absolute inset-8 border-2 border-white/60 border-dashed rounded-xl pointer-events-none flex items-center justify-center">
                <span className="text-[10px] font-mono text-white/80 bg-black/60 px-2 py-0.5 rounded">
                  Align Package PDP Inside Frame
                </span>
              </div>

              {cameraError && (
                <div className="absolute inset-0 bg-black/90 p-6 flex flex-col items-center justify-center text-center text-xs text-rose-300 space-y-2">
                  <span className="text-2xl">⚠️</span>
                  <p>{cameraError}</p>
                </div>
              )}
            </div>

            <div className="p-4 bg-neutral-50 border-t border-[#E5E7EB] flex items-center justify-between">
              <button
                type="button"
                onClick={() => {
                  setFacingMode((prev) => (prev === "environment" ? "user" : "environment"));
                  handleStartCamera();
                }}
                className="px-3 py-2 rounded-lg text-xs font-semibold bg-white border border-[#D1D5DB] text-neutral-700 hover:bg-neutral-100"
              >
                🔄 Flip Camera
              </button>

              <button
                type="button"
                onClick={handleCapturePhoto}
                disabled={Boolean(cameraError)}
                className="px-6 py-2.5 rounded-xl text-xs font-bold uppercase tracking-widest bg-black text-white hover:bg-neutral-900 shadow transition-all active:scale-95 disabled:opacity-50"
              >
                Snap Photo 📸
              </button>

              <button
                type="button"
                onClick={handleStopCamera}
                className="px-3 py-2 rounded-lg text-xs font-medium text-neutral-500 hover:text-black"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

