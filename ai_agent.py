
import json
import difflib
from typing import Dict, Optional

from google import genai


class AIAgent:
    def __init__(self, api_key: Optional[str] = None):
        if not api_key:
            raise ValueError("Gemini API key not provided")

        self.client = genai.Client(api_key=api_key)

        self.model_name = "gemini-3-flash-preview"

    def _call_ai(self, prompt: str) -> str:
        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt
            )

            if not response or not response.text:
                raise RuntimeError("Empty response from Gemini")

            return response.text.strip()

        except Exception as e:
            print("🔥 GEMINI API ERROR:", e)
            raise

    def generate_commit_message(self, diff: str) -> Dict[str, str]:
        prompt = f"""
You are an expert software engineer.

Generate a conventional commit message.

Rules:
- Return ONLY valid JSON
- No markdown
- No explanations

Changes:
{diff}

JSON:
{{
  "title": "short commit title",
  "description": "what and why",
  "risk_level": "low | medium | high"
}}
"""

        try:
            return self._extract_json(self._call_ai(prompt))
        except Exception:
            return {
                "title": "Update files",
                "description": "Multiple changes",
                "risk_level": "medium",
            }

    def review_code(self, diff: str, file_path: str) -> Dict:
        prompt = f"""
You are a senior security engineer performing a secure code review.

Analyze the following source code and identify:

- Security vulnerabilities
- Logic bugs
- Insecure coding patterns
- OWASP Top 10 risks
- Performance concerns

Then provide a security and code quality score.

SCORING RULES:
- Score must be an integer from 1 to 10
- 1 = Extremely insecure / critical flaws
- 5 = Moderate issues
- 10 = Secure, clean, production-ready
- Score must reflect security, structure, and reliability

STRICT OUTPUT RULES:
- Return ONLY valid JSON
- No markdown
- No explanations outside JSON
- "overall_quality" must be a number, not text

File: {file_path}

Code:
{diff}

JSON FORMAT:
{{
  "issues": ["list vulnerabilities or bugs"],
  "suggestions": ["recommended fixes"],
  "overall_quality": 8
}}
"""


        try:
            return self._extract_json(self._call_ai(prompt))
        except Exception as e:
            print("❌ SECURITY SCAN FAILED:", e)
            return {
                "issues": ["Unable to analyze code"],
                "suggestions": ["Check code manually"],
                "overall_quality": 5,
            }

    def natural_language_command(self, command: str, context: Dict) -> Dict:
        prompt = f"""
You are an intelligent assistant for a version control system.

User input:
{command}

Repository context:
{json.dumps(context, indent=2)}

Respond clearly and concisely.
"""

        try:
            return {
                "action": "chat",
                "explanation": self._call_ai(prompt),
            }
        except Exception:
            return {
                "action": "chat",
                "explanation": "AI unavailable at the moment.",
            }

    def _extract_json(self, text: str) -> Dict:
        text = text.strip()

        if "```" in text:
            text = text.split("```")[1].strip()

        start = text.find("{")
        end = text.rfind("}") + 1

        if start == -1 or end == -1:
            raise ValueError("No JSON found in Gemini response")

        return json.loads(text[start:end])


class DiffGenerator:
    @staticmethod
    def generate_diff(old: str, new: str, filename="file") -> str:
        return "".join(
            difflib.unified_diff(
                old.splitlines(True),
                new.splitlines(True),
                fromfile=f"a/{filename}",
                tofile=f"b/{filename}",
            )
        )
