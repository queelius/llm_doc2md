#!/usr/bin/env python3
import argparse
import llm_doc2md.utils as utils

import os
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()

def main():
    parser = argparse.ArgumentParser(
        description="Convert documents (PDF, DOCX, TXT, MD) to clean Markdown using an LLM via Ollama.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    subparsers = parser.add_subparsers(dest="command", help="Subcommands")

    # Main conversion subcommand (default action)
    convert_parser = subparsers.add_parser("convert", help="Convert an input file to Markdown")
    convert_parser.add_argument("-i", "--input", required=True, help="Path to the input file (pdf, docx, txt, md)")
    convert_parser.add_argument("-o", "--output", default="output.md", help="Path to the output Markdown file")
    convert_parser.add_argument("-m", "--model", default="llama3.2", help="Model name to use (e.g., llama3.2)")
    convert_parser.add_argument("--chunk-size", type=int, default=1000, help="Chunk size in characters")
    convert_parser.add_argument("--tail-size", type=int, default=200, help="Tail size from previous chunk for context")
    convert_parser.add_argument("--prompt-template", type=str, default=None,
                        help="Prompt template with placeholders {context} and {current}")
    convert_parser.add_argument("--endpoint", default="http://localhost:11434/api", help="LLM endpoint base URL (Ollama API base or OpenAI compatible)")
    convert_parser.add_argument("--api-key", default=None, help="API key for OpenAI-compatible endpoints (or set OPENAI_API_KEY env)")
    convert_parser.add_argument("--config", type=str, default=None, help="Path to JSON config file to override options")

    # Subcommand to generate default config file
    config_parser = subparsers.add_parser("init-config", help="Generate a default configuration file")
    config_parser.add_argument("--output", type=str, default=utils.default_config_path(),
                               help=f"Path to write the default config file (default: {utils.default_config_path()})")

    # Subcommand to show the current config
    show_parser = subparsers.add_parser("show-config", help="Display the current configuration")
    show_parser.add_argument("--config", type=str, default=utils.default_config_path(),
                             help=f"Path to the config file (default: {utils.default_config_path()})")

    args = parser.parse_args()

    if args.command == "init-config":
        utils.generate_default_config(args.output)
        return

    if args.command == "show-config":
        utils.show_config(args.config)
        return

    # Default behavior: conversion
    if args.config:
        config_file = args.config
    else:
        config_file = utils.default_config_path()

    if os.path.exists(config_file):
        console.print(f"[blue]Loading configuration from:[/blue] {config_file}")
        config = utils.load_config(config_file)
        args.model = config.get("model", args.model)
        args.chunk_size = config.get("chunk_size", args.chunk_size)
        args.tail_size = config.get("tail_size", args.tail_size)
        if not args.prompt_template:
            args.prompt_template = config.get("prompt_template", "")
        args.endpoint = config.get("endpoint", config.get("api_url", args.endpoint))  # support old api_url key for migrations
        args.api_key  = config.get("api_key", args.api_key)

    utils.process_text_to_markdown(
        input_file=args.input,
        output_file=args.output,
        model=args.model,
        chunk_size=args.chunk_size,
        tail_size=args.tail_size,
        prompt_template=args.prompt_template,
        endpoint=args.endpoint,
        api_key=args.api_key
    )

if __name__ == '__main__':
    main()
