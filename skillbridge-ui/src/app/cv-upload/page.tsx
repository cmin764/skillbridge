"use client";
import { useState } from "react";
import CVUploadForm from "@/components/CVUploadForm";

export default function CVUploadPage() {
  const [isLoading, setIsLoading] = useState(false);
  const [result, setResult] = useState<object | null>(null);
  const [error, setError] = useState<string | null>(null);

  return (
    <div className="min-h-screen bg-gray-50">
      <main className="max-w-4xl mx-auto py-12 px-4">
        <h1 className="text-3xl font-bold mb-8">Step 1: Upload CV</h1>
        <CVUploadForm setIsLoading={setIsLoading} setResult={setResult} setError={setError} />
        {isLoading && (
          <div className="my-8 text-center">
            <div className="animate-spin h-8 w-8 border-4 border-blue-500 border-t-transparent rounded-full mx-auto"></div>
            <p className="mt-2 text-gray-600">Processing CV...</p>
          </div>
        )}
        {error && (
          <div className="my-8 p-4 bg-red-50 border border-red-200 rounded-md">
            <p className="text-red-600">{error}</p>
          </div>
        )}
        {result && typeof result === 'object' && (
          <div className="my-8 p-4 bg-green-50 border border-green-200 rounded-md">
            <pre className="text-green-800 text-sm whitespace-pre-wrap">{JSON.stringify(result, null, 2)}</pre>
          </div>
        )}
      </main>
    </div>
  );
}
