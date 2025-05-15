"use client";
import { useState } from "react";
import JobForm from "@/components/JobForm";
import ResultCard from "@/components/ResultCard";

interface JobResult {
  id: number;
  title: string;
  requirements: string[];
}

export default function JobPage() {
  const [result, setResult] = useState<JobResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  return (
    <div className="min-h-screen bg-gray-50">
      <main className="max-w-4xl mx-auto py-12 px-4">
        <h1 className="text-3xl font-bold mb-8">Step 2: Create Job</h1>
        <JobForm setResult={setResult} setError={setError} />
        {error && (
          <div className="my-8 p-4 bg-red-50 border border-red-200 rounded-md">
            <p className="text-red-600">{error}</p>
          </div>
        )}
        {result && (
          <div className="my-8">
            <ResultCard title="Job Created Successfully">
              <p className="mb-2"><strong>Job ID:</strong> {result.id}</p>
              <p className="mb-2"><strong>Title:</strong> {result.title}</p>
              <p className="mb-2"><strong>Requirements:</strong> {result.requirements.join(', ')}</p>
            </ResultCard>
          </div>
        )}
      </main>
    </div>
  );
}
