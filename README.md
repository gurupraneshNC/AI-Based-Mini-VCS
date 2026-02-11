
# 🤖 AI-Based Mini VCS

![Python](https://img.shields.io/badge/Python-3.x-blue?style=for-the-badge&logo=python)
![GUI](https://img.shields.io/badge/GUI-Tkinter-green?style=for-the-badge)
![AI](https://img.shields.io/badge/AI-Google%20Gemini-orange?style=for-the-badge&logo=google)
![License](https://img.shields.io/badge/License-MIT-purple?style=for-the-badge)

**A next-generation Version Control System built from scratch, powered by Google Gemini to automate commit messages and secure your code.**

---

## 📖 Overview

**AI-Based Mini VCS** is a custom version control system that goes beyond standard file tracking. It implements a DAG-based commit history and content-addressable storage (similar to Git) but adds an intelligent layer: an AI agent that helps you write commit messages, reviews your code for security vulnerabilities, and answers questions about your repository.

## ✨ Key Features

### 🧠 AI-Powered Capabilities
* **Auto-Generate Commit Messages**: The AI analyzes your diffs and generates conventional commit messages with titles, descriptions, and risk levels.
* **Automated Security Reviews**: Perform deep scans on your code to identify OWASP risks, logic bugs, and vulnerabilities with a 1-10 security score.
* **Intelligent Chat Assistant**: A built-in chatbot that can explain repository context or general coding concepts.

### 🛠️ Core Version Control
* **DAG Architecture**: Robust commit history tracking using a Directed Acyclic Graph.
* **Smart Branching**: Create, switch, and manage branches for parallel development.
* **Time Travel**: Rollback to any previous commit state instantly.
* **Efficient Storage**: Uses SHA-1 content-addressable storage to deduplicate file content.

### 🖥️ Modern GUI
* **Visual History Tree**: View your entire commit log, authors, and timestamps in a clean tree structure.
* **Interactive Dashboard**: Dedicated tabs for Staging, History, Chat, and Security Reviews.
* **Offline Mode**: Includes a fallback assistant for basic help when the AI is disconnected.

---

## ⚙️ Tech Stack

* **Language**: Python 3.x
* **Interface**: Tkinter (Standard Python GUI)
* **AI Engine**: Google GenAI SDK (`gemini-3-flash-preview`)
* **Data Structure**: JSON & SHA-1 Hashing

---

## 🚀 Getting Started

### Prerequisites
* Python 3.8+
* Google Gemini API Key (Required for AI features)

### Installation

1.  **Clone the repository**
    ```bash
    git clone [https://github.com/yourusername/ai-based-mini-vcs.git](https://github.com/yourusername/ai-based-mini-vcs.git)
    cd ai-based-mini-vcs
    ```

2.  **Install Dependencies**
    ```bash
    pip install google-genai
    ```

3.  **Run the Application**
    ```bash
    python gui_app.py
    ```

---

## 🎮 Usage Guide

### 1. Setup
Launch the app and click **"New Repo"** to initialize a repository in your target folder. If you have an existing one, click **"Open Repo"**.

### 2. Configure AI
Navigate to `AI > Configure Gemini AI` in the menu bar and paste your API key. This unlocks the smart features.

### 3. Workflow
| Action | Description |
| :--- | :--- |
| **Stage** | Click `Add Files` to select files for tracking. |
| **Commit** | Click `Commit`. The AI can auto-fill the message based on your changes. |
| **Review** | Go to the `Code Security Review` tab, pick a file, and hit `Run Security Scan`. |
| **Branch** | Use `Create Branch` to start a new feature line. |

---

## 📂 Project Structure

```text
📦 ai-based-mini-vcs
 ┣ 📜 vcs_core.py          # Core logic (DAG, Commits, Storage)
 ┣ 📜 ai_agent.py          # AI integration (Gemini Client, Prompts)
 ┣ 📜 gui_app.py           # Tkinter Graphical User Interface
 ┣ 📜 offline_assistant.py # Fallback logic for offline mode
 ┗ 📜 LICENSE              # MIT License
