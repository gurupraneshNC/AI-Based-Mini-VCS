
from typing import Dict


class OfflineAssistant:
    def respond(self, message: str, context: Dict) -> str:
        msg = message.lower()

        if "security" in msg or "vulnerability" in msg:
            return (
                "⚠️ AI security scan requires an API key.\n\n"
                "General secure coding tips:\n"
                "• Validate all user input\n"
                "• Avoid hardcoded secrets\n"
                "• Use parameterized queries\n"
                "• Handle exceptions safely\n"
                "• Follow least privilege\n"
            )

        if "commit" in msg:
            return (
                "A commit saves a snapshot of your project.\n"
                "Steps:\n"
                "1. Add files\n"
                "2. Write a message\n"
                "3. Commit changes"
            )

        if not context.get("branch"):
            return (
                "No repository loaded.\n"
                "Click 'New Repo' or 'Open Repo' to begin."
            )

        return (
            "I’m your offline assistant.\n"
            "Configure AI for advanced analysis and security review."
        )
