"use client";
import { Dispatch, SetStateAction, useState, useRef } from "react";

interface CVUploadFormProps {
  setIsLoading: Dispatch<SetStateAction<boolean>>;
  setResult: Dispatch<SetStateAction<object | null>>;
  setError: Dispatch<SetStateAction<string | null>>;
}

export default function CVUploadForm({ setIsLoading, setResult, setError }: CVUploadFormProps) {
  const [file, setFile] = useState<File | null>(null);
  const [fileName, setFileName] = useState("");
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      setFile(e.target.files[0]);
      setFileName(e.target.files[0].name);
    }
  };

  const handleDragOver = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
  };

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      setFile(e.dataTransfer.files[0]);
      setFileName(e.dataTransfer.files[0].name);
    }
  };

  const handleUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file) {
      setError("Please select a file to upload");
      return;
    }
    setIsLoading(true);
    setError(null);
    try {
      // Step 1: Upload the CV
      const formData = new FormData();
      formData.append("file", file);
      const uploadRes = await fetch("http://localhost:8000/api/cv-uploads/", {
        method: "POST",
        body: formData,
      });
      if (!uploadRes.ok) {
        console.debug('Upload response:', uploadRes);
        throw new Error("Failed to upload CV");
      }
      const uploadResult = await uploadRes.json();
      // Step 2: Parse the CV into a candidate
      const parseRes = await fetch(`http://localhost:8000/api/cv-uploads/${uploadResult.id}/parse/`, {
        method: "POST",
      });
      if (!parseRes.ok) {
        console.debug('Parse response:', parseRes);
        throw new Error("Failed to parse CV");
      }
      const parseResult = await parseRes.json();
      setResult({ ...uploadResult, candidate: parseResult });
    } catch (error) {
      const err = error as Error;
      console.debug('Upload/Parse error:', err);
      setError(err.message || "Failed to upload CV");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="bg-white shadow-md rounded-lg p-6">
      <form onSubmit={handleUpload}>
        <div
          className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center cursor-pointer"
          onDragOver={handleDragOver}
          onDrop={handleDrop}
          onClick={() => fileInputRef.current?.click()}
        >
          <input
            type="file"
            ref={fileInputRef}
            onChange={handleFileChange}
            accept=".pdf,.doc,.docx"
            className="hidden"
          />
          {!fileName ? (
            <div>
              <p className="mt-1 text-sm text-gray-600">
                Drag and drop your CV here, or click to select a file
              </p>
              <p className="mt-1 text-xs text-gray-500">Supports PDF, DOC, DOCX</p>
            </div>
          ) : (
            <div>
              <p className="mt-1 text-sm font-medium">{fileName}</p>
              <p className="mt-1 text-xs text-gray-500">Click to change file</p>
            </div>
          )}
        </div>
        <div className="mt-6">
          <button
            type="submit"
            disabled={!file}
            className="w-full bg-blue-500 hover:bg-blue-600 text-white py-2 px-4 rounded-md disabled:bg-gray-300 disabled:cursor-not-allowed"
          >
            Upload and Parse CV
          </button>
        </div>
      </form>
    </div>
  );
}
