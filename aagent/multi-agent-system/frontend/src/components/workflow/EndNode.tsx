import React, { memo } from 'react';
import { Handle, Position, NodeProps } from 'reactflow';
import { StopCircle } from 'lucide-react';

export const EndNode = memo(({ selected }: NodeProps) => {
  return (
    <div
      className={`px-4 py-2 shadow-md rounded-full bg-red-500 text-white border-2 ${
        selected ? 'border-primary' : 'border-red-600'
      }`}
    >
      <Handle
        type="target"
        position={Position.Top}
        className="w-2 h-2 !bg-white"
      />
      
      <div className="flex items-center gap-2">
        <StopCircle className="w-4 h-4" />
        <div className="text-sm font-medium">End</div>
      </div>
    </div>
  );
});

EndNode.displayName = 'EndNode';