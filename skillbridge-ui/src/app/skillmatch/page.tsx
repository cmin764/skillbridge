import Link from 'next/link';

export default function SkillmatchDashboard() {
  return (
    <div className="min-h-screen bg-gray-50">
      <main className="max-w-7xl mx-auto py-12 px-4">
        <h1 className="text-3xl font-bold text-center mb-12">SkillBridge Matching System</h1>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          <Link href="/cv-upload">
            <div className="bg-white shadow-md rounded-lg p-6 hover:shadow-lg transition-shadow cursor-pointer">
              <h2 className="text-xl font-bold mb-4">Step 1: Upload CV</h2>
              <p className="text-gray-600">Upload candidate CV files for parsing and analysis.</p>
            </div>
          </Link>
          <Link href="/jobs">
            <div className="bg-white shadow-md rounded-lg p-6 hover:shadow-lg transition-shadow cursor-pointer">
              <h2 className="text-xl font-bold mb-4">Step 2: Create Job</h2>
              <p className="text-gray-600">Define job requirements and skills needed.</p>
            </div>
          </Link>
          <Link href="/matches">
            <div className="bg-white shadow-md rounded-lg p-6 hover:shadow-lg transition-shadow cursor-pointer">
              <h2 className="text-xl font-bold mb-4">Step 3: Match Candidates</h2>
              <p className="text-gray-600">Run the AI matching algorithm to find the best candidates.</p>
            </div>
          </Link>
        </div>
      </main>
    </div>
  );
}
