import React from 'react';
import { X, User, PlayCircle, StopCircle, GitBranch, Layers, GitMerge } from 'lucide-react';

interface NodePanelProps {
  onAddNode: (type: string) => void;
  onClose: () => void;
}

const nodeTypes = [
  { type: 'agent', label: 'Agent', icon: User, color: 'text-primary' },
  { type: 'start', label: 'Start', icon: PlayCircle, color: 'text-green-500' },
  { type: 'end', label: 'End', icon: StopCircle, color: 'text-red-500' },
  { type: 'condition', label: 'Condition', icon: GitBranch, color: 'text-orange-500' },
  { type: 'parallel', label: 'Parallel', icon: Layers, color: 'text-blue-500' },
  { type: 'join', label: 'Join', icon: GitMerge, color: 'text-purple-500' },
];

export const NodePanel: React.FC<NodePanelProps> = ({ onAddNode, onClose }) => {
  return (
    <div className="absolute left-4 top-20 z-50 w-64 bg-white rounded-lg shadow-lg border">
      <div className="flex items-center justify-between p-4 border-b">
        <h3 className="font-semibold">Add Node</h3>
        <button
          onClick={onClose}
          className="p-1 hover:bg-gray-100 rounded"
        >
          <X className="w-4 h-4" />
        </button>
      </div>
      
      <div className="p-4 space-y-2">
        {nodeTypes.map(({ type, label, icon: Icon, color }) => (
          <button
            key={type}
            onClick={() => onAddNode(type)}
            className="w-full flex items-center gap-3 p-3 hover:bg-gray-50 rounded-md transition-colors"
          >
            <Icon className={`w-5 h-5 ${color}`} />
            <span className="text-sm font-medium">{label}</span>
          </button>
        ))}
      </div>
    </div>
  );
};