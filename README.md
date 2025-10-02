# Log-Os: A Self-Bootstrapping Reflective Language

Log-Os is an experimental programming language and environment built on the principle of **reflection** and **bootstrapping**. The ultimate goal is to create an intelligent system that can understand, analyze, and rewrite its own code to evolve and improve.

This repository contains the initial seed, `Logos-0`, a minimal LISP-like interpreter written in Python, designed to be just powerful enough to start the self-improvement loop.

## Vision

The long-term vision for Log-Os is to evolve it into a hybrid probabilistic, causal modeling language that integrates concepts from category theory, the free energy principle, and algebraic topology to reason about and build complex software systems.

## Logos-0: The Seed

The initial version is a simple interpreter for an S-expression based language. Its core feature is **homoiconicity**: the code is represented by the language's own data structures (nested lists), making metaprogramming trivial.

### Core Features
- LISP-like syntax (S-expressions).
- A simple, recursive `evaluate` interpreter written in Python.
- Reflective capabilities: `(read-source)` and `(write-source)` to allow a Log-Os program to manipulate its own source code.

## Getting Started

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/your-username/log-os.git
    cd log-os
    ```

2.  **Setup virtual environment and install dependencies:**
    ```bash
    python -m venv venv
    source venv/bin/activate
    pip install -e .[dev]
    ```

3.  **Run the tests:**
    ```bash
    pytest
    ```

## The Bootstrapping Plan

1.  **Phase 0 (Current):** Build a stable `Logos-0` interpreter in Python.
2.  **Phase 1:** Use `Logos-0` to write simple refactoring and analysis tools for its own code (e.g., `bootstrap/refactor.l0`).
3.  **Phase 2:** Use these tools to help design and implement a static type system for the next version, `Logos-1`.
4.  **Phase 3 and beyond:** Continue this evolutionary cycle, adding features like probabilistic types, a JIT compiler, and eventually rewriting the interpreter itself in Log-Os.

## Project Structure

-   `/core`: The Python source code for the `Logos-0` interpreter.
-   `/bootstrap`: The first Log-Os (`.l0`) programs designed to analyze and modify the system.
-   `/tests`: Unit tests for the Python core.

---
*This project is a journey into the fundamental principles of computation, intelligence, and self-organization. Join the exploration.*