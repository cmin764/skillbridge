"use client";
import { Dispatch, SetStateAction, useState } from "react";

interface JobResult {
  id: number;
  title: string;
  requirements: string[];
}

interface JobFormProps {
  setResult: Dispatch<SetStateAction<JobResult | null>>;
  setError: Dispatch<SetStateAction<string | null>>;
}

export default function JobForm({ setResult, setError }: JobFormProps) {
  const [title, setTitle] = useState("");
  const [requirements, setRequirements] = useState("");
  const [isLoading, setLocalLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!title || !requirements) {
      setError("Please fill in all fields");
      return;
    }
    setLocalLoading(true);
    setError(null);
    try {
      const requirementsArray = requirements
        .split(',')
        .map(req => req.trim())
        .filter(req => req.length > 0);
      const jobData = {
        title,
        requirements: requirementsArray
      };
      const res = await fetch("http://localhost:8000/api/jobs/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(jobData),
      });
      if (!res.ok) {
        console.debug('Job creation response:', res);
        throw new Error("Failed to create job");
      }
      const result = await res.json();
      setResult(result);
    } catch (error) {
      const err = error as Error;
      console.debug('Job creation error:', err);
      setError(err.message || "Failed to create job");
    } finally {
      setLocalLoading(false);
    }
  };

  return (
    <div className="bg-white shadow-md rounded-lg p-6">
      <form onSubmit={handleSubmit}>
        <div className="mb-4">
          <label htmlFor="title" className="block text-sm font-medium text-gray-700 mb-1">
            Job Title
          </label>
          <input
            id="title"
            type="text"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md"
            placeholder="e.g. Senior Django Developer"
          />
        </div>
        <div className="mb-6">
          <label htmlFor="requirements" className="block text-sm font-medium text-gray-700 mb-1">
            Requirements (comma separated)
          </label>
          <textarea
            id="requirements"
            value={requirements}
            onChange={(e) => setRequirements(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md"
            placeholder="e.g. Python, Django, PostgreSQL, AWS"
            rows={4}
          />
          <p className="mt-1 text-xs text-gray-500">
            Enter skills separated by commas
          </p>
        </div>
        <button
          type="submit"
          disabled={isLoading}
          className="w-full bg-blue-500 hover:bg-blue-600 text-white py-2 px-4 rounded-md disabled:bg-gray-300 disabled:cursor-not-allowed"
        >
          Create Job
        </button>
      </form>
    </div>
  );
}
