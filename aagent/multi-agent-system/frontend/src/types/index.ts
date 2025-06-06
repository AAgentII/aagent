// Workflow types
export interface WorkflowNode {
  id: string;
  type: 'agent' | 'start' | 'end' | 'condition' | 'parallel' | 'join';
  position: { x: number; y: number };
  data: {
    label: string;
    config?: Record<string, any>;
    agent_config?: AgentConfig;
  };
}

export interface WorkflowEdge {
  id: string;
  source: string;
  target: string;
  sourceHandle?: string;
  targetHandle?: string;
  data?: {
    condition?: string;
  };
}

export interface Workflow {
  id: string;
  name: string;
  description: string;
  status: 'draft' | 'active' | 'paused' | 'archived';
  definition: {
    nodes: WorkflowNode[];
    edges: WorkflowEdge[];
  };
  created_at: string;
  updated_at: string;
}

// Agent types
export interface AgentConfig {
  name: string;
  role: AgentRole;
  model: string;
  temperature: number;
  max_tokens: number;
  system_prompt?: string;
  tools: string[];
}

export enum AgentRole {
  COORDINATOR = 'coordinator',
  SUPERVISOR = 'supervisor',
  WORKER = 'worker',
  VALIDATOR = 'validator',
  RESEARCHER = 'researcher',
  ANALYZER = 'analyzer',
}

export interface Agent {
  id: string;
  name: string;
  role: AgentRole;
  model: string;
  temperature: number;
  max_tokens: number;
  system_prompt?: string;
  tools: string[];
  config: Record<string, any>;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

// Execution types
export enum ExecutionStatus {
  PENDING = 'pending',
  RUNNING = 'running',
  COMPLETED = 'completed',
  FAILED = 'failed',
  CANCELLED = 'cancelled',
}

export interface WorkflowExecution {
  id: string;
  workflow_id: string;
  status: ExecutionStatus;
  input_data: Record<string, any>;
  output_data?: Record<string, any>;
  error_message?: string;
  started_at: string;
  completed_at?: string;
}

export interface NodeExecution {
  id: string;
  node_id: string;
  node_type: string;
  status: ExecutionStatus;
  input_data?: Record<string, any>;
  output_data?: Record<string, any>;
  error_message?: string;
  started_at: string;
  completed_at?: string;
}

// UI types
export interface Toast {
  id: string;
  title: string;
  description?: string;
  type: 'default' | 'success' | 'error' | 'warning';
  duration?: number;
}