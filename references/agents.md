# Evaluating Agents and Integrating Your Own

Harbor supports evaluating various agents and allows you to integrate your own custom agents.

## Supported Agents

Harbor comes with pre-integrated support for popular CLI agents:

- **oracle** - Pre-written reference solutions
- **claude-code** - Anthropic's Claude Code
- **codex** - OpenAI's Codex CLI
- **terminus** - Terminus agent
- **openhands** - OpenHands agent

## Running with Built-in Agents

### Basic Usage

```bash
# Run with a specific agent
harbor run -d terminal-bench@2.0 -a claude-code

# Specify model
harbor run -d terminal-bench@2.0 -a claude-code -m anthropic/claude-opus-4-1

# Run multiple concurrent trials
harbor run -d terminal-bench@2.0 -a claude-code -n 4
```

### Using Cloud Environments

```bash
# Run on Daytona
export DAYTONA_API_KEY="<your-key>"
export ANTHROPIC_API_KEY="<your-key>"
harbor run -d terminal-bench@2.0 -a claude-code --env daytona -n 100
```

## Integrating Your Own Agent

### Method 1: Command-Line Agent

If your agent can be installed in a container and run via command line, you can use it directly:

```bash
harbor run -d terminal-bench@2.0 -a "your-agent-command" -m "model-name"
```

### Method 2: Custom Agent Class

For more complex integrations, create a custom agent class:

```python
from harbor.agents import BaseAgent

class MyAgent(BaseAgent):
    def __init__(self, model_name: str, **kwargs):
        self.model_name = model_name
        self.kwargs = kwargs
    
    def run(self, instruction: str, environment: Environment) -> ActionResult:
        # Implement your agent logic here
        pass
    
    def supports(self, environment: Environment) -> bool:
        # Return True if your agent supports this environment
        pass
```

### Method 3: Adapter Development

For full control, create a Harbor adapter:

```bash
# Initialize a new adapter
harbor adapters init my-agent

# Or with specific arguments
harbor adapters init my-agent --name "My Custom Agent"
```

## Agent Configuration in Jobs

When running jobs, specify agents in the YAML configuration:

```yaml
agents:
  - name: claude-code
    model_name: anthropic/claude-3-opus-20240229
    override_timeout_sec: 600
  
  - name: custom-agent
    import_path: my_package.my_agent
    model_name: openai/gpt-4
    kwargs:
      custom_option: value
```

## Evaluating Custom Agents

1. **Test locally first**: Run with oracle to verify task is solvable
2. **Iterative development**: Start with simple tasks, then scale up
3. **Compare baselines**: Compare against established agents like claude-code
4. **Collect metrics**: Use reward.json for multi-metric evaluation

## Best Practices

- **Timeout management**: Set appropriate timeouts for your agent
- **Environment compatibility**: Ensure your agent works in the container environment
- **Error handling**: Handle failures gracefully and return appropriate rewards
- **Logging**: Use the logging system for debugging

## Viewing Available Agents

```bash
harbor run --help
```

This shows all supported agents and their configuration options.
