import React from 'react';

interface ExecutionPanelProps {
  onClose: () => void;
}

export const ExecutionPanel: React.FC<ExecutionPanelProps> = ({ onClose }) => {
  return (
    <div className="absolute bottom-0 left-0 right-0 h-64 bg-white shadow-lg border-t p-4">
      <div className="flex items-center justify-between mb-4">
        <h3 className="font-semibold">Execution Status</h3>
        <button onClick={onClose} className="text-gray-500 hover:text-gray-700">×</button>
      </div>
      <div className="space-y-2">
        <div className="flex items-center gap-2">
          <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
          <span className="text-sm">Execution in progress...</span>
        </div>
      </div>
    </div>
  );
};