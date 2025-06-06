import React from 'react';
import { Node } from 'reactflow';

interface PropertiesPanelProps {
  node: Node;
  onUpdate: (node: Node) => void;
  onClose: () => void;
}

export const PropertiesPanel: React.FC<PropertiesPanelProps> = ({ node, onUpdate, onClose }) => {
  return (
    <div className="absolute right-0 top-0 h-full w-80 bg-white shadow-lg border-l p-4">
      <div className="flex items-center justify-between mb-4">
        <h3 className="font-semibold">Node Properties</h3>
        <button onClick={onClose} className="text-gray-500 hover:text-gray-700">×</button>
      </div>
      <div className="space-y-4">
        <div>
          <label className="block text-sm font-medium mb-1">Label</label>
          <input 
            type="text" 
            value={node.data.label || ''} 
            onChange={(e) => onUpdate({...node, data: {...node.data, label: e.target.value}})}
            className="w-full p-2 border rounded"
          />
        </div>
        <div>
          <label className="block text-sm font-medium mb-1">Type</label>
          <div className="p-2 bg-gray-100 rounded">{node.type}</div>
        </div>
      </div>
    </div>
  );
};