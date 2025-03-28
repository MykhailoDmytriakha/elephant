import React from 'react';

export default function StageSection({ title, items }) {
  if (!items || items.length === 0) return null;

  return (
    <div className="mt-8">
      <h3 className="text-lg font-medium text-gray-900 mb-4">{title}</h3>
      <ul className="space-y-1 pl-6 list-disc text-sm">
        {items.map((item, index) => (
          <li key={`${title.toLowerCase()}-${index}`}>{item}</li>
        ))}
      </ul>
    </div>
  );
} 