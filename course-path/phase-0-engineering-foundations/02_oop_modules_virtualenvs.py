"""
0.2 — OOP, Modules, Virtual Environments: the parts framework code uses.

Runnable: `python 02_oop_modules_virtualenvs.py`   (stdlib only)

What this proves practically:
  1. ABC refuses to instantiate a subclass that forgot a method — at
     construction time, not at 3am in production.
  2. A MUTABLE class attribute is SHARED by every instance. The classic bug.
  3. Forgetting super().__init__() silently loses parent attributes.
  4. __repr__ decides whether your logs are useful or useless.
  5. Attribute lookup walks instance -> class -> parent (the MRO).
"""

from abc import ABC, abstractmethod

SEP = "=" * 68


# ====================================================================== 1
class Tool(ABC):
    """Abstract base defining the contract every tool must satisfy.

    This is exactly the pattern LangChain uses for BaseTool (6.13): the
    error arrives when you try to build the object, not when an agent
    finally calls the missing method mid-run.
    """

    # CLASS attribute: shared by all instances unless shadowed.
    name: str = "unnamed"

    # MUTABLE class attribute — deliberately included to demonstrate the bug.
    call_log: list[str] = []

    def __init__(self, timeout: float = 10.0) -> None:
        # INSTANCE attribute: one per object.
        self.timeout = timeout

    @abstractmethod
    def run(self, query: str) -> str:
        """Subclasses MUST implement. No default on purpose."""

    def __repr__(self) -> str:
        return f"{type(self).__name__}(name={self.name!r}, timeout={self.timeout})"


class SQLTool(Tool):
    name = "sql_query"

    def __init__(self, dsn: str, timeout: float = 30.0) -> None:
        super().__init__(timeout=timeout)     # <- correct
        self.dsn = dsn

    def run(self, query: str) -> str:
        self.call_log.append(f"{self.name}:{query}")
        return f"[{self.dsn}] would execute: {query}"


class SearchTool(Tool):
    name = "web_search"

    def __init__(self, endpoint: str, timeout: float = 15.0) -> None:
        super().__init__(timeout=timeout)
        self.endpoint = endpoint

    def run(self, query: str) -> str:
        self.call_log.append(f"{self.name}:{query}")
        return f"[{self.endpoint}] would search: {query}"


class BrokenTool(Tool):
    """Deliberately forgets run(). Demonstrates the ABC guarantee."""
    name = "broken"


class ForgotSuper(Tool):
    """Deliberately skips super().__init__(). Demonstrates the bug."""
    name = "forgot_super"

    def __init__(self, dsn: str) -> None:
        # NO super().__init__() call — self.timeout never gets set.
        self.dsn = dsn

    def run(self, query: str) -> str:
        return "ok"


def demo_abc_contract() -> None:
    print(SEP)
    print("DEMO 1 — ABC refuses an incomplete subclass AT CONSTRUCTION")
    print(SEP)
    try:
        BrokenTool()
    except TypeError as e:
        print(f"  BrokenTool()  -> TypeError: {e}")
    print("  ^ Caught when building the object, NOT when an agent calls run().")

    ok = SQLTool(dsn="oracle://finance")
    print(f"  SQLTool(...)  -> {ok}          <- __repr__ fires here")


def demo_mutable_class_attribute() -> None:
    print(SEP)
    print("DEMO 2 — the classic bug: a MUTABLE class attribute is SHARED")
    print(SEP)

    a = SQLTool(dsn="oracle://a")
    b = SearchTool(endpoint="https://search")

    a.run("SELECT 1")
    b.run("langgraph docs")

    print(f"  a.call_log            : {a.call_log}")
    print(f"  b.call_log            : {b.call_log}")
    print(f"  same list object?     : {a.call_log is b.call_log}")
    print(f"  Tool.call_log         : {Tool.call_log}")
    print("  ^ ONE list shared by every instance AND the class itself.")
    print("    Fix: create it per-instance in __init__ (self.call_log = []).")


def demo_forgot_super() -> None:
    print(SEP)
    print("DEMO 3 — forgetting super().__init__() loses parent attributes")
    print(SEP)

    good = SQLTool(dsn="oracle://finance")
    bad = ForgotSuper(dsn="oracle://finance")

    print(f"  SQLTool.timeout       : {good.timeout}")
    try:
        print(bad.timeout)
    except AttributeError as e:
        print(f"  ForgotSuper.timeout   : AttributeError: {e}")
    print("  ^ The symptom appears FAR from the cause — some later line reads")
    print("    self.timeout and blows up, with nothing pointing at __init__.")


def demo_attribute_lookup() -> None:
    print(SEP)
    print("DEMO 4 — attribute lookup: instance -> class -> parent (the MRO)")
    print(SEP)

    t = SQLTool(dsn="oracle://finance")

    print(f"  t.dsn      -> {t.dsn!r:22} found on the INSTANCE")
    print(f"  t.name     -> {t.name!r:22} found on SQLTool (shadows Tool)")
    print(f"  Tool.name  -> {Tool.name!r:22} the parent's value, untouched")
    print(f"  MRO        : {[c.__name__ for c in type(t).__mro__]}")

    # Shadowing: assigning on the instance hides the class attribute.
    t.name = "instance_override"
    print(f"\n  after t.name = 'instance_override':")
    print(f"  t.name       -> {t.name!r}")
    print(f"  SQLTool.name -> {SQLTool.name!r}   <- class value UNCHANGED")


def demo_polymorphism() -> None:
    print(SEP)
    print("DEMO 5 — polymorphism: why agent frameworks take list[Tool]")
    print(SEP)

    def describe(t: Tool) -> str:
        # This function was written ONCE and works for every subclass, and
        # for subclasses that do not exist yet. That is the whole extension
        # mechanism behind tool registries in 6.13.
        return f"{t.name:<12} times out after {t.timeout}s"

    tools: list[Tool] = [
        SQLTool(dsn="oracle://finance"),
        SearchTool(endpoint="https://search"),
    ]
    for t in tools:
        print(f"  {describe(t)}")
    print(f"\n  all isinstance(Tool)? {all(isinstance(t, Tool) for t in tools)}")


def demo_repr_matters() -> None:
    print(SEP)
    print("DEMO 6 — __repr__ decides if a log line is useful")
    print(SEP)

    class NoRepr(Tool):
        name = "no_repr"
        def run(self, q: str) -> str: return "ok"
        # inherits Tool.__repr__? No — we shadow it to show the default.
        __repr__ = object.__repr__

    print(f"  with __repr__    : {SQLTool(dsn='oracle://finance')}")
    print(f"  without __repr__ : {NoRepr()}")
    print("  ^ The second tells you nothing when tracing an agent run (7.6).")


def main() -> None:
    demo_abc_contract()
    demo_mutable_class_attribute()
    demo_forgot_super()
    demo_attribute_lookup()
    demo_polymorphism()
    demo_repr_matters()
    print(SEP)


if __name__ == "__main__":
    main()
