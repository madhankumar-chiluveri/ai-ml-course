"""
1.1 - Vectors, Vector Spaces, Norms
===================================================================

WHAT THIS RUNS
    Seven numbered demos that NUMERICALLY VERIFY the mathematics of vectors
    and norms rather than merely illustrating it. Wherever possible a quantity
    is computed two independent ways (closed form vs brute force, hand formula
    vs library, analytic vs Monte Carlo) and the agreement is printed.

REQUIREMENTS
    python 3.10+, numpy, matplotlib, scikit-learn.
    Tested on Windows 11 / CPython 3.14.4 / numpy 2.4.4 / matplotlib 3.11.1 /
    scikit-learn 1.9.0. Exits 0.

SAFE AND OFFLINE
    No network calls of any kind. No environment variables read. Writes exactly
    ONE file - "01_unit_balls.png" - into the same folder as this script, and
    reports its byte size. Nothing else on disk is touched. Total runtime is a
    few seconds on a laptop CPU; no GPU is used.

REPRODUCIBILITY
    Every random number comes from np.random.default_rng(SEED + k) with
    SEED = 1729 declared below, so re-running gives byte-identical numbers.

WHAT THIS PROVES PRACTICALLY
    1. R^n really is a vector space - all eight axioms checked on random
       vectors - BUT float64 satisfies associativity only to ~1e-16, and the
       demo counts the exact violations instead of pretending they do not exist.
    2. L1 = 7, L2 = 5, Linf = 4 for the vector [3, -4, 0], each computed by hand
       and cross-checked against numpy to 0.0 absolute difference.
    3. The textbook L2 formula sqrt(sum(v_i^2)) OVERFLOWS to inf and UNDERFLOWS
       to 0 on perfectly ordinary-looking data, while the scaled algorithm gets
       the right answer. Shown side by side.
    4. The L1 unit ball has corners on the axes and the L2 ball does not. The
       constrained optimum is found by brute-force search over each boundary,
       and the L1 answer lands EXACTLY on a corner with a coordinate of 0.0.
    5. Soft-thresholding (the L1 update) sends coefficients to exactly 0.0 and
       the demo counts how many; the L2 update produces exactly 0 zeros no
       matter how hard it shrinks. That count is the Lasso-vs-Ridge mechanism.
    6. After L2 normalisation, cosine similarity IS the plain dot product, and
       squared Euclidean distance IS 2 - 2*cosine - both verified to machine
       precision. This is why vector databases store normalised embeddings.
    7. Distance concentration is measured, not asserted: (max-min)/min over
       pairwise distances collapses as dimension grows, and it decays at the
       predicted 1/sqrt(d) rate.

WHERE THIS RETURNS IN THE COURSE
    2.3 feature rows in linear regression, 2.5 Lasso vs Ridge, 1.4 cosine
    geometry, 3.1 activations, 5.1 embeddings and vector search.
"""

from __future__ import annotations

import math
import os
import sys

import numpy as np

import matplotlib
matplotlib.use("Agg")  # headless backend: never opens a window, never blocks
import matplotlib.pyplot as plt  # noqa: E402

SEED = 1729
HERE = os.path.dirname(os.path.abspath(__file__))
BAR = "=" * 70


# --------------------------------------------------------------------------
# small shared helpers
# --------------------------------------------------------------------------
def pnorm(v: np.ndarray, p: float) -> float:
    """Hand-written p-norm so nothing is hidden inside a library call.

    ||v||_p = (sum_i |v_i|^p)^(1/p) for p >= 1, and max_i |v_i| for p = inf.
    Every norm in this course is a special case of this one line.
    """
    a = np.abs(v)
    if math.isinf(p):
        return float(a.max())
    return float((a ** p).sum() ** (1.0 / p))


def safe_l2(v: np.ndarray) -> float:
    """Overflow/underflow-safe L2 norm: factor out the largest magnitude first.

    ||v||_2 = m * ||v/m||_2 with m = max|v_i|. Squaring v/m can never overflow
    (every entry is <= 1) and can never underflow to a total of zero (the
    largest entry becomes exactly 1). This is what BLAS's dnrm2 does.
    """
    m = float(np.abs(v).max())
    if m == 0.0:
        return 0.0
    scaled = v / m
    return m * float(np.sqrt((scaled * scaled).sum()))


def soft_threshold(x, lam):
    """Proximal operator of the L1 penalty - the entire Lasso mechanism (2.5).

    prox(x) = sign(x) * max(|x| - lam, 0).  Note the max(..., 0): every input
    with |x| <= lam is mapped to EXACTLY 0.0, not to something small.
    """
    return np.sign(x) * np.maximum(np.abs(x) - lam, 0.0)


def ridge_shrink(x, lam):
    """Proximal operator of the squared-L2 penalty - the Ridge mechanism (2.5).

    prox(x) = x / (1 + 2*lam).  This is multiplication by a constant strictly
    between 0 and 1, so a nonzero input can never become exactly zero.
    """
    return x / (1.0 + 2.0 * lam)


def constrained_argmin_on_boundary(A, b, points):
    """Brute-force the minimum of a quadratic loss over a set of boundary points.

    loss(w) = (w - b)^T A (w - b).  `points` is an (N, 2) array tracing the
    boundary of a norm ball. Returning the argmin by exhaustive search means
    the answer owes nothing to an optimiser's tolerance - if a coordinate comes
    back as exactly 0.0 it is because the geometry put it there.
    """
    d = points - b
    loss = np.einsum("ij,jk,ik->i", d, A, d)
    i = int(np.argmin(loss))
    return points[i], float(loss[i])


def l1_ball_boundary(n_per_edge=250001, r=1.0):
    """Trace the L1 unit ball (a diamond) - its four CORNERS sit on the axes."""
    verts = np.array([[r, 0.0], [0.0, r], [-r, 0.0], [0.0, -r], [r, 0.0]])
    segs = []
    for k in range(4):
        t = np.linspace(0.0, 1.0, n_per_edge)[:, None]
        segs.append(verts[k] * (1 - t) + verts[k + 1] * t)
    return np.vstack(segs)


def l2_ball_boundary(n=1000001, r=1.0):
    """Trace the L2 unit ball (a circle) - perfectly smooth, no corners at all."""
    th = np.linspace(0.0, 2 * np.pi, n)
    return np.column_stack([r * np.cos(th), r * np.sin(th)])


# --------------------------------------------------------------------------
# DEMO 1
# --------------------------------------------------------------------------
def demo1_vector_space_axioms():
    print(BAR)
    print("DEMO 1 - a vector, and the eight rules that make R^n a vector space")
    print(BAR)
    rng = np.random.default_rng(SEED + 1)

    # A vector is just an ordered list of numbers. The MEANING comes from what
    # the slots represent. Same object, three jobs, all later in this course.
    feature_row = np.array([3.0, -4.0, 0.0])      # one row of a design matrix (2.3)
    activation = np.array([0.0, 0.0, 1.7, 0.0])   # a ReLU layer's output (3.1)
    embedding = np.array([0.12, -0.87, 0.31])     # a 3-d toy embedding (5.1)
    print("  the SAME mathematical object wearing three different hats:")
    print("    feature row (2.3) :", feature_row, " shape", feature_row.shape)
    print("    activation  (3.1) :", activation, " shape", activation.shape)
    print("    embedding   (5.1) :", embedding, " shape", embedding.shape)
    print()

    # The eight axioms. A "vector space" is not a shape - it is a promise that
    # these eight rules hold, which is what lets you do algebra on data at all.
    u = rng.standard_normal(6)
    v = rng.standard_normal(6)
    w = rng.standard_normal(6)
    a, b = float(rng.standard_normal()), float(rng.standard_normal())
    zero = np.zeros(6)

    checks = [
        ("1. u + v == v + u              commutative", u + v, v + u),
        ("2. (u+v) + w == u + (v+w)      associative", (u + v) + w, u + (v + w)),
        ("3. u + 0 == u                  zero vector", u + zero, u),
        ("4. u + (-u) == 0               additive inverse", u + (-u), zero),
        ("5. a(u+v) == au + av           distributes over vectors", a * (u + v), a * u + a * v),
        ("6. (a+b)u == au + bu           distributes over scalars", (a + b) * u, a * u + b * u),
        ("7. (ab)u == a(bu)              scaling is compatible", (a * b) * u, a * (b * u)),
        ("8. 1*u == u                    scalar identity", 1.0 * u, u),
    ]
    print("  axiom                                                   max abs diff")
    print("  " + "-" * 69)
    worst = 0.0
    for label, lhs, rhs in checks:
        d = float(np.max(np.abs(lhs - rhs)))
        worst = max(worst, d)
        print("  %-55s %10.3e" % (label, d))
    print("  worst disagreement across all eight axioms: %.3e" % worst)
    print()

    # HONEST CAVEAT. In exact arithmetic axiom 2 is an identity. In float64 it
    # is not: addition rounds, and rounding depends on the order of operations.
    # Count how often that bites, because it is the reason two "identical"
    # pipelines can print different last digits.
    n_trials = 200_000
    x = rng.standard_normal(n_trials)
    y = rng.standard_normal(n_trials)
    z = rng.standard_normal(n_trials)
    left = (x + y) + z
    right = x + (y + z)
    exact_ties = int(np.sum(left == right))
    diffs = np.abs(left - right)
    print("  reality check on axiom 2 in float64, over %s random triples:" % format(n_trials, ","))
    print("    bit-for-bit identical : %d  (%.1f%%)"
          % (exact_ties, 100.0 * exact_ties / n_trials))
    print("    NOT identical         : %d  (%.1f%%)"
          % (n_trials - exact_ties, 100.0 * (n_trials - exact_ties) / n_trials))
    print("    largest disagreement  : %.3e   (machine epsilon = %.3e)"
          % (float(diffs.max()), float(np.finfo(np.float64).eps)))
    print("  -> the axiom is exactly true in R^n and only ~1e-16 true in float64.")
    print()


# --------------------------------------------------------------------------
# DEMO 2
# --------------------------------------------------------------------------
def demo2_three_norms():
    print(BAR)
    print("DEMO 2 - L1, L2, Linf: one vector, three honest answers to 'how big'")
    print(BAR)
    rng = np.random.default_rng(SEED + 2)

    v = np.array([3.0, -4.0, 0.0])  # the skip-test vector
    l1 = float(np.abs(v).sum())
    l2 = float(np.sqrt((v ** 2).sum()))
    linf = float(np.abs(v).max())
    print("  v = [3, -4, 0]        <- the skip-test vector, done by hand")
    print("    L1   = |3| + |-4| + |0|         = 3 + 4 + 0      = %.1f" % l1)
    print("    L2   = sqrt(3^2 + (-4)^2 + 0^2) = sqrt(9+16+0)   = %.1f" % l2)
    print("    Linf = max(|3|, |-4|, |0|)      = max(3, 4, 0)   = %.1f" % linf)
    print("    (3,4,5 right triangle: L2 is literally the ruler distance)")
    print()

    # Cross-check the hand arithmetic against numpy. Zero difference or bust.
    print("  hand formula vs numpy.linalg.norm, absolute difference:")
    for name, mine, theirs in [
        ("L1  ", l1, float(np.linalg.norm(v, 1))),
        ("L2  ", l2, float(np.linalg.norm(v, 2))),
        ("Linf", linf, float(np.linalg.norm(v, np.inf))),
    ]:
        print("    %s  mine=%.6f  numpy=%.6f  diff=%.1e" % (name, mine, theirs, abs(mine - theirs)))
    print()

    # The p-norm family: one formula, a dial. Watch it slide from 7 down to 4.
    print("  the whole family ||v||_p = (sum |v_i|^p)^(1/p), same vector:")
    print("     p        ||v||_p")
    for p in [1.0, 1.5, 2.0, 3.0, 5.0, 10.0, 50.0, 200.0]:
        print("    %6.1f   %10.6f" % (p, pnorm(v, p)))
    print("       inf   %10.6f   <- the limit: only the biggest entry survives" % pnorm(v, np.inf))
    print("  -> raising p puts more weight on the largest entry, so the norm falls.")
    print()

    # The three norm AXIOMS, checked on random data rather than asserted.
    U = rng.standard_normal((200_000, 8))
    V = rng.standard_normal((200_000, 8))
    scal = rng.standard_normal(200_000)[:, None]
    print("  norm axioms verified on 200,000 random vector pairs in R^8:")
    for name, p in [("L1", 1.0), ("L2", 2.0), ("Linf", np.inf)]:
        nu = np.linalg.norm(U, ord=p, axis=1)
        nv = np.linalg.norm(V, ord=p, axis=1)
        nuv = np.linalg.norm(U + V, ord=p, axis=1)
        # triangle inequality: ||u+v|| <= ||u|| + ||v||  (going direct is never
        # longer than going via a detour - this is what makes a norm a distance)
        slack = (nu + nv) - nuv
        viol = int(np.sum(slack < -1e-9))
        # absolute homogeneity: ||a*v|| == |a| * ||v||
        lhs = np.linalg.norm(scal * V, ord=p, axis=1)
        rhs = np.abs(scal[:, 0]) * nv
        hom = float(np.max(np.abs(lhs - rhs)))
        print("    %-4s triangle violations: %d      homogeneity max diff: %.3e"
              % (name, viol, hom))
    print("    positive definiteness: ||0|| = %.1f, and it is the only vector with norm 0"
          % np.linalg.norm(np.zeros(8)))
    print()

    # WHERE THE NAIVE FORMULA BREAKS. Nothing here is exotic data - these are
    # just numbers with large or small exponents, which is what you get from an
    # unscaled feature column (2.3) or a saturating activation (3.1).
    print("  the textbook formula sqrt(sum(v_i^2)) FAILS on ordinary-looking data:")

    def fmt(x):
        return "%-14s" % (x if (math.isinf(x) or math.isnan(x)) else "%.6e" % x)

    big = np.array([3e200, -4e200])
    small = np.array([3e-200, -4e-200])
    with np.errstate(over="ignore", under="ignore"):
        naive_big = float(np.sqrt((big ** 2).sum()))
        naive_small = float(np.sqrt((small ** 2).sum()))
        np_big = float(np.linalg.norm(big))
        np_small = float(np.linalg.norm(small))
    print("    v = [3e200, -4e200]    true answer 5.000000e+200")
    print("      naive sqrt(sum(v^2)) -> %s (v^2 = 9e400 OVERFLOWS float64)" % fmt(naive_big))
    print("      numpy.linalg.norm    -> %s (numpy squares too - same trap)" % fmt(np_big))
    print("      scaled algorithm     -> %s <- correct" % fmt(safe_l2(big)))
    print("    v = [3e-200, -4e-200]  true answer 5.000000e-200")
    print("      naive sqrt(sum(v^2)) -> %s (v^2 = 9e-400 UNDERFLOWS to 0)" % fmt(naive_small))
    print("      numpy.linalg.norm    -> %s (numpy squares too - same trap)" % fmt(np_small))
    print("      scaled algorithm     -> %s <- correct" % fmt(safe_l2(small)))
    print("    float64 range: largest %.3e, smallest normal %.3e"
          % (np.finfo(np.float64).max, np.finfo(np.float64).tiny))
    print("  -> the fix is one line: factor out m = max|v_i| first, then ||v|| = m*||v/m||.")
    print()


# --------------------------------------------------------------------------
# DEMO 3
# --------------------------------------------------------------------------
def demo3_unit_balls():
    print(BAR)
    print("DEMO 3 - unit balls: diamond, circle, square (and their real areas)")
    print(BAR)
    rng = np.random.default_rng(SEED + 3)

    # A "unit ball" is every point whose norm is <= 1. Change the norm and the
    # SHAPE changes. That shape is the whole of skip-test question 2.
    print("  the unit ball {v : ||v|| <= 1} in R^2, by Monte Carlo vs exact area:")
    n = 4_000_000
    pts = rng.uniform(-1.0, 1.0, size=(n, 2))  # uniform over the square [-1,1]^2
    box_area = 4.0
    rows = [
        ("L1   (diamond)", np.abs(pts).sum(axis=1), 2.0, "2"),
        ("L2   (circle) ", np.sqrt((pts ** 2).sum(axis=1)), math.pi, "pi"),
        ("Linf (square) ", np.abs(pts).max(axis=1), 4.0, "4"),
    ]
    print("    ball             sampled area   exact area   rel. error   formula")
    for name, norms, exact, sym in rows:
        frac = float(np.mean(norms <= 1.0))
        est = box_area * frac
        print("    %-15s  %10.6f   %10.6f   %9.2e   %s"
              % (name, est, exact, abs(est - exact) / exact, sym))
    print("    (%s uniform samples in [-1,1]^2, seed %d)" % (format(n, ","), SEED + 3))
    print("  -> the diamond is the SMALLEST, the square the largest, for the same radius 1.")
    print()

    # High dimensions: the L2 ball's share of the cube collapses. Monte Carlo
    # against the exact volume formula V_d = pi^(d/2) / Gamma(d/2 + 1).
    print("  same experiment in d dimensions - L2 ball volume vs the cube it sits in:")
    print("      d   ball/cube fraction   sampled volume    exact volume   rel.err")
    m = 2_000_000
    last_frac = None
    for d in [2, 3, 5, 8, 12]:
        P = rng.uniform(-1.0, 1.0, size=(m, d))
        inside = float(np.mean((P ** 2).sum(axis=1) <= 1.0))
        est = (2.0 ** d) * inside
        exact = math.pi ** (d / 2) / math.gamma(d / 2 + 1)
        rel = abs(est - exact) / exact
        last_frac = inside
        print("    %3d   %17.6f   %14.6f   %13.6f   %7.2e" % (d, inside, est, exact, rel))
    print("  -> at d=12 the ball fills %.4f%% of the cube: essentially all the volume"
          % (100.0 * last_frac))
    print("     sits in the CORNERS. That is the first face of the curse of dimensionality,")
    print("     and Monte Carlo agrees with the exact formula throughout.")
    print()

    # ---- figure -----------------------------------------------------------
    # Panel A: the three balls. Panels B and C: why the corner matters (2.5).
    A = np.array([[1.0, 0.72], [0.72, 1.0]])  # correlated design, X^T X shape
    b = np.array([1.9, 0.55])                 # unconstrained (OLS) optimum
    w_l1, _ = constrained_argmin_on_boundary(A, b, l1_ball_boundary())
    w_l2, _ = constrained_argmin_on_boundary(A, b, l2_ball_boundary())

    fig, axes = plt.subplots(1, 3, figsize=(13.5, 4.4))
    th = np.linspace(0, 2 * np.pi, 400)

    ax = axes[0]
    dia = np.array([[1, 0], [0, 1], [-1, 0], [0, -1], [1, 0]], dtype=float)
    sq = np.array([[1, 1], [-1, 1], [-1, -1], [1, -1], [1, 1]], dtype=float)
    ax.plot(sq[:, 0], sq[:, 1], color="#7f5539", lw=2, label="Linf ball (square), area 4")
    ax.plot(np.cos(th), np.sin(th), color="#005f73", lw=2, label="L2 ball (circle), area pi")
    ax.plot(dia[:, 0], dia[:, 1], color="#9b2226", lw=2, label="L1 ball (diamond), area 2")
    ax.scatter([1, 0, -1, 0], [0, 1, 0, -1], color="#9b2226", zorder=5, s=45)
    ax.set_title("unit balls: same radius 1, three norms")
    ax.legend(fontsize=7, loc="upper right")

    for ax, pts_b, wsol, col, ttl in [
        (axes[1], dia, w_l1, "#9b2226", "L1 constraint -> touches a CORNER"),
        (axes[2], np.column_stack([np.cos(th), np.sin(th)]), w_l2, "#005f73",
         "L2 constraint -> touches a smooth side"),
    ]:
        g = np.linspace(-2.6, 2.6, 400)
        GX, GY = np.meshgrid(g, g)
        D0, D1 = GX - b[0], GY - b[1]
        Z = A[0, 0] * D0 ** 2 + 2 * A[0, 1] * D0 * D1 + A[1, 1] * D1 ** 2
        ax.contour(GX, GY, Z, levels=14, colors="#a5a58d", linewidths=0.7)
        ax.plot(pts_b[:, 0], pts_b[:, 1], color=col, lw=2)
        ax.scatter([b[0]], [b[1]], color="#6b705c", s=40, zorder=5)
        ax.annotate("OLS optimum", (b[0], b[1]), fontsize=7, xytext=(4, 6),
                    textcoords="offset points")
        ax.scatter([wsol[0]], [wsol[1]], color="#1b4332", s=70, zorder=6)
        ax.annotate("w = (%.4f, %.4f)" % (wsol[0], wsol[1]), (wsol[0], wsol[1]),
                    fontsize=7, xytext=(6, -12), textcoords="offset points")
        ax.set_title(ttl, fontsize=10)

    for ax in axes:
        ax.set_aspect("equal")
        ax.axhline(0, color="#cccccc", lw=0.8)
        ax.axvline(0, color="#cccccc", lw=0.8)
        ax.set_xlim(-2.6, 2.6)
        ax.set_ylim(-2.6, 2.6)
    fig.tight_layout()
    out = os.path.join(HERE, "01_unit_balls.png")
    fig.savefig(out, dpi=120)
    plt.close(fig)
    print("  figure written: %s" % os.path.basename(out))
    print("    size on disk: %d bytes" % os.path.getsize(out))
    print()


# --------------------------------------------------------------------------
# DEMO 4
# --------------------------------------------------------------------------
def demo4_corner_geometry():
    print(BAR)
    print("DEMO 4 - the corner: why L1 lands ON an axis and L2 never does")
    print(BAR)

    # Same loss, same budget, two different ball shapes. loss(w) = (w-b)'A(w-b)
    # is exactly the least-squares surface of 2.3 with A = X^T X and b = OLS.
    A = np.array([[1.0, 0.72], [0.72, 1.0]])
    b = np.array([1.9, 0.55])
    print("  loss(w) = (w - b)^T A (w - b),  A = [[1, 0.72], [0.72, 1]],  b = [1.9, 0.55]")
    print("  b is the unconstrained least-squares answer (2.3); ||b||_1 = %.2f." % np.abs(b).sum())
    print("  Now cap the size of w with a budget t and see where the optimum lands.")
    print()
    print("  brute-force search over 1,000,001 points on each ball boundary")
    print("  (no optimiser, no tolerance - just evaluate the loss everywhere):")
    print()
    print("   budget t   L1-constrained w            zeros    L2-constrained w            zeros")
    print("   " + "-" * 84)
    for t in [0.4, 0.8, 1.0, 1.2, 1.5, 2.0]:
        w1, _ = constrained_argmin_on_boundary(A, b, l1_ball_boundary(r=t))
        w2, _ = constrained_argmin_on_boundary(A, b, l2_ball_boundary(r=t))
        z1 = int(np.sum(w1 == 0.0))
        z2 = int(np.sum(w2 == 0.0))
        print("   %8.2f   (%9.6f, %9.6f)   %d        (%9.6f, %9.6f)   %d"
              % (t, w1[0], w1[1], z1, w2[0], w2[1], z2))
    print()
    print("  -> read the 'zeros' columns. For a TIGHT budget the L1 optimum is the corner")
    print("     (t, 0): the second coordinate is not 1e-9, it is the float 0.0. Loosen the")
    print("     budget past t=1.2 and the optimum slides off the corner onto a flat edge,")
    print("     and the zero disappears - weak regularisation, no sparsity, exactly as in")
    print("     2.5. The L2 column never produces a zero at ANY budget, because a circle")
    print("     has no corners to land on.")
    print()

    # The same fact as an update rule, which is what a solver actually runs (2.5).
    rng = np.random.default_rng(SEED + 4)
    coefs = rng.standard_normal(2000)
    lam = 0.30
    l1_out = soft_threshold(coefs, lam)
    l2_out = ridge_shrink(coefs, lam)
    z1 = int(np.sum(l1_out == 0.0))
    z2 = int(np.sum(l2_out == 0.0))
    nz1 = np.abs(l1_out[l1_out != 0.0])
    nz2 = np.abs(l2_out[l2_out != 0.0])
    print("  one update step applied to the SAME 2000 random coefficients, lam = %.2f:" % lam)
    print("    L1 (soft threshold, sign(w)*max(|w|-lam, 0)):")
    print("      exact zeros: %4d / 2000  (%.1f%%)     smallest surviving |w|: %.3e"
          % (z1, 100.0 * z1 / 2000, float(nz1.min())))
    print("    L2 (shrink, w / (1 + 2*lam)):")
    print("      exact zeros: %4d / 2000  (%.1f%%)     smallest surviving |w|: %.3e"
          % (z2, 100.0 * z2 / 2000, float(nz2.min())))
    print("      every coefficient multiplied by %.6f - a nonzero times a nonzero"
          % (1.0 / (1.0 + 2.0 * lam)))
    print("      is nonzero, forever. That is the whole difference.")
    print()

    # Now on a real regression, with the answer checked against scikit-learn.
    print("  a real fit: n=200 samples, p=30 features, only 5 truly matter (2.3, 2.5)")
    rng2 = np.random.default_rng(SEED + 40)
    n, p = 200, 30
    X = rng2.standard_normal((n, p))
    X = (X - X.mean(axis=0)) / X.std(axis=0)  # standardise, else the penalty is unfair
    beta_true = np.zeros(p)
    beta_true[[2, 7, 11, 19, 25]] = [3.0, -2.0, 1.5, -1.0, 2.5]
    y = X @ beta_true + 0.5 * rng2.standard_normal(n)

    def lasso_cd(X, y, alpha, iters=3000, tol=1e-14):
        """Cyclic coordinate descent for (1/2n)||y-Xw||^2 + alpha*||w||_1."""
        n_, p_ = X.shape
        w = np.zeros(p_)
        cs = (X ** 2).sum(axis=0) / n_
        r = y - X @ w
        for _ in range(iters):
            biggest = 0.0
            for j in range(p_):
                r += X[:, j] * w[j]              # remove feature j's contribution
                rho = X[:, j] @ r / n_           # correlation of feature j with the residual
                new = soft_threshold(rho, alpha) / cs[j]   # <- the exact-zero step
                biggest = max(biggest, abs(new - w[j]))
                w[j] = new
                r -= X[:, j] * w[j]              # put it back
            if biggest < tol:
                break
        return w

    from sklearn.linear_model import Lasso, Ridge  # local import keeps startup fast

    alpha = 0.20
    w_mine = lasso_cd(X, y, alpha)
    sk = Lasso(alpha=alpha, fit_intercept=False, tol=1e-12, max_iter=200000).fit(X, y)
    print("    my 12-line coordinate descent vs sklearn.linear_model.Lasso:")
    print("      max abs coefficient difference: %.3e   <- same algorithm, same answer"
          % float(np.max(np.abs(w_mine - sk.coef_))))
    print()
    true_idx = np.nonzero(beta_true)[0]
    print("    alpha   Lasso zeros   Ridge zeros   real 5 kept   Lasso MSE   Ridge MSE")
    print("    " + "-" * 71)
    Xt = rng2.standard_normal((2000, p))
    Xt = (Xt - Xt.mean(axis=0)) / Xt.std(axis=0)
    yt = Xt @ beta_true + 0.5 * rng2.standard_normal(2000)
    for al in [0.02, 0.05, 0.10, 0.20, 0.50]:
        wl = lasso_cd(X, y, al)
        wr = Ridge(alpha=al * len(y), fit_intercept=False).fit(X, y).coef_
        zl = int(np.sum(wl == 0.0))          # EXACT equality to 0.0, not a threshold
        zr = int(np.sum(wr == 0.0))
        kept = int(np.sum(wl[true_idx] != 0.0))
        ml = float(np.mean((Xt @ wl - yt) ** 2))
        mr = float(np.mean((Xt @ wr - yt) ** 2))
        print("    %5.2f   %11d   %11d   %11s   %9.4f   %9.4f"
              % (al, zl, zr, "%d / 5" % kept, ml, mr))
    print("    (30 features, 5 of them real -> 25 zeros is the perfect answer)")
    print("  -> Lasso DELETES features and keeps all five real ones. Ridge zeroes nothing")
    print("     at any alpha, and its test error is worse here because the 25 junk")
    print("     features are still in the model, merely quietened.")
    print()


# --------------------------------------------------------------------------
# DEMO 5
# --------------------------------------------------------------------------
def demo5_normalisation_and_cosine():
    print(BAR)
    print("DEMO 5 - L2 normalisation turns cosine into a plain dot product")
    print(BAR)
    rng = np.random.default_rng(SEED + 5)

    # cos(u,v) = (u . v) / (||u||_2 ||v||_2).  If both vectors already have
    # ||.||_2 == 1 the denominator is 1 and cosine IS the dot product. This is
    # why vector databases (5.1) store normalised embeddings and why 1.4 can
    # treat "angle" and "inner product" as the same measurement.
    n, d = 100_000, 64
    U = rng.standard_normal((n, d))
    V = rng.standard_normal((n, d))
    cos_full = np.sum(U * V, axis=1) / (np.linalg.norm(U, axis=1) * np.linalg.norm(V, axis=1))
    Uh = U / np.linalg.norm(U, axis=1, keepdims=True)
    Vh = V / np.linalg.norm(V, axis=1, keepdims=True)
    dot_hat = np.sum(Uh * Vh, axis=1)
    print("  %s random pairs in R^%d:" % (format(n, ","), d))
    print("    max | cos(u,v)  -  u_hat . v_hat |            = %.3e" % float(np.max(np.abs(cos_full - dot_hat))))
    print("    max | ||u_hat||_2 - 1 |                       = %.3e"
          % float(np.max(np.abs(np.linalg.norm(Uh, axis=1) - 1.0))))

    # The other identity that makes normalisation worth doing: on the unit
    # sphere, Euclidean distance and cosine are the SAME ranking.
    sqd = np.sum((Uh - Vh) ** 2, axis=1)
    print("    max | ||u_hat - v_hat||^2  -  (2 - 2*cos) |   = %.3e"
          % float(np.max(np.abs(sqd - (2.0 - 2.0 * dot_hat)))))
    print("  -> every gap is a small multiple of machine epsilon (%.2e), i.e. rounding and"
          % np.finfo(np.float64).eps)
    print("     nothing else. These are identities, not approximations. So on normalised")
    print("     vectors a nearest-neighbour search by dot product returns the IDENTICAL")
    print("     ranking as one by Euclidean distance - which is what lets a vector index")
    print("     (5.1) use the cheaper inner product and still answer the cosine question.")
    print()

    # WHERE SKIPPING NORMALISATION BITES. Length is not relevance.
    print("  what normalisation removes - a worked case:")
    query = np.array([1.0, 1.0, 0.0, 0.0])
    docs = {
        "A  on-topic, short   ": np.array([1.0, 1.0, 0.0, 0.0]),
        "B  on-topic, 10x long": np.array([10.0, 10.0, 0.0, 0.0]),
        "C  off-topic, huge   ": np.array([0.0, 0.0, 40.0, 40.0]),
        "D  half-topic, medium": np.array([6.0, 0.0, 0.0, 0.0]),
    }
    print("    query = [1, 1, 0, 0]")
    print("    doc                     raw dot   L2 norm   cosine")
    for k, dv in docs.items():
        raw = float(query @ dv)
        cs = raw / (np.linalg.norm(query) * np.linalg.norm(dv))
        print("    %s  %8.3f  %8.3f  %7.4f" % (k, raw, float(np.linalg.norm(dv)), cs))
    best_raw = max(docs, key=lambda k: float(query @ docs[k]))
    best_cos = max(docs, key=lambda k: float(query @ docs[k]) / (np.linalg.norm(query) * np.linalg.norm(docs[k])))
    print("    ranked by raw dot product -> winner: %s" % best_raw.strip())
    print("    ranked by cosine          -> winner: %s" % best_cos.strip())
    print("  -> raw dot product rewards LENGTH. Doc B is the same document as A, repeated,")
    print("     and it wins on magnitude alone. Cosine scores A and B identically (%.4f),"
          % (float(query @ docs["A  on-topic, short   "]) /
             (np.linalg.norm(query) * np.linalg.norm(docs["A  on-topic, short   "]))))
    print("     which is what you wanted. Normalise once at write time (5.1), not per query.")
    print()


# --------------------------------------------------------------------------
# DEMO 6
# --------------------------------------------------------------------------
def demo6_curse_of_dimensionality():
    print(BAR)
    print("DEMO 6 - measured: distances stop being different in high dimensions")
    print(BAR)
    rng = np.random.default_rng(SEED + 6)

    # "High-dimensional space is weird" is a slogan until you measure it. The
    # relative contrast (dmax - dmin) / dmin says how much the nearest point
    # stands out from the farthest. If it collapses, "nearest neighbour" stops
    # meaning anything - which is the central engineering problem of 5.1.
    n_data, n_query = 2000, 200
    print("  %d uniform points in [0,1]^d, %d queries, L2 distances:" % (n_data, n_query))
    print("       d     mean dist    min dist    max dist   (max-min)/min   x sqrt(d)")
    print("    " + "-" * 68)
    contrasts = {}
    for d in [2, 10, 100, 1000, 5000]:
        data = rng.uniform(0.0, 1.0, size=(n_data, d))
        q = rng.uniform(0.0, 1.0, size=(n_query, d))
        # ||q - x||^2 = ||q||^2 - 2 q.x + ||x||^2, computed blockwise
        dd = np.sqrt(np.maximum(
            (q ** 2).sum(1)[:, None] - 2.0 * (q @ data.T) + (data ** 2).sum(1)[None, :], 0.0))
        dmin = dd.min(axis=1)
        dmax = dd.max(axis=1)
        contrast = float(np.mean((dmax - dmin) / dmin))
        contrasts[d] = contrast
        print("    %5d   %10.4f  %10.4f  %10.4f   %13.4f   %9.4f"
              % (d, float(dd.mean()), float(dmin.mean()), float(dmax.mean()),
                 contrast, contrast * math.sqrt(d)))
    print("  -> contrast collapses from %.1f at d=2 to %.4f at d=5000: the farthest point"
          % (contrasts[2], contrasts[5000]))
    print("     is only %.1f%% farther away than the nearest one. Be honest about the last"
          % (100.0 * contrasts[5000]))
    print("     column: it is NOT flat at d=2 or d=10 (too few points to fill a small")
    print("     space), but from d=100 on it settles near 4, which is the predicted")
    print("     1/sqrt(d) decay showing up in real measurements.")
    print()

    # The angular version of the same collapse: random directions in high
    # dimensions are almost exactly orthogonal. cos has mean 0 and variance 1/d.
    print("  random unit vectors are almost orthogonal - cosine between random pairs:")
    print("       d    mean cos     std cos    std * sqrt(d)   theory: 1.0")
    for d in [2, 10, 100, 1000, 10000]:
        A = rng.standard_normal((4000, d))
        B = rng.standard_normal((4000, d))
        A /= np.linalg.norm(A, axis=1, keepdims=True)
        B /= np.linalg.norm(B, axis=1, keepdims=True)
        c = np.sum(A * B, axis=1)
        print("    %5d  %10.5f  %10.5f  %14.5f" % (d, float(c.mean()), float(c.std()),
                                                   float(c.std()) * math.sqrt(d)))
    print("  -> the last column sits at 1.0 for every d: measurement matching the")
    print("     analytic variance 1/d. In R^10000 two random embeddings are orthogonal")
    print("     to within about %.3f. Any cosine well above that is real signal (1.4)."
          % (2.0 / math.sqrt(10000)))
    print()


# --------------------------------------------------------------------------
# DEMO 7
# --------------------------------------------------------------------------
def demo7_norm_choice_changes_the_answer():
    print(BAR)
    print("DEMO 7 - the norm you pick changes which neighbour you retrieve")
    print(BAR)
    rng = np.random.default_rng(SEED + 7)

    # Nothing above says which norm is "right". This demo measures how often
    # the choice actually changes the retrieved item - the practical stake for
    # 5.1 (which metric does the index use?) and 1.4 (angle vs distance).
    print("  100 queries against 5000 points, nearest neighbour under each norm:")
    print("       d   L1 vs L2 disagree   L2 vs Linf disagree   L1 vs Linf disagree")
    print("    " + "-" * 68)
    for d in [2, 5, 20, 100]:
        data = rng.standard_normal((5000, d))
        q = rng.standard_normal((100, d))
        diff = q[:, None, :] - data[None, :, :]
        nn1 = np.argmin(np.abs(diff).sum(axis=2), axis=1)
        nn2 = np.argmin((diff ** 2).sum(axis=2), axis=1)
        nni = np.argmin(np.abs(diff).max(axis=2), axis=1)
        print("    %4d   %17s   %19s   %19s"
              % (d,
                 "%3d / 100" % int(np.sum(nn1 != nn2)),
                 "%3d / 100" % int(np.sum(nn2 != nni)),
                 "%3d / 100" % int(np.sum(nn1 != nni))))
    print("  -> in R^2 the three norms mostly agree; by R^100 they mostly do not.")
    print("     'nearest' is not a property of the data, it is a property of the norm.")
    print()

    # One last identity worth carrying: the norms bracket each other, always.
    # ||v||_inf <= ||v||_2 <= ||v||_1 <= sqrt(d) * ||v||_2 <= d * ||v||_inf
    print("  the inequality chain that holds for EVERY vector, 200,000 samples in R^25:")
    d = 25
    V = rng.standard_normal((200_000, d))
    a = np.linalg.norm(V, ord=np.inf, axis=1)
    b2 = np.linalg.norm(V, ord=2, axis=1)
    c = np.linalg.norm(V, ord=1, axis=1)
    print("    ||v||_inf <= ||v||_2            violations: %d" % int(np.sum(a > b2 + 1e-12)))
    print("    ||v||_2   <= ||v||_1            violations: %d" % int(np.sum(b2 > c + 1e-12)))
    print("    ||v||_1   <= sqrt(d)*||v||_2    violations: %d  (d = %d, sqrt(d) = %.4f)"
          % (int(np.sum(c > math.sqrt(d) * b2 + 1e-9)), d, math.sqrt(d)))
    print("    largest observed ratio ||v||_1 / ||v||_2  : %.4f  (ceiling sqrt(d) = %.4f)"
          % (float(np.max(c / b2)), math.sqrt(d)))
    print("  -> the norms differ by at most a factor of sqrt(d). In R^25 that is 5x;")
    print("     in a 1536-d embedding space (5.1) it is 39x, which is why the choice matters.")
    print()


def main():
    print("1.1 - Vectors, Vector Spaces, Norms")
    print("python %s | numpy %s | seed %d"
          % (sys.version.split()[0], np.__version__, SEED))
    print("all randomness from np.random.default_rng(SEED + demo_number)")
    print()
    demo1_vector_space_axioms()
    demo2_three_norms()
    demo3_unit_balls()
    demo4_corner_geometry()
    demo5_normalisation_and_cosine()
    demo6_curse_of_dimensionality()
    demo7_norm_choice_changes_the_answer()
    print(BAR)
    print("done - no network, no state changed, one PNG written beside this script")
    print(BAR)


if __name__ == "__main__":
    main()
