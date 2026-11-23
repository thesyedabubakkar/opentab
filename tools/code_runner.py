import io
import sys
import traceback
from typing import Any, Dict

async def run_python_code(code: str) -> Dict[str, Any]:
    """Executes a short Python snippet in an isolated context and captures output."""
    old_stdout = sys.stdout
    old_stderr = sys.stderr
    redirected_out = sys.stdout = io.StringIO()
    redirected_err = sys.stderr = io.StringIO()

    safe_globals = {
        "__builtins__": {
            "print": print,
            "len": len,
            "range": range,
            "int": int,
            "float": float,
            "str": str,
            "bool": bool,
            "list": list,
            "dict": dict,
            "set": set,
            "tuple": tuple,
            "sum": sum,
            "min": min,
            "max": max,
            "sorted": sorted,
            "abs": abs,
            "round": round,
            "math": __import__("math"),
            "datetime": __import__("datetime"),
            "json": __import__("json"),
            "re": __import__("re"),
        }
    }
    local_vars: Dict[str, Any] = {}

    try:
        exec(code, safe_globals, local_vars)
        output = redirected_out.getvalue()
        err_output = redirected_err.getvalue()
        return {
            "status": "success",
            "stdout": output,
            "stderr": err_output,
            "result": local_vars.get("result", None)
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "traceback": traceback.format_exc()
        }
    finally:
        sys.stdout = old_stdout
        sys.stderr = old_stderr

CODE_RUNNER_SCHEMA = {
    "type": "function",
    "function": {
        "name": "run_python_code",
        "description": "Executes Python code for complex math, data calculations, date arithmetic, or format conversions.",
        "parameters": {
            "type": "object",
            "properties": {
                "code": {
                    "type": "string",
                    "description": "Python source code string. Use 'print(...)' or assign to 'result' to return outputs."
                }
            },
            "required": ["code"]
        }
    }
}
