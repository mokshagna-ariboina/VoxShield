import React, { useState, useRef, useEffect, useCallback } from 'react';
import AudioUploader from '../components/AudioUploader';
import RiskGauge from '../components/RiskGauge';
import SignalBreakdownChart from '../components/SignalBreakdown';
import LivenessChallenge from '../components/LivenessChallenge';
import { useAnalyzeMutation, useVerifyMutation, useChallengeMutation } from '../hooks/useAnalysis';
import { analyzeAudio } from '../api/client';
import { AnalysisResponse } from '../api/types';
import { ShieldAlert, AlertTriangle, Radio, Upload, Square, Clock } from 'lucide-react';

// ─── Live-feed chunk result for the scrolling log ───
interface ChunkResult {
  timestamp: Date;
  chunkIndex: number;
  composite_risk_score: number;
  risk_level: string;
  transcript: string;
}

const CHUNK_DURATION_MS = 5000; // 5 seconds per chunk

const ConsumerAlert: React.FC = () => {
  // ─── Shared state ───
  const [callerId, setCallerId] = useState('');
  const [transactionAmount, setTransactionAmount] = useState<number | ''>('');
  const [recipientAccount, setRecipientAccount] = useState('');
  const [recipientIsNew, setRecipientIsNew] = useState(false);
  const [isInternational, setIsInternational] = useState(false);
  const [mode, setMode] = useState<'upload' | 'live'>('upload');

  // ─── Upload mode state ───
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const resultsRef = useRef<HTMLDivElement>(null);
  const analyzeMutation = useAnalyzeMutation();
  const challengeMutation = useChallengeMutation();
  const verifyMutation = useVerifyMutation();

  // ─── Live mode state ───
  const [isLiveActive, setIsLiveActive] = useState(false);
  const [liveResult, setLiveResult] = useState<AnalysisResponse | null>(null);
  const [chunkLog, setChunkLog] = useState<ChunkResult[]>([]);
  const [liveError, setLiveError] = useState<string | null>(null);
  const [chunkCounter, setChunkCounter] = useState(0);
  const [isProcessing, setIsProcessing] = useState(false);

  // Refs for cleanup
  const mediaStreamRef = useRef<MediaStream | null>(null);
  const recorderRef = useRef<MediaRecorder | null>(null);
  const isLiveActiveRef = useRef(false);
  const chunkCounterRef = useRef(0);
  const logContainerRef = useRef<HTMLDivElement>(null);

  // Keep ref in sync with state
  useEffect(() => {
    isLiveActiveRef.current = isLiveActive;
  }, [isLiveActive]);

  // ─── Upload mode handlers ───
  const handleAnalyze = () => {
    if (selectedFile) {
      analyzeMutation.mutate({ 
        file: selectedFile, 
        callerId,
        transactionAmount: transactionAmount ? Number(transactionAmount) : 0,
        recipientAccount,
        recipientIsNew,
        isInternational
      });
    }
  };

  useEffect(() => {
    if (analyzeMutation.isSuccess && resultsRef.current) {
      resultsRef.current.scrollIntoView({ behavior: 'smooth', block: 'start' });
      if (analyzeMutation.data.risk_level === 'challenge') {
        challengeMutation.mutate(analyzeMutation.data.id);
      }
    }
  }, [analyzeMutation.isSuccess, analyzeMutation.data]);

  const handleChallengeResponse = (file: File) => {
    if (challengeMutation.data) {
      verifyMutation.mutate({
        challengeId: challengeMutation.data.challenge_id,
        audioFile: file
      });
    }
  };

  // ─── Live mode: liveness challenge trigger ───
  const liveChallengeTriggeredRef = useRef(false);

  useEffect(() => {
    if (
      liveResult &&
      liveResult.risk_level === 'challenge' &&
      !liveChallengeTriggeredRef.current
    ) {
      liveChallengeTriggeredRef.current = true;
      challengeMutation.mutate(liveResult.id);
    }
  }, [liveResult]);

  // ─── Live mode: start recording ───
  const startLiveCapture = useCallback(async () => {
    setLiveError(null);
    setChunkLog([]);
    setLiveResult(null);
    setChunkCounter(0);
    chunkCounterRef.current = 0;
    liveChallengeTriggeredRef.current = false;

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      mediaStreamRef.current = stream;
      setIsLiveActive(true);
      isLiveActiveRef.current = true;

      // Start the first recording cycle
      recordChunk(stream);
    } catch (err: any) {
      const msg = err?.name === 'NotAllowedError'
        ? 'Microphone access denied. Please allow microphone permissions.'
        : `Failed to access microphone: ${err?.message || err}`;
      setLiveError(msg);
    }
  }, [callerId, transactionAmount, recipientAccount, recipientIsNew, isInternational]);

  // ─── Live mode: record a single chunk, then recurse ───
  const recordChunk = useCallback((stream: MediaStream) => {
    if (!isLiveActiveRef.current) return;

    // Determine MIME type support
    const mimeType = MediaRecorder.isTypeSupported('audio/webm;codecs=opus')
      ? 'audio/webm;codecs=opus'
      : MediaRecorder.isTypeSupported('audio/webm')
        ? 'audio/webm'
        : 'audio/ogg';

    const recorder = new MediaRecorder(stream, { mimeType });
    recorderRef.current = recorder;
    const chunks: Blob[] = [];

    recorder.ondataavailable = (e) => {
      if (e.data.size > 0) chunks.push(e.data);
    };

    recorder.onstop = async () => {
      if (!isLiveActiveRef.current) return;

      // Build file from recorded chunks
      const blob = new Blob(chunks, { type: mimeType });
      const ext = mimeType.includes('webm') ? 'webm' : 'ogg';
      const idx = ++chunkCounterRef.current;
      setChunkCounter(idx);
      const file = new File([blob], `live_chunk_${idx}.${ext}`, { type: mimeType });

      // Immediately start next recording
      recordChunk(stream);

      // POST to /api/analyze
      setIsProcessing(true);
      try {
        const result = await analyzeAudio(
          file, 
          callerId || undefined,
          transactionAmount ? Number(transactionAmount) : 0,
          recipientIsNew,
          isInternational,
          recipientAccount || undefined
        );
        setLiveResult(result);
        setChunkLog(prev => [
          {
            timestamp: new Date(),
            chunkIndex: idx,
            composite_risk_score: result.composite_risk_score,
            risk_level: result.risk_level,
            transcript: result.transcript || '',
          },
          ...prev,
        ].slice(0, 50)); // keep last 50
      } catch (err: any) {
        console.error('Chunk analysis failed:', err);
        // Don't stop live capture on individual chunk failure
      } finally {
        setIsProcessing(false);
      }
    };

    recorder.start();

    // Stop after CHUNK_DURATION_MS to trigger onstop → process → restart
    setTimeout(() => {
      if (recorder.state === 'recording') {
        recorder.stop();
      }
    }, CHUNK_DURATION_MS);
  }, [callerId, transactionAmount, recipientAccount, recipientIsNew, isInternational]);

  // ─── Live mode: stop ───
  const stopLiveCapture = useCallback(() => {
    isLiveActiveRef.current = false;
    setIsLiveActive(false);

    if (recorderRef.current && recorderRef.current.state === 'recording') {
      recorderRef.current.stop();
    }
    if (mediaStreamRef.current) {
      mediaStreamRef.current.getTracks().forEach(t => t.stop());
      mediaStreamRef.current = null;
    }
  }, []);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      isLiveActiveRef.current = false;
      if (recorderRef.current && recorderRef.current.state === 'recording') {
        recorderRef.current.stop();
      }
      if (mediaStreamRef.current) {
        mediaStreamRef.current.getTracks().forEach(t => t.stop());
      }
    };
  }, []);

  // Auto-scroll chunk log
  useEffect(() => {
    if (logContainerRef.current) {
      logContainerRef.current.scrollTop = 0;
    }
  }, [chunkLog]);

  // ─── Risk level color helper ───
  const riskColor = (level: string) => {
    switch (level) {
      case 'escalate': return 'text-red-400';
      case 'challenge': return 'text-amber-400';
      default: return 'text-green-400';
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-8 animate-in fade-in duration-500 pb-12">
      <div className="text-center space-y-2 mb-8">
        <h1 className="text-3xl font-bold text-white tracking-tight">Audio Analysis</h1>
        <p className="text-gray-400">Upload a call recording or activate live monitoring to detect AI voice cloning and fraud risks.</p>
      </div>

      {/* ─── Mode Toggle ─── */}
      <div className="flex justify-center">
        <div className="inline-flex bg-navy-light/60 border border-white/10 rounded-lg p-1">
          <button
            onClick={() => { if (!isLiveActive) setMode('upload'); }}
            className={`flex items-center px-5 py-2.5 rounded-md text-sm font-medium transition-all ${
              mode === 'upload'
                ? 'bg-electric-blue text-white shadow-lg'
                : 'text-gray-400 hover:text-white'
            }`}
          >
            <Upload className="w-4 h-4 mr-2" />
            File Upload
          </button>
          <button
            onClick={() => setMode('live')}
            className={`flex items-center px-5 py-2.5 rounded-md text-sm font-medium transition-all ${
              mode === 'live'
                ? 'bg-electric-blue text-white shadow-lg'
                : 'text-gray-400 hover:text-white'
            }`}
          >
            <Radio className="w-4 h-4 mr-2" />
            Live Call Mode
          </button>
        </div>
      </div>

      {/* ─── Context Form (shared) ─── */}
      <div className="glass-card p-6 md:p-8">
        <div className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Caller Phone (Optional)</label>
              <input
                type="text"
                value={callerId}
                onChange={(e) => setCallerId(e.target.value)}
                placeholder="+1 (555) 012-3456"
                disabled={isLiveActive}
                className="w-full bg-navy-dark border border-white/10 rounded-lg p-3 text-white focus:outline-none focus:border-electric-blue transition-colors disabled:opacity-50"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Transaction Amount (₹)</label>
              <input
                type="number"
                value={transactionAmount}
                onChange={(e) => setTransactionAmount(e.target.value ? Number(e.target.value) : '')}
                placeholder="0.00"
                disabled={isLiveActive}
                className="w-full bg-navy-dark border border-white/10 rounded-lg p-3 text-white focus:outline-none focus:border-electric-blue transition-colors disabled:opacity-50"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Recipient Account/Phone</label>
              <input
                type="text"
                value={recipientAccount}
                onChange={(e) => setRecipientAccount(e.target.value)}
                placeholder="Account ID or Phone"
                disabled={isLiveActive}
                className="w-full bg-navy-dark border border-white/10 rounded-lg p-3 text-white focus:outline-none focus:border-electric-blue transition-colors disabled:opacity-50"
              />
            </div>
            <div className="flex flex-col justify-end space-y-2 pb-2">
              <label className="flex items-center space-x-2 text-sm text-gray-300 cursor-pointer">
                <input
                  type="checkbox"
                  checked={recipientIsNew}
                  onChange={(e) => setRecipientIsNew(e.target.checked)}
                  disabled={isLiveActive}
                  className="rounded border-gray-600 bg-navy-dark text-electric-blue focus:ring-electric-blue"
                />
                <span>Explicitly Mark as New Recipient</span>
              </label>
              <label className="flex items-center space-x-2 text-sm text-gray-300 cursor-pointer">
                <input
                  type="checkbox"
                  checked={isInternational}
                  onChange={(e) => setIsInternational(e.target.checked)}
                  disabled={isLiveActive}
                  className="rounded border-gray-600 bg-navy-dark text-electric-blue focus:ring-electric-blue"
                />
                <span>International Transfer</span>
              </label>
            </div>
          </div>

          {/* ═══════════════ UPLOAD MODE ═══════════════ */}
          {mode === 'upload' && (
            <>
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">Audio Recording</label>
                <AudioUploader
                  onFileSelected={setSelectedFile}
                  isLoading={analyzeMutation.isPending}
                />
              </div>
              <button
                onClick={handleAnalyze}
                disabled={!selectedFile || analyzeMutation.isPending}
                className="w-full py-4 bg-electric-blue hover:bg-electric-blue-light disabled:bg-gray-700 disabled:text-gray-500 text-white rounded-lg font-bold text-lg transition-colors flex justify-center items-center"
              >
                {analyzeMutation.isPending ? 'Analyzing...' : 'Analyze Recording'}
              </button>
            </>
          )}

          {/* ═══════════════ LIVE MODE ═══════════════ */}
          {mode === 'live' && (
            <div className="space-y-4">
              {!isLiveActive ? (
                <button
                  onClick={startLiveCapture}
                  className="w-full py-4 bg-green-600 hover:bg-green-500 text-white rounded-lg font-bold text-lg transition-colors flex justify-center items-center"
                >
                  <Radio className="w-5 h-5 mr-2" />
                  Start Live Monitoring
                </button>
              ) : (
                <button
                  onClick={stopLiveCapture}
                  className="w-full py-4 bg-red-600 hover:bg-red-500 text-white rounded-lg font-bold text-lg transition-colors flex justify-center items-center"
                >
                  <Square className="w-5 h-5 mr-2" />
                  Stop Live Monitoring
                </button>
              )}

              {isLiveActive && (
                <div className="flex items-center justify-center space-x-3 text-sm">
                  <span className="relative flex h-3 w-3">
                    <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-red-400 opacity-75"></span>
                    <span className="relative inline-flex rounded-full h-3 w-3 bg-red-500"></span>
                  </span>
                  <span className="text-red-400 font-medium">LIVE — Chunk #{chunkCounter}{isProcessing ? ' (analyzing...)' : ''}</span>
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {/* ─── Error display (shared) ─── */}
      {(analyzeMutation.isError || liveError) && (
        <div className="bg-red-500/10 border border-red-500/50 rounded-lg p-4 flex items-start space-x-3 text-red-400">
          <AlertTriangle className="w-5 h-5 flex-shrink-0 mt-0.5" />
          <p>
            {liveError || 
             (analyzeMutation.error as any)?.response?.data?.detail || 
             (analyzeMutation.error as any)?.message || 
             'An error occurred during analysis. Please try again.'}
          </p>
        </div>
      )}

      {/* ═══════════════ UPLOAD RESULTS ═══════════════ */}
      {mode === 'upload' && analyzeMutation.isSuccess && analyzeMutation.data && (
        <div ref={resultsRef} className="space-y-6">
          {analyzeMutation.data.risk_level === 'escalate' && (
            <div className="bg-red-500/20 border border-red-500 rounded-lg p-6 flex items-center space-x-4 animate-in slide-in-from-top-4">
              <ShieldAlert className="w-10 h-10 text-red-500 flex-shrink-0" />
              <div>
                <h3 className="text-xl font-bold text-red-400">High Risk Detected</h3>
                <p className="text-red-300/80 mt-1">This call has been flagged for immediate review.</p>
              </div>
            </div>
          )}

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="glass-card p-6 flex flex-col items-center justify-center">
              <h3 className="text-lg font-medium text-gray-300 mb-2">Overall Risk Score</h3>
              <RiskGauge
                score={analyzeMutation.data.composite_risk_score}
                riskLevel={analyzeMutation.data.risk_level}
              />
              <div className="mt-6 pt-4 border-t border-white/10 w-full text-center">
                <p className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-1">Recommended Action</p>
                <p className={
                  `text-lg font-bold uppercase tracking-wider ` + 
                  (analyzeMutation.data.recommended_action === 'block' ? 'text-red-500' :
                   analyzeMutation.data.recommended_action === 'hold' ? 'text-orange-500' :
                   analyzeMutation.data.recommended_action === 'require liveness' ? 'text-amber-500' :
                   'text-green-500')
                }>
                  {analyzeMutation.data.recommended_action}
                </p>
              </div>
            </div>
            <div className="glass-card p-6">
              <SignalBreakdownChart
                breakdown={analyzeMutation.data.signal_breakdown}
                matchedPatterns={analyzeMutation.data.matched_patterns}
              />
            </div>
          </div>

          {analyzeMutation.data.risk_level === 'challenge' && challengeMutation.data && (
            <div className="mt-6">
              <LivenessChallenge
                challengeText={challengeMutation.data.challenge_text}
                digits={challengeMutation.data.digits}
                onSubmitResponse={handleChallengeResponse}
                isVerifying={verifyMutation.isPending}
                result={verifyMutation.data}
              />
            </div>
          )}

          {analyzeMutation.data.transcript && (
            <div className="glass-card p-6 mt-6">
              <h3 className="text-lg font-medium text-gray-300 mb-4">Call Transcript</h3>
              <div className="bg-navy-dark p-4 rounded-lg border border-white/5 max-h-64 overflow-y-auto">
                <p className="text-gray-300 leading-relaxed whitespace-pre-wrap font-serif">
                  {analyzeMutation.data.transcript}
                </p>
              </div>
            </div>
          )}
        </div>
      )}

      {/* ═══════════════ LIVE FEED RESULTS ═══════════════ */}
      {mode === 'live' && (isLiveActive || liveResult) && (
        <div className="space-y-6">
          {/* Escalation alert */}
          {liveResult?.risk_level === 'escalate' && (
            <div className="bg-red-500/20 border border-red-500 rounded-lg p-6 flex items-center space-x-4 animate-in slide-in-from-top-4">
              <ShieldAlert className="w-10 h-10 text-red-500 flex-shrink-0" />
              <div>
                <h3 className="text-xl font-bold text-red-400">High Risk Detected — Live</h3>
                <p className="text-red-300/80 mt-1">Active call is flagged. Consider immediate intervention.</p>
              </div>
            </div>
          )}

          {/* Live gauge + breakdown */}
          {liveResult && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="glass-card p-6 flex flex-col items-center justify-center">
                <h3 className="text-lg font-medium text-gray-300 mb-2">Live Risk Score</h3>
                <p className="text-xs text-gray-500 mb-4">Updates every ~{CHUNK_DURATION_MS / 1000}s</p>
                <RiskGauge
                  score={liveResult.composite_risk_score}
                  riskLevel={liveResult.risk_level}
                />
                <div className="mt-6 pt-4 border-t border-white/10 w-full text-center">
                  <p className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-1">Recommended Action</p>
                  <p className={
                    `text-lg font-bold uppercase tracking-wider ` + 
                    (liveResult.recommended_action === 'block' ? 'text-red-500' :
                     liveResult.recommended_action === 'hold' ? 'text-orange-500' :
                     liveResult.recommended_action === 'require liveness' ? 'text-amber-500' :
                     'text-green-500')
                  }>
                    {liveResult.recommended_action}
                  </p>
                </div>
              </div>
              <div className="glass-card p-6">
                <SignalBreakdownChart
                  breakdown={liveResult.signal_breakdown}
                  matchedPatterns={liveResult.matched_patterns}
                />
              </div>
            </div>
          )}

          {/* Liveness challenge (triggered when a live chunk returns 'challenge') */}
          {liveResult?.risk_level === 'challenge' && challengeMutation.data && (
            <div className="mt-6">
              <LivenessChallenge
                challengeText={challengeMutation.data.challenge_text}
                digits={challengeMutation.data.digits}
                onSubmitResponse={handleChallengeResponse}
                isVerifying={verifyMutation.isPending}
                result={verifyMutation.data}
              />
            </div>
          )}

          {/* Scrolling chunk log */}
          <div className="glass-card p-6">
            <h3 className="text-sm font-semibold text-gray-300 uppercase tracking-wider mb-4 flex items-center">
              <Clock className="w-4 h-4 mr-2 text-electric-blue" />
              Chunk Analysis Log
            </h3>
            <div
              ref={logContainerRef}
              className="bg-navy-dark rounded-lg border border-white/5 max-h-48 overflow-y-auto divide-y divide-white/5"
            >
              {chunkLog.length === 0 ? (
                <div className="p-4 text-center text-gray-500 text-sm">
                  {isLiveActive ? 'Waiting for first chunk...' : 'No chunks recorded.'}
                </div>
              ) : (
                chunkLog.map((entry, idx) => (
                  <div key={idx} className="flex items-center justify-between px-4 py-2.5 text-xs">
                    <div className="flex items-center space-x-3">
                      <span className="font-mono text-gray-500">
                        #{entry.chunkIndex}
                      </span>
                      <span className="text-gray-400">
                        {entry.timestamp.toLocaleTimeString()}
                      </span>
                      {entry.transcript && (
                        <span className="text-gray-500 max-w-[200px] truncate" title={entry.transcript}>
                          "{entry.transcript}"
                        </span>
                      )}
                    </div>
                    <div className="flex items-center space-x-3">
                      <span className={`font-mono font-bold ${riskColor(entry.risk_level)}`}>
                        {(entry.composite_risk_score * 100).toFixed(0)}%
                      </span>
                      <span className={`uppercase font-bold text-[10px] tracking-wider ${riskColor(entry.risk_level)}`}>
                        {entry.risk_level}
                      </span>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>

          {/* Live transcript (latest chunk) */}
          {liveResult?.transcript && (
            <div className="glass-card p-6">
              <h3 className="text-lg font-medium text-gray-300 mb-4">Latest Chunk Transcript</h3>
              <div className="bg-navy-dark p-4 rounded-lg border border-white/5 max-h-32 overflow-y-auto">
                <p className="text-gray-300 leading-relaxed whitespace-pre-wrap font-serif text-sm">
                  {liveResult.transcript}
                </p>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default ConsumerAlert;
