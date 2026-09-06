import React, { useRef, useState } from 'react';
import { Mic, FileAudio } from 'lucide-react';
import { clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

interface AudioUploaderProps {
  onFileSelected: (file: File) => void;
  isLoading?: boolean;
  disabled?: boolean;
}

const AudioUploader: React.FC<AudioUploaderProps> = ({ onFileSelected, isLoading, disabled }) => {
  const [isDragging, setIsDragging] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    if (!disabled && !isLoading) setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    if (disabled || isLoading) return;

    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      const file = e.dataTransfer.files[0];
      handleFile(file);
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      handleFile(e.target.files[0]);
    }
  };

  const handleFile = (file: File) => {
    // Accept any audio file — backend will validate the extension
    setSelectedFile(file);
    onFileSelected(file);
  };

  return (
    <div
      className={twMerge(
        clsx(
          'relative w-full p-8 border-2 border-dashed rounded-xl flex flex-col items-center justify-center transition-all duration-300',
          isDragging ? 'border-electric-blue bg-electric-blue/10 shadow-[0_0_15px_rgba(59,130,246,0.5)]' : 'border-gray-600 bg-navy-light/30',
          (disabled || isLoading) ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer hover:border-gray-400'
        )
      )}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
      onClick={() => !disabled && !isLoading && fileInputRef.current?.click()}
    >
      <input
        type="file"
        ref={fileInputRef}
        className="hidden"
        accept=".wav,.mp3,.flac,.m4a,.ogg,audio/*"
        onChange={handleFileChange}
        disabled={disabled || isLoading}
      />
      
      {selectedFile ? (
        <div className="flex flex-col items-center space-y-4">
          <div className="p-4 bg-electric-blue/20 rounded-full">
            <FileAudio className="w-10 h-10 text-electric-blue" />
          </div>
          <div className="text-center">
            <p className="text-sm font-medium text-white">{selectedFile.name}</p>
            <p className="text-xs text-gray-400 mt-1">{(selectedFile.size / 1024 / 1024).toFixed(2)} MB</p>
          </div>
          <button
            className="text-xs text-electric-blue hover:text-white transition-colors mt-2"
            onClick={(e) => {
              e.stopPropagation();
              setSelectedFile(null);
            }}
          >
            Clear selection
          </button>
        </div>
      ) : (
        <div className="flex flex-col items-center space-y-4">
          <div className="p-4 bg-gray-800 rounded-full">
            <Mic className="w-10 h-10 text-gray-400" />
          </div>
          <div className="text-center">
            <p className="text-sm font-medium text-white">Drag & drop audio here</p>
            <p className="text-xs text-gray-400 mt-1">or click to browse files</p>
          </div>
        </div>
      )}
      
      {isLoading && (
        <div className="absolute inset-0 bg-navy/80 flex items-center justify-center rounded-xl backdrop-blur-sm">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-electric-blue"></div>
        </div>
      )}
    </div>
  );
};

export default AudioUploader;
