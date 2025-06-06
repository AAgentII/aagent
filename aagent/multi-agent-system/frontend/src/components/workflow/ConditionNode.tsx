import React, { memo } from 'react';
import { Handle, Position, NodeProps } from 'reactflow';
import { GitBranch } from 'lucide-react';

export const ConditionNode = memo(({ data, selected }: NodeProps) => {
  return (
    <div
      className={`px-4 py-2 shadow-md rounded-md bg-orange-100 border-2 ${
        selected ? 'border-primary' : 'border-orange-400'
      }`}
    >
      <Handle
        type="target"
        position={Position.Top}
        className="w-2 h-2 !bg-orange-400"
      />
      
      <div className="flex items-center gap-2">
        <GitBranch className="w-4 h-4 text-orange-600" />
        <div className="text-sm font-medium">{data.label}</div>
      </div>
      
      <Handle
        type="source"
        position={Position.Bottom}
        id="true"
        style={{ left: '30%' }}
        className="w-2 h-2 !bg-green-500"
      />
      
      <Handle
        type="source"
        position={Position.Bottom}
        id="false"
        style={{ left: '70%' }}
        className="w-2 h-2 !bg-red-500"
      />
    </div>
  );
});

ConditionNode.displayName = 'ConditionNode';