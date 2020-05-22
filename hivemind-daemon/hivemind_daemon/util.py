from typing import Any

from hivemind_daemon import errors


def truncate_str(obj: Any, maxlength: int) -> str:
    # assume maxlength >= 3
    s = None
    try:
        s = str(obj)
    except errors.HivemindException:
        raise
    except Exception:
        try:
            s = repr(obj)
        except errors.HivemindException:
            raise
        except Exception:
            s = f'Unrepresentable object @{id(s)}'
            
    if len(s) > maxlength:
        s = s[:maxlength - 3] + '...'
    
    return s
