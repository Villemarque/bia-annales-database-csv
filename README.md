```py
def pretty(reps: str):
    return '\n'.join([f"{i//20 + 1}.{i % 20 + 1} {rep.lower()}" for (i, rep) in enumerate(reps)])
```