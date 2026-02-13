# Core Concepts

Core concepts and terminology in Harbor

Harbor has the following core concepts:

## Task

A task is a single instruction, container environment, and test script. Tasks are used to evaluate agents and models. A task is implemented as a directory of files in the Harbor task format.

See [Task Structure](task-structure.md) for details on creating tasks.

## Dataset

A dataset is a collection of tasks. Datasets are used to evaluate agents and models. Usually, a dataset corresponds to a benchmark (e.g. Terminal-Bench, SWE-Bench Verified, etc.). Datasets can optionally be distributed via the Harbor registry.

```bash
# List available datasets
harbor datasets list
```

## Agent

An agent is a program that completes tasks. Agents are defined by implementing the `BaseAgent` or `BaseInstalledAgent` interfaces.

See [Agents](agents.md) for details on supported agents and how to integrate your own.

## Environment

Environments in Harbor are containers, typically defined as Docker images using a `Dockerfile`. The `BaseEnvironment` interface provides a unified interface for interacting with environments.

Many cloud container runtimes are already supported out of the box, including:
- **Daytona** - Cloud development environments
- **Modal** - Serverless computing platform
- **E2B** - AI-powered sandbox environments

Other container runtimes can be supported by implementing the `BaseEnvironment` interface.

## Trial

A trial is an agent's attempt at completing a task. Trials can be configured using the `TrialConfig` class.

Essentially, a trial is a rollout that produces a reward.

```bash
# Run a single trial
harbor trials start -p examples/tasks/hello-world
```

## Job

A job is a collection of trials. Jobs are used to evaluate agents and models. A job can consist of multiple datasets, agents, tasks, and models. Jobs can be configured using the `JobConfig` class.

Once you define your `job.yaml` or `job.json` file, you can run it using:

```bash
harbor run -c "<path/to/job.yaml>"
```

Alternatively, you can create an adhoc job by configuring the `harbor run` flags.

Under the hood, a job generates a bunch of `TrialConfig` objects and runs them in parallel.

## Summary

- **Task**: Single instruction + environment + test = one evaluation unit
- **Dataset**: Collection of tasks (e.g., Terminal-Bench)
- **Agent**: Program that tries to complete tasks
- **Environment**: Container where the agent runs
- **Trial**: One attempt by an agent on one task
- **Job**: Collection of trials across multiple tasks/agents/models
