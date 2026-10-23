import subprocess
import sys

USER = {"username": "maria", "email": "maria@example.com", "password": "Abcdef12"}


def test_initial_concurrent_construction_in_fresh_process():
    script = """
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier, local, settrace
import inspect
from app.facade import FacadeSingletonController
assert FacadeSingletonController._instance is None
barrier = Barrier(16)
lines, first_line = inspect.getsourcelines(FacadeSingletonController.__new__)
lock_line = first_line + next(i for i, line in enumerate(lines) if "with cls._lock:" in line)
state = local()
def trace(frame, event, arg):
    if (event == "line" and frame.f_code is FacadeSingletonController.__new__.__code__
        and frame.f_lineno == lock_line and not getattr(state, "arrived", False)):
        state.arrived = True
        barrier.wait(timeout=10)
    return trace
# Força todas as primeiras chamadas a passar pela checagem externa antes da trava.
settrace(trace)
def obtain(index):
    return (FacadeSingletonController() if index % 2 else FacadeSingletonController.get_instance())
with ThreadPoolExecutor(max_workers=16) as executor:
    instances = list(executor.map(obtain, range(16)))
assert len({id(instance) for instance in instances}) == 1
assert instances[0] is FacadeSingletonController.get_instance()
assert vars(instances[0]) == {}
"""
    result = subprocess.run(
        [sys.executable, "-c", script], capture_output=True, text=True, timeout=30
    )
    assert result.returncode == 0, result.stderr
