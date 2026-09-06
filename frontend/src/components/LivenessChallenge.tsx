import React, { useState } from 'react';
import { CheckCircle2, XCircle, ArrowRight } from 'lucide-react';
import AudioUploader from './AudioUploader';
import { VerifyResponse } from '../api/types';

interface LivenessChallengeProps {
  challengeText: string;
  digits: string;          // backend returns a string like "482901"
  onSubmitResponse: (file: File) => void;
  result?: VerifyResponse;
  isVerifying?: boolean;
}

const LivenessChallenge: React.FC<LivenessChallengeProps> = ({
  challengeText,
  digits,
  onSubmitResponse,
  result,
  isVerifying = false,
}) => {
  const [step, setStep] = useState<1 | 2 | 3>(1);

  // Split digit string into individual characters for display
  const digitArray = typeof digits === 'string' ? digits.split('') : [];

  // Automatically move to step 3 if we get a result
  React.useEffect(() => {
    if (result) {
      setStep(3);
    }
  }, [result]);

  return (
    <div className="glass-card p-6 border-amber-500/30 overflow-hidden relative">
      <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-amber-500 to-orange-600" />
      
      <div className="mb-6 flex justify-between items-center">
        <h3 className="text-lg font-bold text-white">Security Verification Required</h3>
        <div className="flex space-x-2">
          <div className={`h-2 w-2 rounded-full ${step >= 1 ? 'bg-amber-500' : 'bg-gray-600'}`} />
          <div className={`h-2 w-2 rounded-full ${step >= 2 ? 'bg-amber-500' : 'bg-gray-600'}`} />
          <div className={`h-2 w-2 rounded-full ${step >= 3 ? 'bg-amber-500' : 'bg-gray-600'}`} />
        </div>
      </div>

      <div className="relative">
        {step === 1 && (
          <div className="animate-in fade-in slide-in-from-right-4 duration-500">
            <p className="text-gray-300 mb-6 text-center">To verify you are a live human, please read the following text clearly:</p>
            <div className="bg-navy-dark p-6 rounded-xl border border-white/5 mb-6">
              <p className="text-center text-xl font-medium text-white mb-4">"{challengeText}"</p>
              <div className="flex justify-center space-x-3">
                {digitArray.map((digit, idx) => (
                  <span key={idx} className="w-10 h-12 flex items-center justify-center bg-gray-800 rounded-lg text-2xl font-bold text-amber-500 shadow-inner">
                    {digit}
                  </span>
                ))}
              </div>
            </div>
            <button
              onClick={() => setStep(2)}
              className="w-full py-3 px-4 bg-electric-blue hover:bg-electric-blue-light text-white rounded-lg font-medium transition-colors flex items-center justify-center"
            >
              Ready to Record <ArrowRight className="ml-2 w-4 h-4" />
            </button>
          </div>
        )}

        {step === 2 && (
          <div className="animate-in fade-in slide-in-from-right-4 duration-500">
            <p className="text-gray-300 mb-4 text-center">Upload your voice recording reading the phrase</p>
            <AudioUploader 
              onFileSelected={onSubmitResponse} 
              isLoading={isVerifying} 
            />
            {isVerifying && (
              <p className="text-center text-sm text-electric-blue mt-4 animate-pulse">
                Analyzing voice response...
              </p>
            )}
          </div>
        )}

        {step === 3 && result && (
          <div className="animate-in fade-in zoom-in-95 duration-500 flex flex-col items-center py-6">
            {result.passed ? (
              <>
                <CheckCircle2 className="w-16 h-16 text-green-500 mb-4" />
                <h4 className="text-xl font-bold text-white mb-2">Verification Passed</h4>
                <p className="text-gray-400 text-center">Identity confirmed securely.</p>
              </>
            ) : (
              <>
                <XCircle className="w-16 h-16 text-red-500 mb-4" />
                <h4 className="text-xl font-bold text-white mb-2">Verification Failed</h4>
                <p className="text-red-400 text-center">Liveness check did not pass. Digits matched: {result.digits_matched ? 'Yes' : 'No'}</p>
                <button
                  onClick={() => setStep(1)}
                  className="mt-6 text-sm text-electric-blue hover:text-white transition-colors"
                >
                  Try Again
                </button>
              </>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default LivenessChallenge;
