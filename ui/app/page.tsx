import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'; // Assuming these are available UI components
import { useState, useEffect } from 'react';
import { fetchImportZip } from '@/lib/api'; // New API function for importing zip

// NOTE: In a real application, you would fetch the list of zip files from the backend.
// For simplicity, we'll hardcode the known zip file for now.
const availableZips = [
  '7b1fd17984deb928ac0a346a0c0c69d0538463a661ef0d821d0885b7978a2f17-2025-12-31-19-26-07-e1c81942d5614bbea9cfc345acf044e9.zip',
];

export default function IngestPage() {
  const [selectedZip, setSelectedZip] = useState('');
  const [importStatus, setImportStatus] = useState('');

  const handleImport = async () => {
    if (!selectedZip) {
      setImportStatus('Please select a zip file.');
      return;
    }
    setImportStatus('Importing...');
    try {
      // Assuming fetchImportZip is an async function in ui/lib/api.ts
      // that takes the zip file name and returns a status message.
      const response = await fetchImportZip(selectedZip);
      setImportStatus(response.message || 'Import successful!');
    } catch (error) {
      console.error('Import failed:', error);
      setImportStatus('Import failed. Please check server logs.');
    }
  };

  return (
    <div className="max-w-4xl mx-auto p-8">
      <h1 className="text-2xl font-bold mb-8">Ingest Chat Data</h1>
      <div className="flex flex-col gap-4 mb-8 items-start">
        <Select value={selectedZip} onValueChange={setSelectedZip}>
          <SelectTrigger className="w-[300px]">
            <SelectValue placeholder="Select a zip file to ingest" />
          </SelectTrigger>
          <SelectContent>
            {availableZips.map((zipFile) => (
              <SelectItem key={zipFile} value={zipFile}>
                {zipFile}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        <Button onClick={handleImport} disabled={!selectedZip}>
          Import Selected Zip
        </Button>
      </div>

      {importStatus && (
        <div className={`mt-4 p-4 rounded ${importStatus.includes('failed') ? 'bg-red-100 border border-red-400 text-red-700' : 'bg-green-100 border border-green-400 text-green-700'}`}>
          {importStatus}
        </div>
      )}
    </div>
  );
}
