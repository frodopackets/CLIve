import { describe, it, expect, beforeEach } from 'vitest';
import { CommandProcessor } from '../commandProcessor';

describe('CommandProcessor', () => {
  let processor: CommandProcessor;

  beforeEach(() => {
    processor = new CommandProcessor();
  });

  it('processes help command', () => {
    const result = processor.processCommand('help');
    expect(result.type).toBe('info');
    expect(result.output).toContain('Available Commands');
    expect(result.output).toContain('help');
    expect(result.output).toContain('clear');
  });

  it('processes clear command', () => {
    const result = processor.processCommand('clear');
    expect(result.type).toBe('success');
    expect(result.output).toBe('CLEAR_SCREEN');
  });

  it('processes version command', () => {
    const result = processor.processCommand('version');
    expect(result.type).toBe('info');
    expect(result.output).toContain('AI Assistant CLI v1.0.0');
  });

  it('processes status command', () => {
    const result = processor.processCommand('status');
    expect(result.type).toBe('info');
    expect(result.output).toContain('Status: Ready');
  });

  it('handles unknown commands as AI input', () => {
    const result = processor.processCommand('tell me about AI');
    expect(result.type).toBe('info');
    expect(result.output).toContain('Sending to AI: tell me about AI');
  });

  it('handles empty input', () => {
    const result = processor.processCommand('');
    expect(result.type).toBe('info');
    expect(result.output).toBeUndefined();
  });

  it('handles whitespace-only input', () => {
    const result = processor.processCommand('   ');
    expect(result.type).toBe('info');
    expect(result.output).toBeUndefined();
  });

  it('is case insensitive for commands', () => {
    const result1 = processor.processCommand('HELP');
    const result2 = processor.processCommand('Help');
    const result3 = processor.processCommand('help');
    
    expect(result1.output).toBe(result2.output);
    expect(result2.output).toBe(result3.output);
  });

  it('can register custom commands', () => {
    processor.registerCommand('test', () => ({ type: 'success', output: 'Test command executed' }));
    
    const result = processor.processCommand('test');
    expect(result.type).toBe('success');
    expect(result.output).toBe('Test command executed');
  });

  it('returns available commands', () => {
    const commands = processor.getAvailableCommands();
    expect(commands).toContain('help');
    expect(commands).toContain('clear');
    expect(commands).toContain('version');
    expect(commands).toContain('status');
    expect(commands).toContain('history');
  });
});