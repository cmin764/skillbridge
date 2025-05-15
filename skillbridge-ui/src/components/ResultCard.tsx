import { ReactNode } from 'react';

export default function ResultCard({ title, children }: { title: string, children: ReactNode }) {
  return (
    <div className="bg-white shadow-md rounded-lg p-6 border-l-4 border-green-500">
      <h3 className="text-xl font-bold mb-4 text-green-700">{title}</h3>
      <div className="text-gray-700">
        {children}
      </div>
    </div>
  );
}
