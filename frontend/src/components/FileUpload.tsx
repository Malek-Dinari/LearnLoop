"use client";

import { useState, useCallback } from "react";
import { Upload, FileText, X } from "lucide-react";

interface Props {
  onFileSelect: (file: File) => void;
  disabled?: boolean;
}

export default function FileUpload({ onFileSelect, disabled }: Props) {
  const [dragOver, setDragOver] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);

  const handleFile = useCallback(
    (file: File) => {
      const ext = file.name.split(".").pop()?.toLowerCase();
      if (ext !== "pdf" && ext !== "txt") {
        alert("Only PDF and TXT files are supported");
        return;
      }
      setSelectedFile(file);
      onFileSelect(file);
    },
    [onFileSelect]
  );

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2 text-navy font-semibold text-lg">
        <Upload size={20} />
        Upload a Document
      </div>
      <div
        onDragOver={(e) => {
          e.preventDefault();
          setDragOver(true);
        }}
        onDragLeave={() => setDragOver(false)}
        onDrop={(e) => {
          e.preventDefault();
          setDragOver(false);
          const file = e.dataTransfer.files[0];
          if (file) handleFile(file);
        }}
        className={`border-2 border-dashed rounded-xl p-8 text-center transition-all cursor-pointer
          ${dragOver ? "border-teal bg-teal/5" : "border-gray-300 hover:border-teal/50"}
          ${disabled ? "opacity-50 cursor-not-allowed" : ""}`}
        onClick={() => {
          if (disabled) return;
          const input = document.createElement("input");
          input.type = "file";
          input.accept = ".pdf,.txt";
          input.onchange = (e) => {
            const file = (e.target as HTMLInputElement).files?.[0];
            if (file) handleFile(file);
          };
          input.click();
        }}
      >
        {selectedFile ? (
          <div className="flex items-center justify-center gap-3">
            <FileText size={24} className="text-teal" />
            <span className="text-navy font-medium">{selectedFile.name}</span>
            <button
              onClick={(e) => {
                e.stopPropagation();
                setSelectedFile(null);
              }}
              className="p-1 hover:bg-gray-100 rounded"
            >
              <X size={16} />
            </button>
          </div>
        ) : (
          <div className="space-y-2">
            <Upload size={32} className="mx-auto text-gray-400" />
            <p className="text-gray-600">
              Drag & drop a <strong>PDF</strong> or <strong>TXT</strong> file here
            </p>
            <p className="text-sm text-gray-400">or click to browse</p>
          </div>
        )}
      </div>
    </div>
  );
}
