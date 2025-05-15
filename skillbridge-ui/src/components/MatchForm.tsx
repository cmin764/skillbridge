"use client";
import { Dispatch, SetStateAction, useEffect, useState } from "react";

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

interface MatchFormProps {
  setResult: Dispatch<SetStateAction<MatchResult | null>>;
  setError: Dispatch<SetStateAction<string | null>>;
}

export default function MatchForm({ setResult, setError }: MatchFormProps) {
  const [candidates, setCandidates] = useState<Candidate[]>([]);
  const [jobs, setJobs] = useState<Job[]>([]);
  const [candidateId, setCandidateId] = useState("");
  const [jobId, setJobId] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    async function fetchData() {
      try {
        const [candidatesRes, jobsRes] = await Promise.all([
          fetch("http://localhost:8000/api/candidates/"),
          fetch("http://localhost:8000/api/jobs/")
        ]);
        if (!candidatesRes.ok || !jobsRes.ok) throw new Error("Failed to load candidates or jobs");
        const candidatesData = await candidatesRes.json();
        const jobsData = await jobsRes.json();
        setCandidates(candidatesData.results || []);
        setJobs(jobsData.results || []);
      } catch {
        setError("Failed to load candidates or jobs");
      }
    }
    fetchData();
  }, [setError]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!candidateId || !jobId) {
      setError("Please select both a candidate and a job");
      return;
    }
    setIsLoading(true);
    setError(null);
    try {
      const matchData = {
        candidate_id: Number(candidateId),
        job_id: Number(jobId)
      };
      const res = await fetch("http://localhost:8000/api/matches/create_match/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(matchData),
      });
      if (!res.ok) {
        console.debug('Match creation response:', res);
        throw new Error("Failed to create match");
      }
      const result = await res.json();
      setResult(result);
    } catch (error) {
      const err = error as Error;
      console.debug('Match creation error:', err);
      setError(err.message || "Failed to create match");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="bg-white shadow-md rounded-lg p-6">
      <form onSubmit={handleSubmit}>
        <div className="mb-4">
          <label htmlFor="candidate" className="block text-sm font-medium text-gray-700 mb-1">
            Select Candidate
          </label>
          {candidates.length === 0 ? (
            <p className="text-yellow-600 text-sm">No candidates available. Please upload CVs first.</p>
          ) : (
            <select
              id="candidate"
              value={candidateId}
              onChange={(e) => setCandidateId(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md bg-white"
            >
              <option value="">-- Select a candidate --</option>
              {candidates.map(candidate => (
                <option key={candidate.id} value={candidate.id}>
                  {candidate.name} ({candidate.skills.join(', ')})
                </option>
              ))}
            </select>
          )}
        </div>
        <div className="mb-6">
          <label htmlFor="job" className="block text-sm font-medium text-gray-700 mb-1">
            Select Job
          </label>
          {jobs.length === 0 ? (
            <p className="text-yellow-600 text-sm">No jobs available. Please create jobs first.</p>
          ) : (
            <select
              id="job"
              value={jobId}
              onChange={(e) => setJobId(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md bg-white"
            >
              <option value="">-- Select a job --</option>
              {jobs.map(job => (
                <option key={job.id} value={job.id}>
                  {job.title} ({job.requirements.join(', ')})
                </option>
              ))}
            </select>
          )}
        </div>
        <button
          type="submit"
          disabled={isLoading || !candidateId || !jobId}
          className="w-full bg-blue-500 hover:bg-blue-600 text-white py-2 px-4 rounded-md disabled:bg-gray-300 disabled:cursor-not-allowed"
        >
          {isLoading ? 'Creating Match...' : 'Match Candidate to Job'}
        </button>
      </form>
    </div>
  );
}
