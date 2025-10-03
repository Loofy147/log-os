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
    git clone https://github.com/username/log-os.git
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

## Roadmap & Vision

This project is more than just a language; it's a long-term research exploration into computational intelligence and self-improving systems. We have a formal, multi-phase plan to guide our development from a simple interpreter to a fully reflective, self-aware system.

**[Read the full project roadmap in ROADMAP.md](ROADMAP.md)**

## Project Structure

-   `/core`: The Python source code for the `Logos-0` interpreter.
-   `/tests`: Unit tests for the Python core.

---
*This project is a journey into the fundamental principles of computation, intelligence, and self-organization. Join the exploration.*