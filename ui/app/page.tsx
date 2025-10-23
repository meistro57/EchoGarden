'use client';

import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { useState } from 'react';
import { fetchSearch } from '@/lib/api';

export default function SearchPage() {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);

  const handleSearch = async () => {
    const data = await fetchSearch(query);
    setResults(data.results);
  };

  return (
    <div className="max-w-4xl mx-auto p-8">
      <div className="flex gap-4 mb-8">
        <Input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Search chat logs..."
          className="flex-1"
        />
        <Button onClick={handleSearch}>Search</Button>
      </div>

      <div className="space-y-4">
        {results.map((hit: any, idx) => (
          <div key={idx} className="border p-4 rounded">
            <div className="font-medium">{hit.conv_id}</div>
            <div className="text-sm text-gray-600">{hit.text.slice(0, 200)}...</div>
          </div>
        ))}
      </div>
    </div>
  );
}