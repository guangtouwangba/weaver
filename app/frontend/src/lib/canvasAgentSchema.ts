/**
 * Canvas Agent Schema - JSON Schema definitions for LLM function calling
 * 
 * Defines the schema for AI agents to generate canvas commands.
 * Compatible with OpenAI function calling format.
 */

// ============================================================================
// OpenAI Function Calling Format
// ============================================================================

export interface FunctionDefinition {
  name: string;
  description: string;
  parameters: {
    type: 'object';
    properties: Record<string, PropertyDefinition>;
    required?: string[];
  };
}

interface PropertyDefinition {
  type: 'string' | 'number' | 'boolean' | 'array' | 'object';
  description: string;
  enum?: string[];
  items?: PropertyDefinition;
  properties?: Record<string, PropertyDefinition>;
}

// ============================================================================
// Canvas Action Functions
// ============================================================================

export const canvasActionFunctions: FunctionDefinition[] = [
  // -------------------------------------------------------------------------
  // Node Functions
  // -------------------------------------------------------------------------
  {
    name: 'canvas_add_node',
    description: 'Add a new node to the canvas. Use this to create sticky notes, ideas, or any content on the whiteboard.',
    parameters: {
      type: 'object',
      properties: {
        content: {
          type: 'string',
          description: 'The text content of the node',
        },
        title: {
          type: 'string',
          description: 'Optional title for the node',
        },
        type: {
          type: 'string',
          description: 'Type of node to create',
          enum: ['sticky', 'default', 'insight'],
        },
        x: {
          type: 'number',
          description: 'X position on canvas (optional, defaults to viewport center)',
        },
        y: {
          type: 'number',
          description: 'Y position on canvas (optional, defaults to viewport center)',
        },
        color: {
          type: 'string',
          description: 'Node color (optional). Use hex colors like #fef3c7 for yellow',
        },
      },
      required: ['content'],
    },
  },
  
  {
    name: 'canvas_delete_node',
    description: 'Delete a node from the canvas by its ID.',
    parameters: {
      type: 'object',
      properties: {
        nodeId: {
          type: 'string',
          description: 'The ID of the node to delete',
        },
      },
      required: ['nodeId'],
    },
  },
  
  {
    name: 'canvas_update_node',
    description: 'Update the content or properties of an existing node.',
    parameters: {
      type: 'object',
      properties: {
        nodeId: {
          type: 'string',
          description: 'The ID of the node to update',
        },
        content: {
          type: 'string',
          description: 'New content for the node',
        },
        title: {
          type: 'string',
          description: 'New title for the node',
        },
      },
      required: ['nodeId'],
    },
  },

  // -------------------------------------------------------------------------
  // Edge/Connection Functions
  // -------------------------------------------------------------------------
  {
    name: 'canvas_connect_nodes',
    description: 'Create a connection (edge) between two nodes to show their relationship.',
    parameters: {
      type: 'object',
      properties: {
        sourceNodeId: {
          type: 'string',
          description: 'The ID of the source node',
        },
        targetNodeId: {
          type: 'string',
          description: 'The ID of the target node',
        },
        label: {
          type: 'string',
          description: 'Label for the connection describing the relationship',
        },
        relationType: {
          type: 'string',
          description: 'Type of relationship',
          enum: ['related', 'leads_to', 'contradicts', 'supports', 'causes', 'custom'],
        },
      },
      required: ['sourceNodeId', 'targetNodeId'],
    },
  },
  
  {
    name: 'canvas_disconnect_nodes',
    description: 'Remove a connection between two nodes.',
    parameters: {
      type: 'object',
      properties: {
        edgeId: {
          type: 'string',
          description: 'The ID of the edge to remove',
        },
      },
      required: ['edgeId'],
    },
  },

  // -------------------------------------------------------------------------
  // Viewport Functions
  // -------------------------------------------------------------------------
  {
    name: 'canvas_zoom',
    description: 'Adjust the canvas zoom level.',
    parameters: {
      type: 'object',
      properties: {
        action: {
          type: 'string',
          description: 'Zoom action to perform',
          enum: ['in', 'out', 'fit', 'reset'],
        },
        level: {
          type: 'number',
          description: 'Specific zoom level (0.1 to 5.0). Only used if action is not provided.',
        },
      },
    },
  },

  // -------------------------------------------------------------------------
  // Generation Functions
  // -------------------------------------------------------------------------
  {
    name: 'canvas_generate',
    description: 'Generate content from the uploaded documents and place it on the canvas.',
    parameters: {
      type: 'object',
      properties: {
        type: {
          type: 'string',
          description: 'Type of content to generate',
          enum: ['mindmap', 'summary', 'flashcards', 'action_list'],
        },
      },
      required: ['type'],
    },
  },

  // -------------------------------------------------------------------------
  // Synthesis Functions
  // -------------------------------------------------------------------------
  {
    name: 'canvas_synthesize',
    description: 'Synthesize multiple nodes into a new insight. Combines ideas from selected nodes.',
    parameters: {
      type: 'object',
      properties: {
        nodeIds: {
          type: 'array',
          description: 'Array of node IDs to synthesize',
          items: { type: 'string', description: 'Node ID' },
        },
        mode: {
          type: 'string',
          description: 'Synthesis mode',
          enum: ['connect', 'inspire', 'debate'],
        },
      },
      required: ['nodeIds', 'mode'],
    },
  },
];

// ============================================================================
// Function Call to Slash Command Conversion
// ============================================================================

interface FunctionCallResult {
  name: string;
  arguments: Record<string, unknown>;
}

/**
 * Convert an AI function call to a slash command string
 */
export function functionCallToSlashCommand(call: FunctionCallResult): string {
  const { name, arguments: args } = call;

  switch (name) {
    case 'canvas_add_node': {
      const content = args.content as string;
      const parts = [`/add-node "${content}"`];
      if (args.type) parts.push(`--type ${args.type}`);
      if (args.x !== undefined && args.y !== undefined) {
        parts.push(`--at ${args.x},${args.y}`);
      }
      if (args.color) parts.push(`--color ${args.color}`);
      return parts.join(' ');
    }

    case 'canvas_delete_node':
      return `/delete ${args.nodeId}`;

    case 'canvas_update_node': {
      const parts = [`/update ${args.nodeId}`];
      if (args.content) parts.push(`--content "${args.content}"`);
      if (args.title) parts.push(`--title "${args.title}"`);
      return parts.join(' ');
    }

    case 'canvas_connect_nodes': {
      const parts = [`/connect ${args.sourceNodeId} ${args.targetNodeId}`];
      if (args.label) parts.push(`--label "${args.label}"`);
      if (args.relationType) parts.push(`--type ${args.relationType}`);
      return parts.join(' ');
    }

    case 'canvas_disconnect_nodes':
      return `/disconnect ${args.edgeId}`;

    case 'canvas_zoom': {
      if (args.action) return `/zoom ${args.action}`;
      if (args.level) return `/zoom ${args.level}`;
      return '/zoom fit';
    }

    case 'canvas_generate':
      return `/generate ${args.type}`;

    case 'canvas_synthesize':
      return `/synthesize ${(args.nodeIds as string[]).join(' ')} --mode ${args.mode}`;

    default:
      return `# Unknown function: ${name}`;
  }
}

// ============================================================================
// System Prompt for Canvas Agent
// ============================================================================

export const CANVAS_AGENT_SYSTEM_PROMPT = `You are a canvas assistant that helps users organize their thoughts on a visual whiteboard.

When users ask you to manipulate the canvas, you can:
- Add nodes: Create sticky notes with ideas, insights, or notes
- Connect nodes: Draw relationships between ideas
- Generate content: Create mindmaps, summaries, or flashcards from documents
- Organize: Help arrange and synthesize ideas

When responding with canvas actions, output them as slash commands that the user can review and execute:

Available commands:
- /add-node "content" [--type sticky|default|insight] [--at x,y] [--color COLOR]
- /delete NODE_ID
- /update NODE_ID --content "text" | --title "text"
- /connect SOURCE TARGET [--label "text"] [--type related|leads_to|contradicts|supports]
- /disconnect EDGE_ID
- /zoom in|out|fit|LEVEL
- /generate mindmap|summary|flashcards|action_list
- /synthesize NODE_IDS --mode connect|inspire|debate

Example responses:
- "I'll add a note for that idea: \`/add-node \"Key insight about X\"\`"
- "Let me connect those concepts: \`/connect node-1 node-2 --label \"leads to\"\`"
- "I can generate a mindmap: \`/generate mindmap\`"

Always explain what the command will do before showing it, so the user understands the action.`;

// ============================================================================
// Export for OpenAI API
// ============================================================================

export const openAITools = canvasActionFunctions.map(fn => ({
  type: 'function' as const,
  function: fn,
}));

