"""
1.12 - Numerical Stability: Floating Point, Log-Sum-Exp, Softmax Overflow.

Runnable: `python 12_numerical_stability.py`
Requires: numpy. torch is optional - Demo 6 (bfloat16) is skipped without it.

SAFE + OFFLINE: pure computation. No files written, no network, no API keys.

What this proves practically:
  1. Floats are not the reals. 0.1 + 0.2 != 0.3, and equality testing is a bug.
  2. Naive softmax returns nan for logits a real model produces. The one-line
     fix returns the identical answer, provably.
  3. log(sum(exp(x))) overflows going up AND underflows going down. The
     log-sum-exp trick survives both, at the same cost.
  4. log(softmax(x)) loses precision that log_softmax keeps. Measured.
  5. float16 overflows at 65504; bfloat16 does not, because it trades
     precision for the SAME exponent range as float32. That is why 4.12
     prefers bf16 for training.
  6. Adding numbers in a different ORDER gives a different answer. NumPy
     already protects you here; a hand-written loop does not.
  7. The textbook variance formula catastrophically fails on shifted data.
     Welford's algorithm does not. Same data, same formula, different result.
"""

import numpy as np

SEP = "=" * 70
rng = np.random.default_rng(1729)     # seeded -> reproducible


# ===================================================================== 1
def demo_floats_are_not_reals() -> None:
    print(SEP)
    print("DEMO 1 - floats are not the real numbers")
    print(SEP)

    print(f"  0.1 + 0.2            = {0.1 + 0.2!r}")
    print(f"  0.1 + 0.2 == 0.3     -> {0.1 + 0.2 == 0.3}")
    print(f"  difference           = {abs((0.1 + 0.2) - 0.3):.3e}")
    print("  ^ 0.1 and 0.2 are not exactly representable in binary, the same")
    print("    way 1/3 is not exactly representable in decimal. The error is")
    print("    tiny and it is REAL - so `==` on floats is a bug (0.5 taught")
    print("    pytest.approx for exactly this).")

    eps = np.finfo(np.float64).eps
    print(f"\n  machine epsilon (float64) = {eps:.3e}")
    print(f"  1.0 + eps/2 == 1.0        -> {1.0 + eps / 2 == 1.0}")
    print("  ^ eps is the gap between 1.0 and the next float. Add less than")
    print("    half of it and NOTHING HAPPENS. This is not a rounding")
    print("    display issue; the addition genuinely did not occur.")

    # Catastrophic cancellation: subtracting two nearly equal numbers
    # destroys the significant digits that made them different.
    a, b = 1.0, 1.0 + 1e-13
    print(f"\n  catastrophic cancellation:")
    print(f"    b - a          = {b - a:.20e}")
    print(f"    true answer    = {1e-13:.20e}")
    rel = abs((b - a) - 1e-13) / 1e-13
    print(f"    relative error = {rel:.2%}")
    print("  ^ Both inputs were accurate to ~16 digits. Their DIFFERENCE is")
    print("    accurate to about 3. Precision was destroyed by subtraction,")
    print("    which is the whole reason Demo 7 exists.")


# ===================================================================== 2
def softmax_naive(x):
    """The formula exactly as written in a textbook."""
    e = np.exp(x)
    return e / e.sum()


def softmax_stable(x):
    """The same function, mathematically identical, numerically survivable.

    exp(x_i) / sum_j exp(x_j)  ==  exp(x_i - c) / sum_j exp(x_j - c)

    for ANY constant c, because exp(x-c) = exp(x)/exp(c) and the exp(c)
    cancels top and bottom. Choosing c = max(x) makes the largest exponent
    exactly 0, so the biggest term is exp(0) = 1 and NOTHING can overflow.
    """
    z = x - x.max()
    e = np.exp(z)
    return e / e.sum()


def demo_softmax_overflow() -> None:
    print(SEP)
    print("DEMO 2 - naive softmax returns nan on logits a real model produces")
    print(SEP)

    print(f"  float64 overflows exp() above x = {np.log(np.finfo(np.float64).max):.1f}")
    print(f"  float32 overflows exp() above x = {np.log(np.finfo(np.float32).max):.1f}")
    print("  ^ float32 is what a model actually runs in. A logit of 90 is")
    print("    unremarkable; a logit of 800 appears in an unnormalised or")
    print("    diverging model. Both break the textbook formula.\n")

    print(f"  {'logits':<26} {'naive':<26} {'stable':<26}")
    print(f"  {'-'*26} {'-'*26} {'-'*26}")
    cases = [
        np.array([1.0, 2.0, 3.0]),
        np.array([100.0, 101.0, 102.0]),
        np.array([800.0, 801.0, 802.0]),
        np.array([-800.0, -801.0, -802.0]),
    ]
    for x in cases:
        with np.errstate(over="ignore", invalid="ignore", under="ignore"):
            n = softmax_naive(x)
            s = softmax_stable(x)
        label = f"[{x[0]:.0f}, {x[1]:.0f}, {x[2]:.0f}]"
        print(f"  {label:<26} {np.array2string(n, precision=4):<26} "
              f"{np.array2string(s, precision=4):<26}")

    print("\n  Row 3 is the failure: exp(802) is larger than any float64, so")
    print("  the numerator and denominator are both inf, and inf/inf is nan.")
    print("  Row 4 is the quieter failure: exp(-802) underflows to 0.0, so")
    print("  the naive version computes 0/0 - also nan.")
    print("  The stable column is CORRECT in all four rows, and it is the")
    print("  same function: shifting by a constant provably cannot change")
    print("  the result. Every real softmax subtracts the max (4.2, 3.3).")

    # Prove the shift-invariance claim rather than asserting it.
    x = rng.normal(0, 5, 12)
    a, b = softmax_naive(x), softmax_stable(x)
    print(f"\n  proof of identity on safe inputs: max|naive - stable| = "
          f"{np.abs(a - b).max():.3e}")
    print(f"  both sum to 1.0: {a.sum():.15f}  {b.sum():.15f}")


# ===================================================================== 3
def logsumexp_naive(x):
    return np.log(np.exp(x).sum())


def logsumexp_stable(x):
    """log(sum(exp(x))) = c + log(sum(exp(x - c))), with c = max(x).

    Same algebra as the softmax shift. The largest term becomes exp(0) = 1,
    so the sum is at least 1 and log() never sees 0.
    """
    c = x.max()
    return c + np.log(np.exp(x - c).sum())


def demo_logsumexp() -> None:
    print(SEP)
    print("DEMO 3 - log-sum-exp: it fails going UP and going DOWN")
    print(SEP)
    print(f"  {'input':<22} {'naive':<16} {'stable':<16} {'why naive failed'}")
    print(f"  {'-'*22} {'-'*16} {'-'*16} {'-'*22}")

    cases = [
        (np.array([1.0, 2.0, 3.0]), "fine"),
        (np.array([1000.0, 1001.0]), "exp() -> inf, log(inf) = inf"),
        (np.array([-1000.0, -1001.0]), "exp() -> 0.0, log(0) = -inf"),
    ]
    for x, why in cases:
        with np.errstate(over="ignore", divide="ignore", under="ignore"):
            n = logsumexp_naive(x)
            s = logsumexp_stable(x)
        label = f"[{', '.join(f'{v:.0f}' for v in x)}]"
        print(f"  {label:<22} {n:<16.6f} {s:<16.6f} {why if not np.isfinite(n) else ''}")

    print("\n  Overflow is the famous one. UNDERFLOW is the dangerous one:")
    print("  it returns -inf silently, which then poisons a loss instead of")
    print("  raising. Log-probabilities are routinely around -1000 when you")
    print("  score a long sequence (4.6), so this is not a contrived input.")
    print("\n  Both directions are fixed by the same one-line shift, at the")
    print("  same computational cost. There is no tradeoff to weigh here.")


# ===================================================================== 4
def demo_log_softmax() -> None:
    print(SEP)
    print("DEMO 4 - log(softmax(x)) throws away precision log_softmax keeps")
    print(SEP)

    x = np.array([0.0, -30.0, -60.0])
    with np.errstate(divide="ignore"):
        two_step = np.log(softmax_stable(x))
    # log_softmax(x) = x - logsumexp(x), computed WITHOUT ever forming the
    # probability. The probability is what loses the small values: once
    # softmax rounds 1e-27 to a float, its log has already lost digits.
    one_step = x - logsumexp_stable(x)

    print(f"  {'logit':>8} {'log(softmax(x))':>20} {'x - logsumexp(x)':>20} {'abs diff':>12}")
    for xi, t, o in zip(x, two_step, one_step):
        print(f"  {xi:>8.0f} {t:>20.12f} {o:>20.12f} {abs(t - o):>12.3e}")

    # Now make it fail outright, not just lose digits.
    x2 = np.array([0.0, -800.0])
    with np.errstate(divide="ignore", under="ignore"):
        bad = np.log(softmax_stable(x2))
    good = x2 - logsumexp_stable(x2)
    print(f"\n  logits [0, -800]:")
    print(f"    log(softmax(x)) -> {bad}")
    print(f"    x - logsumexp   -> {good}")
    print("  ^ softmax rounded the second probability to exactly 0.0, and")
    print("    log(0) is -inf. The one-step form returns -800.0, which is")
    print("    the correct answer and is perfectly representable.")
    print("\n  This is why frameworks expose log_softmax and why the loss in")
    print("  3.3 takes LOGITS, not probabilities. Handing it probabilities")
    print("  means the precision was already gone before it was called.")


# ===================================================================== 5
def demo_float_formats() -> None:
    print(SEP)
    print("DEMO 5 - float16 vs bfloat16 vs float32: range beats precision")
    print(SEP)

    for name, dt in [("float16", np.float16), ("float32", np.float32),
                     ("float64", np.float64)]:
        fi = np.finfo(dt)
        print(f"  {name:<9} max={float(fi.max):<12.4g} "
              f"tiny={float(fi.tiny):<12.4g} eps={float(fi.eps):.3e} "
              f"({fi.bits} bits)")

    big = np.float32(70000.0)
    with np.errstate(over="ignore"):      # the overflow IS the demonstration
        as16 = np.float16(big)
    print(f"\n  70000 in float32 = {big}")
    print(f"  70000 in float16 = {as16}   <- OVERFLOWED to inf")
    print(f"  float16 max      = {np.finfo(np.float16).max}")
    print("  ^ 70000 is not an exotic number. Attention scores and squared")
    print("    gradients exceed 65504 routinely, which is why pure fp16")
    print("    training needs loss scaling to survive at all.")

    try:
        import torch
    except ImportError:
        print("\n  (torch not installed - bfloat16 comparison skipped)")
        return

    t = torch.tensor([70000.0, 1e-8, 3.14159265358979])
    f16 = t.to(torch.float16)
    bf16 = t.to(torch.bfloat16)
    print(f"\n  {'value':>22} {'float16':>14} {'bfloat16':>14}")
    for i, v in enumerate(t.tolist()):
        print(f"  {v:>22.10g} {f16[i].item():>14.6g} {bf16[i].item():>14.6g}")

    print("\n  bfloat16 keeps 70000 and 1e-8; float16 loses BOTH (inf and 0).")
    print("  bfloat16 is worse at pi - it has fewer mantissa bits.")
    print("  That is the whole trade: bf16 spends its 16 bits on the SAME")
    print("  exponent range as float32 and accepts coarser precision.")
    print("  Training cares about range (gradients span many magnitudes)")
    print("  far more than about the 4th decimal place, which is why 4.12")
    print("  reaches for bf16 rather than fp16 wherever the hardware allows.")


# ===================================================================== 6
def demo_summation_order() -> None:
    print(SEP)
    print("DEMO 6 - addition is not associative in floating point")
    print(SEP)

    n = 1_000_000
    exact = 1e8 + n * 1.0            # 101,000,000 - only 9 significant digits

    # The FIRST version of this demo used float64 and proved nothing: 1e8 plus
    # a million ones needs 9 digits and float64 carries ~16, so every method
    # was exact. Order only matters once the running total's OWN precision is
    # coarser than the values being added. Two ways to reach that, both real.
    print(f"  (A) float64, 1e8 + {n:,} x 1.0  -> needs 9 digits, float64 has ~16")
    acc = 0.0
    for _ in range(n):
        acc += 1.0
    acc64 = 1e8 + acc
    xs64 = np.concatenate([[1e8], np.full(n, 1.0)])
    print(f"      naive loop  : {acc64:.1f}   error {abs(acc64-exact):>12,.1f}")
    print(f"      np.sum      : {float(np.sum(xs64)):.1f}   error "
          f"{abs(float(np.sum(xs64))-exact):>12,.1f}")
    print("      Both exact. There was no problem here to solve.\n")

    # (B) float32 is what models actually compute in. Its eps near 1e8 is
    # larger than 1.0, so the accumulator literally cannot move.
    xs32 = np.concatenate([[1e8], np.full(n, 1.0)]).astype(np.float32)
    acc32 = np.float32(0.0)
    for v in xs32:
        acc32 = np.float32(acc32 + v)         # left-to-right, float32
    np32 = float(np.sum(xs32))                # numpy uses PAIRWISE summation
    sorted32 = float(np.sum(np.sort(xs32)))   # smallest first
    step = np.spacing(np.float32(1e8))
    print(f"  (B) SAME numbers in float32 (what 3.x and 4.x actually run in)")
    print(f"      gap between neighbouring float32 values near 1e8: {step:.1f}")
    print(f"      -> adding 1.0 to 1e8 in float32 CANNOT change it: "
          f"{np.float32(1e8) + np.float32(1.0) == np.float32(1e8)}")
    print(f"      exact answer: {exact:,.0f}")
    print(f"      naive loop  : {float(acc32):>14,.0f}   error "
          f"{abs(float(acc32)-exact):>12,.0f}")
    print(f"      np.sum      : {np32:>14,.0f}   error {abs(np32-exact):>12,.0f}")
    print(f"      sorted first: {sorted32:>14,.0f}   error "
          f"{abs(sorted32-exact):>12,.0f}")

    print("\n  The float32 loop lost a million real increments - every 1.0 was")
    print("  below the resolution of a running total near 1e8, so each one")
    print("  rounded away entirely. Same numbers, same operation, different")
    print("  ORDER and different dtype, wildly different answer.")
    print("  np.sum survives it by summing in pairs rather than left to right,")
    print("  and sorting smallest-first recovers more still.")
    print("  This is one more reason 0.6 pushed vectorised operations, and it")
    print("  is why averaging a loss over a large eval set (7.1) accumulates")
    print("  in float32 at your peril.")


# ===================================================================== 7
def demo_variance_stability() -> None:
    print(SEP)
    print("DEMO 7 - the textbook variance formula, and where it breaks")
    print(SEP)

    def var_naive(x):
        # Var = E[X^2] - (E[X])^2. Algebraically correct. Two large, nearly
        # equal numbers get subtracted - exactly Demo 1's cancellation.
        return (x * x).mean() - x.mean() ** 2

    def var_welford(x):
        # One pass, tracking the mean and the sum of squared DEVIATIONS.
        # Never forms a large intermediate, so nothing cancels.
        mean = 0.0
        m2 = 0.0
        for i, v in enumerate(x, start=1):
            d = v - mean
            mean += d / i
            m2 += d * (v - mean)
        return m2 / len(x)

    base = rng.normal(0.0, 1.0, 10_000)
    print(f"  {'data':<28} {'naive':>16} {'Welford':>16} {'np.var':>16}")
    print(f"  {'-'*28} {'-'*16} {'-'*16} {'-'*16}")
    for shift in [0.0, 1e6, 1e8, 1e9]:
        x = base + shift
        print(f"  {'values near ' + f'{shift:.0e}':<28} {var_naive(x):>16.8f} "
              f"{var_welford(x):>16.8f} {np.var(x):>16.8f}")

    print("\n  Shifting every value by a constant CANNOT change the variance -")
    print("  the spread is identical. The naive column drifts anyway, and at")
    print("  1e9 it is meaningless. It computed a difference of two numbers")
    print("  around 1e18 that agree to 17 digits, and float64 has ~16.")
    print("  Welford and np.var hold steady because neither ever forms that")
    print("  large intermediate. Same mathematics, different arithmetic.")
    print("\n  Real data looks like this: timestamps, prices in paise, token")
    print("  counts. 'Correct formula' and 'correct program' are not the")
    print("  same claim, which is the point of this whole topic (1.8, 7.9).")


def main() -> None:
    print(f"numpy {np.__version__}  |  seed 1729")
    demo_floats_are_not_reals()
    demo_softmax_overflow()
    demo_logsumexp()
    demo_log_softmax()
    demo_float_formats()
    demo_summation_order()
    demo_variance_stability()
    print(SEP)
    print("Every failure above is silent. Nothing raised an exception; the")
    print("answers were just nan, -inf, or quietly wrong. That is why this")
    print("topic is 4 hours of prevention rather than a debugging session")
    print("during 3.6 when a loss goes NaN at step 4,000.")
    print(SEP)


if __name__ == "__main__":
    main()
