"""
1.4 - Dot Product, Projection, Cosine Geometry (companion script)

WHAT THIS RUNS
    Seven numbered demos that do not merely draw pictures of the dot product -
    they NUMERICALLY VERIFY it. Wherever possible a quantity is computed two or
    more genuinely independent ways and the disagreement is printed, so you can
    see with your own eyes that it is machine rounding noise (about 1e-16) and
    not an argument you are being asked to trust.

REQUIREMENTS
    numpy and matplotlib only. matplotlib runs on the "Agg" backend, so no
    window is ever opened and the script works over SSH or in CI.

SAFETY
    Completely offline. No network calls, no environment variables read, no
    files deleted, no subprocesses. The single file written is a .png saved
    next to this script; its byte size is printed at the end.

REPRODUCIBILITY
    Every random number comes from np.random.default_rng(1729). The seed is
    printed at startup. Re-running reproduces the notes' numbers exactly.

WHAT THIS PROVES PRACTICALLY
    1. The dot product computed four independent ways - an explicit loop, a
       numpy call, the polarization identity (which uses only LENGTHS), and
       ||a||*||b||*cos(theta) - agrees to about 1e-15.
    2. The residual left after projecting a onto b is exactly orthogonal to b:
       measured dot product around 1e-17, and Pythagoras holds to 1e-16.
    3. Raw dot product and cosine RANK RETRIEVAL CANDIDATES DIFFERENTLY. The
       best-matching document by direction comes LAST under raw dot product and
       FIRST under cosine. L2-normalise every vector and the two rankings become
       bit-for-bit identical.
    4. Over 20,000 random retrieval trials the two disagree on the top hit about
       half the time when candidate lengths vary, and ZERO times when all
       candidates share one common length - which is the exact condition.
    5. Random directions in high dimensions are nearly orthogonal: std(cos) is
       exactly 1/sqrt(d), verified by simulation from d=2 to d=10000.
    6. The variance of a raw attention score grows linearly with head dimension,
       so dividing by sqrt(d) is what keeps softmax out of its saturated region.
       Measured: unscaled softmax puts 1.000 of its mass on one key; scaled
       spreads it over several.
    7. For unit vectors squared-L2 distance equals 2 - 2*cos exactly, so cosine
       and L2 give the same ranking - but only after normalisation.
"""

import os

import matplotlib

matplotlib.use("Agg")  # headless: never opens a window, never calls plt.show()
import matplotlib.pyplot as plt
import numpy as np

SEED = 1729
RNG = np.random.default_rng(SEED)
HERE = os.path.dirname(os.path.abspath(__file__))
PNG_PATH = os.path.join(HERE, "04_cosine_vs_dimension.png")

LINE = "=" * 70


def banner(title):
    print(LINE)
    print(title)
    print(LINE)


# ----------------------------------------------------------------------------
# Shared helpers
# ----------------------------------------------------------------------------
def unit(v, axis=-1):
    """L2-normalise: divide every vector by its own length so ||v|| == 1.

    This single operation is what makes dot product and cosine interchangeable,
    which is why every embedding store (5.1) offers it as a switch.
    """
    return v / np.linalg.norm(v, axis=axis, keepdims=True)


def softmax_stable(x):
    """Softmax with the max subtracted first - the version everyone should use.

    Subtracting a constant from every logit does not change the result
    mathematically (the constant cancels top and bottom), but it stops exp()
    from overflowing. Demo 6 shows the naive version failing on real numbers.
    """
    z = x - np.max(x)
    e = np.exp(z)
    return e / e.sum()


def softmax_naive(x):
    """The textbook formula written literally. Overflows for large logits."""
    e = np.exp(x)
    return e / e.sum()


def entropy_nats(p):
    """Shannon entropy in nats. 0 means all mass on one item (saturated)."""
    p = p[p > 0]
    return float(-(p * np.log(p)).sum())


# ----------------------------------------------------------------------------
# DEMO 1 - one dot product, four independent routes
# ----------------------------------------------------------------------------
def demo1_four_routes():
    banner("DEMO 1 - one dot product, four independent routes to one number")

    a = np.array([3.0, -1.0, 2.0, 0.5])
    b = np.array([1.0, 4.0, -2.0, 6.0])
    print(f"  a = {a}")
    print(f"  b = {b}")
    print()

    # Route A - the definition, one multiply-and-add at a time in pure Python.
    # This is what the formula literally says: sum over i of a_i * b_i.
    running = 0.0
    parts = []
    for i in range(a.size):
        term = float(a[i]) * float(b[i])
        running += term
        parts.append(f"{a[i]:+.1f}*{b[i]:+.1f}={term:+.2f}")
    route_a = running
    print("  route A - explicit sum, term by term (the definition)")
    print("    " + "  ".join(parts))
    print(f"    total = {route_a:.15f}")
    print()

    # Route B - numpy's BLAS-backed kernel. Different code, different order of
    # summation, possibly SIMD. Agreement here is not a tautology.
    route_b = float(np.dot(a, b))
    print(f"  route B - np.dot (BLAS kernel, different summation order)")
    print(f"    total = {route_b:.15f}")
    print()

    # Route C - the polarization identity:
    #     a.b = ( ||a+b||^2 - ||a-b||^2 ) / 4
    # This route never multiplies a_i by b_i at all. It only measures LENGTHS
    # (1.1). That is the deep fact: the dot product is fully determined by the
    # lengths of a, b, a+b and a-b. Geometry alone recovers the algebra.
    len_sum = float(np.linalg.norm(a + b))
    len_dif = float(np.linalg.norm(a - b))
    route_c = (len_sum**2 - len_dif**2) / 4.0
    print("  route C - polarization identity, LENGTHS ONLY, no a_i*b_i product")
    print(f"    ||a+b|| = {len_sum:.15f}")
    print(f"    ||a-b|| = {len_dif:.15f}")
    print(f"    (||a+b||^2 - ||a-b||^2)/4 = {route_c:.15f}")
    print()

    # Route D - the geometric form ||a||*||b||*cos(theta). To keep this honest,
    # theta is recovered from the LAW OF COSINES using only the three lengths,
    # never from the dot product itself - otherwise the check would be circular.
    na = float(np.linalg.norm(a))
    nb = float(np.linalg.norm(b))
    cos_theta = (na**2 + nb**2 - len_dif**2) / (2.0 * na * nb)
    theta = float(np.arccos(np.clip(cos_theta, -1.0, 1.0)))
    route_d = na * nb * np.cos(theta)
    print("  route D - ||a||*||b||*cos(theta), theta from the law of cosines")
    print(f"    ||a|| = {na:.15f}   ||b|| = {nb:.15f}")
    print(f"    cos(theta) = {cos_theta:.15f}   theta = {np.degrees(theta):.6f} deg")
    print(f"    ||a||*||b||*cos(theta) = {route_d:.15f}")
    print()

    vals = np.array([route_a, route_b, route_c, route_d])
    spread = float(np.max(vals) - np.min(vals))
    print(f"  four routes, max abs spread: {spread:.3e}")
    print("  -> they are the same number; the spread is float64 rounding only")
    print()

    # An angle above 90 degrees means a NEGATIVE dot product: the vectors point
    # partly against each other. In retrieval (5.5) that is a candidate scoring
    # worse than an unrelated one.
    print(f"  theta = {np.degrees(theta):.2f} deg is > 90, so a.b is NEGATIVE:"
          f" {route_b:+.2f}")
    print("  sign of a.b:  > 0 same general direction | = 0 orthogonal"
          " | < 0 opposed")


# ----------------------------------------------------------------------------
# DEMO 2 - projection, and the orthogonal residual
# ----------------------------------------------------------------------------
def demo2_projection():
    banner("DEMO 2 - projection: the shadow of a on b, and what is left over")

    a = np.array([5.0, 1.0, -2.0])
    b = np.array([1.0, 2.0, 2.0])  # length exactly 3, chosen for readability
    nb = float(np.linalg.norm(b))
    dot_ab = float(np.dot(a, b))

    # SCALAR projection: how far along b you travel. Units of length.
    comp = dot_ab / nb
    # VECTOR projection: that distance turned back into a vector along b.
    proj = (dot_ab / float(np.dot(b, b))) * b
    # RESIDUAL: the part of a that b cannot explain at all.
    resid = a - proj

    print(f"  a = {a}    b = {b}   (||b|| = {nb:.1f})")
    print(f"  a.b = {dot_ab:.6f}")
    print()
    print("  scalar projection  comp_b(a) = a.b / ||b||")
    print(f"    = {dot_ab:.6f} / {nb:.6f} = {comp:.15f}")
    print("  vector projection  proj_b(a) = (a.b / b.b) * b")
    print(f"    = ({dot_ab:.4f} / {float(np.dot(b, b)):.4f}) * b"
          f" = {np.array2string(proj, precision=6)}")
    print(f"  residual           r = a - proj_b(a)"
          f" = {np.array2string(resid, precision=6)}")
    print()

    # THE CHECK. If proj really is the shadow, then whatever is left over must
    # be perpendicular to b - there is nothing of b's direction remaining.
    orth = float(np.dot(resid, b))
    print(f"  CHECK 1  r . b = {orth:+.3e}   (must be 0 - it is, to 1e-16)")

    # Pythagoras: shadow and residual are the two legs of a right triangle
    # whose hypotenuse is a. ||a||^2 = ||proj||^2 + ||r||^2.
    lhs = float(np.dot(a, a))
    rhs = float(np.dot(proj, proj)) + float(np.dot(resid, resid))
    print(f"  CHECK 2  ||a||^2 = {lhs:.15f}")
    print(f"           ||proj||^2 + ||r||^2 = {rhs:.15f}")
    print(f"           abs diff = {abs(lhs - rhs):.3e}")

    # Projecting twice changes nothing: the shadow of a shadow is the shadow.
    proj2 = (float(np.dot(proj, b)) / float(np.dot(b, b))) * b
    print(f"  CHECK 3  proj(proj(a)) - proj(a) max abs"
          f" = {float(np.max(np.abs(proj2 - proj))):.3e}   (idempotent)")

    # cos(theta) is just the scalar projection measured in units of ||a||.
    cos_t = comp / float(np.linalg.norm(a))
    cos_direct = dot_ab / (float(np.linalg.norm(a)) * nb)
    print(f"  CHECK 4  comp_b(a)/||a|| = {cos_t:.15f}")
    print(f"           a.b/(||a|| ||b||) = {cos_direct:.15f}   "
          f"diff = {abs(cos_t - cos_direct):.3e}")
    print("  -> cosine IS the projection, rescaled so length cannot matter")
    print()

    # Same claim, stress-tested in 200 dimensions over 2000 random pairs, so it
    # is not an artefact of three tidy numbers. Orthogonal residuals are the
    # engine behind orthogonal bases (1.3).
    d, trials = 200, 2000
    A = RNG.normal(size=(trials, d))
    B = RNG.normal(size=(trials, d))
    coef = np.einsum("td,td->t", A, B) / np.einsum("td,td->t", B, B)
    R = A - coef[:, None] * B
    residual_dots = np.einsum("td,td->t", R, B)
    lhs_v = np.einsum("td,td->t", A, A)
    rhs_v = (coef**2) * np.einsum("td,td->t", B, B) + np.einsum("td,td->t", R, R)
    print(f"  stress test: {trials} random pairs in d={d}")
    print(f"    max |r . b|                 = "
          f"{float(np.max(np.abs(residual_dots))):.3e}")
    print(f"    max Pythagoras relative err = "
          f"{float(np.max(np.abs(lhs_v - rhs_v) / lhs_v)):.3e}")


# ----------------------------------------------------------------------------
# DEMO 3 - the retrieval lesson: dot and cosine disagree
# ----------------------------------------------------------------------------
def demo3_ranking_disagreement():
    banner("DEMO 3 - dot vs cosine RANK DIFFERENTLY (the retrieval lesson)")

    axes = ["vector-db", "transformers", "python", "cooking", "sports", "finance"]
    # A hand-built toy embedding space so every number is inspectable. Each
    # coordinate is "how much this document is about that topic". Real
    # embeddings (5.1) are learned and dense, but the geometry is identical.
    query = np.array([0.20, 1.00, 0.30, 0.00, 0.00, 0.00])
    names = [
        "note-attention-scores",     # short, focused, almost exactly on topic
        "megapage-everything-ml",    # long, covers everything, huge norm
        "guide-vector-db-tuning",
        "cheatsheet-python-basics",
        "summary-transformer-paper",
    ]
    docs = np.array([
        [0.11, 0.66, 0.19, 0.00, 0.00, 0.00],
        [2.60, 2.90, 2.70, 1.80, 1.40, 2.20],
        [1.90, 0.40, 0.90, 0.00, 0.00, 0.10],
        [0.10, 0.10, 2.40, 0.00, 0.00, 0.00],
        [0.30, 1.60, 0.40, 0.00, 0.00, 0.00],
    ])

    print("  axes: " + ", ".join(axes))
    print(f"  query 'how do attention scores work' = {query}")
    print(f"  ||query|| = {float(np.linalg.norm(query)):.6f}")
    print()

    dots = docs @ query
    norms = np.linalg.norm(docs, axis=1)
    cos = dots / (norms * float(np.linalg.norm(query)))
    l2 = np.linalg.norm(docs - query, axis=1)

    print("  document                    ||d||     dot      cosine    L2 dist")
    print("  ------------------------- -------  -------   --------   --------")
    for i, n in enumerate(names):
        print(f"  {n:<25} {norms[i]:7.4f}  {dots[i]:7.4f}   {cos[i]:8.5f}   "
              f"{l2[i]:8.5f}")
    print()

    order_dot = np.argsort(-dots)
    order_cos = np.argsort(-cos)
    order_l2 = np.argsort(l2)
    print("  ranking by DOT     : " + " > ".join(names[i] for i in order_dot))
    print("  ranking by COSINE  : " + " > ".join(names[i] for i in order_cos))
    print("  ranking by L2      : " + " > ".join(names[i] for i in order_l2))
    print()

    key = 0
    print(f"  '{names[key]}' is the best match by DIRECTION"
          f" (cos = {cos[key]:.5f})")
    print(f"    its rank under cosine : {int(np.where(order_cos == key)[0][0]) + 1}"
          f" of {len(names)}")
    print(f"    its rank under dot    : {int(np.where(order_dot == key)[0][0]) + 1}"
          f" of {len(names)}  <- LAST")
    fat = 1
    print(f"  '{names[fat]}' wins on dot only because it is LONG:"
          f" ||d|| = {norms[fat]:.4f}")
    print(f"    dot = {dots[fat]:.4f} = cos {cos[fat]:.5f} * ||q|| "
          f"{float(np.linalg.norm(query)):.4f} * ||d|| {norms[fat]:.4f}")
    print("    that is the whole bug: dot = cosine TIMES the two lengths")
    print()

    # THE FIX. Normalise every document (and the query) to length 1. Now the
    # length factor is 1*1 and dot product IS cosine.
    print("  --- now L2-normalise every vector to length 1 ---")
    q_u = unit(query)
    d_u = unit(docs, axis=1)
    dots_u = d_u @ q_u
    cos_u = dots_u / (np.linalg.norm(d_u, axis=1) * float(np.linalg.norm(q_u)))
    print(f"  max |dot_normalised - cosine_original| = "
          f"{float(np.max(np.abs(dots_u - cos))):.3e}")
    order_dot_u = np.argsort(-dots_u)
    order_cos_u = np.argsort(-cos_u)
    print("  ranking by DOT on unit vectors   : "
          + " > ".join(names[i] for i in order_dot_u))
    print("  ranking by COSINE on unit vectors: "
          + " > ".join(names[i] for i in order_cos_u))
    print(f"  identical ordering: {bool(np.array_equal(order_dot_u, order_cos_u))}")
    print(f"  matches the ORIGINAL cosine ordering:"
          f" {bool(np.array_equal(order_dot_u, order_cos))}")


# ----------------------------------------------------------------------------
# DEMO 4 - exactly when the two agree, measured over 20,000 trials
# ----------------------------------------------------------------------------
def demo4_when_they_agree():
    banner("DEMO 4 - 20,000 random trials: when do dot and cosine agree?")

    trials, k, d = 20000, 8, 32
    print(f"  {trials} trials, {k} candidates each, d = {d}, seed {SEED}")
    print()

    Q = RNG.normal(size=(trials, d))
    C = RNG.normal(size=(trials, k, d))
    C_dir = C / np.linalg.norm(C, axis=2, keepdims=True)  # pure directions

    def measure(lengths, label, show_longest):
        cand = C_dir * lengths[..., None]
        dots = np.einsum("td,tkd->tk", Q, cand)
        cn = np.linalg.norm(cand, axis=2)
        qn = np.linalg.norm(Q, axis=1, keepdims=True)
        cos = dots / (qn * cn)
        top_dot = dots.argmax(axis=1)
        top_cos = cos.argmax(axis=1)
        top1 = float(np.mean(top_dot != top_cos))
        full = float(np.mean(np.any(np.argsort(-dots, axis=1)
                                    != np.argsort(-cos, axis=1), axis=1)))
        print(f"  {label}")
        print(f"    top-1 hit differs      : {top1 * 100:6.2f}% of trials")
        print(f"    full ranking differs   : {full * 100:6.2f}% of trials")
        if show_longest:
            # Only meaningful when lengths actually differ. With all lengths
            # equal there is no "longest", so the statistic would be noise.
            longest = lengths.argmax(axis=1)
            print(f"    dot's winner is also")
            print(f"      the LONGEST candidate: "
                  f"{float(np.mean(top_dot == longest)) * 100:6.2f}% of trials"
                  f"   (chance = {100 / k:.2f}%)")
        return top1, full

    # Case A - candidate lengths vary, as real document embeddings do.
    varied = RNG.lognormal(mean=0.0, sigma=0.8, size=(trials, k))
    print(f"  case A: candidate lengths VARY "
          f"(lognormal, min {varied.min():.3f} max {varied.max():.3f})")
    measure(varied, "  measured:", True)
    print()

    # Case B - all candidates forced to one common length. Note it is 2.5, not
    # 1.0: the condition is EQUAL norms, not UNIT norms. Unit norm is just the
    # convenient choice that also makes the score land in [-1, 1].
    equal = np.full((trials, k), 2.5)
    print("  case B: every candidate rescaled to the SAME length 2.5"
          " (not 1.0 - equality is what matters)")
    top1_b, full_b = measure(equal, "  measured:", False)
    print()
    print(f"  -> with equal candidate lengths the two agree on"
          f" {(1 - full_b) * 100:.2f}% of ALL {trials} full rankings")
    print("  -> this is skip-test (1) answered by measurement, not assertion")
    print()

    # The query's own length is a single positive constant multiplying every
    # score, so it can never reorder anything. Verified rather than asserted.
    scale = RNG.uniform(0.01, 100.0, size=(trials, 1))
    cand = C_dir * varied[..., None]
    base = np.einsum("td,tkd->tk", Q, cand)
    scaled = np.einsum("td,tkd->tk", Q * scale, cand)
    same = bool(np.array_equal(np.argsort(-base, axis=1),
                               np.argsort(-scaled, axis=1)))
    print(f"  bonus: multiply the QUERY by a random factor in [0.01, 100]")
    print(f"    every one of {trials} dot-product rankings unchanged: {same}")
    print("    (query length is a common positive factor - it cancels out;")
    print("     only the CANDIDATE lengths can reorder results)")


# ----------------------------------------------------------------------------
# DEMO 5 - random high-dimensional vectors are nearly orthogonal
# ----------------------------------------------------------------------------
def demo5_near_orthogonality():
    banner("DEMO 5 - in high dimensions, random vectors are nearly orthogonal")

    dims = [2, 3, 10, 100, 1000, 10000]
    n = 20000
    print(f"  {n} random pairs at each dimension; cos measured directly")
    print()
    print("      d   mean|cos|   sqrt(2/(pi d))    std(cos)   1/sqrt(d)"
          "   P(|cos|<0.05)")
    print("  ------ ----------  --------------  ----------  ----------"
          "  -------------")
    means, stds = [], []
    for d in dims:
        A = RNG.normal(size=(n, d))
        B = RNG.normal(size=(n, d))
        c = (np.einsum("nd,nd->n", A, B)
             / (np.linalg.norm(A, axis=1) * np.linalg.norm(B, axis=1)))
        m = float(np.mean(np.abs(c)))
        s = float(np.std(c))
        means.append(m)
        stds.append(s)
        theory_m = float(np.sqrt(2.0 / (np.pi * d)))
        theory_s = 1.0 / np.sqrt(d)
        frac = float(np.mean(np.abs(c) < 0.05))
        print(f"  {d:6d}  {m:10.6f}  {theory_m:14.6f}  {s:10.6f}"
              f"  {theory_s:10.6f}  {frac * 100:11.2f}%")
    print()
    # std(cos) = 1/sqrt(d) is EXACT for every d, not an approximation. This is
    # the strong check: analytic result versus brute-force simulation.
    rel = [abs(stds[i] - 1 / np.sqrt(d)) / (1 / np.sqrt(d))
           for i, d in enumerate(dims)]
    print(f"  std(cos) vs the exact analytic 1/sqrt(d):"
          f" worst relative error {max(rel) * 100:.3f}%")
    print("    (that identity is exact at EVERY d - simulation confirms it)")
    # mean|cos| ~ sqrt(2/(pi d)) is only asymptotic. Say so honestly.
    err2 = abs(means[0] - np.sqrt(2 / (np.pi * 2))) / means[0]
    err10 = abs(means[2] - np.sqrt(2 / (np.pi * 10))) / means[2]
    print(f"  mean|cos| vs sqrt(2/(pi d)): off by {err2 * 100:.1f}% at d=2,"
          f" {err10 * 100:.1f}% at d=10")
    print("    (that one is an ASYMPTOTIC approximation - visibly wrong when d"
          " is tiny)")
    print()
    print("  WHY THIS MATTERS: at d=2 two random directions are typically 50 deg"
          " apart;")
    print(f"  at d=1000 the mean |cos| is {means[4]:.4f} - essentially"
          " perpendicular.")
    print("  Unrelated things get scores near zero for free, so a high cosine"
          " really")
    print("  means something. That is why 768 dimensions holds so much meaning"
          " (5.1).")

    # ---- plot -------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(7.0, 4.2), dpi=130)
    dd = np.array(dims, dtype=float)
    ax.loglog(dd, means, "o-", color="#005f73", lw=2, label="measured mean |cos|")
    ax.loglog(dd, np.sqrt(2.0 / (np.pi * dd)), "--", color="#b08968", lw=2,
              label="sqrt(2/(pi d))  (asymptotic)")
    ax.loglog(dd, stds, "s-", color="#1b4332", lw=2, label="measured std(cos)")
    ax.loglog(dd, 1.0 / np.sqrt(dd), ":", color="#9b2226", lw=2,
              label="1/sqrt(d)  (exact)")
    ax.set_xlabel("dimension d")
    ax.set_ylabel("cosine between two random vectors")
    ax.set_title("Random directions become orthogonal as d grows")
    ax.grid(True, which="both", alpha=0.3)
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(PNG_PATH)
    plt.close(fig)
    print()
    print(f"  saved plot: {os.path.basename(PNG_PATH)}"
          f"  ({os.path.getsize(PNG_PATH)} bytes)")


# ----------------------------------------------------------------------------
# DEMO 6 - attention: the same dot product, wearing a different name
# ----------------------------------------------------------------------------
def demo6_attention_scaling():
    banner("DEMO 6 - attention scores ARE dot products, and why sqrt(d) is there")

    # ---- part A: one attention row, two independent ways -------------------
    d_head, n_keys, d_val = 4, 5, 3
    q = RNG.normal(size=d_head)
    K = RNG.normal(size=(n_keys, d_head))
    V = RNG.normal(size=(n_keys, d_val))

    # Matrix form - exactly what softmax(Q K^T / sqrt(d)) V computes (4.2).
    scores = (K @ q) / np.sqrt(d_head)
    w = softmax_stable(scores)
    out_matrix = w @ V

    # Loop form - dot product by dot product, no matmul anywhere.
    scores_loop = np.array([float(np.dot(K[i], q)) / np.sqrt(d_head)
                            for i in range(n_keys)])
    w_loop = softmax_stable(scores_loop)
    out_loop = np.zeros(d_val)
    for i in range(n_keys):
        out_loop += w_loop[i] * V[i]

    print(f"  one query, {n_keys} keys, head dim d = {d_head}")
    print("  raw scores  q.k_i         : "
          + " ".join(f"{float(np.dot(K[i], q)):+7.4f}" for i in range(n_keys)))
    print(f"  scaled      q.k_i/sqrt(d): "
          + " ".join(f"{s:+7.4f}" for s in scores))
    print("  softmax weights          : " + " ".join(f"{x:7.4f}" for x in w))
    print(f"  weights sum to {float(w.sum()):.15f}")
    print(f"  output (matmul) = {np.array2string(out_matrix, precision=6)}")
    print(f"  output (loop)   = {np.array2string(out_loop, precision=6)}")
    print(f"  max abs diff = "
          f"{float(np.max(np.abs(out_matrix - out_loop))):.3e}")
    print("  -> an attention row is nothing but these dot products turned into")
    print("     weights, then used to average the value vectors (4.2)")
    print()

    # ---- part B: score variance grows with d -------------------------------
    print("  why divide by sqrt(d)? because raw scores GROW with d:")
    print("     d    std(q.k)   sqrt(d)   std(q.k/sqrt(d))")
    print("  -----  ---------  --------  -----------------")
    for dh in [8, 64, 512, 4096]:
        n = 50000
        A = RNG.normal(size=(n, dh))
        B = RNG.normal(size=(n, dh))
        s = np.einsum("nd,nd->n", A, B)
        print(f"  {dh:5d}  {float(np.std(s)):9.4f}  {np.sqrt(dh):8.4f}"
              f"  {float(np.std(s / np.sqrt(dh))):17.4f}")
    print("  -> each of d coordinates contributes independent variance 1, so")
    print("     Var(q.k) = d exactly, and std = sqrt(d). Dividing by sqrt(d)")
    print("     pins the spread at 1.0 no matter how wide the head is.")
    print()

    # ---- part C: what saturation actually costs ----------------------------
    dh, nk = 512, 8
    qq = RNG.normal(size=dh)
    KK = RNG.normal(size=(nk, dh))
    raw = KK @ qq
    scaled = raw / np.sqrt(dh)
    for label, logits in (("UNSCALED q.k", raw), ("SCALED q.k/sqrt(d)", scaled)):
        p = softmax_stable(logits)
        h = entropy_nats(p)
        print(f"  {label:<20} logit range [{logits.min():+8.2f},"
              f" {logits.max():+8.2f}]")
        print(f"    weights           : " + " ".join(f"{x:6.4f}" for x in p))
        print(f"    largest weight    : {float(p.max()):.6f}")
        print(f"    entropy (nats)    : {h:.6f}")
        print(f"    effective #keys   : {np.exp(h):.3f} of {nk}")
        print(f"    max p*(1-p)       : {float(np.max(p * (1 - p))):.3e}"
              "   <- softmax gradient scale")
    print("  -> unscaled, one key takes essentially all the weight and the")
    print("     gradient factor collapses; the layer stops learning. The")
    print("     sqrt(d) divisor exists to prevent exactly this.")
    print()

    # ---- part D: the naive softmax failing, next to the correct one --------
    print("  and the softmax itself has a naive version that FAILS:")
    big = np.array([800.0, 799.0, 795.0])
    with np.errstate(over="ignore", invalid="ignore"):
        bad = softmax_naive(big)
    good = softmax_stable(big)
    print(f"    logits              : {big}")
    print(f"    naive exp(x)/sum    : {bad}   <- inf/inf = nan")
    print(f"    stable exp(x-max)/..: {np.array2string(good, precision=6)}")
    print(f"    stable weights sum  : {float(good.sum()):.15f}")
    print("    both formulas are the SAME mathematics; only one survives"
          " float64.")


# ----------------------------------------------------------------------------
# DEMO 7 - cosine, dot and L2: three names, one geometry
# ----------------------------------------------------------------------------
def demo7_three_metrics():
    banner("DEMO 7 - cosine vs dot vs L2: the choice every vector search makes")

    n, d = 100000, 64
    A = unit(RNG.normal(size=(n, d)), axis=1)
    B = unit(RNG.normal(size=(n, d)), axis=1)
    cos = np.einsum("nd,nd->n", A, B)
    sq_l2 = np.einsum("nd,nd->n", A - B, A - B)
    identity_err = float(np.max(np.abs(sq_l2 - (2.0 - 2.0 * cos))))
    print(f"  {n} random UNIT pairs in d = {d}")
    print("  claim: for unit vectors,  ||a - b||^2 = 2 - 2*cos(theta)")
    print(f"    max abs difference over all {n} pairs: {identity_err:.3e}")
    print("  -> squared L2 distance is a strictly DECREASING function of"
          " cosine,")
    print("     so on unit vectors the two produce the SAME ranking, always.")
    print()

    trials, k = 5000, 10
    Q = RNG.normal(size=(trials, d))
    C = RNG.normal(size=(trials, k, d))

    def rank_clash(qs, cs):
        dots = np.einsum("td,tkd->tk", qs, cs)
        cn = np.linalg.norm(cs, axis=2)
        qn = np.linalg.norm(qs, axis=1, keepdims=True)
        co = dots / (qn * cn)
        l2 = np.linalg.norm(cs - qs[:, None, :], axis=2)
        cos_order = np.argsort(-co, axis=1)
        l2_order = np.argsort(l2, axis=1)
        dot_order = np.argsort(-dots, axis=1)
        return (float(np.mean(np.any(cos_order != l2_order, axis=1))),
                float(np.mean(np.any(cos_order != dot_order, axis=1))))

    raw_l2, raw_dot = rank_clash(Q, C)
    print(f"  {trials} retrieval trials, {k} candidates, RAW vectors:")
    print(f"    cosine ranking differs from L2  : {raw_l2 * 100:6.2f}% of trials")
    print(f"    cosine ranking differs from dot : {raw_dot * 100:6.2f}% of trials")

    n_l2, n_dot = rank_clash(unit(Q, axis=1), unit(C, axis=2))
    print(f"  same {trials} trials, every vector L2-NORMALISED:")
    print(f"    cosine ranking differs from L2  : {n_l2 * 100:6.2f}% of trials")
    print(f"    cosine ranking differs from dot : {n_dot * 100:6.2f}% of trials")
    print()
    print("  metric        keeps length?  score range   use when")
    print("  ------------  -------------  ------------  -------------------------")
    print("  dot product   YES            (-inf, inf)   length carries meaning,")
    print("                                             or vectors are already")
    print("                                             normalised (fastest)")
    print("  cosine        NO             [-1, 1]       you want topic match and")
    print("                                             not document length (5.5)")
    print("  L2 distance   YES            [0, inf)      absolute position matters;")
    print("                                             equals cosine order only")
    print("                                             after normalisation")


# ----------------------------------------------------------------------------
def main():
    print(f"numpy {np.__version__} | seed {SEED} | offline, no network")
    print(f"script dir: {HERE}")
    demo1_four_routes()
    demo2_projection()
    demo3_ranking_disagreement()
    demo4_when_they_agree()
    demo5_near_orthogonality()
    demo6_attention_scaling()
    demo7_three_metrics()
    print(LINE)
    print("done - every claim above was computed, not asserted")
    print(LINE)


if __name__ == "__main__":
    main()
