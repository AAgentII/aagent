import React, { memo } from 'react';
import { Handle, Position, NodeProps } from 'reactflow';
import { PlayCircle } from 'lucide-react';

export const StartNode = memo(({ selected }: NodeProps) => {
  return (
    <div
      className={`px-4 py-2 shadow-md rounded-full bg-green-500 text-white border-2 ${
        selected ? 'border-primary' : 'border-green-600'
      }`}
    >
      <div className="flex items-center gap-2">
        <PlayCircle className="w-4 h-4" />
        <div className="text-sm font-medium">Start</div>
      </div>
      
      <Handle
        type="source"
        position={Position.Bottom}
        className="w-2 h-2 !bg-white"
      />
    </div>
  );
});

StartNode.displayName = 'StartNode';