"""
1.2 - Matrices and Matrix Multiplication as Linear Maps
======================================================

What this runs
--------------
Seven self-contained demos that treat a matrix as a FUNCTION that moves points
around space, and matrix multiplication as COMPOSITION of two such functions.
Everything is checked numerically rather than asserted: quantities are computed
two independent ways and the disagreement is printed.

Requirements
------------
numpy (tested on 2.4.4) and matplotlib (tested on 3.11.1, Agg backend only).
Python 3.14 on Windows is the reference environment. No network access, no file
writes outside this script's own directory, no subprocesses. One PNG is saved
beside this script; its byte size is printed. Safe to run offline, repeatedly.

Reproducibility
---------------
Every random number comes from np.random.default_rng(SEED) with SEED = 1202.
Re-running gives byte-identical numbers.

What this proves practically
----------------------------
1.  The columns of a matrix ARE the images of the basis vectors: A @ e_j equals
    column j of A exactly, and a hand-written triple loop reproduces numpy's
    matrix-vector product to machine precision.
2.  A diagonal matrix stretches each coordinate AXIS independently by its
    diagonal entry - measured per-axis, not asserted (skip test 2).
3.  det(A) is the area scale factor of the map: the shoelace area of the
    transformed unit square, a Monte-Carlo area estimate, and np.linalg.det
    all agree, with the Monte-Carlo error shrinking as sample count grows.
4.  Matrix multiplication is composition: (A @ B) @ x equals A @ (B @ x) to
    machine precision, while A @ B != B @ A - order is composition order.
5.  A projection matrix satisfies P @ P == P (idempotence) to machine
    precision, and the residual is exactly orthogonal to the target line.
6.  Shape discipline: (n,d) @ (d,k) -> (n,k) is the only legal contraction;
    the real ValueError text from a wrong-way multiply is printed (skip test 1).
7.  A singular matrix has det 0, no inverse, collapses the plane onto a line,
    and destroys the solution of a linear system - shown alongside a
    near-singular matrix whose answer is quietly wrong.
"""

from __future__ import annotations

import os

import matplotlib

matplotlib.use("Agg")  # headless: never opens a window, never calls plt.show()

import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

SEED = 1202
RNG = np.random.default_rng(SEED)

HERE = os.path.dirname(os.path.abspath(__file__))
PNG_PATH = os.path.join(HERE, "02_matrices_as_linear_maps.png")


def banner(title: str) -> None:
    """Every demo announces itself the same way so the transcript is scannable."""
    print("=" * 70)
    print(title)
    print("=" * 70)


# The four canonical 2x2 maps used throughout. Each is a FUNCTION from the plane
# to the plane; the name describes what it does to a point, not what it looks
# like as a grid of numbers.
THETA = np.deg2rad(30.0)
ROT = np.array([[np.cos(THETA), -np.sin(THETA)],
                [np.sin(THETA),  np.cos(THETA)]])
SCALE = np.array([[2.0, 0.0],
                  [0.0, 0.5]])
SCALE_UP = np.array([[1.5, 0.0],
                     [0.0, 2.0]])
SHEAR = np.array([[1.0, 1.5],
                  [0.0, 1.0]])
# Projection onto the line spanned by u (a 45-degree line). Built as the outer
# product u u^T / (u^T u) - the general formula that returns in 2.3 as the hat
# matrix of least squares.
U = np.array([1.0, 1.0])
PROJ = np.outer(U, U) / (U @ U)

UNIT_SQUARE = np.array([[0.0, 0.0],
                        [1.0, 0.0],
                        [1.0, 1.0],
                        [0.0, 1.0]])  # shape (4, 2): FOUR points, each 2-D


def shoelace_area(poly: np.ndarray) -> float:
    """Signed area of a simple polygon given as (n, 2) vertices in order.

    This is an independent, geometry-only measurement of area. It never calls
    np.linalg.det, which is the whole point: demo 3 compares it against det.
    """
    x = poly[:, 0]
    y = poly[:, 1]
    return 0.5 * float(np.sum(x * np.roll(y, -1) - np.roll(x, -1) * y))


# ---------------------------------------------------------------------------
# DEMO 1
# ---------------------------------------------------------------------------
def demo1_matrix_is_a_function() -> None:
    banner("DEMO 1 - a matrix is a FUNCTION; its columns are where the axes go")

    A = np.array([[2.0, -1.0],
                  [1.0,  3.0]])
    e1 = np.array([1.0, 0.0])
    e2 = np.array([0.0, 1.0])

    print("  A =")
    for row in A:
        print("      [{: .4f} {: .4f}]".format(row[0], row[1]))
    print()
    # This is the single most useful fact about matrices: applying A to the
    # basis vector e_j simply READS OFF column j. Nothing is computed that was
    # not already written down. Every weight matrix in 3.1 is therefore a list
    # of "where each input axis lands".
    print("  A @ e1 = {}   <- exactly column 0 of A".format(A @ e1))
    print("  A @ e2 = {}   <- exactly column 1 of A".format(A @ e2))
    print("  max abs diff vs the literal columns: {:.3e}".format(
        float(np.max(np.abs(np.column_stack([A @ e1, A @ e2]) - A)))))
    print()

    # Linearity, stated as an equation and then MEASURED. A(av + bw) = aAv + bAw
    # is the entire definition of "linear map"; everything else follows from it.
    v = RNG.normal(size=2)
    w = RNG.normal(size=2)
    a, b = 2.5, -1.75
    lhs = A @ (a * v + b * w)
    rhs = a * (A @ v) + b * (A @ w)
    print("  linearity check  A(av + bw) == aAv + bAw")
    print("    a = {:.2f}   b = {:.2f}".format(a, b))
    print("    v = {}".format(np.array2string(v, precision=6)))
    print("    w = {}".format(np.array2string(w, precision=6)))
    print("    LHS = {}".format(np.array2string(lhs, precision=12)))
    print("    RHS = {}".format(np.array2string(rhs, precision=12)))
    print("    max abs diff: {:.3e}".format(float(np.max(np.abs(lhs - rhs)))))
    print()

    # Hand-rolled matrix-vector product. Written as the textbook double loop so
    # the row-dot-column definition is visible, then compared with numpy. If the
    # definition in your head is right, this difference is ~1e-16.
    def matvec_by_hand(M: np.ndarray, x: np.ndarray) -> np.ndarray:
        out = np.zeros(M.shape[0])
        for i in range(M.shape[0]):        # one output component per ROW
            s = 0.0
            for j in range(M.shape[1]):    # sum over the shared dimension
                s += M[i, j] * x[j]
            out[i] = s
        return out

    B = RNG.normal(size=(5, 4))
    x = RNG.normal(size=4)
    print("  hand-written double loop vs numpy '@', B is 5x4, x is length 4")
    print("    numpy : {}".format(np.array2string(B @ x, precision=10)))
    print("    byhand: {}".format(np.array2string(matvec_by_hand(B, x), precision=10)))
    print("    max abs diff: {:.3e}".format(
        float(np.max(np.abs(matvec_by_hand(B, x) - B @ x)))))


# ---------------------------------------------------------------------------
# DEMO 2  (skip test 2)
# ---------------------------------------------------------------------------
def demo2_diagonal_stretches_axes() -> None:
    banner("DEMO 2 - a DIAGONAL matrix stretches each axis independently")

    D = np.diag([3.0, 0.5, -2.0])
    print("  D = diag(3.0, 0.5, -2.0)")
    print("  D @ e1 = {}".format(D @ np.eye(3)[0]))
    print("  D @ e2 = {}".format(D @ np.eye(3)[1]))
    print("  D @ e3 = {}".format(D @ np.eye(3)[2]))
    print()

    # MEASURE the per-axis scale factor instead of asserting it: take random
    # points, transform them, and divide componentwise. If the claim "axis j is
    # scaled by d_j and nothing else happens" is true, every ratio in column j
    # is identical and equals d_j.
    pts = RNG.normal(size=(6, 3))
    out = pts @ D.T          # rows are points -> right-multiply by D transpose
    ratios = out / pts       # componentwise, so column j is the axis-j ratio
    print("  measured per-axis ratio out[:, j] / in[:, j] over 6 random points")
    print("    axis 0: min {:.12f}  max {:.12f}".format(
        float(ratios[:, 0].min()), float(ratios[:, 0].max())))
    print("    axis 1: min {:.12f}  max {:.12f}".format(
        float(ratios[:, 1].min()), float(ratios[:, 1].max())))
    print("    axis 2: min {:.12f}  max {:.12f}".format(
        float(ratios[:, 2].min()), float(ratios[:, 2].max())))
    print("    max spread within any axis: {:.3e}   (0 => pure axis scaling)".format(
        float(np.max(ratios.max(axis=0) - ratios.min(axis=0)))))
    print()

    # No mixing: a diagonal matrix never lets coordinate i affect coordinate j.
    # That is exactly why diagonal matrices are cheap - the "matmul" degenerates
    # into an elementwise multiply, which is what a per-channel scale layer is.
    elementwise = pts * np.array([3.0, 0.5, -2.0])
    print("  diag(d) @ x is the SAME as elementwise x * d")
    print("    max abs diff: {:.3e}".format(float(np.max(np.abs(out - elementwise)))))
    print("  determinant of D  = {:.6f}   (product of the diagonal: 3 * 0.5 * -2)".format(
        float(np.linalg.det(D))))
    print("  |det| = 3.0 => volumes triple; the negative sign flips orientation")
    print()

    # 2-D version, so it lines up with the saved picture and with demo 3.
    D2 = np.diag([2.0, 0.5])
    sq = UNIT_SQUARE @ D2.T
    print("  2-D: diag(2.0, 0.5) applied to the unit square corners")
    print("    corners in : {}".format(
        np.array2string(UNIT_SQUARE, precision=1).replace("\n", "")))
    print("    corners out: {}".format(
        np.array2string(sq, precision=1).replace("\n", "")))
    print("    width  1.0 -> {:.4f}   height 1.0 -> {:.4f}".format(
        float(sq[:, 0].max() - sq[:, 0].min()),
        float(sq[:, 1].max() - sq[:, 1].min())))
    print("    area   1.0 -> {:.4f}   det = {:.4f}".format(
        abs(shoelace_area(sq)), float(np.linalg.det(D2))))
    print("    note the det is 1, because 2 * 0.5 = 1: the square became a")
    print("    wide flat rectangle. The SHAPE changed; the AREA did not.")


# ---------------------------------------------------------------------------
# DEMO 3
# ---------------------------------------------------------------------------
def demo3_determinant_is_area_scale() -> None:
    banner("DEMO 3 - det(A) is the AREA SCALE FACTOR, measured three ways")

    maps = [("rotation 30 deg", ROT),
            ("scale (2, 0.5)", SCALE),
            ("scale (1.5, 2.0)", SCALE_UP),
            ("shear (1.5 in x)", SHEAR),
            ("shear @ scale_up", SHEAR @ SCALE_UP),
            ("projection onto y=x", PROJ)]

    print("  unit square starts with area 1.0 (shoelace: {:.6f})".format(
        abs(shoelace_area(UNIT_SQUARE))))
    print()
    print("  {:<20} {:>12} {:>16} {:>12}".format(
        "map", "det(A)", "shoelace area", "abs diff"))
    print("  " + "-" * 62)
    for name, M in maps:
        img = UNIT_SQUARE @ M.T          # transform all four corners at once
        area = shoelace_area(img)        # SIGNED - keeps orientation info
        d = float(np.linalg.det(M))
        print("  {:<20} {:>12.8f} {:>16.8f} {:>12.2e}".format(
            name, d, area, abs(area - d)))
    print()
    # Composing two maps multiplies their area factors, so det(AB)=det(A)det(B).
    # This is not a separate rule to memorise - it is what "areas multiply" means.
    print("  det(SHEAR @ SCALE_UP) = {:.8f} = det(SHEAR) {:.4f} x det(SCALE_UP) {:.4f}".format(
        float(np.linalg.det(SHEAR @ SCALE_UP)),
        float(np.linalg.det(SHEAR)), float(np.linalg.det(SCALE_UP))))
    print("    diff: {:.3e}   -> composing maps MULTIPLIES their area factors".format(
        abs(float(np.linalg.det(SHEAR @ SCALE_UP)
                  - np.linalg.det(SHEAR) * np.linalg.det(SCALE_UP)))))
    print()
    print("  the signed shoelace area equals det EXACTLY, sign included:")
    print("  a negative det means the map turned the square inside out.")
    flip = np.array([[0.0, 1.0], [1.0, 0.0]])   # swap x and y = a mirror
    img = UNIT_SQUARE @ flip.T
    print("    mirror [[0,1],[1,0]]: det = {:+.6f}  signed area = {:+.6f}".format(
        float(np.linalg.det(flip)), shoelace_area(img)))
    print()

    # Third, fully independent measurement: throw darts. If det really is the
    # area scale factor, a Monte-Carlo estimate of the image area must converge
    # to |det|, with error falling roughly like 1/sqrt(N).
    A = SHEAR @ SCALE_UP       # composition: scale first, then shear -> det 3
    target = abs(float(np.linalg.det(A)))
    corners = UNIT_SQUARE @ A.T
    lo = corners.min(axis=0)
    hi = corners.max(axis=0)
    box_area = float(np.prod(hi - lo))
    Ainv = np.linalg.inv(A)
    print("  Monte-Carlo: area of the image of the unit square under SHEAR @ SCALE_UP")
    print("    |det| = {:.8f}   bounding box area = {:.6f}".format(target, box_area))
    print("    {:>10} {:>14} {:>14}".format("N darts", "area estimate", "abs error"))
    rng = np.random.default_rng(SEED)          # separate stream, same seed rule
    for n in (10 ** 3, 10 ** 4, 10 ** 5, 10 ** 6):
        pts = rng.uniform(lo, hi, size=(n, 2))
        back = pts @ Ainv.T                    # undo the map, land back home
        inside = np.all((back >= 0.0) & (back <= 1.0), axis=1)
        est = box_area * float(inside.mean())
        print("    {:>10} {:>14.6f} {:>14.6f}".format(n, est, abs(est - target)))
    print("  error shrinks as N grows: the geometric claim survives measurement.")


# ---------------------------------------------------------------------------
# DEMO 4
# ---------------------------------------------------------------------------
def demo4_multiplication_is_composition() -> None:
    banner("DEMO 4 - matmul is COMPOSITION: (AB)x == A(Bx), and AB != BA")

    A, B = ROT, SCALE
    x = RNG.normal(size=2)
    lhs = (A @ B) @ x
    rhs = A @ (B @ x)
    print("  A = rotation 30 deg, B = scale (2, 0.5), x = {}".format(
        np.array2string(x, precision=6)))
    print("    (A @ B) @ x = {}".format(np.array2string(lhs, precision=14)))
    print("    A @ (B @ x) = {}".format(np.array2string(rhs, precision=14)))
    print("    max abs diff: {:.3e}".format(float(np.max(np.abs(lhs - rhs)))))
    print("  -> the matrix AB IS the single function 'do B, then do A'.")
    print("     This is why a stack of layers in 3.1 with no nonlinearity")
    print("     collapses into ONE matrix, and why backprop in 3.4 is a")
    print("     chain of matrix products read in the opposite order.")
    print()

    # Associativity holds for any conformable shapes, not just square ones, and
    # the ORDER YOU BRACKET IT changes the cost enormously. This is the whole
    # trick behind cheap attention variants in 4.2/4.3.
    P = RNG.normal(size=(200, 3))
    Q = RNG.normal(size=(3, 200))
    v = RNG.normal(size=200)
    left = (P @ Q) @ v          # builds a 200x200 matrix first
    right = P @ (Q @ v)         # never builds it
    print("  associativity with rectangles: P(200x3), Q(3x200), v(200,)")
    print("    (P @ Q) @ v  builds a 200x200 intermediate: {} multiply-adds".format(
        200 * 3 * 200 + 200 * 200))
    print("    P @ (Q @ v)  builds nothing bigger than 3: {} multiply-adds".format(
        3 * 200 + 200 * 3))
    print("    cost ratio: {:.1f}x more work for the SAME answer".format(
        (200 * 3 * 200 + 200 * 200) / (3 * 200 + 200 * 3)))
    print("    max abs diff between the two: {:.3e}".format(
        float(np.max(np.abs(left - right)))))
    print()

    # Non-commutativity, with a point you can watch move. rotate-then-scale and
    # scale-then-rotate are genuinely different functions.
    AB = A @ B
    BA = B @ A
    print("  A @ B (scale FIRST, then rotate) =")
    for row in AB:
        print("      [{: .6f} {: .6f}]".format(row[0], row[1]))
    print("  B @ A (rotate FIRST, then scale) =")
    for row in BA:
        print("      [{: .6f} {: .6f}]".format(row[0], row[1]))
    print("    max abs diff |AB - BA|: {:.6f}   -> NOT the same function".format(
        float(np.max(np.abs(AB - BA)))))
    p = np.array([1.0, 0.0])
    print("    point (1, 0) goes to {} under AB".format(
        np.array2string(AB @ p, precision=6)))
    print("    point (1, 0) goes to {} under BA".format(
        np.array2string(BA @ p, precision=6)))
    print("    distance between the two answers: {:.6f}".format(
        float(np.linalg.norm(AB @ p - BA @ p))))
    print("    both have det {:.6f} - equal area change, different shape.".format(
        float(np.linalg.det(AB))))
    print()

    # Rotations are special: R^T R = I means the map preserves every length and
    # every angle. That is the property 1.14 and 4.2 lean on when they normalise.
    print("  rotation sanity: R^T R should be the identity")
    print("    max abs diff from I: {:.3e}".format(
        float(np.max(np.abs(ROT.T @ ROT - np.eye(2))))))
    y = RNG.normal(size=2)
    print("    ||y|| = {:.12f}   ||R y|| = {:.12f}   diff {:.3e}".format(
        float(np.linalg.norm(y)), float(np.linalg.norm(ROT @ y)),
        abs(float(np.linalg.norm(y) - np.linalg.norm(ROT @ y)))))


# ---------------------------------------------------------------------------
# DEMO 5
# ---------------------------------------------------------------------------
def demo5_projection_is_idempotent() -> None:
    banner("DEMO 5 - a PROJECTION matrix: P @ P == P, verified numerically")

    print("  u = (1, 1); P = u u^T / (u^T u) projects onto the line y = x")
    for row in PROJ:
        print("      [{: .6f} {: .6f}]".format(row[0], row[1]))
    print()
    # Idempotence is the DEFINING property: once a point is already on the line,
    # projecting again does nothing. Applying P twice must equal applying it once.
    print("  P @ P - P, max abs entry: {:.3e}   (idempotent)".format(
        float(np.max(np.abs(PROJ @ PROJ - PROJ)))))
    print("  P applied 10 times minus P, max abs entry: {:.3e}".format(
        float(np.max(np.abs(np.linalg.matrix_power(PROJ, 10) - PROJ)))))
    print("  det(P) = {:.3e}   rank = {}   -> area is crushed to zero".format(
        float(np.linalg.det(PROJ)), int(np.linalg.matrix_rank(PROJ))))
    print()

    x = np.array([3.0, -1.0])
    px = PROJ @ x
    resid = x - px
    print("  x = {}   P x = {}".format(x, np.array2string(px, precision=6)))
    print("  residual r = x - Px = {}".format(np.array2string(resid, precision=6)))
    # Orthogonality of the residual is the reason least squares in 2.3 works:
    # the projection is the CLOSEST point on the line, and "closest" and
    # "perpendicular residual" are the same statement.
    print("  r . u = {:.3e}   -> the residual is perpendicular to the line".format(
        float(resid @ U)))
    print("  ||x||^2 = {:.6f} ; ||Px||^2 + ||r||^2 = {:.6f} ; diff {:.3e}".format(
        float(x @ x), float(px @ px + resid @ resid),
        abs(float(x @ x - (px @ px + resid @ resid)))))
    print()

    # Same construction in higher dimensions, which is literally the hat matrix
    # of ordinary least squares - the object 2.3 builds a design matrix for.
    Xd = RNG.normal(size=(50, 3))
    H = Xd @ np.linalg.inv(Xd.T @ Xd) @ Xd.T     # 50x50 projection onto col(X)
    print("  hat matrix H = X (X^T X)^-1 X^T for a random 50x3 design matrix")
    print("    shape {}   rank {}   trace {:.10f}  (trace = rank for a projection)".format(
        H.shape, int(np.linalg.matrix_rank(H)), float(np.trace(H))))
    print("    max abs entry of H @ H - H: {:.3e}".format(
        float(np.max(np.abs(H @ H - H)))))
    print("    max abs entry of H - H^T:   {:.3e}   (also symmetric)".format(
        float(np.max(np.abs(H - H.T)))))
    b = RNG.normal(size=50)
    r = b - H @ b
    print("    residual is orthogonal to every column of X: max |X^T r| = {:.3e}".format(
        float(np.max(np.abs(Xd.T @ r)))))


# ---------------------------------------------------------------------------
# DEMO 6  (skip test 1)
# ---------------------------------------------------------------------------
def demo6_shape_discipline() -> None:
    banner("DEMO 6 - SHAPE DISCIPLINE: (n,d) @ (d,k) -> (n,k), and nothing else")

    A = RNG.normal(size=(4, 3))
    B = RNG.normal(size=(3, 7))
    print("  A is {}, B is {}".format(A.shape, B.shape))
    print("  A @ B is {}   <- inner 3 and 3 match and CANCEL; outer 4 and 7 survive".format(
        (A @ B).shape))
    print("  the contraction sums over the shared dimension of length 3:")
    manual = np.zeros((4, 7))
    for i in range(4):
        for j in range(7):
            for k in range(3):          # k is the dimension that disappears
                manual[i, j] += A[i, k] * B[k, j]
    print("    triple loop vs numpy, max abs diff: {:.3e}".format(
        float(np.max(np.abs(manual - A @ B)))))
    print()

    print("  now the wrong way round - B @ A, which is (3,7) @ (4,3):")
    try:
        _ = B @ A
    except ValueError as exc:
        # Printing the REAL exception text matters: this is the message you will
        # actually meet in 3.1 and 4.2, and reading it is a skill (1.14).
        print("    ValueError: {}".format(exc))
    print("    7 != 4, so there is no shared dimension to sum over.")
    print("    In function terms: B sends 7-D vectors to 3-D vectors; A wants a")
    print("    3-D input. B cannot eat A's 4-D output. Composition is undefined.")
    print()

    # The batch convention: rows are examples. This is why every framework writes
    # X @ W and not W @ X (3.1, 2.3).
    n, d, k = 32, 5, 3
    X = RNG.normal(size=(n, d))         # 32 examples, each a 5-D feature vector
    W = RNG.normal(size=(d, k))         # maps 5-D features to 3-D outputs
    bias = RNG.normal(size=k)
    out = X @ W + bias                  # broadcast adds bias to every row
    print("  batch of {} examples, {} features in, {} outputs".format(n, d, k))
    print("    X {} @ W {} + b {} -> {}   <- one layer of 3.1, exactly".format(
        X.shape, W.shape, bias.shape, out.shape))
    # Row i of the output must equal W^T applied to row i of the input, plus b.
    # Verifying this is what makes the batch convention believable rather than
    # magic: the matmul is 32 independent applications of the SAME function.
    per_row = np.stack([W.T @ X[i] + bias for i in range(n)])
    print("    row-by-row recomputation, max abs diff: {:.3e}".format(
        float(np.max(np.abs(per_row - out)))))
    print("    -> one matmul = {} independent applications of the same map.".format(n))
    print()
    print("  W @ X would be (5,3) @ (32,5):")
    try:
        _ = W @ X
    except ValueError as exc:
        print("    ValueError: {}".format(exc))
    print()

    # An attention-shaped chain, purely to show shapes cancelling in sequence.
    # 4.2 computes Q K^T; 4.3 does it h times in parallel.
    T, dm, dk = 6, 8, 4
    Xs = RNG.normal(size=(T, dm))
    Wq = RNG.normal(size=(dm, dk))
    Wk = RNG.normal(size=(dm, dk))
    Q = Xs @ Wq
    K = Xs @ Wk
    scores = Q @ K.T / np.sqrt(dk)
    print("  attention-shaped chain (4.2): T={}, d_model={}, d_k={}".format(T, dm, dk))
    print("    X {} @ Wq {} -> Q {}".format(Xs.shape, Wq.shape, Q.shape))
    print("    X {} @ Wk {} -> K {}".format(Xs.shape, Wk.shape, K.shape))
    print("    Q {} @ K^T {} -> scores {}  (token-by-token, d_k cancelled)".format(
        Q.shape, K.T.shape, scores.shape))
    print("    scores[0, 1] = {:.6f}; recomputed as Q[0] . K[1] / sqrt(d_k) = {:.6f}".format(
        float(scores[0, 1]), float(Q[0] @ K[1] / np.sqrt(dk))))


# ---------------------------------------------------------------------------
# DEMO 7
# ---------------------------------------------------------------------------
def demo7_singular_matrix() -> None:
    banner("DEMO 7 - a SINGULAR matrix: det 0, no inverse, information destroyed")

    S = np.array([[2.0, 4.0],
                  [1.0, 2.0]])          # row 2 is exactly half of row 1
    print("  S = [[2, 4], [1, 2]]   (column 1 is exactly 2x column 0)")
    print("    det(S) = {:.3e}   rank = {}   (full rank would be 2)".format(
        float(np.linalg.det(S)), int(np.linalg.matrix_rank(S))))
    img = UNIT_SQUARE @ S.T
    print("    image of the unit square, shoelace area = {:.3e}".format(
        abs(shoelace_area(img))))
    print("    the four corners land on: {}".format(
        np.array2string(img, precision=3).replace("\n", "")))
    print("    every one of them sits on the line y = x/2: the whole PLANE")
    print("    is crushed onto a LINE. Area 1 -> area 0, exactly as det says.")
    print()

    try:
        np.linalg.inv(S)
    except np.linalg.LinAlgError as exc:
        print("    np.linalg.inv(S) -> LinAlgError: {}".format(exc))
    print("    There is no inverse because the map is not reversible: infinitely")
    print("    many inputs share one output, so 'undo it' has no single answer.")
    v1 = np.array([2.0, -1.0])
    print("    proof: S @ (2, -1) = {} and S @ (0, 0) = {} - same output".format(
        S @ v1, S @ np.zeros(2)))
    print()

    b_on = S @ np.array([1.0, 1.0])     # b that IS reachable
    b_off = np.array([1.0, 5.0])        # b that is NOT on the line
    print("  solving S x = b:")
    print("    b = {} lies ON the image line -> infinitely many solutions".format(b_on))
    sol, res, rank, sv = np.linalg.lstsq(S, b_on, rcond=None)
    print("      lstsq picks the smallest one: x = {}, ||Sx - b|| = {:.3e}".format(
        np.array2string(sol, precision=6), float(np.linalg.norm(S @ sol - b_on))))
    sol2, _, _, _ = np.linalg.lstsq(S, b_off, rcond=None)
    print("    b = {} lies OFF the line -> no solution at all".format(b_off))
    print("      best possible x = {}, ||Sx - b|| = {:.6f}  (cannot be driven to 0)".format(
        np.array2string(sol2, precision=6), float(np.linalg.norm(S @ sol2 - b_off))))
    print("      that leftover distance is exactly the least-squares residual of 2.3.")
    print("    singular values of S: {}  <- one is 0, that IS the collapse".format(
        np.array2string(sv, precision=6)))
    print()

    # Near-singular is worse than singular, because nothing raises. The rule is
    # rel_err(x) <= cond(A) * rel_err(b): a matrix that is ALMOST collapsing
    # amplifies any wobble in the data. Here the wobble is 1e-12 relative -
    # smaller than any real measurement error - and it is applied in a fixed
    # random direction. This is the stability lesson that returns in 3.4.
    print("  NEAR-singular is more dangerous than singular - it does not raise.")
    print("  Rule: rel_err(x) <= cond(A) * rel_err(b). We nudge b by 1e-12")
    print("  relative (far below any real measurement error) and watch x move.")
    print("    {:>8} {:>12} {:>12} {:>13} {:>13} {:>10}".format(
        "eps", "det", "cond(A)", "rel err x", "amplifn", "cond/ampl"))
    x_true = np.array([3.0, -1.0])
    direction = RNG.normal(size=2)
    direction = direction / np.linalg.norm(direction)   # unit wobble direction
    rel_b = 1e-12
    for eps in (1e-2, 1e-6, 1e-10, 1e-14, 1e-16):
        A = np.array([[1.0, 1.0],
                      [1.0, 1.0 + eps]])
        b = A @ x_true                    # a b that has an exact answer
        b_pert = b + rel_b * np.linalg.norm(b) * direction
        try:
            x_hat = np.linalg.solve(A, b_pert)
            rel_x = float(np.linalg.norm(x_hat - x_true) / np.linalg.norm(x_true))
            amp = rel_x / rel_b
            print("    {:>8.0e} {:>12.3e} {:>12.3e} {:>13.3e} {:>13.3e} {:>10.1f}".format(
                eps, float(np.linalg.det(A)), float(np.linalg.cond(A)),
                rel_x, amp, float(np.linalg.cond(A)) / amp))
        except np.linalg.LinAlgError as exc:
            print("    {:>8.0e} {:>12} {:>12} {:>13} {:>13} {:>10}".format(
                eps, "-", "-", "-", "LinAlgError", "-"))
            print("      ({})".format(exc))
    print("  'amplifn' is how many times the input wobble was magnified. It")
    print("  tracks cond(A), staying under it because the wobble direction is")
    print("  random rather than worst-case. No exception is raised for any of")
    print("  the middle rows: numpy returns a confident, wrong answer.")
    print("  Read the last usable row: x_true = {} came back with a".format(x_true))
    print("  relative error you would never accept, from a perturbation of 1e-12.")


# ---------------------------------------------------------------------------
# DEMO 8 - the picture
# ---------------------------------------------------------------------------
def demo8_save_picture() -> None:
    banner("DEMO 8 - the same square under six maps, saved as a PNG")

    maps = [("identity", np.eye(2)),
            ("rotation 30 deg", ROT),
            ("scale (2, 0.5)", SCALE),
            ("shear (1.5)", SHEAR),
            ("projection y=x", PROJ),
            ("singular [[2,4],[1,2]]", np.array([[2.0, 4.0], [1.0, 2.0]]))]

    fig, axes = plt.subplots(2, 3, figsize=(12, 8))
    closed = np.vstack([UNIT_SQUARE, UNIT_SQUARE[:1]])   # repeat first vertex
    for ax, (name, M) in zip(axes.ravel(), maps):
        img = closed @ M.T
        ax.plot(closed[:, 0], closed[:, 1], color="#a5a58d",
                linestyle="--", linewidth=1.5, label="unit square")
        ax.plot(img[:, 0], img[:, 1], color="#005f73", linewidth=2.5, label="image")
        ax.arrow(0, 0, M[0, 0], M[1, 0], color="#9b2226",
                 width=0.02, length_includes_head=True)
        ax.arrow(0, 0, M[0, 1], M[1, 1], color="#1b4332",
                 width=0.02, length_includes_head=True)
        d = float(np.linalg.det(M))
        ax.set_title("{}\ndet = {:.4f}  area = {:.4f}".format(
            name, d, abs(shoelace_area(UNIT_SQUARE @ M.T))), fontsize=10)
        ax.set_xlim(-1.5, 3.5)
        ax.set_ylim(-1.5, 3.0)
        ax.set_aspect("equal")
        ax.grid(alpha=0.3)
        ax.axhline(0, color="k", linewidth=0.8)
        ax.axvline(0, color="k", linewidth=0.8)
    fig.suptitle("A matrix is a function: red arrow = image of e1, "
                 "green arrow = image of e2", fontsize=12)
    fig.tight_layout()
    fig.savefig(PNG_PATH, dpi=110)
    plt.close(fig)

    size = os.path.getsize(PNG_PATH)
    print("  saved: {}".format(os.path.basename(PNG_PATH)))
    print("  bytes: {}".format(size))
    print("  each panel: dashed grey = the unit square before, teal = after.")
    print("  the red and green arrows are literally the COLUMNS of the matrix.")


def main() -> None:
    print("1.2 - Matrices and Matrix Multiplication as Linear Maps")
    print("numpy {} | seed {} | all randomness from default_rng(seed)".format(
        np.__version__, SEED))
    print()
    demo1_matrix_is_a_function()
    demo2_diagonal_stretches_axes()
    demo3_determinant_is_area_scale()
    demo4_multiplication_is_composition()
    demo5_projection_is_idempotent()
    demo6_shape_discipline()
    demo7_singular_matrix()
    demo8_save_picture()
    print("=" * 70)
    print("done - every claim above was measured, not asserted.")


if __name__ == "__main__":
    main()
