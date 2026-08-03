"""
1.3 - Eigenvalues, Eigenvectors, SVD  (companion script)

WHAT THIS RUNS
--------------
Seven numbered demos that NUMERICALLY VERIFY the linear algebra of eigen-
decomposition and the singular value decomposition. Nothing here is a picture
of an idea: every claim is checked by computing the same quantity two
independent ways and printing how far apart the answers are, or by measuring an
error that shrinks as a parameter grows.

REQUIREMENTS
------------
    numpy, matplotlib (Agg backend), scikit-learn.
    Tested on Python 3.14 / numpy 2.4.4 / matplotlib 3.11.1 / sklearn 1.9.0.

SAFETY
------
    Fully offline. No network calls, no subprocesses, no environment changes.
    Writes exactly ONE file: 03_svd_low_rank.png, beside this script.
    Reads nothing from disk. All data is generated procedurally from a fixed
    seed (SEED = 1729), so every number below reproduces exactly.

WHAT THIS PROVES PRACTICALLY
----------------------------
    1. An eigenvector really is a direction the matrix does not turn: the
       residual ||A v - lambda v|| is at machine precision, and the angle
       between v and A v is 0 degrees, while an ordinary vector gets turned.
    2. Repeatedly applying A drives any starting vector toward the dominant
       eigenvector, and the leftover angle shrinks by exactly the predicted
       ratio |lambda_2 / lambda_1| per step.
    3. A symmetric matrix has eigenvectors that are mutually perpendicular
       (Q.T @ Q equals the identity to machine precision); a non-symmetric one
       does not, and a rotation has no real eigenvector at all.
    4. Truncating the SVD at k terms gives a reconstruction error that matches
       the closed-form spectral formula to machine precision, and that error
       falls as k rises - this is what "which dimensions can I discard" means.
    5. The rank-k SVD truncation beats every one of 500 random rank-k
       approximations. That is the Eckart-Young theorem, measured.
    6. A rank-8 update to a 4096 x 4096 weight matrix costs 0.39% of the
       parameters of a full update - the arithmetic behind LoRA in 4.11 - and
       whether that is USEFUL depends entirely on the spectrum, which is
       measured both ways here.
    7. PCA is exactly the SVD of centred data: sklearn's components and a raw
       numpy SVD agree to machine precision once the sign ambiguity is fixed,
       and forgetting to centre produces a first component that just points at
       the mean.
    8. On an ill-conditioned system a relative change of 1e-8 in the right-hand
       side moves the solution by orders of magnitude more, bounded by the
       condition number, which is s_max / s_min from the SVD.
"""

import os

import matplotlib

matplotlib.use("Agg")  # headless: never opens a window, never blocks
import matplotlib.pyplot as plt
import numpy as np
from sklearn.decomposition import PCA

SEED = 1729
rng = np.random.default_rng(SEED)

HERE = os.path.dirname(os.path.abspath(__file__))
PNG_PATH = os.path.join(HERE, "03_svd_low_rank.png")
BAR = "=" * 70


def banner(title):
    print(BAR)
    print(title)
    print(BAR)


# ---------------------------------------------------------------------------
# DEMO 1 - what an eigenvector actually is
# ---------------------------------------------------------------------------
def demo1_eigenvector_is_a_direction():
    banner("DEMO 1 - an eigenvector is a direction the matrix does not turn")

    # A is a linear map (1.2): it takes a vector in and gives a vector out.
    # Chosen so the arithmetic is clean: trace 7, determinant 10, so the
    # characteristic polynomial is lambda^2 - 7*lambda + 10 = (l-5)(l-2).
    A = np.array([[4.0, 1.0], [2.0, 3.0]])
    print("  A =")
    for row in A:
        print("        [%6.2f %6.2f]" % (row[0], row[1]))

    vals, vecs = np.linalg.eig(A)
    order = np.argsort(-np.abs(vals))  # dominant first
    vals, vecs = vals.real[order], vecs.real[:, order]

    print()
    print("  eigenvalues from numpy : %.12f, %.12f" % (vals[0], vals[1]))
    # Two independent checks of the same numbers: trace = sum, det = product.
    print("  trace(A)  = %.12f   sum(eigenvalues)     = %.12f"
          % (np.trace(A), vals.sum()))
    print("  det(A)    = %.12f   product(eigenvalues) = %.12f"
          % (np.linalg.det(A), vals.prod()))

    print()
    print("  test          vector v        A @ v            angle turned   ||A v - lam v||")
    print("  ------------- --------------- ---------------- -------------- ----------------")
    for i in range(2):
        v = vecs[:, i] / np.linalg.norm(vecs[:, i])
        Av = A @ v
        # cos of the angle between v and A v. For an eigenvector this is
        # exactly +1 (or -1 for a negative eigenvalue): direction preserved.
        cos = float(np.dot(v, Av) / (np.linalg.norm(v) * np.linalg.norm(Av)))
        ang = np.degrees(np.arccos(np.clip(cos, -1.0, 1.0)))
        resid = np.linalg.norm(Av - vals[i] * v)
        print("  eigvec lam=%.1f [%6.3f %6.3f] [%7.3f %7.3f]  %8.4f deg   %.3e"
              % (vals[i], v[0], v[1], Av[0], Av[1], ang, resid))

    # An ordinary vector gets turned. That is the whole contrast.
    for label, w in (("plain e1", np.array([1.0, 0.0])),
                     ("plain e2", np.array([0.0, 1.0]))):
        Aw = A @ w
        cos = float(np.dot(w, Aw) / (np.linalg.norm(w) * np.linalg.norm(Aw)))
        ang = np.degrees(np.arccos(np.clip(cos, -1.0, 1.0)))
        print("  %-13s [%6.3f %6.3f] [%7.3f %7.3f]  %8.4f deg   (not an eigenvector)"
              % (label, w[0], w[1], Aw[0], Aw[1], ang))

    # Power iteration: apply A over and over. The leftover angle to the
    # dominant eigenvector must shrink by the factor |lam2/lam1| each step.
    print()
    print("  Repeatedly applying A pulls ANY start toward the dominant direction.")
    print("  predicted shrink factor per step = |lam2/lam1| = %.6f"
          % (abs(vals[1]) / abs(vals[0])))
    v1 = vecs[:, 0] / np.linalg.norm(vecs[:, 0])
    x = rng.normal(size=2)
    x /= np.linalg.norm(x)
    prev = None
    print("   step   angle to dominant eigvec   ratio to previous")
    for step in range(1, 11):
        x = A @ x
        x /= np.linalg.norm(x)
        cos = abs(float(np.dot(x, v1)))
        ang = np.degrees(np.arccos(np.clip(cos, -1.0, 1.0)))
        ratio = "     -" if prev is None else "%10.6f" % (ang / prev)
        print("   %4d   %20.10f deg   %s" % (step, ang, ratio))
        prev = ang
    print("  the ratio settles on 0.4 = 2/5, exactly |lam2|/|lam1|.")
    print()


# ---------------------------------------------------------------------------
# DEMO 2 - symmetric matrices give perpendicular eigenvectors
# ---------------------------------------------------------------------------
def demo2_symmetric_gives_orthogonal():
    banner("DEMO 2 - symmetric => orthogonal eigenvectors, verified Q.T @ Q = I")

    M = rng.normal(size=(5, 5))
    S = M.T @ M  # symmetric AND positive semi-definite by construction
    S = (S + S.T) / 2.0  # kill the last bit of floating-point asymmetry
    print("  S = M.T @ M  (5x5, symmetric by construction)")
    print("  max |S - S.T|          = %.3e   (0 => exactly symmetric)"
          % np.max(np.abs(S - S.T)))

    w, Q = np.linalg.eigh(S)  # eigh is the SYMMETRIC solver; always real
    w = w[::-1]
    Q = Q[:, ::-1]
    print("  eigenvalues (all real, all >= 0 because S = M.T M):")
    print("    " + "  ".join("%.6f" % v for v in w))
    print()
    print("  ORTHOGONALITY  max |Q.T @ Q - I|      = %.3e"
          % np.max(np.abs(Q.T @ Q - np.eye(5))))
    print("  RECONSTRUCTION max |Q diag(w) Q.T - S| = %.3e"
          % np.max(np.abs(Q @ np.diag(w) @ Q.T - S)))
    print("  trace(S) = %.10f    sum(eigenvalues) = %.10f"
          % (np.trace(S), w.sum()))
    print("  det(S)   = %.10f    prod(eigenvalues) = %.10f"
          % (np.linalg.det(S), w.prod()))

    # Now the contrast. Build a NON-symmetric matrix with known real
    # eigenvalues by conjugating a diagonal with a non-orthogonal P.
    P = np.array([[1.0, 1.0, 0.0],
                  [0.0, 1.0, 1.0],
                  [1.0, 0.0, 1.0]])
    N = P @ np.diag([4.0, 2.0, 1.0]) @ np.linalg.inv(P)
    nw, nv = np.linalg.eig(N)
    nv = nv / np.linalg.norm(nv, axis=0)
    print()
    print("  Non-symmetric N with the SAME kind of real eigenvalues %s:"
          % np.array2string(np.sort(nw.real)[::-1], precision=4))
    worst = 0.0
    for i in range(3):
        for j in range(i + 1, 3):
            c = abs(float(np.dot(nv[:, i], nv[:, j])))
            worst = max(worst, c)
    print("  max |cos angle| between distinct eigenvectors of N = %.6f  (%.2f deg apart)"
          % (worst, np.degrees(np.arccos(worst))))
    print("  max |V.T @ V - I| for N = %.3e   <- NOT an orthogonal basis"
          % np.max(np.abs(nv.T @ nv - np.eye(3))))

    # And a rotation: no real eigenvector exists at all.
    th = np.radians(30.0)
    R = np.array([[np.cos(th), -np.sin(th)], [np.sin(th), np.cos(th)]])
    rw = np.linalg.eigvals(R)
    print()
    print("  A 30-degree rotation turns EVERY direction, so it has no real eigenvector:")
    print("    eigenvalues = %.6f%+.6fj , %.6f%+.6fj   (|lambda| = %.6f)"
          % (rw[0].real, rw[0].imag, rw[1].real, rw[1].imag, abs(rw[0])))
    print()


# ---------------------------------------------------------------------------
# DEMO 3 - SVD low-rank reconstruction, with the error predicted in advance
# ---------------------------------------------------------------------------
def build_image(n=128):
    """A procedural 128x128 'image' with a deliberately controlled rank."""
    t = np.linspace(-1.0, 1.0, n)
    X, Y = np.meshgrid(t, t)
    img = np.zeros((n, n))
    img += 0.90 * np.sin(3.0 * np.pi * X)        # rank 1 (depends on X only)
    img += 0.60 * np.cos(2.0 * np.pi * Y)        # rank 1 (depends on Y only)
    img += 0.50 * X * Y                          # rank 1 (outer product)
    for (cx, cy, s, a) in ((-0.5, 0.4, 0.18, 1.2),
                           (0.45, -0.35, 0.12, -0.9),
                           (0.1, 0.6, 0.25, 0.7)):
        # a 2-D Gaussian factorises into (function of x) * (function of y),
        # so each blob adds exactly 1 to the rank
        img += a * np.exp(-((X - cx) ** 2) / (2 * s * s)) \
                 * np.exp(-((Y - cy) ** 2) / (2 * s * s))
    block = ((np.abs(X + 0.6) < 0.25) * 1.0)[:, :] * ((np.abs(Y + 0.7) < 0.2) * 1.0)
    img += 0.8 * block                            # rank 1 (indicator outer product)
    noise = 0.02 * rng.normal(size=(n, n))        # full-rank, and NOT compressible
    return img + noise, noise


def demo3_low_rank_reconstruction(A, noise):
    banner("DEMO 3 - low-rank reconstruction: which dimensions can be discarded")

    m, n = A.shape
    U, s, Vt = np.linalg.svd(A, full_matrices=False)
    total_energy = float(np.sum(s ** 2))  # equals ||A||_F^2

    print("  matrix: %d x %d, full rank = %d, ||A||_F = %.6f"
          % (m, n, min(m, n), np.linalg.norm(A, "fro")))
    print("  ||A||_F^2 = %.6f   sum of s_i^2 = %.6f   rel diff = %.3e"
          % (np.linalg.norm(A, "fro") ** 2, total_energy,
             abs(np.linalg.norm(A, "fro") ** 2 - total_energy) / total_energy))
    print("  top 12 singular values:")
    print("    " + "  ".join("%.3f" % v for v in s[:12]))
    print("  s[64] = %.6f   s[127] = %.6f   (the noise floor)" % (s[64], s[127]))
    # The image was built as (structure) + (noise). The noise is full rank, so
    # no truncation can ever remove it. Measure how much energy it holds, and
    # the error floor sqrt(noise energy / total energy) it therefore imposes.
    noise_energy = float(np.sum(noise ** 2))
    print("  injected noise holds %.4f%% of the energy -> an error floor near %.6f"
          % (100.0 * noise_energy / total_energy,
             np.sqrt(noise_energy / total_energy)))

    print()
    print("    k   rel.err (direct)  rel.err (spectral formula)   |diff|      "
          "energy kept   floats stored   vs full")
    print("  ----  ----------------  --------------------------  ----------  "
          "-----------   -------------   -------")
    rows = []
    for k in (1, 2, 4, 8, 16, 32, 64, 128):
        # Reconstruction the direct way: rebuild and subtract.
        Ak = (U[:, :k] * s[:k]) @ Vt[:k, :]
        err_direct = np.linalg.norm(A - Ak, "fro") / np.linalg.norm(A, "fro")
        # Reconstruction error the ANALYTIC way, straight from the spectrum:
        # ||A - A_k||_F = sqrt(sum_{i>k} s_i^2). Two independent routes.
        tail = float(np.sum(s[k:] ** 2))
        err_spec = np.sqrt(tail / total_energy)
        kept = 100.0 * (1.0 - tail / total_energy)
        stored = k * (m + n + 1)
        rows.append((k, err_direct, kept, stored))
        print("  %4d  %16.12f  %26.12f  %.3e  %9.4f%%   %13d   %6.2fx"
              % (k, err_direct, err_spec, abs(err_direct - err_spec), kept,
                 stored, (m * n) / stored))

    print()
    print("  The two error columns are computed by completely different routes")
    print("  (rebuild-and-subtract vs a formula that never touches U or V) and")
    print("  they agree to machine precision. That IS the theorem, measured.")
    print("  Note the plateau after k=8: the remaining error is the injected")
    print("  noise, which is full rank, so extra terms buy noise, not picture.")

    # Save the picture.
    ks = (1, 2, 4, 8, 16, 32)
    fig, axes = plt.subplots(2, 4, figsize=(13, 6.5))
    axes = axes.ravel()
    axes[0].imshow(A, cmap="viridis")
    axes[0].set_title("original (rank %d)" % min(m, n), fontsize=10)
    axes[0].axis("off")
    for idx, k in enumerate(ks, start=1):
        Ak = (U[:, :k] * s[:k]) @ Vt[:k, :]
        e = np.linalg.norm(A - Ak, "fro") / np.linalg.norm(A, "fro")
        axes[idx].imshow(Ak, cmap="viridis")
        axes[idx].set_title("k=%d   rel.err %.3f" % (k, e), fontsize=10)
        axes[idx].axis("off")
    axes[7].semilogy(np.arange(1, len(s) + 1), s, marker=".", linewidth=1)
    axes[7].set_title("singular values (log scale)", fontsize=10)
    axes[7].set_xlabel("index i")
    axes[7].grid(alpha=0.3)
    fig.suptitle("1.3 - SVD low-rank reconstruction (seed %d)" % SEED)
    fig.tight_layout()
    fig.savefig(PNG_PATH, dpi=110)
    plt.close(fig)
    print()
    print("  saved %s  (%d bytes)" % (os.path.basename(PNG_PATH),
                                      os.path.getsize(PNG_PATH)))
    print()
    return U, s, Vt, rows


# ---------------------------------------------------------------------------
# DEMO 4 - Eckart-Young, checked against 500 random competitors
# ---------------------------------------------------------------------------
def demo4_eckart_young(A, trials=500, k=8):
    banner("DEMO 4 - Eckart-Young: SVD truncation beats every random rank-%d rival" % k)

    m, n = A.shape
    normA = np.linalg.norm(A, "fro")
    U, s, Vt = np.linalg.svd(A, full_matrices=False)
    Ak = (U[:, :k] * s[:k]) @ Vt[:k, :]
    svd_err = np.linalg.norm(A - Ak, "fro") / normA

    # A random rank-k competitor gets every possible advantage: we pick a
    # random k-dimensional subspace and then project A onto it OPTIMALLY.
    # That is the best rank-k matrix living in that subspace, so the only
    # thing being tested is the CHOICE of subspace.
    errs = np.empty(trials)
    for t in range(trials):
        Rm = rng.normal(size=(m, k))
        Q, _ = np.linalg.qr(Rm)          # orthonormal basis of a random subspace
        Ar = Q @ (Q.T @ A)               # optimal projection onto it
        errs[t] = np.linalg.norm(A - Ar, "fro") / normA

    print("  rank-%d SVD truncation  rel. Frobenius error = %.10f" % (k, svd_err))
    print("  %d random rank-%d subspaces (each optimally projected):" % (trials, k))
    print("      best  = %.10f" % errs.min())
    print("      mean  = %.10f" % errs.mean())
    print("      worst = %.10f" % errs.max())
    print("  random trials that beat the SVD: %d out of %d"
          % (int(np.sum(errs < svd_err - 1e-15)), trials))
    print("  the best random rival is %.2fx worse than the SVD."
          % (errs.min() / svd_err))
    print()
    print("  'Optimal' is not a figure of speech: no rank-%d matrix of any kind" % k)
    print("  has smaller Frobenius error than the truncated SVD. That is why")
    print("  PCA (2.14) and low-rank adapters (4.11) both reduce to this one call.")
    print()


# ---------------------------------------------------------------------------
# DEMO 5 - the LoRA arithmetic (4.11), and the honest caveat
# ---------------------------------------------------------------------------
def demo5_lora_parameter_budget():
    banner("DEMO 5 - why a rank-8 adapter is practical (the 4.11 arithmetic)")

    print("  A full weight update dW is m x n. A rank-r update is B @ A with")
    print("  B: m x r and A: r x n, so it costs r*(m+n) numbers instead of m*n.")
    print()
    print("     m      n      r    full params   LoRA params    ratio     savings")
    print("  -----  -----  -----  ------------  ------------  --------  ---------")
    for (m, n) in ((768, 768), (4096, 4096), (4096, 11008)):
        for r in (4, 8, 16, 64):
            full = m * n
            lora = r * (m + n)
            print("  %5d  %5d  %5d  %12d  %12d  %7.4f%%  %8.1fx"
                  % (m, n, r, full, lora, 100.0 * lora / full, full / lora))
    print()
    print("  4096 x 4096 at rank 8: 65,536 numbers instead of 16,777,216 - 0.39%.")
    print("  That is the whole reason a 7B model can be adapted on one GPU.")

    # But cheap is not the same as USEFUL. Rank-8 only helps if the thing you
    # are approximating actually has a fast-decaying spectrum. Measure both.
    print()
    print("  Cheap is not automatically useful. Rank 8 only captures the update")
    print("  if the update's spectrum decays. Two 512x512 matrices, same size:")
    d = 512
    Bsig = rng.normal(size=(d, 8))
    Asig = rng.normal(size=(8, d))
    structured = Bsig @ Asig + 0.05 * rng.normal(size=(d, d))  # rank 8 + noise
    dense = rng.normal(size=(d, d))                            # flat spectrum

    print()
    print("    matrix                         energy kept by rank 8   rel. error")
    print("    -----------------------------  ---------------------   ----------")
    for label, Mx in (("rank-8 signal + small noise", structured),
                      ("dense random (flat spectrum)", dense)):
        sv = np.linalg.svd(Mx, compute_uv=False)
        kept = 100.0 * np.sum(sv[:8] ** 2) / np.sum(sv ** 2)
        err = np.sqrt(np.sum(sv[8:] ** 2) / np.sum(sv ** 2))
        print("    %-29s  %19.4f%%   %10.6f" % (label, kept, err))
    print()
    print("  Same parameter count, wildly different result. LoRA works because")
    print("  fine-tuning updates empirically look like the first row, not the")
    print("  second - not because rank 8 approximates arbitrary matrices well.")
    print()


# ---------------------------------------------------------------------------
# DEMO 6 - PCA IS the SVD of centred data (2.14), sign ambiguity and all
# ---------------------------------------------------------------------------
def demo6_pca_is_svd():
    banner("DEMO 6 - PCA is literally the SVD of CENTRED data (2.14)")

    n_samples, d = 500, 5
    # Latent 2-D structure, lifted into 5-D, plus noise, plus a big offset so
    # that forgetting to centre is visibly catastrophic.
    latent = rng.normal(size=(n_samples, 2)) * np.array([5.0, 1.5])
    mixing = rng.normal(size=(2, d))
    X = latent @ mixing + 0.4 * rng.normal(size=(n_samples, d))
    X = X + np.array([20.0, -8.0, 3.0, 12.0, -15.0])  # the offset

    # Route 1: sklearn.
    pca = PCA(n_components=d).fit(X)

    # Route 2: numpy SVD, by hand, on the CENTRED matrix.
    Xc = X - X.mean(axis=0)
    U, s, Vt = np.linalg.svd(Xc, full_matrices=False)
    my_components = Vt
    my_var = s ** 2 / (n_samples - 1)  # sample variance along each direction

    print("  data: %d samples x %d features, mean = %s"
          % (n_samples, d, np.array2string(X.mean(axis=0), precision=3)))
    print()
    print("  explained variance")
    print("    sklearn : " + "  ".join("%.6f" % v for v in pca.explained_variance_))
    print("    my SVD  : " + "  ".join("%.6f" % v for v in my_var))
    print("    max abs diff = %.3e"
          % np.max(np.abs(pca.explained_variance_ - my_var)))
    print("    (my formula is s_i^2 / (n-1) - nothing else)")

    print()
    print("  components, compared RAW (no sign fix):")
    raw = np.max(np.abs(pca.components_ - my_components))
    print("    max abs diff = %.6f   <- large, and it is NOT a bug" % raw)
    print("    per-component dot product with sklearn's:")
    signs = np.empty(d)
    for i in range(d):
        dot = float(np.dot(pca.components_[i], my_components[i]))
        signs[i] = np.sign(dot)
        print("      component %d: dot = %+.12f  (magnitude 1 => same LINE)"
              % (i, dot))

    print()
    print("  Why: if v is the unit direction of maximum variance then so is -v.")
    print("  Both are correct answers; the sign is not determined by the data.")
    print("  Any code comparing components MUST align signs first.")
    aligned = my_components * signs[:, None]
    print("  components after sign alignment: max abs diff = %.3e"
          % np.max(np.abs(pca.components_ - aligned)))

    # And what happens if you forget to centre.
    Uu, su, Vtu = np.linalg.svd(X, full_matrices=False)  # NOT centred
    mean_dir = X.mean(axis=0) / np.linalg.norm(X.mean(axis=0))
    cos_mean = abs(float(np.dot(Vtu[0], mean_dir)))
    cos_true = abs(float(np.dot(Vtu[0], pca.components_[0])))
    print()
    print("  FORGETTING TO CENTRE - SVD of the raw X:")
    print("    |cos| between its 1st right-singular vector and the MEAN direction = %.10f"
          % cos_mean)
    print("    |cos| between it and the true 1st principal component             = %.10f"
          % cos_true)
    print("    It points at where the data IS, not at how the data VARIES.")
    print("    Centring is not a formality; it is what makes it PCA.")
    print()


# ---------------------------------------------------------------------------
# DEMO 7 - condition number: s_max / s_min, and what it costs (1.12)
# ---------------------------------------------------------------------------
def demo7_conditioning():
    banner("DEMO 7 - condition number = s_max/s_min, and the damage it does (1.12)")

    n = 8
    # The Hilbert matrix H[i,j] = 1/(i+j+1): symmetric, invertible, famously
    # ill-conditioned. Nothing about it looks dangerous.
    H = np.array([[1.0 / (i + j + 1) for j in range(n)] for i in range(n)])
    sH = np.linalg.svd(H, compute_uv=False)
    print("  Hilbert %dx%d, H[i,j] = 1/(i+j+1). Every entry is between 0 and 1." % (n, n))
    print("    s_max = %.6e   s_min = %.6e" % (sH[0], sH[-1]))
    print("    s_max/s_min      = %.6e" % (sH[0] / sH[-1]))
    print("    np.linalg.cond(H)= %.6e   rel diff = %.3e"
          % (np.linalg.cond(H),
             abs(sH[0] / sH[-1] - np.linalg.cond(H)) / np.linalg.cond(H)))

    x_true = np.ones(n)
    b = H @ x_true
    x0 = np.linalg.solve(H, b)
    print()
    print("  Solve H x = b where the true answer is all ones.")
    print("    ||x_solved - x_true||/||x_true|| = %.6e   (before ANY perturbation)"
          % (np.linalg.norm(x0 - x_true) / np.linalg.norm(x_true)))

    rel_b = 1e-8
    # (a) a random nudge to b
    db = rng.normal(size=n)
    db = db / np.linalg.norm(db) * rel_b * np.linalg.norm(b)
    xr = np.linalg.solve(H, b + db)
    amp_rand = (np.linalg.norm(xr - x0) / np.linalg.norm(x0)) / rel_b
    # (b) the WORST possible nudge of the same size: along the smallest
    #     left singular direction, which H^-1 stretches by 1/s_min
    Uh, _, Vth = np.linalg.svd(H)
    dw = Uh[:, -1] * rel_b * np.linalg.norm(b)
    xw = np.linalg.solve(H, b + dw)
    amp_worst = (np.linalg.norm(xw - x0) / np.linalg.norm(x0)) / rel_b

    print()
    print("  Nudge b by a relative %.0e and re-solve:" % rel_b)
    print("    random direction : ||dx||/||x|| = %.6e  -> amplified %.3e x"
          % (np.linalg.norm(xr - x0) / np.linalg.norm(x0), amp_rand))
    print("    worst direction  : ||dx||/||x|| = %.6e  -> amplified %.3e x"
          % (np.linalg.norm(xw - x0) / np.linalg.norm(x0), amp_worst))
    print("    theoretical ceiling = cond(H) = %.3e   (never exceeded above)"
          % np.linalg.cond(H))

    # A well-conditioned control, so the comparison is honest.
    Qr, _ = np.linalg.qr(rng.normal(size=(n, n)))
    G = Qr @ np.diag(np.linspace(1.0, 2.0, n)) @ Qr.T
    bg = G @ x_true
    xg0 = np.linalg.solve(G, bg)
    dbg = rng.normal(size=n)
    dbg = dbg / np.linalg.norm(dbg) * rel_b * np.linalg.norm(bg)
    xg1 = np.linalg.solve(G, bg + dbg)
    print()
    print("  Control: a well-conditioned matrix, cond(G) = %.6f" % np.linalg.cond(G))
    print("    same %.0e nudge -> ||dx||/||x|| = %.6e  -> amplified %.3f x"
          % (rel_b, np.linalg.norm(xg1 - xg0) / np.linalg.norm(xg0),
             (np.linalg.norm(xg1 - xg0) / np.linalg.norm(xg0)) / rel_b))

    # Truncating the small singular values buys stability at the cost of bias.
    # This is the same trade regularisation makes in 2.5.
    print()
    print("  Fix: throw away the tiny singular values (truncated pseudo-inverse).")
    print("    keep k   ||x_k - x_true||/||x_true||   sensitivity to the worst nudge")
    print("    ------   ---------------------------   -----------------------------")
    for k in (3, 4, 5, 6, 8):
        xk = Vth[:k].T @ ((Uh[:, :k].T @ b) / sH[:k])
        xk2 = Vth[:k].T @ ((Uh[:, :k].T @ (b + dw)) / sH[:k])
        bias = np.linalg.norm(xk - x_true) / np.linalg.norm(x_true)
        sens = (np.linalg.norm(xk2 - xk) / np.linalg.norm(xk)) / rel_b
        print("    %6d   %27.6e   %25.3e x" % (k, bias, sens))
    print()
    print("  Keeping fewer directions makes the answer WRONGER but far more STABLE.")
    print("  That trade - accept bias to kill variance - is exactly 2.5.")
    print()


def main():
    print("1.3 - Eigenvalues, Eigenvectors, SVD | seed = %d | numpy %s"
          % (SEED, np.__version__))
    print("all data generated in-process; no network, no files read")
    print()
    demo1_eigenvector_is_a_direction()
    demo2_symmetric_gives_orthogonal()
    A, noise = build_image(128)
    demo3_low_rank_reconstruction(A, noise)
    demo4_eckart_young(A)
    demo5_lora_parameter_budget()
    demo6_pca_is_svd()
    demo7_conditioning()
    banner("DONE - one file written: %s" % os.path.basename(PNG_PATH))


if __name__ == "__main__":
    main()
