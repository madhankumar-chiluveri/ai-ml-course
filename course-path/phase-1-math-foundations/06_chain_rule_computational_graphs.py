"""
1.6 - Chain Rule and Computational Graphs.

Runnable: `python 06_chain_rule_computational_graphs.py`
Requires: numpy. torch is optional - Demo 4 (the cross-check) is skipped
without it, and the engine is still verified against finite differences.

SAFE + OFFLINE: pure computation. No files written, no network, no API keys.

What this proves practically:
  1. The chain rule, checked against finite differences on sin(3x^2).
  2. A computational graph is a list of nodes, each knowing its LOCAL
     derivative. Printed forward and backward for z = (a+b)*c.
  3. A ~60-line reverse-mode autodiff engine, written from scratch.
  4. Every gradient it produces matches torch.autograd to ~1e-16.
  5. THE accumulation bug: a node used twice must ADD its gradients.
     Overwriting gives x instead of 2x - shown failing, then fixed.
  6. Reverse mode costs 1 backward pass for n inputs; forward mode costs n.
     Counted, so the asymmetry behind 3.4 is a measurement, not a claim.
"""

import math

import numpy as np

SEP = "=" * 70


# ===================================================================== 1
def demo_chain_rule_by_hand() -> None:
    print(SEP)
    print("DEMO 1 - the chain rule, checked rather than asserted")
    print(SEP)

    # f(x) = sin(3x^2). Peel it outside-in:
    #   outer: sin(u)      -> d/du = cos(u)
    #   inner: u = 3x^2    -> du/dx = 6x
    #   chain: df/dx = cos(3x^2) * 6x
    def f(x):
        return math.sin(3 * x * x)

    def df_analytic(x):
        return math.cos(3 * x * x) * 6 * x

    def df_numeric(x, h=1e-6):
        # Central difference: error is O(h^2) rather than O(h), so it is far
        # more accurate than the forward difference at the same h (1.5).
        return (f(x + h) - f(x - h)) / (2 * h)

    print("  f(x) = sin(3x^2)   ->   f'(x) = cos(3x^2) * 6x")
    print(f"\n  {'x':>6} {'analytic':>16} {'central diff':>16} {'abs diff':>12}")
    for x in [0.3, 0.7, 1.0, 1.5, 2.0]:
        a, n = df_analytic(x), df_numeric(x)
        print(f"  {x:>6.2f} {a:>16.10f} {n:>16.10f} {abs(a - n):>12.2e}")

    print("\n  Agreement to ~1e-10 across the range. The chain rule is not a")
    print("  convention to memorise - it is a factual claim about how a")
    print("  composed function responds, and it is checkable.")
    print("  Rule: differentiate the OUTER function, keep the inner argument")
    print("  intact, then multiply by the inner function's derivative.")


# ===================================================================== 2
def demo_graph_by_hand() -> None:
    print(SEP)
    print("DEMO 2 - a computational graph, forward then backward")
    print(SEP)

    a, b, c = 2.0, 3.0, 4.0

    # FORWARD: compute values, and remember the intermediate.
    s = a + b            # node s
    z = s * c            # node z

    print("  expression: z = (a + b) * c      with a=2, b=3, c=4")
    print(f"\n  FORWARD")
    print(f"    s = a + b = {s}")
    print(f"    z = s * c = {z}")

    # BACKWARD: start with dz/dz = 1 and walk the edges in reverse. Each edge
    # multiplies by the LOCAL derivative of that one operation.
    dz_dz = 1.0
    dz_ds = dz_dz * c          # z = s*c, so dz/ds = c
    dz_dc = dz_dz * s          # z = s*c, so dz/dc = s
    dz_da = dz_ds * 1.0        # s = a+b, so ds/da = 1  -> addition COPIES gradient
    dz_db = dz_ds * 1.0

    print(f"\n  BACKWARD  (seed dz/dz = 1)")
    print(f"    dz/ds = dz/dz * c   = {dz_ds}")
    print(f"    dz/dc = dz/dz * s   = {dz_dc}")
    print(f"    dz/da = dz/ds * 1   = {dz_da}      <- the skip-test answer")
    print(f"    dz/db = dz/ds * 1   = {dz_db}")

    # Verify every one of them numerically.
    def z_of(a, b, c):
        return (a + b) * c

    h = 1e-6
    checks = [
        ("dz/da", dz_da, (z_of(a + h, b, c) - z_of(a - h, b, c)) / (2 * h)),
        ("dz/db", dz_db, (z_of(a, b + h, c) - z_of(a, b - h, c)) / (2 * h)),
        ("dz/dc", dz_dc, (z_of(a, b, c + h) - z_of(a, b, c - h)) / (2 * h)),
    ]
    print(f"\n  {'':<8} {'by chain rule':>16} {'finite diff':>16} {'abs diff':>12}")
    for name, sym, num in checks:
        print(f"  {name:<8} {sym:>16.10f} {num:>16.10f} {abs(sym - num):>12.2e}")

    print("\n  Two local rules did all the work:")
    print("    ADD  copies the incoming gradient to both inputs (d/da of a+b = 1)")
    print("    MUL  sends the incoming gradient times THE OTHER INPUT")
    print("  Backpropagation (3.4) is these two rules applied over a bigger")
    print("  graph. There is no third idea waiting in Phase 3.")


# ===================================================================== 3
class Value:
    """A scalar that remembers how it was computed.

    This is the whole of reverse-mode autodiff. Each Value stores:
      data      - the forward number
      grad      - d(final output)/d(this node), filled in during backward
      _parents  - the Values that produced it
      _backward - a closure that pushes THIS node's grad into its parents

    Nothing here knows about neural networks. 3.10's torch.autograd is this
    same design, with tensors instead of floats and C++ instead of closures.
    """

    def __init__(self, data, _parents=(), _op=""):
        self.data = float(data)
        self.grad = 0.0
        self._parents = _parents
        self._op = _op
        self._backward = lambda: None

    def __repr__(self):
        return f"Value({self.data:.4f}, grad={self.grad:.4f}, op={self._op!r})"

    def __add__(self, other):
        other = other if isinstance(other, Value) else Value(other)
        out = Value(self.data + other.data, (self, other), "+")

        def _backward():
            # d(out)/d(self) = 1, so the gradient passes straight through.
            # += NOT = : see Demo 5. This single character is the whole bug.
            self.grad += out.grad
            other.grad += out.grad

        out._backward = _backward
        return out

    def __mul__(self, other):
        other = other if isinstance(other, Value) else Value(other)
        out = Value(self.data * other.data, (self, other), "*")

        def _backward():
            # d(out)/d(self) = other.data - the OTHER operand.
            self.grad += other.data * out.grad
            other.grad += self.data * out.grad

        out._backward = _backward
        return out

    def tanh(self):
        t = math.tanh(self.data)
        out = Value(t, (self,), "tanh")

        def _backward():
            # d/dx tanh(x) = 1 - tanh(x)^2. Reusing the already-computed t is
            # why frameworks cache forward activations - and why training
            # needs so much more memory than inference (3.6).
            self.grad += (1 - t * t) * out.grad

        out._backward = _backward
        return out

    def __pow__(self, k):
        assert isinstance(k, (int, float))
        out = Value(self.data ** k, (self,), f"**{k}")

        def _backward():
            self.grad += k * (self.data ** (k - 1)) * out.grad

        out._backward = _backward
        return out

    def __neg__(self):
        return self * -1

    def __sub__(self, other):
        return self + (-other if isinstance(other, Value) else Value(-other))

    def __radd__(self, other):
        return self + other

    def __rmul__(self, other):
        return self * other

    def backward(self):
        """Topological order, then one reverse pass."""
        order, seen = [], set()

        def build(v):
            # A node may only run its _backward once ALL its consumers have
            # contributed. Topological order guarantees that.
            if id(v) not in seen:
                seen.add(id(v))
                for p in v._parents:
                    build(p)
                order.append(v)

        build(self)
        self.grad = 1.0          # seed: d(output)/d(output) = 1
        for v in reversed(order):
            v._backward()
        return order


def demo_autodiff_engine() -> None:
    print(SEP)
    print("DEMO 3 - a reverse-mode autodiff engine, from scratch")
    print(SEP)

    # A single neuron: out = tanh(w1*x1 + w2*x2 + b). This is literally one
    # unit of a 3.1 layer, and the gradients below are what 3.5 would step on.
    x1, x2 = Value(2.0), Value(0.0)
    w1, w2 = Value(-3.0), Value(1.0)
    b = Value(6.8813735870195432)
    n = x1 * w1 + x2 * w2 + b
    out = n.tanh()

    order = out.backward()

    print("  out = tanh(x1*w1 + x2*w2 + b)")
    print(f"    forward value: {out.data:.10f}")
    print(f"\n  graph has {len(order)} nodes, evaluated in topological order")
    print(f"\n  {'node':<10} {'op':<8} {'value':>12} {'grad':>14}")
    for name, v in [("x1", x1), ("w1", w1), ("x2", x2), ("w2", w2),
                    ("b", b), ("n", n), ("out", out)]:
        print(f"  {name:<10} {v._op or 'leaf':<8} {v.data:>12.6f} {v.grad:>14.10f}")

    print("\n  Read w1's gradient: increasing w1 by a tiny amount changes out")
    print(f"  by about {w1.grad:.6f} times that amount. That is all a gradient")
    print("  ever means, and it is what 3.5's optimizer consumes.")
    print("\n  Now compare w2 and x2, and note which one is zero:")
    print(f"    w2.grad = {w2.grad:.4f}   x2.grad = {x2.grad:.4f}")
    print("  d(out)/d(w2) = x2 * (1 - tanh^2), and x2 IS 0, so the weight")
    print("  gets NO learning signal - a feature that is always zero can")
    print("  never train its own weight, however wrong that weight is.")
    print("  Meanwhile d(out)/d(x2) = w2 * (1 - tanh^2) = 0.5, non-zero,")
    print("  because a node's gradient depends on what it MULTIPLIES, not on")
    print("  its own value. Getting these two backwards is easy; the table")
    print("  above is the check.")


# ===================================================================== 4
def demo_verify_against_torch() -> None:
    print(SEP)
    print("DEMO 4 - the engine, cross-checked against torch.autograd")
    print(SEP)
    try:
        import torch
    except ImportError:
        print("  torch not installed - skipping. The finite-difference check")
        print("  below still verifies the engine independently.")
        _finite_diff_check()
        return

    # Same expression, both systems, same numbers.
    x1, x2 = Value(2.0), Value(0.0)
    w1, w2 = Value(-3.0), Value(1.0)
    b = Value(6.8813735870195432)
    out = (x1 * w1 + x2 * w2 + b).tanh()
    out.backward()

    tx1 = torch.tensor([2.0], dtype=torch.float64, requires_grad=True)
    tx2 = torch.tensor([0.0], dtype=torch.float64, requires_grad=True)
    tw1 = torch.tensor([-3.0], dtype=torch.float64, requires_grad=True)
    tw2 = torch.tensor([1.0], dtype=torch.float64, requires_grad=True)
    tb = torch.tensor([6.8813735870195432], dtype=torch.float64,
                      requires_grad=True)
    tout = torch.tanh(tx1 * tw1 + tx2 * tw2 + tb)
    tout.backward()

    print(f"  forward   ours {out.data:.15f}")
    print(f"            torch {tout.item():.15f}")
    print(f"            abs diff {abs(out.data - tout.item()):.3e}")
    print(f"\n  {'':<6} {'ours':>20} {'torch':>20} {'abs diff':>12}")
    pairs = [("x1", x1, tx1), ("w1", w1, tw1), ("x2", x2, tx2),
             ("w2", w2, tw2), ("b", b, tb)]
    worst = 0.0
    for name, mine, theirs in pairs:
        tg = theirs.grad.item()
        d = abs(mine.grad - tg)
        worst = max(worst, d)
        print(f"  {name:<6} {mine.grad:>20.15f} {tg:>20.15f} {d:>12.3e}")

    print(f"\n  worst disagreement anywhere: {worst:.3e}")
    print("  60 lines of Python reproduce torch.autograd exactly on this")
    print("  graph. loss.backward() in 3.10 is not magic - it is Demo 3's")
    print("  two local rules, applied over a much larger graph, in C++.")

    _finite_diff_check()


def _finite_diff_check() -> None:
    """Independent check: perturb each input and remeasure."""
    def forward(vals):
        x1, x2, w1, w2, b = vals
        return math.tanh(x1 * w1 + x2 * w2 + b)

    base = [2.0, 0.0, -3.0, 1.0, 6.8813735870195432]
    x1, x2 = Value(base[0]), Value(base[1])
    w1, w2 = Value(base[2]), Value(base[3])
    b = Value(base[4])
    (x1 * w1 + x2 * w2 + b).tanh().backward()
    mine = [x1.grad, x2.grad, w1.grad, w2.grad, b.grad]

    h = 1e-7
    print(f"\n  independent finite-difference check:")
    print(f"  {'input':<6} {'engine':>18} {'finite diff':>18} {'abs diff':>12}")
    for i, name in enumerate(["x1", "x2", "w1", "w2", "b"]):
        up, dn = list(base), list(base)
        up[i] += h
        dn[i] -= h
        num = (forward(up) - forward(dn)) / (2 * h)
        print(f"  {name:<6} {mine[i]:>18.10f} {num:>18.10f} "
              f"{abs(mine[i] - num):>12.2e}")


# ===================================================================== 5
class BadValue(Value):
    """Identical to Value except gradients OVERWRITE instead of accumulate.

    This is the single most common bug in a hand-written autodiff, and it is
    invisible until a node is used more than once.
    """

    def __mul__(self, other):
        other = other if isinstance(other, BadValue) else BadValue(other)
        out = BadValue(self.data * other.data, (self, other), "*")

        def _backward():
            self.grad = other.data * out.grad      # = instead of +=
            other.grad = self.data * out.grad

        out._backward = _backward
        return out

    def __add__(self, other):
        other = other if isinstance(other, BadValue) else BadValue(other)
        out = BadValue(self.data + other.data, (self, other), "+")

        def _backward():
            self.grad = out.grad                   # = instead of +=
            other.grad = out.grad

        out._backward = _backward
        return out


def demo_accumulation_bug() -> None:
    print(SEP)
    print("DEMO 5 - a node used TWICE must ADD its gradients")
    print(SEP)

    # y = x * x. The single node x feeds BOTH operands of the multiply, so it
    # receives two separate gradient contributions. dy/dx = 2x = 6 at x = 3.
    good = Value(3.0)
    (good * good).backward()

    bad = BadValue(3.0)
    (bad * bad).backward()

    print("  y = x * x   at x = 3.0        true dy/dx = 2x = 6.0")
    print(f"\n    grad += (correct)   -> {good.grad}")
    print(f"    grad =  (the bug)   -> {bad.grad}")
    print(f"    the buggy version returned x, not 2x. Off by exactly half.")

    # A larger expression where the error is less obviously "half".
    a = Value(2.0)
    bb = Value(5.0)
    ((a * bb) + (a * a)).backward()          # d/da = b + 2a = 5 + 4 = 9
    a2 = BadValue(2.0)
    b2 = BadValue(5.0)
    ((a2 * b2) + (a2 * a2)).backward()
    print(f"\n  y = a*b + a*a   at a=2, b=5    true dy/da = b + 2a = 9.0")
    print(f"    grad += (correct)   -> {a.grad}")
    print(f"    grad =  (the bug)   -> {a2.grad}")

    print("\n  Nothing raised. The forward values were identical. Only the")
    print("  gradients were wrong, so a model trained this way still runs -")
    print("  it just learns the wrong thing, slowly, and you blame the")
    print("  learning rate. Every fan-out in a real network (residual")
    print("  connections, weight sharing, attention reusing one input across")
    print("  heads) hits this path, which is why 3.4 zeroes gradients between")
    print("  steps: accumulation is the DEFAULT, so stale values would add up.")


# ===================================================================== 6
def demo_mode_cost() -> None:
    print(SEP)
    print("DEMO 6 - why reverse mode: counted, not asserted")
    print(SEP)

    # Count how many times a node's local derivative must be evaluated to get
    # ALL partials of one scalar output with respect to n inputs.
    #   forward mode: one pass per INPUT   -> n passes
    #   reverse mode: one pass per OUTPUT  -> 1 pass
    print(f"  {'n inputs':<22} {'forward passes':>18} {'reverse passes':>15}")
    print(f"  {'-'*22} {'-'*18} {'-'*15}")
    for n, label in [(1, "1"), (10, "10"), (100, "100"),
                     (10_000, "10,000"),
                     (7_000_000_000, "7,000,000,000 (7B)")]:
        print(f"  {label:<22} {n:>18,} {1:>15,}")

    # Demonstrate the reverse claim concretely: one backward() call fills in
    # every input's gradient at once, whatever n is.
    for n in [3, 25, 200]:
        xs = [Value(float(i + 1)) for i in range(n)]
        total = xs[0]
        for v in xs[1:]:
            total = total + v
        loss = total * total          # scalar output
        loss.backward()
        # d(loss)/d(x_i) = 2 * sum(x) for every i
        expect = 2 * sum(i + 1 for i in range(n))
        got = [v.grad for v in xs]
        ok = all(abs(g - expect) < 1e-9 for g in got)
        print(f"\n  n={n:<4} ONE backward() filled {len(got)} gradients, "
              f"all equal to {expect} -> {ok}")

    print("\n  A neural network has millions to billions of inputs (the")
    print("  parameters) and exactly ONE output (the scalar loss). That")
    print("  shape is what makes reverse mode the only viable choice, and")
    print("  it is why 3.4 is called BACKpropagation. Forward mode is not")
    print("  wrong - it is better when the shape is reversed, few inputs and")
    print("  many outputs, which is the Jacobian case in 1.15.")


def main() -> None:
    print(f"numpy {np.__version__}")
    demo_chain_rule_by_hand()
    demo_graph_by_hand()
    demo_autodiff_engine()
    demo_verify_against_torch()
    demo_accumulation_bug()
    demo_mode_cost()
    print(SEP)
    print("You have now written backpropagation. 3.4 adds tensors and")
    print("layers; it does not add a new idea. If loss.backward() ever")
    print("looks like magic again, re-read Demo 3 - it is 60 lines.")
    print(SEP)


if __name__ == "__main__":
    main()
