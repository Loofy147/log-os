# Log-Os: A Self-Bootstrapping Reflective Language

Log-Os is an experimental programming language and environment built on the principle of **reflection** and **bootstrapping**. The ultimate goal is to create an intelligent system that can understand, analyze, and rewrite its own code to evolve and improve.

This repository contains `Logos-0`, a powerful LISP-like interpreter written in Python, designed to be the foundation for a self-aware software system.

## Vision

The long-term vision for Log-Os is to evolve it into a hybrid probabilistic, causal modeling language that integrates concepts from category theory, the free energy principle, and algebraic topology to reason about and build complex software systems.

## Logos-0: The Core Interpreter

The current version is a surprisingly capable LISP dialect with a rich set of primitive operations. Its core feature is **homoiconicity**: the code is represented by the language's own data structures (nested lists), making metaprogramming trivial.

### Core Features
- **LISP-like Syntax:** S-expressions provide a simple, uniform structure for code and data.
- **Rich Primitives:** A robust set of built-in functions and special forms, including:
  - **Control Flow:** `if`, `and`, `or`, `while`.
  - **Variable Bindings:** `defvar` (global), `set!` (mutation), `let` (local).
  - **Data Structures:** Lists, Symbols, Strings, Numbers, and a full `hash-map` type.
  - **Metaprogramming:** `quote`, `eval` (implicitly via interpreter).
- **Reflective Capabilities:** The interpreter can interact with its own environment:
  - `(load "filepath")` provides a simple module system.
  - `(read-source "filepath")` parses a source file into an AST.
  - `(list-directory "path")` inspects the filesystem.

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

4.  **Start the REPL:**
    ```bash
    python repl.py
    ```

## The Bootstrapping Plan

The core interpreter is now stable and feature-rich. The next phase focuses on using these capabilities to build sophisticated analysis tools in Log-Os itself.

1.  **Phase 0 (Complete):** Build a stable and powerful `Logos-0` interpreter in Python.
2.  **Phase 1 (Current):** Use `Logos-0` to write a suite of static analysis tools for Log-Os code. This will involve creating a standard library (`stdlib/`) for analysis, starting with tools that can build a full call graph of a project.
3.  **Phase 2 and beyond:** Use these analysis tools to enable the system to reason about its own structure, complexity, and behavior, paving the way for automated refactoring, optimization, and eventually, self-compilation.

## Project Structure

-   `/core`: The Python source code for the `Logos-0` interpreter.
-   `/tests`: Unit tests for the Python core.

---
*This project is a journey into the fundamental principles of computation, intelligence, and self-organization. Join the exploration.*