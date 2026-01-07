/**
 * Command Parser - Converts slash commands to CanvasAction objects
 * 
 * Supports commands like:
 *   /add-node "My Idea" --type sticky --at 100,200
 *   /connect node-1 node-2 --label "leads to"
 *   /zoom 150%
 */

import { CanvasAction } from './canvasActions';

// ============================================================================
// Types
// ============================================================================

export interface CommandDefinition {
  name: string;
  aliases: string[];
  description: string;
  usage: string;
  examples: string[];
  parse: (args: string[], flags: Record<string, string>) => CanvasAction | null;
}

export interface ParseResult {
  success: boolean;
  action?: CanvasAction;
  error?: string;
  suggestions?: string[];
}

// ============================================================================
// Argument Parsing Utilities
// ============================================================================

/**
 * Parse a command string into command name, args, and flags
 * Example: `/add-node "My Note" --type sticky --at 100,200`
 * Returns: { command: 'add-node', args: ['My Note'], flags: { type: 'sticky', at: '100,200' } }
 */
export function tokenize(input: string): {
  command: string;
  args: string[];
  flags: Record<string, string>;
} {
  const trimmed = input.trim();
  
  if (!trimmed.startsWith('/')) {
    return { command: '', args: [], flags: {} };
  }
  
  // Remove leading slash
  const withoutSlash = trimmed.slice(1);
  
  // Tokenize respecting quoted strings
  const tokens: string[] = [];
  let current = '';
  let inQuotes = false;
  let quoteChar = '';
  
  for (let i = 0; i < withoutSlash.length; i++) {
    const char = withoutSlash[i];
    
    if ((char === '"' || char === "'") && !inQuotes) {
      inQuotes = true;
      quoteChar = char;
    } else if (char === quoteChar && inQuotes) {
      inQuotes = false;
      quoteChar = '';
    } else if (char === ' ' && !inQuotes) {
      if (current) {
        tokens.push(current);
        current = '';
      }
    } else {
      current += char;
    }
  }
  
  if (current) {
    tokens.push(current);
  }
  
  if (tokens.length === 0) {
    return { command: '', args: [], flags: {} };
  }
  
  const command = tokens[0].toLowerCase();
  const args: string[] = [];
  const flags: Record<string, string> = {};
  
  let i = 1;
  while (i < tokens.length) {
    const token = tokens[i];
    
    if (token.startsWith('--')) {
      const flagName = token.slice(2);
      const nextToken = tokens[i + 1];
      
      if (nextToken && !nextToken.startsWith('-')) {
        flags[flagName] = nextToken;
        i += 2;
      } else {
        flags[flagName] = 'true';
        i++;
      }
    } else if (token.startsWith('-') && token.length === 2) {
      // Short flags like -t, -a
      const flagName = token.slice(1);
      const nextToken = tokens[i + 1];
      
      if (nextToken && !nextToken.startsWith('-')) {
        flags[flagName] = nextToken;
        i += 2;
      } else {
        flags[flagName] = 'true';
        i++;
      }
    } else {
      args.push(token);
      i++;
    }
  }
  
  return { command, args, flags };
}

/**
 * Parse position string like "100,200" to { x, y }
 */
function parsePosition(posStr: string): { x: number; y: number } | null {
  const parts = posStr.split(',').map(s => parseFloat(s.trim()));
  if (parts.length !== 2 || parts.some(isNaN)) {
    return null;
  }
  return { x: parts[0], y: parts[1] };
}

// ============================================================================
// Command Registry
// ============================================================================

export const commands: CommandDefinition[] = [
  // -------------------------------------------------------------------------
  // Node Commands
  // -------------------------------------------------------------------------
  {
    name: 'add-node',
    aliases: ['add', 'new', 'create'],
    description: 'Create a new node on the canvas',
    usage: '/add-node "content" [--type TYPE] [--at X,Y] [--color COLOR]',
    examples: [
      '/add-node "My Idea"',
      '/add-node "Note" --type sticky --at 100,200',
      '/add-node "Task" --color yellow',
    ],
    parse: (args, flags) => {
      const content = args[0] || 'New Note';
      const position = flags.at ? parsePosition(flags.at) : null;
      
      return {
        type: 'addNode',
        payload: {
          content,
          title: content.slice(0, 50),
          type: flags.type || flags.t || 'sticky',
          color: flags.color || flags.c,
          ...(position && { x: position.x, y: position.y }),
        },
      };
    },
  },
  
  {
    name: 'delete',
    aliases: ['remove', 'del', 'rm'],
    description: 'Delete a node or selected nodes',
    usage: '/delete NODE_ID | selected',
    examples: [
      '/delete node-123',
      '/delete selected',
    ],
    parse: (args) => {
      if (args[0] === 'selected') {
        // Would need to get selection from context - return selectAll for now
        return { type: 'deleteNodes', payload: { nodeIds: [] } };
      }
      
      if (args.length === 1) {
        return { type: 'deleteNode', payload: { nodeId: args[0] } };
      }
      
      return { type: 'deleteNodes', payload: { nodeIds: args } };
    },
  },
  
  {
    name: 'update',
    aliases: ['edit', 'set'],
    description: 'Update node properties',
    usage: '/update NODE_ID --content "text" | --title "text"',
    examples: [
      '/update node-123 --content "New content"',
      '/update node-123 --title "New Title"',
    ],
    parse: (args, flags) => {
      const nodeId = args[0];
      if (!nodeId) return null;
      
      const updates: Record<string, string> = {};
      if (flags.content) updates.content = flags.content;
      if (flags.title) updates.title = flags.title;
      if (flags.color) updates.color = flags.color;
      
      return {
        type: 'updateNode',
        payload: { nodeId, updates },
      };
    },
  },
  
  {
    name: 'move',
    aliases: [],
    description: 'Move a node to a new position',
    usage: '/move NODE_ID --to X,Y',
    examples: [
      '/move node-123 --to 500,300',
    ],
    parse: (args, flags) => {
      const nodeId = args[0];
      const position = flags.to ? parsePosition(flags.to) : null;
      
      if (!nodeId || !position) return null;
      
      return {
        type: 'moveNode',
        payload: { nodeId, x: position.x, y: position.y },
      };
    },
  },
  
  // -------------------------------------------------------------------------
  // Edge Commands
  // -------------------------------------------------------------------------
  {
    name: 'connect',
    aliases: ['link', 'edge'],
    description: 'Create a connection between two nodes',
    usage: '/connect SOURCE TARGET [--label TEXT] [--type TYPE]',
    examples: [
      '/connect node-1 node-2',
      '/connect node-1 node-2 --label "leads to"',
      '/connect node-1 node-2 --type contradicts',
    ],
    parse: (args, flags) => {
      const source = args[0];
      const target = args[1];
      
      if (!source || !target) return null;
      
      return {
        type: 'addEdge',
        payload: {
          source,
          target,
          label: flags.label || flags.l,
          relationType: flags.type || flags.t,
        },
      };
    },
  },
  
  {
    name: 'disconnect',
    aliases: ['unlink'],
    description: 'Remove a connection',
    usage: '/disconnect EDGE_ID | SOURCE TARGET',
    examples: [
      '/disconnect edge-123',
      '/disconnect node-1 node-2',
    ],
    parse: (args) => {
      if (args.length === 1) {
        return { type: 'deleteEdge', payload: { edgeId: args[0] } };
      }
      // If two args, we'd need to find the edge by source/target
      // For now, just support edge ID
      return null;
    },
  },
  
  // -------------------------------------------------------------------------
  // Selection Commands
  // -------------------------------------------------------------------------
  {
    name: 'select',
    aliases: ['sel'],
    description: 'Select nodes',
    usage: '/select NODE_IDS... | all | none',
    examples: [
      '/select node-1 node-2',
      '/select all',
      '/select none',
    ],
    parse: (args) => {
      if (args[0] === 'all') {
        return { type: 'selectAll', payload: {} };
      }
      if (args[0] === 'none') {
        return { type: 'clearSelection', payload: {} };
      }
      return { type: 'selectNodes', payload: { nodeIds: args } };
    },
  },
  
  // -------------------------------------------------------------------------
  // Viewport Commands
  // -------------------------------------------------------------------------
  {
    name: 'zoom',
    aliases: ['z'],
    description: 'Adjust viewport zoom',
    usage: '/zoom LEVEL | in | out | fit',
    examples: [
      '/zoom 150%',
      '/zoom 1.5',
      '/zoom in',
      '/zoom out',
      '/zoom fit',
    ],
    parse: (args) => {
      const arg = args[0]?.toLowerCase();
      
      if (arg === 'in') {
        return { type: 'zoomIn', payload: {} };
      }
      if (arg === 'out') {
        return { type: 'zoomOut', payload: {} };
      }
      if (arg === 'fit') {
        return { type: 'fitToContent', payload: {} };
      }
      
      // Parse as percentage or decimal
      let scale = parseFloat(arg?.replace('%', '') || '1');
      if (arg?.includes('%')) {
        scale = scale / 100;
      }
      
      if (isNaN(scale)) return null;
      
      return { type: 'zoomTo', payload: { scale } };
    },
  },
  
  {
    name: 'pan',
    aliases: ['goto'],
    description: 'Pan viewport to position',
    usage: '/pan X,Y | to NODE_ID',
    examples: [
      '/pan 500,300',
      '/pan to node-123',
    ],
    parse: (args, flags) => {
      if (flags.to || args[0] === 'to') {
        // Pan to node - would need to look up node position
        // For now, just return null
        return null;
      }
      
      const position = parsePosition(args[0] || '');
      if (!position) return null;
      
      return { type: 'panTo', payload: position };
    },
  },
  
  {
    name: 'fit',
    aliases: ['fit-view', 'fitview'],
    description: 'Fit all content in view',
    usage: '/fit',
    examples: ['/fit'],
    parse: () => {
      return { type: 'fitToContent', payload: {} };
    },
  },
  
  // -------------------------------------------------------------------------
  // Generation Commands
  // -------------------------------------------------------------------------
  {
    name: 'generate',
    aliases: ['gen'],
    description: 'Generate content from documents',
    usage: '/generate TYPE [--at X,Y]',
    examples: [
      '/generate mindmap',
      '/generate summary',
      '/generate summary --at 100,200',
    ],
    parse: (args, flags) => {
      const contentType = args[0] as 'mindmap' | 'summary' | 'flashcards' | 'action_list' | 'article';
      if (!contentType) return null;
      
      const position = flags.at ? parsePosition(flags.at) : undefined;
      
      return {
        type: 'generateContent',
        payload: { contentType, position },
      };
    },
  },
  
  {
    name: 'synthesize',
    aliases: ['synth', 'combine'],
    description: 'Synthesize selected nodes',
    usage: '/synthesize selected --mode MODE',
    examples: [
      '/synthesize selected --mode connect',
      '/synthesize selected --mode inspire',
      '/synthesize selected --mode debate',
    ],
    parse: (args, flags) => {
      const mode = (flags.mode || flags.m || 'connect') as 'connect' | 'inspire' | 'debate';
      
      // Would need to get selected nodes from context
      return {
        type: 'synthesizeNodes',
        payload: { nodeIds: [], mode },
      };
    },
  },
  
  // -------------------------------------------------------------------------
  // Help Command
  // -------------------------------------------------------------------------
  {
    name: 'help',
    aliases: ['h', '?'],
    description: 'Show help information',
    usage: '/help [COMMAND]',
    examples: [
      '/help',
      '/help add-node',
    ],
    parse: () => {
      // Help doesn't produce an action - handled separately
      return null;
    },
  },
];

// ============================================================================
// Command Lookup
// ============================================================================

/**
 * Find a command by name or alias
 */
export function findCommand(name: string): CommandDefinition | null {
  const lowerName = name.toLowerCase();
  return commands.find(
    cmd => cmd.name === lowerName || cmd.aliases.includes(lowerName)
  ) || null;
}

/**
 * Get all command names and aliases for autocomplete
 */
export function getAllCommandNames(): string[] {
  const names: string[] = [];
  for (const cmd of commands) {
    names.push(cmd.name);
    names.push(...cmd.aliases);
  }
  return names.sort();
}

/**
 * Filter commands by prefix for autocomplete
 */
export function filterCommands(prefix: string): CommandDefinition[] {
  const lowerPrefix = prefix.toLowerCase();
  return commands.filter(
    cmd => cmd.name.startsWith(lowerPrefix) ||
           cmd.aliases.some(a => a.startsWith(lowerPrefix))
  );
}

// ============================================================================
// Main Parser
// ============================================================================

/**
 * Parse a slash command string into a CanvasAction
 */
export function parseCommand(input: string): ParseResult {
  const { command, args, flags } = tokenize(input);
  
  if (!command) {
    return {
      success: false,
      error: 'Invalid command format. Commands start with /',
    };
  }
  
  const cmdDef = findCommand(command);
  
  if (!cmdDef) {
    const similar = filterCommands(command.slice(0, 2));
    return {
      success: false,
      error: `Unknown command: /${command}`,
      suggestions: similar.map(c => `/${c.name}`),
    };
  }
  
  // Special handling for help command
  if (cmdDef.name === 'help') {
    const helpTarget = args[0];
    if (helpTarget) {
      const targetCmd = findCommand(helpTarget);
      if (targetCmd) {
        return {
          success: true,
          action: undefined, // No action, just help display
          error: `**/${targetCmd.name}**\n${targetCmd.description}\n\nUsage: \`${targetCmd.usage}\`\n\nExamples:\n${targetCmd.examples.map(e => `  ${e}`).join('\n')}`,
        };
      }
    }
    // General help
    const helpText = commands
      .filter(c => c.name !== 'help')
      .map(c => `  /${c.name} - ${c.description}`)
      .join('\n');
    return {
      success: true,
      action: undefined,
      error: `Available commands:\n${helpText}\n\nType /help COMMAND for details.`,
    };
  }
  
  const action = cmdDef.parse(args, flags);
  
  if (!action) {
    return {
      success: false,
      error: `Invalid arguments for /${cmdDef.name}\n\nUsage: ${cmdDef.usage}`,
    };
  }
  
  return {
    success: true,
    action,
  };
}

/**
 * Check if a string looks like it might be a command
 */
export function isCommand(input: string): boolean {
  return input.trim().startsWith('/');
}

/**
 * Get help text for a specific command
 */
export function getCommandHelp(commandName: string): string | null {
  const cmd = findCommand(commandName);
  if (!cmd) return null;
  
  return [
    `**/${cmd.name}**`,
    cmd.description,
    '',
    `Usage: \`${cmd.usage}\``,
    '',
    'Examples:',
    ...cmd.examples.map(e => `  ${e}`),
  ].join('\n');
}

