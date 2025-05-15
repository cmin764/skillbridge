"use client";
import { useState } from "react";
import MatchForm from "@/components/MatchForm";
import ResultCard from "@/components/ResultCard";

interface Candidate {
  id: number;
  name: string;
  skills: string[];
}

interface Job {
  id: number;
  title: string;
  requirements: string[];
}

interface MatchResult {
  id: number;
  score: number;
  rationale: string;
  candidate: Candidate;
  job: Job;
}

export default function MatchesPage() {
  const [result, setResult] = useState<MatchResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  return (
    <div className="min-h-screen bg-gray-50">
      <main className="max-w-4xl mx-auto py-12 px-4">
        <h1 className="text-3xl font-bold mb-8">Step 3: Match Candidates to Jobs</h1>
        {!result && <MatchForm setResult={setResult} setError={setError} />}
        {error && (
          <div className="my-8 p-4 bg-red-50 border border-red-200 rounded-md">
            <p className="text-red-600">{error}</p>
          </div>
        )}
        {result && (
          <div className="my-8">
            <ResultCard title="Match Created Successfully">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <h3 className="font-semibold text-lg mb-2">Candidate</h3>
                  <p><strong>Name:</strong> {result.candidate.name}</p>
                  <p><strong>Skills:</strong> {(result.candidate.skills ?? []).join(', ')}</p>
                </div>
                <div>
                  <h3 className="font-semibold text-lg mb-2">Job</h3>
                  <p><strong>Title:</strong> {result.job.title}</p>
                  <p><strong>Requirements:</strong> {(result.job.requirements ?? []).join(', ')}</p>
                </div>
              </div>
              <div className="mt-4 p-4 bg-gray-50 rounded-md">
                <p className="font-semibold text-lg">Match Results</p>
                <p className="text-2xl font-bold text-blue-600">{result.score}% Match</p>
                <p className="mt-2 text-gray-700">{result.rationale}</p>
              </div>
              <div className="mt-6">
                <button
                  onClick={() => setResult(null)}
                  className="bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded-md"
                >
                  Create Another Match
                </button>
              </div>
            </ResultCard>
          </div>
        )}
      </main>
    </div>
  );
}
