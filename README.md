# 🕵️‍♂️ XfeaturesANTI-AI Tool

> **A deep forensic code auditor that distinguishes between Human Enterprise Code and AI Spaghetti.**

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)
[![Powered By](https://img.shields.io/badge/Powered%20By-OpenRouter-purple)](https://openrouter.ai/)

**XfeaturesANTI-AI** is a command-line tool that analyzes website source code to determine authorship probability (Human vs. AI). Unlike simple pattern matchers, it uses state-of-the-art LLMs (Llama 3.3 70B, Gemini Pro) via OpenRouter to perform a semantic audit of HTML, CSS, and JavaScript structure.

## 🚀 Features

* **Deep Forensic Analysis**: Scans for "Context Amnesia" (duplicate imports), "Russian Doll Styling" (styles in body), and logic hallucinations.
* **False Positive Protection**: Distinguishes between messy AI code and minified/obfuscated Enterprise code (Google, Amazon, React/Vite apps).
* **Detailed Reporting**: Generates a CLI dashboard and saves `.txt` reports with evidence logs.
* **Free to Use**: Configured to work with free tier models via OpenRouter (e.g., Llama 3.3, Gemini Flash).
* **Robust Parsing**: Handles unstructured LLM outputs using a hybrid JSON/AST parser.

## 🛠️ Installation

1.  **Clone the repository**
    ```bash
    git clone [https://github.com/XfeaturesGroup/XfeaturesAntiAITool.git](https://github.com/XfeaturesGroup/XfeaturesAntiAITool.git)
    cd XfeaturesANTI-AI-Tool
    ```

2.  **Install dependencies**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Configure API Key**
    Get a free key from [OpenRouter](https://openrouter.ai/).

    Create a `.env` file in the root directory:
    ```bash
    OPENROUTER_API_KEY=sk-or-v1-your-key-here
    ```

## 💻 Usage

Run the script and paste the target URL when prompted:

```bash
python main.py
```

The tool will scan the URL, analyze the architecture, and save a detailed report (e.g., `scan_report_domain_com.txt`) in the project folder.

## 🧠 How It Works

The tool fetches the source code, cleans it (removing SVGs/Base64), and sends a compressed context to an LLM with a strict **Forensic System Prompt**.

It looks for specific signatures:

1. **Context Amnesia**: Did the coder forget they already loaded Bootstrap in the `<head>`?
2. **Panic Fixes**: Are there `!important` selectors on `select *` elements?
3. **Mock Data**: Are there hardcoded review arrays in production code?
4. **Stylistic Fingerprints**: Overuse of `backdrop-filter` and specific gradient angles typical of default AI outputs.

## 🤝 Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

## 📝 License

[MIT](https://www.google.com/search?q=LICENSE)
