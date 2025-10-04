# core/interpreter.py
"""
The evaluator, or interpreter, is the heart of Log-Os. It takes an
AST (Abstract Syntax Tree) and an environment, and computes the result
of the expression.
"""

from .types import Symbol, List, Macro
from .environment import Environment
from .errors import LogosEvaluationError, LogosError
from .parser import parse, parse_stream
from .types import List, Symbol


def expand_quasiquote(x, env, level):
    """
    Recursively expands a quasiquoted expression, handling nesting levels
    of unquote and unquote-splicing.
    """
    if not isinstance(x, List) or not x:
        return x

    op, *rest = x

    if op == Symbol('quasiquote'):
        return [Symbol('quasiquote')] + [expand_quasiquote(rest[0], env, level + 1)]

    if op == Symbol('unquote') or op == Symbol('unquote-splicing'):
        if level == 1:
            result = evaluate(rest[0], env)
            if op == Symbol('unquote-splicing'):
                if not isinstance(result, List):
                    raise LogosEvaluationError("unquote-splicing must be used with a list.")
                return [Symbol.SPLICE] + result
            return result
        else:
            return [op] + [expand_quasiquote(rest[0], env, level - 1)]

    processed_list = []
    for item in x:
        result = expand_quasiquote(item, env, level)
        if isinstance(result, List) and result and result[0] is Symbol.SPLICE:
            processed_list.extend(result[1:])
        else:
            processed_list.append(result)
    return processed_list


def evaluate(x, env: Environment):
    """
    Evaluates an expression in a given environment.
    """
    if isinstance(x, Symbol):
        try:
            # Use the find method to search the scope chain correctly.
            return env.find(x)[x]
        except NameError:
            raise LogosEvaluationError(f"Symbol '{x}' not found.")

    elif not isinstance(x, List):
        return x

    if not x:
        return []

    op, *args = x

    if op == 'quote':
        return args[0]

    elif op == 'quasiquote':
        return expand_quasiquote(args[0], env, level=1)

    elif op == 'if':
        if len(args) not in (2, 3):
            raise LogosEvaluationError(f"if form expects 2 or 3 arguments, but got {len(args)}")
        test_expr, conseq_expr, *alt_expr = args
        alt_expr = alt_expr[0] if alt_expr else None
        if evaluate(test_expr, env):
            return evaluate(conseq_expr, env)
        else:
            return evaluate(alt_expr, env) if alt_expr is not None else None

    elif op == 'defvar':
        (symbol, expr) = args
        # Find the global environment by traversing up the outer chain.
        global_env = env
        while global_env.outer is not None:
            global_env = global_env.outer

        # Only define the variable if it's not already in the global scope.
        if symbol not in global_env:
            value = evaluate(expr, env)
            global_env.define(symbol, value)

        # Return the value from the global scope.
        return global_env[symbol]

    elif op == 'defmacro':
        (name, params, *body) = args
        body_expr = body[0] if len(body) == 1 else [Symbol('begin')] + body
        macro = Macro(params, body_expr, env)
        env.define_macro(name, macro)
        return None

    elif op == 'set!':
        (symbol, expr) = args
        value = evaluate(expr, env)
        env.set(symbol, value)
        return value

    elif op == 'lambda':
        (params, *body) = args
        if not body:
            raise LogosEvaluationError("lambda form must have a body.")
        body_expr = body[0] if len(body) == 1 else [Symbol('begin')] + body
        rest_param = None
        fixed_params = params
        if Symbol('.') in params:
            dot_index = params.index(Symbol('.'))
            if dot_index != len(params) - 2:
                raise LogosEvaluationError("Syntax error: '.' in parameter list.")
            fixed_params = params[:dot_index]
            rest_param = params[dot_index + 1]

        def lambda_func(*arguments):
            local_env = Environment(outer=env)
            if rest_param:
                if len(arguments) < len(fixed_params):
                    raise LogosEvaluationError(f"Procedure expects at least {len(fixed_params)} arguments, got {len(arguments)}")
                local_env.update(zip(fixed_params, arguments))
                local_env.define(rest_param, list(arguments[len(fixed_params):]))
            else:
                if len(fixed_params) != len(arguments):
                    raise LogosEvaluationError(f"Procedure expects {len(fixed_params)} arguments, got {len(arguments)}")
                local_env.update(zip(fixed_params, arguments))
            return evaluate(body_expr, local_env)
        return lambda_func

    elif op == 'defun':
        (name, params, *body) = args
        # Skip docstring if present
        if isinstance(body[0], str) and not isinstance(body[0], Symbol):
            body = body[1:]
        body_expr = body[0] if len(body) == 1 else [Symbol('begin')] + body
        func = evaluate([Symbol('lambda'), params, body_expr], env)
        env.define(name, func)
        return func

    elif op == 'begin':
        result = None
        for expr in args:
            result = evaluate(expr, env)
        return result

    elif op == 'and':
        val = True
        for expr in args:
            val = evaluate(expr, env)
            if not val:
                return False
        return val

    elif op == 'or':
        val = False
        for expr in args:
            val = evaluate(expr, env)
            if val:
                return True
        return val

    elif op == 'load':
        (filepath_expr,) = args
        filepath = evaluate(filepath_expr, env)
        if not isinstance(filepath, str):
            raise LogosEvaluationError(f"load expected a string filepath, but got {type(filepath)}")
        try:
            with open(filepath) as f:
                source = f.read()
        except FileNotFoundError:
            raise LogosError(f"File not found: {filepath}")
        asts = parse_stream(source)
        result = None
        for ast in asts:
            result = evaluate(ast, env)
        return result

    elif op == 'hash-map':
        if len(args) % 2 != 0:
            raise LogosEvaluationError("hash-map requires an even number of arguments for key-value pairs.")
        hash_map = {}
        for i in range(0, len(args), 2):
            key = evaluate(args[i], env)
            value = evaluate(args[i+1], env)
            hash_map[key] = value
        return hash_map

    else:
        # Macro expansion
        if isinstance(op, Symbol):
            macro_env = env.find_macro(op)
            if macro_env:
                macro = macro_env.macros[op]

                # Create a temporary environment for macro expansion
                macro_expansion_env = Environment(outer=macro.env)

                # Bind macro arguments to parameters
                # Handle variadic macros
                params = macro.params
                if Symbol('.') in params:
                    dot_index = params.index(Symbol('.'))
                    fixed_params = params[:dot_index]
                    rest_param = params[dot_index + 1]
                    if len(args) < len(fixed_params):
                        raise LogosEvaluationError(f"Macro '{op}' expects at least {len(fixed_params)} arguments, got {len(args)}")
                    macro_expansion_env.update(zip(fixed_params, args))
                    macro_expansion_env.define(rest_param, list(args[len(fixed_params):]))
                else:
                    if len(params) != len(args):
                        raise LogosEvaluationError(f"Macro '{op}' expects {len(params)} arguments, but got {len(args)}")
                    macro_expansion_env.update(zip(params, args))

                # Evaluate the macro body in the temporary environment to get the expanded code
                expanded_ast = evaluate(macro.body, macro_expansion_env)

                # Evaluate the expanded code in the original environment
                return evaluate(expanded_ast, env)

        # Procedure call
        proc = evaluate(op, env)
        if not callable(proc):
            raise LogosEvaluationError(f"'{op}' is not a procedure.")

        evaluated_args = [evaluate(arg, env) for arg in args]
        try:
            return proc(*evaluated_args)
        except TypeError as e:
            raise LogosEvaluationError(f"Error calling procedure '{op}': {e}")