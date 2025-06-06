import React, { memo } from 'react';
import { Handle, Position, NodeProps } from 'reactflow';
import { User } from 'lucide-react';

export const AgentNode = memo(({ data, selected }: NodeProps) => {
  return (
    <div
      className={`px-4 py-2 shadow-md rounded-md bg-white border-2 ${
        selected ? 'border-primary' : 'border-stone-400'
      }`}
    >
      <Handle
        type="target"
        position={Position.Top}
        className="w-2 h-2 !bg-primary"
      />
      
      <div className="flex items-center gap-2">
        <User className="w-4 h-4 text-primary" />
        <div className="text-sm font-medium">{data.label}</div>
      </div>
      
      {data.agent_config && (
        <div className="text-xs text-muted-foreground mt-1">
          {data.agent_config.role}
        </div>
      )}
      
      <Handle
        type="source"
        position={Position.Bottom}
        className="w-2 h-2 !bg-primary"
      />
    </div>
  );
});

AgentNode.displayName = 'AgentNode';