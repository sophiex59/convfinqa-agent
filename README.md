# ConvFinQA Agent

LLM-driven conversational QA agent for financial documents using the ConvFinQA dataset.

## Setup

### Prerequisites
- Python 3.12+
- [Poetry](https://python-poetry.org/docs/#installation)
- Docker (optional)

### Local Development

```bash
# Install dependencies
poetry install

# Copy environment file and add your API key
cp .env.example .env

# Run the CLI
poetry run convfinqa --help
```

### Docker

```bash
# Build and run
docker-compose up --build agent

# Development shell
docker-compose run --rm dev
```

## Project Structure

```
├── src/
│   ├── agents/       # LangGraph agent definitions
│   ├── tools/        # Agent tools (calculator, lookups)
│   ├── core/         # LLM client, schemas, config
│   ├── evaluation/   # Metrics & evaluation
│   └── cli/          # Typer CLI
├── data/             # ConvFinQA dataset
└── tests/
```

## Usage

```bash
# Chat with a specific record
poetry run convfinqa chat <record_id>

# Evaluate on dev set
poetry run convfinqa evaluate --split dev

# Run tests
poetry run pytest
```
