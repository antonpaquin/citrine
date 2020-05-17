from typing import Any


def truncate_str(obj: Any, maxlength: int) -> str:
    # assume maxlength >= 3
    s = None
    try:
        s = str(obj)
    except Exception:
        try:
            s = repr(obj)
        except Exception:
            s = f'Unrepresentable object @{id(s)}'
            
    if len(s) > maxlength:
        s = s[:maxlength - 3] + '...'
    
    return s
