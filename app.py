import React, { useState, useRef, useEffect } from 'react';
import { 
  Camera, 
  Image as ImageIcon, 
  History, 
  Mic, 
  Zap, 
  ZapOff, 
  RotateCw, 
  Crop, 
  Search, 
  ArrowLeft, 
  Leaf, 
  Droplets, 
  Sun, 
  Wind,
  ExternalLink,
  Trash2,
  CheckCircle,
  AlertCircle,
  Loader2,
  X,
  RotateCcw,
  Minus,
  Plus,
  Maximize2
} from 'lucide-react';

// --- Configuration ---
const API_BASE_URL = "https://plantque.onrender.com"; 

const App = () => {
  // --- States ---
  const [view, setView] = useState('home'); 
  const [capturedImage, setCapturedImage] = useState(null);
  const [compressedImage, setCompressedImage] = useState(null);
  const [isFlashOn, setIsFlashOn] = useState(false);
  const [isScanning, setIsScanning] = useState(false);
  const [searchHistory, setSearchHistory] = useState([]);
  const [voiceQuery, setVoiceQuery] = useState('');
  const [isListening, setIsListening] = useState(false);
  const [apiResult, setApiResult] = useState(null);
  const [errorMsg, setErrorMsg] = useState(null);
  const [previewRotation, setPreviewRotation] = useState(0); 

  // --- Advanced Camera States (Zoom Logic) ---
  const [zoomLevel, setZoomLevel] = useState(1);
  const [maxZoom, setMaxZoom] = useState(1);
  const [minZoom, setMinZoom] = useState(1);
  const [hasZoomSupport, setHasZoomSupport] = useState(false);

  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const userId = useRef("user_" + Math.random().toString(36).substr(2, 9)).current;

  // Load History on Mount
  useEffect(() => {
    const savedHistory = localStorage.getItem('plantque_history');
    if (savedHistory) setSearchHistory(JSON.parse(savedHistory));
  }, []);

  // --- 1. Strong Compression & Rotation Algorithm ---
  const compressImage = (imageDataUrl, rotation = 0) => {
    return new Promise((resolve) => {
      const img = new Image();
      img.src = imageDataUrl;
      img.onload = () => {
        const canvas = document.createElement('canvas');
        const MAX_WIDTH = 1000; // Increased resolution for better identification
        const MAX_HEIGHT = 1000;
        let width = img.width;
        let height = img.height;

        if (width > height) {
          if (width > MAX_WIDTH) {
            height *= MAX_WIDTH / width;
            width = MAX_WIDTH;
          }
        } else {
          if (height > MAX_HEIGHT) {
            width *= MAX_HEIGHT / height;
            height = MAX_HEIGHT;
          }
        }

        if (rotation % 180 !== 0) {
          canvas.width = height;
          canvas.height = width;
        } else {
          canvas.width = width;
          canvas.height = height;
        }

        const ctx = canvas.getContext('2d');
        ctx.translate(canvas.width / 2, canvas.height / 2);
        ctx.rotate((rotation * Math.PI) / 180);
        ctx.drawImage(img, -width / 2, -height / 2, width, height);
        
        const compressedData = canvas.toDataURL('image/jpeg', 0.85); 
        resolve(compressedData);
      };
    });
  };

  // --- 2. Advanced Camera Module with Zoom Controls ---
  const startCamera = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ 
        video: { 
          facingMode: 'environment',
          width: { ideal: 1920 },
          height: { ideal: 1080 }
        } 
      });
      
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        
        // Check for hardware zoom capabilities
        const track = stream.getVideoTracks()[0];
        const capabilities = track.getCapabilities();
        
        if (capabilities.zoom) {
          setHasZoomSupport(true);
          setMinZoom(capabilities.zoom.min || 1);
          setMaxZoom(capabilities.zoom.max || 10);
          setZoomLevel(capabilities.zoom.min || 1);
        }
      }
    } catch (err) {
      setErrorMsg("Camera access nahi mila. Settings check karein.");
    }
  };

  // Zoom Handler Algorithm
  const handleZoomChange = (value) => {
    const newZoom = parseFloat(value);
    setZoomLevel(newZoom);
    const track = videoRef.current?.srcObject?.getVideoTracks()[0];
    if (track && hasZoomSupport) {
      track.applyConstraints({ advanced: [{ zoom: newZoom }] });
    }
  };

  const capturePhoto = async () => {
    const canvas = canvasRef.current;
    const video = videoRef.current;
    if (canvas && video) {
      canvas.width = video.videoWidth;
      canvas.height = video.videoHeight;
      const ctx = canvas.getContext('2d');
      ctx.drawImage(video, 0, 0);
      const dataUrl = canvas.toDataURL('image/png');
      
      setCapturedImage(dataUrl);
      const compressed = await compressImage(dataUrl, 0);
      setCompressedImage(compressed);
      
      const stream = video.srcObject;
      if (stream) stream.getTracks().forEach(track => track.stop());
      setView('preview');
      setPreviewRotation(0); 
    }
  };

  // --- 3. Advanced NLP & Keyword Filter ---
  const isQueryPlantRelated = (text) => {
    const plantKeywords = ['plant', 'ped', 'phool', 'flower', 'leaf', 'tree', 'patti', 'care', 'health', 'mitti', 'soil', 'water', 'khaad', 'fertilizer', 'poda', 'kida', 'rog', 'sehat', 'dhup', 'gamla'];
    return plantKeywords.some(keyword => text.toLowerCase().includes(keyword));
  };

  // --- 4. Secure Backend Communication ---
  const handleIdentify = async () => {
    setIsScanning(true);
    setErrorMsg(null);
    try {
      const finalImage = await compressImage(capturedImage, previewRotation);
      const cleanBase64 = finalImage.split(',')[1];

      const response = await fetch(`${API_BASE_URL}/api/identify`, {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          'X-Client-Platform': 'Web-Premium'
        },
        body: JSON.stringify({
          imageBase64: cleanBase64,
          userId: userId
        })
      });

      const data = await response.json();

      if (!response.ok) throw new Error(data.detail || "Server connection error. Kripya 1 minute baad koshish karein.");
      if (data.error) throw new Error(data.error);

      setApiResult(data);
      
      const newHistory = [{
        id: Date.now(),
        name: data.identity.name,
        date: new Date().toLocaleDateString(),
        img: finalImage,
        fullData: data
      }, ...searchHistory];
      setSearchHistory(newHistory);
      localStorage.setItem('plantque_history', JSON.stringify(newHistory));
      
      setView('result');
    } catch (err) {
      setErrorMsg(err.message);
    } finally {
      setIsScanning(false);
    }
  };

  // --- 5. Voice Interaction Logic ---
  const startVoiceSearch = () => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      setErrorMsg("Aapka device voice recognition support nahi karta.");
      return;
    }
    
    const recognition = new SpeechRecognition();
    recognition.lang = 'hi-IN';
    recognition.onstart = () => setIsListening(true);
    recognition.onend = () => setIsListening(false);
    recognition.onresult = async (event) => {
      const transcript = event.results[0][0].transcript;
      setVoiceQuery(transcript);
      
      if (!isQueryPlantRelated(transcript)) {
        setVoiceQuery("Main sirf paudhon ke baare mein jaanta hoon!");
        return;
      }

      try {
        const res = await fetch(`${API_BASE_URL}/api/voice-query`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ query: transcript, lang: 'hi' })
        });
        const data = await res.json();
        setVoiceQuery(data.answer);
      } catch (e) {
        setErrorMsg("Voice query fail ho gayi.");
      }
    };
    recognition.start();
  };

  // UI Components
  const Header = () => (
    <div className="flex items-center justify-between p-5 bg-emerald-950 text-white sticky top-0 z-50 shadow-xl border-b border-emerald-800">
      <div className="flex items-center gap-3">
        <div className="bg-emerald-500 p-2 rounded-xl shadow-lg shadow-emerald-500/20">
            <Leaf size={24} className="text-white" />
        </div>
        <div>
            <h1 className="text-xl font-black tracking-tighter uppercase italic">PlantQue</h1>
            <p className="text-[10px] text-emerald-400 font-bold tracking-widest leading-none">AI BIOTECH ENGINE</p>
        </div>
      </div>
      <button onClick={() => setView('history')} className="hover:bg-white/10 p-2 rounded-full transition-all">
        <History size={24} />
      </button>
    </div>
  );

  return (
    <div className="min-h-screen bg-[#FDFDFD] font-sans text-slate-900 select-none overflow-x-hidden">
      <style>
        {`
          @keyframes scanLine { 0% { top: 0; } 100% { top: 100%; } }
          .animate-scan-line { animation: scanLine 2.5s ease-in-out infinite; }
          .custom-slider { -webkit-appearance: none; height: 6px; background: rgba(255,255,255,0.2); border-radius: 5px; outline: none; }
          .custom-slider::-webkit-slider-thumb { -webkit-appearance: none; width: 24px; height: 24px; background: white; border-radius: 50%; cursor: pointer; border: 4px solid #10b981; }
        `}
      </style>

      {errorMsg && (
        <div className="fixed inset-0 z-[300] flex items-center justify-center p-6 bg-emerald-950/40 backdrop-blur-xl">
          <div className="bg-white rounded-[40px] p-8 w-full max-w-sm shadow-2xl border border-red-50">
            <div className="text-red-500 mb-4 flex justify-center bg-red-50 w-16 h-16 rounded-full items-center mx-auto">
                <AlertCircle size={32} />
            </div>
            <h3 className="text-center font-black text-2xl mb-2 text-slate-900">Oops! Error</h3>
            <p className="text-center text-slate-500 mb-8 text-sm leading-relaxed">{errorMsg}</p>
            <button onClick={() => setErrorMsg(null)} className="w-full bg-emerald-600 text-white py-5 rounded-[24px] font-black shadow-xl shadow-emerald-200 active:scale-95 transition-all">GOT IT</button>
          </div>
        </div>
      )}

      {/* --- 1. HOME VIEW --- */}
      {view === 'home' && (
        <div className="max-w-4xl mx-auto">
          <Header />
          <div className="p-6">
            <div className="bg-emerald-900 rounded-[40px] p-10 shadow-2xl shadow-emerald-900/20 mb-8 text-center relative overflow-hidden">
              <div className="absolute top-0 right-0 w-32 h-32 bg-emerald-500/10 rounded-full -mr-16 -mt-16 blur-3xl"></div>
              <div className="relative z-10">
                <h2 className="text-3xl font-black text-white mb-2 leading-tight">Advanced Plant Intelligence</h2>
                <p className="text-emerald-300 mb-8 text-sm font-medium">Identify plants & diagnose health in real-time.</p>
                
                <div className="flex flex-col gap-4">
                  <button 
                    onClick={() => { setView('camera'); startCamera(); }}
                    className="w-full bg-white text-emerald-900 font-black py-5 rounded-[24px] flex items-center justify-center gap-3 transition-all hover:shadow-2xl active:scale-95 shadow-lg"
                  >
                    <Camera size={26} strokeWidth={3} /> START CAMERA
                  </button>
                  <label className="w-full bg-emerald-800 border-2 border-emerald-700/50 text-white font-bold py-5 rounded-[24px] flex items-center justify-center gap-3 cursor-pointer transition-all active:scale-95">
                    <ImageIcon size={22} /> OPEN GALLERY
                    <input type="file" className="hidden" accept="image/*" onChange={async (e) => {
                      const file = e.target.files[0];
                      if(file) {
                        const reader = new FileReader();
                        reader.onloadend = async () => {
                          setCapturedImage(reader.result);
                          setCompressedImage(await compressImage(reader.result, 0));
                          setView('preview');
                          setPreviewRotation(0);
                        };
                        reader.readAsDataURL(file);
                      }
                    }} />
                  </label>
                </div>
              </div>
            </div>

            <div className="relative mb-10 group">
              <input 
                type="text" 
                placeholder={isListening ? "Listening closely..." : "Ask: Water schedule for snake plant?"}
                value={voiceQuery}
                readOnly
                className="w-full p-6 pr-20 rounded-[30px] border-2 border-slate-100 focus:border-emerald-500 outline-none shadow-sm bg-white font-bold text-slate-700 transition-all"
              />
              <button onClick={startVoiceSearch} className={`absolute right-3 top-3 p-4 rounded-[22px] transition-all ${isListening ? 'bg-red-500 animate-pulse' : 'bg-emerald-600 hover:scale-105 shadow-lg shadow-emerald-200'} text-white`}>
                <Mic size={24} />
              </button>
            </div>

            <div className="flex justify-between items-end mb-5 px-2">
                <h3 className="text-xl font-black text-slate-900 uppercase tracking-tighter">Recent Analysis</h3>
                <button onClick={() => setView('history')} className="text-xs font-black text-emerald-600 underline">SEE ALL</button>
            </div>
            
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {searchHistory.slice(0, 4).map((item) => (
                <div key={item.id} onClick={() => { setApiResult(item.fullData); setCompressedImage(item.img); setView('result'); }} className="bg-white rounded-[30px] overflow-hidden shadow-sm border border-slate-100 p-2 active:scale-95 transition-all">
                  <div className="relative h-28 rounded-[22px] overflow-hidden mb-3">
                    <img src={item.img} alt="" className="w-full h-full object-cover" />
                  </div>
                  <div className="px-2 pb-2">
                    <p className="font-black text-[12px] truncate text-slate-800">{item.name}</p>
                    <p className="text-[10px] font-bold text-slate-400">{item.date}</p>
                  </div>
                </div>
              ))}
              {searchHistory.length === 0 && (
                <div className="col-span-full py-16 text-center text-slate-300 font-black italic tracking-widest text-sm bg-slate-50 rounded-[40px] border-2 border-dashed border-slate-100">NO RECENT ACTIVITY</div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* --- 2. ADVANCED CAMERA VIEW (ZOOM IMPLEMENTED) --- */}
      {view === 'camera' && (
        <div className="fixed inset-0 bg-black z-[100] flex flex-col">
          <div className="absolute top-8 left-6 right-6 flex justify-between items-center z-20">
            <button onClick={() => setView('home')} className="p-4 rounded-3xl bg-black/40 backdrop-blur-xl text-white border border-white/10"><ArrowLeft size={24} /></button>
            <div className="bg-black/40 backdrop-blur-xl px-4 py-2 rounded-full border border-white/10 text-white text-[10px] font-black tracking-widest uppercase">Live Scanners</div>
            <button onClick={() => setIsFlashOn(!isFlashOn)} className="p-4 rounded-3xl bg-black/40 backdrop-blur-xl text-white border border-white/10">
              {isFlashOn ? <Zap size={24} className="text-yellow-400" /> : <ZapOff size={24} />}
            </button>
          </div>
          
          <div className="flex-1 relative overflow-hidden flex items-center justify-center">
            <video ref={videoRef} autoPlay playsInline className="w-full h-full object-cover" />
            
            {/* Visual AI Overlay */}
            <div className="absolute inset-0 flex items-center justify-center pointer-events-none p-10">
              <div className="w-full aspect-square max-w-[320px] border-2 border-white/10 rounded-[60px] relative overflow-hidden">
                <div className="absolute top-0 left-0 w-16 h-16 border-t-8 border-l-8 border-emerald-500 rounded-tl-[50px]"></div>
                <div className="absolute top-0 right-0 w-16 h-16 border-t-8 border-r-8 border-emerald-500 rounded-tr-[50px]"></div>
                <div className="absolute bottom-0 left-0 w-16 h-16 border-b-8 border-l-8 border-emerald-500 rounded-bl-[50px]"></div>
                <div className="absolute bottom-0 right-0 w-16 h-16 border-b-8 border-r-8 border-emerald-500 rounded-br-[50px]"></div>
                
                <div className="absolute w-full h-1 bg-gradient-to-r from-transparent via-emerald-400 to-transparent shadow-[0_0_30px_#10b981] animate-scan-line"></div>
              </div>
            </div>

            {/* ZOOM CONTROLS OVERLAY */}
            {hasZoomSupport && (
                <div className="absolute bottom-32 left-10 right-10 flex items-center gap-4 bg-black/40 backdrop-blur-md p-4 rounded-[28px] border border-white/10 z-20">
                    <button onClick={() => handleZoomChange(Math.max(minZoom, zoomLevel - 0.5))} className="p-2 bg-white/10 rounded-full text-white"><Minus size={18} /></button>
                    <input 
                        type="range" 
                        min={minZoom} 
                        max={maxZoom} 
                        step="0.1" 
                        value={zoomLevel} 
                        onChange={(e) => handleZoomChange(e.target.value)}
                        className="flex-1 custom-slider"
                    />
                    <button onClick={() => handleZoomChange(Math.min(maxZoom, zoomLevel + 0.5))} className="p-2 bg-white/10 rounded-full text-white"><Plus size={18} /></button>
                    <span className="text-white text-[10px] font-black w-8">{zoomLevel.toFixed(1)}x</span>
                </div>
            )}
          </div>

          <div className="p-10 bg-black flex justify-around items-center border-t border-white/5">
            <div className="w-14 h-14 bg-white/5 rounded-2xl flex items-center justify-center text-white/40"><ImageIcon size={28} /></div>
            <button onClick={capturePhoto} className="w-24 h-24 rounded-full border-[6px] border-white/20 flex items-center justify-center p-2 group">
              <div className="w-full h-full bg-white rounded-full group-active:scale-90 transition-transform shadow-[0_0_40px_rgba(255,255,255,0.3)]"></div>
            </button>
            <div className="w-14 h-14 bg-white/5 rounded-2xl flex items-center justify-center text-white/40"><RotateCcw size={28} /></div>
          </div>
          <canvas ref={canvasRef} className="hidden" />
        </div>
      )}

      {/* --- 3. PREVIEW & ANALYZE VIEW --- */}
      {view === 'preview' && (
        <div className="fixed inset-0 bg-slate-950 z-[100] flex flex-col">
          <div className="p-8 flex items-center justify-between text-white">
            <button onClick={() => { setView('camera'); startCamera(); }} className="flex items-center gap-2 font-black text-xs uppercase tracking-widest bg-white/10 px-4 py-2 rounded-xl"><ArrowLeft size={16} /> Retake</button>
            <div className="flex gap-4">
              <button onClick={() => setPreviewRotation(prev => (prev + 90) % 360)} className="p-3 bg-white/10 rounded-2xl border border-white/10"><RotateCw size={22} /></button>
            </div>
          </div>

          <div className="flex-1 flex items-center justify-center p-6">
            <div className="relative w-full max-h-[60vh] rounded-[50px] overflow-hidden shadow-2xl border-4 border-emerald-500/20">
              <img 
                src={capturedImage} 
                className="w-full h-full object-contain transition-transform duration-500" 
                style={{ transform: `rotate(${previewRotation}deg)` }}
              />
              {isScanning && (
                <div className="absolute inset-0 bg-emerald-950/80 backdrop-blur-xl flex flex-col items-center justify-center text-white p-10 text-center">
                   <div className="relative w-24 h-24 mb-6">
                        <Loader2 className="w-full h-full animate-spin text-emerald-400" strokeWidth={3} />
                        <Leaf className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 text-emerald-400" size={32} />
                   </div>
                   <p className="text-2xl font-black italic tracking-tighter uppercase mb-2">Analyzing Data</p>
                   <p className="text-xs text-emerald-400 font-bold uppercase tracking-widest opacity-60">Pixel Mapping & Health Diagnostic</p>
                </div>
              )}
            </div>
          </div>

          <div className="p-10 bg-white rounded-t-[60px] flex flex-col gap-6 shadow-2xl border-t border-slate-100">
            <div className="flex justify-between items-center text-[10px] font-black text-slate-400 uppercase tracking-widest">
                <span>Optimized Resolution</span>
                <span>Encrypted API Node</span>
            </div>
            <button 
              onClick={handleIdentify} 
              disabled={isScanning} 
              className="w-full bg-emerald-600 hover:bg-emerald-700 text-white font-black py-6 rounded-[30px] flex items-center justify-center gap-4 shadow-2xl shadow-emerald-200 disabled:opacity-50 transition-all uppercase tracking-tighter text-xl"
            >
              {isScanning ? "Processing..." : <><Search size={28} /> RUN ANALYSIS</>}
            </button>
          </div>
        </div>
      )}

      {/* --- 4. RESULT DASHBOARD (PREMIUM UI) --- */}
      {view === 'result' && apiResult && (
        <div className="max-w-4xl mx-auto pb-16 animate-in slide-in-from-bottom duration-700">
          <div className="relative h-[450px] overflow-hidden">
            <img src={compressedImage} className="w-full h-full object-cover scale-105" alt="Result" />
            <div className="absolute inset-0 bg-gradient-to-t from-white via-transparent to-transparent"></div>
            <button onClick={() => setView('home')} className="absolute top-8 left-6 p-4 bg-black/30 backdrop-blur-xl text-white rounded-3xl border border-white/20"><ArrowLeft size={24} /></button>
          </div>

          <div className="px-6 -mt-32 relative z-10">
            {/* Main Info Card */}
            <div className="bg-white rounded-[45px] p-10 shadow-2xl shadow-emerald-900/10 border border-slate-100 mb-8">
              <div className="flex justify-between items-start mb-8">
                <div>
                  <h1 className="text-4xl font-black text-emerald-950 tracking-tighter leading-none mb-1">{apiResult.identity.name}</h1>
                  <p className="text-emerald-500 font-black italic text-sm tracking-widest">{apiResult.identity.scientific_name}</p>
                </div>
                <div className="bg-emerald-500 p-4 rounded-[22px] text-white shadow-xl shadow-emerald-500/30">
                  <Leaf size={32} />
                </div>
              </div>
              
              <div className="bg-emerald-50 rounded-[35px] p-6 flex items-center gap-6 border border-emerald-100">
                <div className="relative w-24 h-24 flex items-center justify-center">
                   <svg className="w-full h-full transform -rotate-90">
                     <circle cx="48" cy="48" r="42" stroke="currentColor" strokeWidth="8" fill="transparent" className="text-emerald-100" />
                     <circle cx="48" cy="48" r="42" stroke="currentColor" strokeWidth="8" fill="transparent" strokeDasharray={264} strokeDashoffset={264 - (264 * apiResult.health.health_percentage) / 100} className="text-emerald-600 transition-all duration-1000 stroke-round" />
                   </svg>
                   <span className="absolute font-black text-xl text-emerald-950">{apiResult.health.health_percentage}%</span>
                </div>
                <div>
                  <h4 className="font-black text-emerald-950 text-xl tracking-tight">VITAL HEALTH SCORE</h4>
                  <p className="text-xs text-emerald-700 font-bold uppercase tracking-widest mb-1">Status: {apiResult.health.health_percentage > 75 ? 'Optimal' : 'Needs Care'}</p>
                  <p className="text-xs text-slate-500 font-medium">Alerts: {apiResult.health.issues}</p>
                </div>
              </div>
            </div>

            <h3 className="text-xl font-black text-slate-900 uppercase tracking-tighter mb-5 ml-2">Environmental Needs</h3>
            <div className="grid grid-cols-2 gap-4 mb-8">
              <div className="bg-orange-50 p-6 rounded-[35px] border border-orange-100">
                <Sun className="text-orange-500 mb-4" size={32} />
                <span className="text-[10px] font-black uppercase text-orange-950/40 tracking-widest">Luminance</span>
                <p className="font-black text-slate-800 text-lg leading-none mt-1">{apiResult.health.sunlight_captured || "Adequate"}</p>
              </div>
              <div className="bg-blue-50 p-6 rounded-[35px] border border-blue-100">
                <Droplets className="text-blue-500 mb-4" size={32} />
                <span className="text-[10px] font-black uppercase text-blue-950/40 tracking-widest">Hydration</span>
                <p className="font-black text-slate-800 text-lg leading-none mt-1">{apiResult.care.water}</p>
              </div>
            </div>

            <div className="bg-emerald-950 rounded-[45px] p-10 text-white shadow-2xl mb-8 relative overflow-hidden">
               <div className="absolute bottom-0 right-0 w-40 h-40 bg-white/5 rounded-full -mb-20 -mr-20 blur-2xl"></div>
               <h3 className="font-black text-2xl mb-6 flex items-center gap-3">
                 <CheckCircle size={28} className="text-emerald-400" /> BIOTECH ADVICE
               </h3>
               <div className="space-y-6">
                 <div className="flex gap-5">
                    <div className="w-10 h-10 rounded-2xl bg-white/10 flex items-center justify-center font-black">01</div>
                    <p className="text-sm text-emerald-100/80 leading-relaxed font-bold">{apiResult.care.soil}</p>
                 </div>
                 <div className="flex gap-5">
                    <div className="w-10 h-10 rounded-2xl bg-white/10 flex items-center justify-center font-black">02</div>
                    <p className="text-sm text-emerald-100/80 leading-relaxed font-bold">{apiResult.care.humidity}</p>
                 </div>
               </div>
            </div>

            <div className="flex gap-4">
                <button className="flex-1 bg-white border-4 border-emerald-600 text-emerald-600 font-black py-6 rounded-[30px] text-xl active:scale-95 transition-all shadow-xl shadow-emerald-200">CARE PLAN</button>
                <button onClick={() => window.open(`https://www.amazon.in/s?k=${apiResult.identity.name}+fertilizer`, '_blank')} className="flex-1 bg-emerald-600 text-white font-black py-6 rounded-[30px] text-xl active:scale-95 transition-all shadow-xl shadow-emerald-500/30">SHOP SUPPLIES</button>
            </div>
          </div>
        </div>
      )}

      {/* --- 5. HISTORY VIEW --- */}
      {view === 'history' && (
        <div className="max-w-4xl mx-auto min-h-screen bg-white">
          <div className="p-6 bg-emerald-950 text-white flex items-center justify-between sticky top-0 z-50">
            <div className="flex items-center gap-4">
                <button onClick={() => setView('home')} className="p-2 hover:bg-white/10 rounded-xl"><ArrowLeft size={28} /></button>
                <h1 className="text-2xl font-black uppercase tracking-tighter">Activity Log</h1>
            </div>
            <button 
              onClick={() => {setSearchHistory([]); localStorage.removeItem('plantque_history');}} 
              className="p-3 text-emerald-400 hover:bg-white/10 rounded-2xl"
            >
              <Trash2 size={24} />
            </button>
          </div>
          <div className="p-6 space-y-6">
            {searchHistory.map((item) => (
              <div 
                key={item.id} 
                onClick={() => { setApiResult(item.fullData); setCompressedImage(item.img); setView('result'); }} 
                className="flex gap-5 p-6 bg-slate-50 rounded-[40px] border-2 border-slate-100 hover:border-emerald-500/30 transition-all active:scale-95 group"
              >
                <div className="w-28 h-28 rounded-[28px] overflow-hidden flex-shrink-0 shadow-lg group-hover:rotate-3 transition-transform">
                  <img src={item.img} className="w-full h-full object-cover" alt="" />
                </div>
                <div className="flex-1 py-1">
                  <div className="flex justify-between items-start">
                    <h4 className="font-black text-emerald-950 uppercase text-sm tracking-tight">{item.name}</h4>
                    <span className="text-[10px] font-black text-slate-300">{item.date}</span>
                  </div>
                  <p className="text-[10px] font-bold text-emerald-600 mt-1 uppercase tracking-widest">{item.fullData.identity.scientific_name}</p>
                  <div className="mt-4 flex gap-2">
                    <span className="px-3 py-1 bg-emerald-100 text-emerald-700 text-[10px] font-black rounded-full uppercase">Health: {item.fullData.health.health_percentage}%</span>
                    <span className="px-3 py-1 bg-blue-100 text-blue-700 text-[10px] font-black rounded-full uppercase">Viewed</span>
                  </div>
                </div>
              </div>
            ))}
            {searchHistory.length === 0 && (
                <div className="flex flex-col items-center justify-center py-40 opacity-20">
                    <History size={100} />
                    <p className="font-black text-2xl uppercase mt-4">Database Empty</p>
                </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default App;
