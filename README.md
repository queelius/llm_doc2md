# llm-doc2md

Convert PDF, DOCX, TXT, or Markdown files to clean Markdown using a large language model via Ollama.

## Features

- Extract text from PDF, DOCX, TXT, and Markdown files.
- Chunk large documents and process with an LLM for structure preservation.
- Configurable chunk size, tail size, and prompt templates.
- Initialize and display configuration files easily.
- Progress bars and rich console output.

## Installation

Install from PyPI:

```bash
pip install llm-doc2md
```

Or install from source:

```bash
git clone https://github.com/queelius/llm-doc2md.git
cd llm-doc2md
pip install .
```

## Requirements

- Python 3.8+
- Ollama running locally (default API URL: `http://localhost:11434/api/generate`)
- Optional: OpenAI account (set `OPENAI_API_KEY` and `OPENAI_API_BASE` environment variables)
- Dependencies: `requests`, `rich`, `PyPDF2`, `docx2txt`

## Usage

Convert a document to Markdown:

```bash
llm-doc2md convert -i input.pdf -o output.md
```

Available options:

```text
  -i, --input           Path to the input file (.pdf, .docx, .txt, .md)  [required]
  -o, --output          Path to the output Markdown file (default: output.md)
  -m, --model           Ollama/OpenAI model name to use (default: llama3.2)
      --chunk-size      Chunk size in characters (default: 1000)
      --tail-size       Tail size from previous chunk for context (default: 200)
      --prompt-template Custom prompt template with {context} and {current}
      --api-url         Ollama API URL (default: http://localhost:11434/api/generate)
      --openai-api-key  OpenAI API key (or set OPENAI_API_KEY env)
      --openai-api-base OpenAI API base URL (or set OPENAI_API_BASE env)
      --config          Path to JSON config file to override options
```  

Generate a default configuration file:

```bash
llm-doc2md init-config --output ~/.llm_doc2md.json
```

Show the current configuration:

```bash
llm-doc2md show-config
```

## Configuration File

The JSON configuration file can override default options:

```json
{
    "model": "llama3.2",
    "chunk_size": 1000,
    "tail_size": 200,
    "prompt_template": "-- your custom template with {context} and {current} --",
    "api_url": "http://localhost:11434/api/generate",
    "openai_api_key": null,
    "openai_api_base": "https://api.openai.com/v1"
}
```

Save this as `~/.llm_doc2md.json` or specify with `--config`.

## Example

```bash
llm-doc2md convert -i document.docx -o document.md --model llama3.2
```

## Contributing

Contributions are welcome! Please open issues or submit pull requests.

## License

MIT License. See [LICENSE](LICENSE) for details.
