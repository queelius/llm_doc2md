from setuptools import setup, find_packages

setup(
    name="llm-doc2md",
    version="0.1.0",
    author="Alex Towell",
    author_email="lex@metafunctor.com",
    description="Convert PDF, DOCX, TXT, or Markdown files to clean Markdown using an LLM via Ollama.",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/queelius/llm-doc2md",
    packages=find_packages(),
    install_requires=[
        "requests",
        "rich",
        "PyPDF2",      # for PDF extraction
        "docx2txt",    # for DOCX extraction
    ],
    entry_points={
        "console_scripts": [
            "llm-doc2md=llm_doc2md.cli:main",
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
)
