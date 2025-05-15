import './globals.css';
import type { ReactNode } from 'react';
import Link from 'next/link';

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body className="bg-gray-50 min-h-screen">
        {/* Navbar with clickable title */}
        <nav className="bg-white shadow-sm mb-8">
          <div className="max-w-7xl mx-auto px-4 py-4 flex items-center justify-between">
            <Link href="/">
              <span className="text-xl font-bold text-blue-600 cursor-pointer">SkillBridge</span>
            </Link>
            <Link href="/skillmatch">
              <button className="ml-4 px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 transition-colors">
                Skillmatch
              </button>
            </Link>
          </div>
        </nav>
        <div className="max-w-7xl mx-auto px-4">{children}</div>
      </body>
    </html>
  );
}
