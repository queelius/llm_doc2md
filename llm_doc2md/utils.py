import json
import os
import sys
import requests
from PyPDF2 import PdfReader
import docx2txt
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, TimeRemainingColumn

console = Console()


# --- File Reading Functions ---

def extract_text_from_pdf(file_path):
    text = ""
    with open(file_path, "rb") as f:
        reader = PdfReader(f)
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    return text

def extract_text_from_docx(file_path):
    return docx2txt.process(file_path)

def read_input_file(file_path):
    ext = os.path.splitext(file_path)[1].lower()
    if ext == ".pdf":
        console.print(f"[cyan]Reading PDF file:[/cyan] {file_path}")
        return extract_text_from_pdf(file_path)
    elif ext in (".docx", ".doc"):
        console.print(f"[cyan]Reading DOCX file:[/cyan] {file_path}")
        return extract_text_from_docx(file_path)
    elif ext in (".txt", ".md"):
        console.print(f"[cyan]Reading text file:[/cyan] {file_path}")
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    else:
        console.print(f"[red]Unsupported file format:[/red] {ext}")
        sys.exit(1)


# --- Chunking and Prompt-Building Functions ---

def split_into_chunks(text, chunk_size):
    """Split text into fixed-size chunks."""
    return [text[i:i + chunk_size] for i in range(0, len(text), chunk_size)]

def build_prompt_with_context(prev_tail, current_chunk, template):
    """
    Build a prompt using a template with two placeholders:
      {context} -> tail from previous chunk (for continuity)
      {current} -> the current segment to convert.
    """
    return template.format(
        context=prev_tail if prev_tail else "[No previous context]",
        current=current_chunk
    )

def create_prompts(text, chunk_size, tail_size, template):
    """
    Split text into chunks and build prompts.
    For each chunk (after the first), include the last 'tail_size' characters
    from the previous chunk as context.
    """
    raw_chunks = split_into_chunks(text, chunk_size)
    prompts = []
    for i, chunk in enumerate(raw_chunks):
        prev_tail = raw_chunks[i - 1][-tail_size:] if i > 0 else ""
        prompt = build_prompt_with_context(prev_tail, chunk, template)
        prompts.append(prompt)
    return prompts


# --- Ollama API Call Function ---

def call_ollama(prompt, model, base_url):
    """
    Call the Ollama API with the given prompt.
    Sends a POST request to the /api/generate endpoint with streaming disabled.
    """
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False
    }
    headers = {"Content-Type": "application/json"}
    response = requests.post(base_url, json=payload, headers=headers)
    if response.status_code != 200:
        raise Exception(f"Ollama API error {response.status_code}: {response.text}")
    result = response.json()
    if "response" in result:
        return result["response"]
    elif "message" in result and "content" in result["message"]:
        return result["message"]["content"]
    else:
        raise Exception("Unexpected API response format.")


def call_openai(prompt, model, endpoint, api_key):
    """
    Call OpenAI completion endpoint with the given prompt.
    """
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    data = {
        "model": model,
        "prompt": prompt,
        "max_tokens": 2048,
        "temperature": 0.7
    }
    response = requests.post(
        f"{endpoint}/v1/completions",
        headers=headers,
        json=data
    )
    if response.status_code != 200:
        raise Exception(f"OpenAI API error {response.status_code}: {response.text}")
    result = response.json()
    if "choices" in result and result["choices"]:
        return result["choices"][0].get("text", "")
    raise Exception("Unexpected OpenAI API response format.")


def call_llm(prompt, model, endpoint, api_key=None):
    """
    Unified call: use OpenAI if API key present, else fallback to Ollama.
    """
    key = api_key or os.getenv("OPENAI_API_KEY")
    if key:
        return call_openai(prompt, model, endpoint, key)
    # assume Ollama: append /generate if not already present
    url = endpoint if endpoint.rstrip('/').endswith('/generate') else f"{endpoint.rstrip('/')}/generate"
    return call_ollama(prompt, model, url)


# --- Main Processing Pipeline ---

def process_text_to_markdown(input_file, output_file, model, chunk_size, tail_size,
                             prompt_template, endpoint, api_key=None):
    text = read_input_file(input_file)
    prompts = create_prompts(text, chunk_size, tail_size, prompt_template)
    markdown_segments = []

    console.print(f"[green]Processing {len(prompts)} chunk(s) using model [bold]{model}[/bold]...[/green]")
    with Progress(
        SpinnerColumn(),
        BarColumn(bar_width=None),
        TextColumn("{task.completed}/{task.total} Chunks"),
        TimeRemainingColumn(),
        transient=True
    ) as progress:
        task = progress.add_task("Processing chunks...", total=len(prompts))
        for idx, prompt in enumerate(prompts, 1):
            try:
                md_output = call_llm(prompt, model, endpoint, api_key)
                markdown_segments.append(md_output)
            except Exception as e:
                error_msg = f"<!-- Error processing chunk {idx}: {e} -->"
                console.print(f"[red]Error processing chunk {idx}:[/red] {e}")
                markdown_segments.append(error_msg)
            progress.update(task, advance=1)

    final_markdown = "\n\n".join(markdown_segments)
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(final_markdown)
    console.print(f"[bold green]Conversion complete![/bold green] Markdown output written to [yellow]{output_file}[/yellow].")


# --- Configuration Loading and Default Config Generation ---

def load_config(config_path):
    """
    Load a JSON configuration file if provided.
    """
    if not os.path.exists(config_path):
        console.print(f"[red]Error:[/red] Config file '{config_path}' not found.")
        sys.exit(1)
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)

def default_config_path():
    """
    Return the default config file path in the user's home directory.
    """
    return os.path.expanduser("~/.llm_doc2md.json")

def generate_default_config(config_path):
    """
    Generate a default configuration file and write it to the specified path.
    """
    try:
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(get_default_config(), f, indent=4)
        console.print(f"[green]Default configuration file written to:[/green] {config_path}")
    except Exception as e:
        console.print(f"[red]Error writing config file:[/red] {e}")
        sys.exit(1)

def get_default_config() -> dict:
    """
    Retrieve a default configuration dict.
    """
    return {
        "model": "gemma3:4b",
        "chunk_size": 4000,
        "tail_size": 200,
        "prompt_template": (
            "The following text is extracted from a document and may contain artifacts such as broken lines, headers, and footers.\n\n"
            "IMPORTANT: The section labeled 'CONTEXT' is provided solely for continuity and should be ignored for conversion.\n"
            "Only the section labeled 'CURRENT SEGMENT' must be converted to clean Markdown, preserving structure such as headings, lists, and paragraphs.\n\n"
            "CONTEXT:\n{context}\n\nCURRENT SEGMENT:\n{current}\n\nMarkdown Output:"
        ),
        "endpoint": "http://localhost:11434/api",
        "api_key": None
    }

def get_config(config_path: str) -> dict:
    """
    Load the configuration file if it exists, otherwise return default values.
    """
    if os.path.exists(config_path):
        return load_config(config_path)
    elif os.path.exists(default_config_path()):
        console.print(f"[yellow]No config file found at {config_path}. Using default configuration at {default_config_path()}.[/yellow]")
        return get_config(default_config_path())
    else:
        console.print(f"[red]Error:[/red] No config file found at {config_path} or default location. Using default configuration.")
        return get_default_config()
    
def show_config(config_path):
    """
    Load and pretty-print the configuration file as JSON using Rich.
    If the file doesn't exist, use the default values.
    """
    if os.path.exists(config_path):
        config = load_config(config_path)
        console.print("[blue]Current Configuration:[/blue]")
    else:
        console.print(f"[yellow]No config file found at {config_path}. Using default configuration:[/yellow]")
        config = get_config(config_path)

    console.print_json(json.dumps(config, indent=4))
