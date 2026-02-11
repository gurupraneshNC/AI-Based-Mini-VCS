import threading
from pathlib import Path
from typing import Optional

import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk

from vcs_core import AIVersionControl
from ai_agent import AIAgent
from offline_assistant import OfflineAssistant


class VCSGui:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("AI Version Control System")
        self.root.geometry("1200x800")

        self.vcs: Optional[AIVersionControl] = None
        self.repo_path: Optional[Path] = None

        self.ai_agent: Optional[AIAgent] = None
        self.offline_assistant = OfflineAssistant()

        self.selected_review_file: Optional[Path] = None

        self._setup_style()
        self._create_menu()
        self._create_layout()
        self._update_status("Ready - No repository loaded")
        self._show_welcome_message()

    def _setup_style(self):
        ttk.Style().theme_use("clam")

    def _create_menu(self):
        menu = tk.Menu(self.root)
        self.root.config(menu=menu)

        repo = tk.Menu(menu, tearoff=0)
        menu.add_cascade(label="Repository", menu=repo)
        repo.add_command(label="Initialize New", command=self.init_repo)
        repo.add_command(label="Open Existing", command=self.open_repo)
        repo.add_command(label="Rollback to Commit", command=self.rollback_dialog)
        repo.add_separator()
        repo.add_command(label="Exit", command=self.root.quit)

        ai = tk.Menu(menu, tearoff=0)
        menu.add_cascade(label="AI", menu=ai)
        ai.add_command(label="Configure Gemini AI", command=self.configure_ai)

    def _create_layout(self):
        toolbar = ttk.Frame(self.root)
        toolbar.pack(fill=tk.X, padx=5, pady=5)

        ttk.Button(toolbar, text="New Repo", command=self.init_repo).pack(side=tk.LEFT, padx=3)
        ttk.Button(toolbar, text="Open Repo", command=self.open_repo).pack(side=tk.LEFT, padx=3)
        ttk.Button(toolbar, text="Add Files", command=self.add_files).pack(side=tk.LEFT, padx=3)
        ttk.Button(toolbar, text="Commit", command=self.commit_dialog).pack(side=tk.LEFT, padx=3)
        ttk.Button(toolbar, text="Refresh", command=self.refresh_all).pack(side=tk.LEFT, padx=3)

        ttk.Button(toolbar, text="Create Branch", command=self.create_branch_dialog).pack(side=tk.LEFT, padx=3)
        ttk.Button(toolbar, text="Switch Branch", command=self.switch_branch_dialog).pack(side=tk.LEFT, padx=3)

        ttk.Button(toolbar, text="Rollback", command=self.rollback_dialog).pack(side=tk.LEFT, padx=3)

        self.status = ttk.Label(self.root, text="")
        self.status.pack(anchor=tk.W, padx=10)

        paned = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True)

        left = ttk.Frame(paned)
        paned.add(left, weight=1)

        ttk.Label(left, text="Staging Area").pack(anchor=tk.W)
        self.staging = tk.Listbox(left)
        self.staging.pack(fill=tk.BOTH, expand=True)

        right = ttk.Notebook(paned)
        paned.add(right, weight=2)

        history_tab = ttk.Frame(right)
        right.add(history_tab, text="Commit History")

        self.history = ttk.Treeview(
            history_tab,
            columns=("id", "msg", "author", "time"),
            show="headings",
        )
        for col in ("id", "msg", "author", "time"):
            self.history.heading(col, text=col.upper())
            self.history.column(col, width=150)
        self.history.pack(fill=tk.BOTH, expand=True)

        chat_tab = ttk.Frame(right)
        right.add(chat_tab, text="AI Assistant")

        self.chat_display = scrolledtext.ScrolledText(chat_tab)
        self.chat_display.pack(fill=tk.BOTH, expand=True)

        chat_input = ttk.Frame(chat_tab)
        chat_input.pack(fill=tk.X)

        self.chat_entry = ttk.Entry(chat_input)
        self.chat_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.chat_entry.bind("<Return>", lambda e: self.send_ai_message())

        ttk.Button(chat_input, text="Send", command=self.send_ai_message).pack(side=tk.RIGHT)

        review_tab = ttk.Frame(right)
        right.add(review_tab, text="Code Security Review")

        ttk.Button(review_tab, text="Select Code File", command=self.select_code_file).pack()
        ttk.Button(review_tab, text="Run Security Scan", command=self.run_security_scan).pack()

        self.review_output = scrolledtext.ScrolledText(review_tab)
        self.review_output.pack(fill=tk.BOTH, expand=True)

    def _update_status(self, text):
        if not self.vcs:
            self.status.config(text="Status: No repository loaded")
            return

        branch = self.vcs.graph.current_branch
        head = self.vcs.graph.head

        self.status.config(
            text=f"Status: {text} | Repo: {self.repo_path.name} | Branch: {branch} | HEAD: {head}"
    )


    def _show_welcome_message(self):
        self.chat_display.insert(
            tk.END,
            "🤖 AI Version Control System\n\n"
            "• Branching\n"
            "• Rollback to commit\n"
            "• AI Security Review\n\n"
        )

    def init_repo(self):
        path = filedialog.askdirectory()
        if not path:
            return

        self.vcs = AIVersionControl(path)
        if not self.vcs.init():
            messagebox.showerror("Error", "Failed to initialize repository")
            return

        self.repo_path = Path(path)
        self.refresh_all()

    def open_repo(self):
        path = filedialog.askdirectory()
        if not path:
            return

        self.vcs = AIVersionControl.load(path)
        if not self.vcs:
            messagebox.showerror("Error", "Not a valid repository")
            return

        self.repo_path = Path(path)
        self.refresh_all()

    def add_files(self):
        if not self.vcs:
            return

        files = filedialog.askopenfilenames(initialdir=self.repo_path)
        for f in files:
            self.vcs.add(str(Path(f).relative_to(self.repo_path)))

        self.refresh_staging()

    def commit_dialog(self):
        if not self.vcs or self.vcs.staging.is_empty():
            messagebox.showwarning("Warning", "No files staged.")
            return

        win = tk.Toplevel(self.root)
        ttk.Label(win, text="Commit Message").pack()
        msg = scrolledtext.ScrolledText(win, height=5)
        msg.pack()

        def commit():
            self.vcs.commit(msg.get("1.0", tk.END).strip())
            win.destroy()
            self.refresh_all()

        ttk.Button(win, text="Commit", command=commit).pack()

    def rollback_dialog(self):
        if not self.vcs:
            messagebox.showwarning("Warning", "Open a repository first.")
            return

        win = tk.Toplevel(self.root)
        win.title("Rollback to Commit")
        win.geometry("500x300")

        ttk.Label(win, text="Select a commit to rollback to").pack(pady=5)

        lb = tk.Listbox(win)
        lb.pack(fill=tk.BOTH, expand=True, padx=10)

        commits = self.vcs.log(50)
        for c in commits:
            lb.insert(tk.END, f"{c['id']} | {c['message']}")

        def rollback():
            sel = lb.curselection()
            if not sel:
                return

            commit_id = commits[sel[0]]["id"]
            if not messagebox.askyesno(
                "Confirm Rollback",
                f"Rollback to commit {commit_id}?\nUncommitted changes will be lost.",
            ):
                return

            self.vcs.checkout(commit_id)

            self.refresh_all()
            win.destroy()

        ttk.Button(win, text="Rollback", command=rollback).pack(pady=10)

    def create_branch_dialog(self):
        if not self.vcs:
            return

        win = tk.Toplevel(self.root)
        ttk.Label(win, text="New Branch Name").pack()
        entry = ttk.Entry(win)
        entry.pack()

        def create():
            self.vcs.create_branch(entry.get().strip())
            win.destroy()
            self.refresh_all()

        ttk.Button(win, text="Create", command=create).pack()

    def switch_branch_dialog(self):
        if not self.vcs:
            return

        win = tk.Toplevel(self.root)
        ttk.Label(win, text="Select Branch").pack()

        lb = tk.Listbox(win)
        lb.pack(fill=tk.BOTH, expand=True)

        for b in self.vcs.branches():
            lb.insert(tk.END, b)

        def switch():
            sel = lb.curselection()
            if sel:
                self.vcs.checkout(lb.get(sel[0]))
                win.destroy()
                self.refresh_all()

        ttk.Button(win, text="Switch", command=switch).pack()

    def send_ai_message(self):
        text = self.chat_entry.get().strip()
        if not text:
            return

        self.chat_display.insert(tk.END, f"You: {text}\n")
        self.chat_entry.delete(0, tk.END)

        def respond():
            reply = (
                self.ai_agent.natural_language_command(text, {})["explanation"]
                if self.ai_agent
                else self.offline_assistant.respond(text, {})
            )
            self.chat_display.insert(tk.END, f"AI: {reply}\n\n")

        threading.Thread(target=respond, daemon=True).start()

    def configure_ai(self):
        win = tk.Toplevel(self.root)
        ttk.Label(win, text="Gemini API Key").pack()
        entry = ttk.Entry(win, show="*", width=40)
        entry.pack()

        def save():
            self.ai_agent = AIAgent(entry.get())
            win.destroy()

        ttk.Button(win, text="Save", command=save).pack()

    def select_code_file(self):
        file = filedialog.askopenfilename(initialdir=self.repo_path)
        if file:
            self.selected_review_file = Path(file)

    def run_security_scan(self):
        if not self.selected_review_file or not self.ai_agent:
            return

        code = self.selected_review_file.read_text(errors="ignore")
        result = self.ai_agent.review_code(code[:3000], str(self.selected_review_file))

        self.review_output.delete("1.0", tk.END)
        for issue in result["issues"]:
            self.review_output.insert(tk.END, f"- {issue}\n")

    def refresh_staging(self):
        self.staging.delete(0, tk.END)

        if not self.vcs or not self.vcs.staging.staged_files:
            self.staging.insert(tk.END, "— No files staged —")
            return

        for f in self.vcs.staging.staged_files:
            self.staging.insert(tk.END, f)

    def refresh_history(self):
        self.history.delete(*self.history.get_children())
        if not self.vcs:
            return

        for c in self.vcs.log(50):
            self.history.insert(
                "", tk.END,
                values=(c["id"], c["message"], c["author"], c["timestamp"])
            )

    def refresh_all(self):
        self.refresh_staging()
        self.refresh_history()

        if self.vcs:
            self._update_status("Repository loaded")
        else:
            self._update_status("No repository loaded")



def main():
    root = tk.Tk()
    VCSGui(root)
    root.mainloop()


if __name__ == "__main__":
    main()
