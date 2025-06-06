import { create } from 'zustand';
import { api } from '@/api/client';
import { Workflow, WorkflowExecution } from '@/types';

interface WorkflowState {
  // State
  workflows: Workflow[];
  currentWorkflow: Workflow | null;
  currentExecution: WorkflowExecution | null;
  isLoading: boolean;
  error: string | null;

  // Actions
  fetchWorkflows: () => Promise<void>;
  createWorkflow: (data: any) => Promise<void>;
  updateWorkflow: (id: string, data: any) => Promise<void>;
  deleteWorkflow: (id: string) => Promise<void>;
  selectWorkflow: (workflow: Workflow | null) => void;
  saveWorkflow: (definition: any) => Promise<void>;
  executeWorkflow: (definition: any) => Promise<void>;
  fetchExecution: (id: string) => Promise<void>;
}

export const useWorkflowStore = create<WorkflowState>((set, get) => ({
  // Initial state
  workflows: [],
  currentWorkflow: null,
  currentExecution: null,
  isLoading: false,
  error: null,

  // Fetch all workflows
  fetchWorkflows: async () => {
    set({ isLoading: true, error: null });
    try {
      const response = await api.workflows.list();
      set({ workflows: response.data, isLoading: false });
    } catch (error: any) {
      set({ error: error.message, isLoading: false });
    }
  },

  // Create new workflow
  createWorkflow: async (data) => {
    set({ isLoading: true, error: null });
    try {
      const response = await api.workflows.create(data);
      const workflows = [...get().workflows, response.data];
      set({ workflows, currentWorkflow: response.data, isLoading: false });
    } catch (error: any) {
      set({ error: error.message, isLoading: false });
    }
  },

  // Update workflow
  updateWorkflow: async (id, data) => {
    set({ isLoading: true, error: null });
    try {
      const response = await api.workflows.update(id, data);
      const workflows = get().workflows.map((w) =>
        w.id === id ? response.data : w
      );
      set({ workflows, currentWorkflow: response.data, isLoading: false });
    } catch (error: any) {
      set({ error: error.message, isLoading: false });
    }
  },

  // Delete workflow
  deleteWorkflow: async (id) => {
    set({ isLoading: true, error: null });
    try {
      await api.workflows.delete(id);
      const workflows = get().workflows.filter((w) => w.id !== id);
      set({ workflows, currentWorkflow: null, isLoading: false });
    } catch (error: any) {
      set({ error: error.message, isLoading: false });
    }
  },

  // Select workflow
  selectWorkflow: (workflow) => {
    set({ currentWorkflow: workflow });
  },

  // Save current workflow
  saveWorkflow: async (definition) => {
    const current = get().currentWorkflow;
    if (!current) {
      // Create new workflow
      await get().createWorkflow({
        name: 'New Workflow',
        description: 'Created from editor',
        definition,
      });
    } else {
      // Update existing workflow
      await get().updateWorkflow(current.id, { definition });
    }
  },

  // Execute workflow
  executeWorkflow: async (definition) => {
    set({ isLoading: true, error: null });
    try {
      let workflowId = get().currentWorkflow?.id;
      
      // Save workflow first if needed
      if (!workflowId) {
        await get().saveWorkflow(definition);
        workflowId = get().currentWorkflow?.id;
      }

      if (!workflowId) {
        throw new Error('No workflow selected');
      }

      // Execute workflow
      const response = await api.executions.create({
        workflow_id: workflowId,
        input_data: {},
      });

      set({ currentExecution: response.data, isLoading: false });
    } catch (error: any) {
      set({ error: error.message, isLoading: false });
    }
  },

  // Fetch execution details
  fetchExecution: async (id) => {
    set({ isLoading: true, error: null });
    try {
      const response = await api.executions.get(id);
      set({ currentExecution: response.data, isLoading: false });
    } catch (error: any) {
      set({ error: error.message, isLoading: false });
    }
  },
}));