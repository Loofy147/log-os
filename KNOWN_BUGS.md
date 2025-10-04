# Known Bugs in Log-Os Interpreter

This document tracks known, deep-seated bugs in the core Log-Os interpreter. These are issues that were discovered during feature development but were deemed too complex to fix immediately without derailing the primary mission. They are documented here to be addressed in a future, focused "Interpreter Hardening" phase.

---

### Conditional Evaluation Bug in `error` / `if`

-   **Symptom:** An `(error ...)` form called from within the `else` clause of an `(if ...)` statement does not reliably raise an exception that can be caught by the test framework or other error-handling logic. This was discovered while testing the `defmulti` macro's error path for a missing method. The test `test_multimethods_l0_error_on_no_method` would fail with `DID NOT RAISE`, even though the logic correctly entered the `else` block containing the `(error ...)` call.

-   **Root Cause (Suspected):** The issue is likely a deep bug in how environments or continuations are managed during the evaluation of nested special forms. When the `if` form is evaluated and takes the `else` branch, the context required for the `error` primitive to correctly throw its exception appears to be lost or corrupted.

-   **Workaround:** The `defmulti` macro in `stdlib/multimethods.l0` has been modified to return a special, quoted symbol (`'*%no-method-found%*`) on failure instead of calling `(error ...)`. The corresponding Python test has been updated to check for this specific symbol, which validates that the error-detection path is being taken without triggering the underlying interpreter bug.

-   **Resolution:** Requires a dedicated debugging and fixing session focused on the interpreter core. A minimal test case that reproduces the error without involving the `defmulti` macro should be created to isolate and resolve the issue. Once fixed, the workaround should be removed.