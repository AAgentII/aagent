import React, { useCallback, useState, useMemo } from 'react';
import ReactFlow, {
  Node,
  Edge,
  Controls,
  Background,
  MiniMap,
  addEdge,
  useNodesState,
  useEdgesState,
  Connection,
  MarkerType,
  NodeTypes,
  EdgeTypes,
} from 'reactflow';
import 'reactflow/dist/style.css';

import { Button } from '@/components/ui/button';
import { Plus, Save, Play, Settings, Code } from 'lucide-react';
import { useWorkflowStore } from '@/store/workflow';
import { AgentNode } from '@/components/workflow/AgentNode';
import { StartNode } from '@/components/workflow/StartNode';
import { EndNode } from '@/components/workflow/EndNode';
import { ConditionNode } from '@/components/workflow/ConditionNode';
import { NodePanel } from '@/components/workflow/NodePanel';
import { PropertiesPanel } from '@/components/workflow/PropertiesPanel';
import { ExecutionPanel } from '@/components/workflow/ExecutionPanel';

const nodeTypes: NodeTypes = {
  agent: AgentNode,
  start: StartNode,
  end: EndNode,
  condition: ConditionNode,
};

const initialNodes: Node[] = [
  {
    id: 'start-1',
    type: 'start',
    position: { x: 100, y: 200 },
    data: { label: 'Start' },
  },
];

const WorkflowEditor: React.FC = () => {
  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);
  const [selectedNode, setSelectedNode] = useState<Node | null>(null);
  const [showNodePanel, setShowNodePanel] = useState(false);
  const [showExecutionPanel, setShowExecutionPanel] = useState(false);

  const { currentWorkflow, saveWorkflow, executeWorkflow } = useWorkflowStore();

  const onConnect = useCallback(
    (params: Connection) => {
      setEdges((eds) =>
        addEdge(
          {
            ...params,
            markerEnd: {
              type: MarkerType.ArrowClosed,
            },
          },
          eds
        )
      );
    },
    [setEdges]
  );

  const onNodeClick = useCallback((event: React.MouseEvent, node: Node) => {
    setSelectedNode(node);
  }, []);

  const onPaneClick = useCallback(() => {
    setSelectedNode(null);
  }, []);

  const onAddNode = useCallback(
    (type: string) => {
      const newNode: Node = {
        id: `${type}-${Date.now()}`,
        type,
        position: { x: 200, y: 200 },
        data: {
          label: type.charAt(0).toUpperCase() + type.slice(1),
          config: {},
        },
      };
      setNodes((nds) => [...nds, newNode]);
      setShowNodePanel(false);
    },
    [setNodes]
  );

  const onSave = useCallback(async () => {
    const workflow = {
      nodes: nodes.map((node) => ({
        id: node.id,
        type: node.type || 'agent',
        position: node.position,
        data: node.data,
      })),
      edges: edges.map((edge) => ({
        id: edge.id,
        source: edge.source,
        target: edge.target,
        data: edge.data,
      })),
    };

    await saveWorkflow(workflow);
  }, [nodes, edges, saveWorkflow]);

  const onExecute = useCallback(async () => {
    const workflow = {
      nodes: nodes.map((node) => ({
        id: node.id,
        type: node.type || 'agent',
        config: node.data.config || {},
        agent_config: node.data.agent_config,
      })),
      edges: edges.map((edge) => ({
        from_node: edge.source,
        to_node: edge.target,
        condition: edge.data?.condition,
      })),
    };

    await executeWorkflow(workflow);
    setShowExecutionPanel(true);
  }, [nodes, edges, executeWorkflow]);

  return (
    <div className="h-screen flex flex-col">
      {/* Header */}
      <div className="border-b bg-background p-4 flex items-center justify-between">
        <div className="flex items-center gap-4">
          <h1 className="text-2xl font-bold">Workflow Editor</h1>
          {currentWorkflow && (
            <span className="text-muted-foreground">
              {currentWorkflow.name}
            </span>
          )}
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => setShowNodePanel(!showNodePanel)}
          >
            <Plus className="h-4 w-4 mr-2" />
            Add Node
          </Button>
          <Button variant="outline" size="sm" onClick={onSave}>
            <Save className="h-4 w-4 mr-2" />
            Save
          </Button>
          <Button variant="outline" size="sm">
            <Code className="h-4 w-4 mr-2" />
            View Code
          </Button>
          <Button onClick={onExecute}>
            <Play className="h-4 w-4 mr-2" />
            Execute
          </Button>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex relative">
        {/* Node Panel */}
        {showNodePanel && (
          <NodePanel
            onAddNode={onAddNode}
            onClose={() => setShowNodePanel(false)}
          />
        )}

        {/* Flow Canvas */}
        <div className="flex-1">
          <ReactFlow
            nodes={nodes}
            edges={edges}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            onConnect={onConnect}
            onNodeClick={onNodeClick}
            onPaneClick={onPaneClick}
            nodeTypes={nodeTypes}
            fitView
          >
            <Background variant="dots" gap={12} size={1} />
            <Controls />
            <MiniMap />
          </ReactFlow>
        </div>

        {/* Properties Panel */}
        {selectedNode && (
          <PropertiesPanel
            node={selectedNode}
            onUpdate={(updatedNode) => {
              setNodes((nds) =>
                nds.map((n) => (n.id === updatedNode.id ? updatedNode : n))
              );
            }}
            onClose={() => setSelectedNode(null)}
          />
        )}

        {/* Execution Panel */}
        {showExecutionPanel && (
          <ExecutionPanel onClose={() => setShowExecutionPanel(false)} />
        )}
      </div>
    </div>
  );
};

export default WorkflowEditor;