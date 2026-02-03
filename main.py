import os
import sys
import json
import re
import ast
import datetime
import textwrap
import requests
from typing import Optional, Dict, List, Any

from bs4 import BeautifulSoup
from openai import OpenAI
from rich.prompt import Prompt
from rich.console import Console

API_KEY_ENV_VAR = "OPENROUTER_API_KEY"
CURRENT_MODEL = "google/gemini-3-flash-preview"

SYSTEM_PROMPT = """
You are "XfeaturesANTI-AI", a strict forensic code auditor. Determine authorship: Human vs. AI.

### CRITICAL RULES:
1. IGNORE MODERN BUNDLERS: 
   - <link rel="modulepreload">, _next/static, vite chunks are NORMAL.
   - Tailwind CSS usage is standard.

2. TRUE AI SIGNATURES:
   - Context Amnesia: Loading bootstrap.min.js or jquery.js TWICE.
   - Russian Doll Styling: Huge <style> blocks inserted inside div or body.
   - Hallucinations: Selectors like select * { !important }.
   - Mock Data: Hardcoded JS arrays like const reviews = [...] in source.
   - Comments: Verbose comments like .

3. VERDICT LOGIC:
   - Compiled React/Vue/Next.js -> HUMAN / FRAMEWORK (Score < 20%).
   - Messy HTML with scripts in random places -> AI GENERATED (Score > 80%).
   - Minified/Obfuscated -> ENTERPRISE (Score < 5%).

Output ONLY valid JSON matching this schema:
{
    "structure": [ {"severity": "HIGH|MEDIUM", "title": "...", "location": "...", "evidence": "...", "analysis": "...", "probability": 0-100} ],
    "css": [],
    "logic": [],
    "verdict": {
        "total_prob": (0-100),
        "model": "Human / Framework / GPT-4o / Claude",
        "integrity": "PROFESSIONAL / SUSPICIOUS",
        "style": "Modern Framework / Minified / AI Spaghetti",
        "recommendation": "Advice."
    }
}
"""

console = Console()


class ReportRenderer:
    def __init__(self):
        self._buffer: List[str] = []

    def log(self, text: str = "") -> None:
        print(text)
        self._buffer.append(text)

    def _wrap_text(self, text: str, indent: int = 12, width: int = 80) -> str:
        if not text:
            return ""
        wrapper = textwrap.TextWrapper(width=width, initial_indent="", subsequent_indent=" " * indent)
        return wrapper.fill(str(text))

    def print_header(self, url: str) -> None:
        ts = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        self.log("XfeaturesANTI-AI-Tool v5.3 -- SCAN REPORT")
        self.log("=" * 77)
        self.log(f"TARGET FILE:    {url}")
        self.log(f"SCAN MODE:      DEEP FORENSIC / ARCHITECTURAL ANALYSIS")
        self.log(f"TIMESTAMP:      {ts}")
        self.log(f"STATUS:         FINISHED")
        self.log("=" * 77 + "\n")

    def print_section(self, title: str, findings: List[Dict[str, Any]]) -> None:
        self.log(f"[{title}]...")
        if not findings:
            self.log(f"> [INFO] No specific {title.lower()} anomalies detected.\n")
            return

        for item in findings:
            severity = item.get('severity', 'MEDIUM').upper()
            title_text = item.get('title', 'Unknown Issue').upper()

            self.log(f"> [{severity}] {title_text}")
            self.log(f"  Location: {item.get('location', 'Unknown')}")

            evidence = self._wrap_text(item.get('evidence', ''))
            self.log(f"  Evidence: {evidence}")

            analysis = self._wrap_text(item.get('analysis', ''))
            self.log(f"  Analysis: {analysis}")

            self.log(f"  AI-Probability: {item.get('probability', '50')}%\n")

    def print_verdict(self, stats: Dict[str, Any]) -> None:
        self.log("=" * 77)
        self.log("FINAL VERDICT")
        self.log("=" * 77)
        self.log(f"OVERALL AI-GENERATION PROBABILITY:  {stats.get('total_prob', 0)}%")
        self.log(f"LIKELY AUTHOR MODEL:                {stats.get('model', 'Unknown')}")
        self.log(f"CODE INTEGRITY:                     {stats.get('integrity', 'Unknown')}")
        self.log(f"ARCHITECTURAL STYLE:                \"{stats.get('style', 'Unknown')}\"")
        self.log()

        rec = self._wrap_text(stats.get('recommendation', ''), indent=32)
        self.log(f"RECOMMENDATION:                 {rec}")
        self.log("=" * 77)
        self.log("END OF LOG\n")

    def save_to_file(self, filename: str) -> None:
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write('\n'.join(self._buffer))
            console.print(
                f"\n[bold green][SUCCESS][/bold green] Full report saved to: [underline]{filename}[/underline]")
        except OSError as e:
            console.print(f"\n[bold red][ERROR][/bold red] Could not save file: {e}")


class CodeAuditor:
    def __init__(self, url: str, api_key: str):
        self.url = url
        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=api_key,
            default_headers={
                "HTTP-Referer": "https://github.com/ai-detective",
                "X-Title": "Xfeatures Code Auditor"
            }
        )

    def fetch_source(self) -> Optional[str]:
        try:
            console.print(f"[*] Connecting to target: [cyan]{self.url}[/cyan] ... ", end="")
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8'
            }
            resp = requests.get(self.url, headers=headers, timeout=20)

            if resp.status_code != 200:
                console.print(f"[bold red]FAILED[/bold red] (Status: {resp.status_code})")
                return None

            console.print("[bold green]OK[/bold green]")
            return resp.text
        except requests.RequestException as e:
            console.print(f"\n[bold red][NETWORK ERROR][/bold red] {e}")
            return None

    def analyze(self, raw_html: str) -> Optional[str]:
        console.print(f"[*] Sending payload to Neural Network ([magenta]{CURRENT_MODEL}[/magenta])... ", end="")

        soup = BeautifulSoup(raw_html, 'html.parser')

        for tag in soup(['svg', 'path']):
            tag.decompose()
        for img in soup.find_all('img'):
            if img.get('src') and 'data:image' in img.get('src'):
                img['src'] = '[base64-skipped]'

        html_str = str(soup)
        if len(html_str) > 60000:
            source_snippet = html_str[:30000] + "\n\n...[SNIPPED MIDDLE CONTENT]...\n\n" + html_str[-20000:]
        else:
            source_snippet = html_str

        try:
            completion = self.client.chat.completions.create(
                model=CURRENT_MODEL,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": f"Analyze this source code:\n\n{source_snippet}"}
                ],
                temperature=0.1,
                seed=42,
                top_p=0.1
            )
            console.print("[bold green]DONE[/bold green]")
            return completion.choices[0].message.content

        except Exception as e:
            console.print(f"\n[bold red][API ERROR][/bold red] {e}")
            return None

    @staticmethod
    def parse_ai_response(response_text: str) -> Optional[Dict[str, Any]]:
        if not response_text:
            return None

        match = re.search(r"\{[\s\S]*\}", response_text)
        clean_payload = match.group(0) if match else response_text

        try:
            return json.loads(clean_payload)
        except json.JSONDecodeError:
            pass

        try:
            py_payload = clean_payload.replace("true", "True") \
                .replace("false", "False") \
                .replace("null", "None")
            return ast.literal_eval(py_payload)
        except (ValueError, SyntaxError):
            console.print(f"\n[bold red][PARSING ERROR][/bold red] Could not interpret AI response.")
            return None


def main():
    api_key = os.getenv(API_KEY_ENV_VAR)
    if not api_key:
        console.print("[bold yellow]OpenRouter API Key not found in environment.[/bold yellow]")
        api_key = Prompt.ask("Enter OpenRouter API Key", password=True)

    if not api_key:
        console.print("[bold red]API Key is required to proceed. Exiting.[/bold red]")
        sys.exit(1)

    target_url = Prompt.ask("\n[bold cyan]Target URL[/bold cyan] (e.g. example.com)").strip()
    if not target_url.startswith('http'):
        target_url = 'https://' + target_url

    auditor = CodeAuditor(target_url, api_key)
    source_code = auditor.fetch_source()

    if not source_code:
        return

    ai_raw_response = auditor.analyze(source_code)
    report_data = CodeAuditor.parse_ai_response(ai_raw_response)

    if report_data:
        renderer = ReportRenderer()
        renderer.print_header(target_url)
        renderer.print_section("SCANNING STRUCTURE", report_data.get('structure', []))
        renderer.print_section("SCANNING CSS HEURISTICS", report_data.get('css', []))
        renderer.print_section("SCANNING LOGIC & JS", report_data.get('logic', []))
        renderer.print_verdict(report_data.get('verdict', {}))

        domain = target_url.split("//")[-1].split("/")[0].replace(".", "_")
        timestamp = datetime.datetime.now().strftime("%H-%M-%S")
        filename = f"scan_report_{domain}_{timestamp}.txt"
        renderer.save_to_file(filename)
    else:
        console.print("\n[bold red][FAILURE][/bold red] No valid report could be generated.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n[yellow]Scan aborted by user.[/yellow]")
        sys.exit(0)