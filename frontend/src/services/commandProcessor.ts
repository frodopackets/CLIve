export interface CommandResult {
  output?: string;
  error?: string;
  type: 'success' | 'error' | 'info';
}

export class CommandProcessor {
  private commands: Map<string, (args: string[]) => CommandResult> = new Map();

  constructor() {
    this.registerBuiltinCommands();
  }

  private registerBuiltinCommands() {
    this.commands.set('help', this.helpCommand.bind(this));
    this.commands.set('clear', this.clearCommand.bind(this));
    this.commands.set('history', this.historyCommand.bind(this));
    this.commands.set('version', this.versionCommand.bind(this));
    this.commands.set('status', this.statusCommand.bind(this));
  }

  public processCommand(input: string): CommandResult {
    const trimmed = input.trim();
    if (!trimmed) {
      return { type: 'info' };
    }

    const parts = trimmed.split(/\s+/);
    const command = parts[0].toLowerCase();
    const args = parts.slice(1);

    const handler = this.commands.get(command);
    if (handler) {
      return handler(args);
    }

    // If not a built-in command, it should be sent to the AI
    return {
      type: 'info',
      output: `Sending to AI: ${input}`,
    };
  }

  private helpCommand(_args: string[]): CommandResult {
    const helpText = `
Available Commands:
  help              Show this help message
  clear             Clear the terminal screen
  history           Show command history
  version           Show application version
  status            Show connection status
  
AI Commands:
  Any other input will be sent to the AI assistant for processing.
  
Examples:
  What is the weather in Birmingham?
  Tell me about machine learning
  Help me write a Python function
    `.trim();

    return {
      type: 'info',
      output: helpText,
    };
  }

  private clearCommand(_args: string[]): CommandResult {
    return {
      type: 'success',
      output: 'CLEAR_SCREEN', // Special command for terminal to clear
    };
  }

  private historyCommand(_args: string[]): CommandResult {
    // This would be implemented with actual history data
    return {
      type: 'info',
      output: 'Command history will be displayed here...',
    };
  }

  private versionCommand(_args: string[]): CommandResult {
    return {
      type: 'info',
      output: 'AI Assistant CLI v1.0.0',
    };
  }

  private statusCommand(_args: string[]): CommandResult {
    return {
      type: 'info',
      output: 'Status: Ready to process commands',
    };
  }

  public registerCommand(name: string, handler: (args: string[]) => CommandResult) {
    this.commands.set(name.toLowerCase(), handler);
  }

  public getAvailableCommands(): string[] {
    return Array.from(this.commands.keys()).sort();
  }
}

export const commandProcessor = new CommandProcessor();