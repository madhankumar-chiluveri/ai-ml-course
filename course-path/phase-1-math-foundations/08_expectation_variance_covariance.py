"""1.8 - Expectation, Variance, Covariance: measured, not asserted.

Seven numbered demonstrations that VERIFY the algebra of expectation,
variance and covariance numerically instead of restating it.

Requirements : numpy, matplotlib (Agg backend only - never opens a window).
Safe/offline : no network, no API keys, no environment variables read, no
               files read. The single file written is
               08_expectation_variance_covariance.png, beside this script.
Reproducible : every random number comes from np.random.default_rng(SEED)
               with SEED = 314159, printed at startup.

What this proves practically
 1. Var(X) = E[X^2] - (E[X])^2 is an identity, not an approximation: both
    sides are computed independently and agree to machine precision. The
    exact worked case E[X]=2, E[X^2]=9 -> Var(X)=5 is checked against a
    two-million-draw simulation.
 2. Covariance ZERO does not imply independence. On y = x^2 with symmetric
    x the relationship is perfectly deterministic, yet the measured
    correlation is ~0. The dependence is then exposed by a second-moment
    test that a correlation coefficient structurally cannot see.
 3. The error of a sample mean shrinks as n^(-1/2). The exponent is fitted
    from measured data, not assumed - and that single number is why a
    50-example eval set cannot resolve a 3-point accuracy difference (7.9).
 4. Var(X+Y) = Var(X) + Var(Y) + 2*Cov(X,Y) holds to ~1e-15 for correlated
    AND uncorrelated pairs; independence is exactly what deletes the cross
    term, which is in turn why Var(sample mean) = Var(X)/n.
 5. A covariance matrix computed by hand from the definition equals
    np.cov to machine precision; its eigenvectors give coordinates in which
    the covariance matrix is DIAGONAL - which is precisely what PCA (2.14)
    does, demonstrated here before PCA is named.
 6. Dividing by n systematically UNDERESTIMATES variance. The bias is
    measured over 200,000 trials and matched against the predicted
    -sigma^2/n; dividing by n-1 removes it. Bessel's correction is measured,
    not asserted.
 7. Concrete cost of demo 3: with 50 eval examples, a model that is truly
    3 points worse wins the comparison a large fraction of the time. The
    sample size needed to fix that is computed and simulated.
"""

import math
import os

import numpy as np

import matplotlib

matplotlib.use("Agg")  # headless: never call plt.show() in course scripts
import matplotlib.pyplot as plt

SEED = 314159
LINE = "=" * 70

# ---------------------------------------------------------------------------
# The reference random variable used throughout demos 1, 3 and 6.
#
# X takes the value 0 with probability 1/2, 3 with probability 1/3, and 6
# with probability 1/6. This is chosen so the closed-form answers are exact
# small integers, which makes any numerical disagreement obvious:
#     E[X]   = 0*(1/2) + 3*(1/3) + 6*(1/6) = 0 + 1 + 1 = 2
#     E[X^2] = 0*(1/2) + 9*(1/3) + 36*(1/6) = 0 + 3 + 6 = 9
#     Var(X) = E[X^2] - (E[X])^2 = 9 - 4 = 5
# Those are exactly the numbers in skip-test question 2.
# ---------------------------------------------------------------------------
VALUES = np.array([0.0, 3.0, 6.0])
PROBS = np.array([1.0 / 2.0, 1.0 / 3.0, 1.0 / 6.0])
TRUE_MEAN = 2.0
TRUE_VAR = 5.0


def sample_x(rng, shape):
    """Draw from the reference distribution via inverse-CDF sampling.

    Much faster than rng.choice for large shapes: one uniform per draw plus
    a binary search. The probability model itself is 1.7 material; here it
    is only a source of data with a KNOWN mean and variance.
    """
    cum = np.cumsum(PROBS)
    u = rng.random(shape)
    return VALUES[np.searchsorted(cum, u)]


def phi(z):
    """Standard normal CDF, from math.erf - avoids a scipy dependency."""
    return 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))


# ---------------------------------------------------------------------------
def demo1_identity():
    """Var(X) = E[X^2] - (E[X])^2, exactly, then confirmed by simulation."""
    print(LINE)
    print("DEMO 1 - expectation, variance, and the identity Var = E[X^2] - E[X]^2")
    print(LINE)

    rng = np.random.default_rng(SEED)

    # ---- closed form, straight from the definition of expectation --------
    # E[g(X)] = sum over outcomes of P(outcome) * g(outcome).  Expectation is
    # a PROBABILITY-WEIGHTED sum, not an arithmetic average of the values.
    e_x = float(np.sum(PROBS * VALUES))
    e_x2 = float(np.sum(PROBS * VALUES**2))
    var_identity = e_x2 - e_x**2
    # The other definition: average squared distance from the mean.
    var_definition = float(np.sum(PROBS * (VALUES - e_x) ** 2))

    print("  X = 0 with p=1/2,  3 with p=1/3,  6 with p=1/6")
    print("  E[X]   (weighted sum)            = %.15f" % e_x)
    print("  E[X^2] (weighted sum)            = %.15f" % e_x2)
    print()
    print("  route A: E[X^2] - (E[X])^2       = %.15f" % var_identity)
    print("  route B: E[(X - E[X])^2]         = %.15f" % var_definition)
    print("  abs diff between the two routes  = %.3e" % abs(var_identity - var_definition))
    print("  -> the identity is algebra, not an approximation")
    print()
    print("  SKIP TEST 2: E[X]=2, E[X^2]=9  ->  Var(X) = 9 - 2^2 = %.1f" % var_identity)
    print("               sd(X) = sqrt(Var) = %.6f" % math.sqrt(var_identity))
    print()

    # ---- same numbers, obtained by brute force ---------------------------
    n = 2_000_000
    x = sample_x(rng, n)
    samp_mean = float(x.mean())
    samp_e_x2 = float((x**2).mean())
    var_via_identity = samp_e_x2 - samp_mean**2  # 1/n version
    var_via_numpy = float(np.var(x))  # numpy default ddof=0, also 1/n

    print("  simulation, n = %d draws" % n)
    print("  sample mean                      = %.6f   (truth %.1f)" % (samp_mean, TRUE_MEAN))
    print("  sample E[X^2]                    = %.6f   (truth %.1f)" % (samp_e_x2, e_x2))
    print("  sample var via E[X^2] - mean^2   = %.12f" % var_via_identity)
    print("  sample var via np.var (ddof=0)   = %.12f" % var_via_numpy)
    print("  max abs diff                     = %.3e" % abs(var_via_identity - var_via_numpy))
    print("  error of sample mean vs truth    = %.6f" % abs(samp_mean - TRUE_MEAN))
    print()
    print("  CAUTION (1.12): the identity is exact in real arithmetic but")
    print("  cancels catastrophically in floating point on shifted data.")
    shifted = x + 1e9  # shifting cannot change a variance -- but watch
    naive_shift = float((shifted**2).mean() - shifted.mean() ** 2)
    print("  same data shifted by 1e9 (spread is unchanged by definition):")
    print("    E[X^2] - mean^2                = %.6f   (raw %.3e)" % (naive_shift, naive_shift))
    print("    np.var (centres first)         = %.6f" % float(np.var(shifted)))
    print("    truth                          = %.6f" % TRUE_VAR)
    return None


# ---------------------------------------------------------------------------
def demo2_zero_cov_not_independence():
    """The centrepiece: cov = 0 with a perfectly deterministic relationship."""
    print(LINE)
    print("DEMO 2 - covariance ZERO does not mean independent")
    print(LINE)

    rng = np.random.default_rng(SEED + 1)
    n = 500_000

    # Case A: y is a DETERMINISTIC function of x. Knowing x tells you y with
    # certainty. There is no stronger dependence than this.
    x = rng.normal(0.0, 1.0, n)
    y = x**2

    # Cov(X,Y) = E[(X-EX)(Y-EY)].  For symmetric x, E[X^3] = 0 and E[X] = 0,
    # so Cov(X, X^2) = E[X^3] - E[X]E[X^2] = 0 - 0 = 0 exactly.
    cov_a = float(np.cov(x, y, ddof=1)[0, 1])
    corr_a = float(np.corrcoef(x, y)[0, 1])

    # Case B: genuinely independent - drawn from separate streams.
    x2 = rng.normal(0.0, 1.0, n)
    z = rng.normal(0.0, 1.0, n)
    cov_b = float(np.cov(x2, z, ddof=1)[0, 1])
    corr_b = float(np.corrcoef(x2, z)[0, 1])

    print("  n = %d draws in each case" % n)
    print()
    print("  case                              Cov(X,Y)        Corr(X,Y)")
    print("  ------------------------------  ------------  ---------------")
    print("  A: Y = X^2 (X standard normal)  %12.6f  %15.6f" % (cov_a, corr_a))
    print("  B: X, Y independent normals     %12.6f  %15.6f" % (cov_b, corr_b))
    print()
    print("  Both correlations are ~0. Only ONE of the two pairs is independent.")
    print()

    # ---- expose the dependence that correlation cannot see ---------------
    # Independence means E[f(X)g(Y)] = E[f(X)]E[g(Y)] for EVERY pair of
    # functions f and g. Covariance only checks the single case f=g=identity.
    # Choose f(x)=x^2 and g(y)=y^2 and the two cases separate immediately.
    lhs_a = float((x**2 * y**2).mean())
    rhs_a = float((x**2).mean() * (y**2).mean())
    lhs_b = float((x2**2 * z**2).mean())
    rhs_b = float((x2**2).mean() * (z**2).mean())

    print("  independence test with f(X)=X^2, g(Y)=Y^2 :")
    print("    case      E[f(X)g(Y)]      E[f(X)]E[g(Y)]        ratio")
    print("    ------  ---------------  ----------------  -----------")
    print("    A       %15.6f  %16.6f  %11.4f" % (lhs_a, rhs_a, lhs_a / rhs_a))
    print("    B       %15.6f  %16.6f  %11.4f" % (lhs_b, rhs_b, lhs_b / rhs_b))
    print("    Independence demands ratio 1. A gives %.3f, B gives %.3f."
          % (lhs_a / rhs_a, lhs_b / rhs_b))
    print("    Covariance never looked at squares, so it never saw this.")
    print()

    # A nonlinear re-encoding restores the visible correlation in case A.
    corr_abs_a = float(np.corrcoef(np.abs(x), y)[0, 1])
    corr_abs_b = float(np.corrcoef(np.abs(x2), z)[0, 1])
    print("  same data, correlating |X| with Y instead of X with Y:")
    print("    case A  Corr(|X|, Y) = %9.6f   <- the dependence was always there" % corr_abs_a)
    print("    case B  Corr(|X|, Y) = %9.6f   <- still nothing, correctly" % corr_abs_b)
    print()

    # ---- conditional means: the parabola, in numbers ---------------------
    edges = np.quantile(x, [0.0, 0.2, 0.4, 0.6, 0.8, 1.0])
    idx_a = np.clip(np.searchsorted(edges[1:-1], x), 0, 4)
    edges_b = np.quantile(x2, [0.0, 0.2, 0.4, 0.6, 0.8, 1.0])
    idx_b = np.clip(np.searchsorted(edges_b[1:-1], x2), 0, 4)

    print("  mean of Y inside each quintile of X:")
    print("    quintile of X          case A E[Y|bin]   case B E[Y|bin]")
    print("    ---------------------  ---------------  ----------------")
    for k in range(5):
        ma = float(y[idx_a == k].mean())
        mb = float(z[idx_b == k].mean())
        print("    %d  (%6.2f .. %6.2f)  %15.4f  %16.4f"
              % (k + 1, edges[k], edges[k + 1], ma, mb))
    print("    case A sweeps high-low-high: a parabola. Case B is flat noise.")
    return {"x": x[:4000], "y": y[:4000], "x2": x2[:4000], "z": z[:4000],
            "corr_a": corr_a, "corr_b": corr_b}


# ---------------------------------------------------------------------------
def demo3_convergence_rate():
    """Measure the exponent in error ~ n^p. It should come out near -0.5."""
    print(LINE)
    print("DEMO 3 - how fast does a sample mean converge? MEASURE the exponent")
    print(LINE)

    rng = np.random.default_rng(SEED + 2)
    n_values = [10, 30, 100, 300, 1000, 3000, 10000, 30000]
    trials = 800
    chunk = 100  # keep peak memory small: at most chunk*n floats at once

    rmse_mean = []
    rmse_var = []
    for n in n_values:
        errs_m = []
        errs_v = []
        done = 0
        while done < trials:
            block = min(chunk, trials - done)
            xs = sample_x(rng, (block, n))
            errs_m.append(xs.mean(axis=1) - TRUE_MEAN)
            errs_v.append(xs.var(axis=1, ddof=1) - TRUE_VAR)
            done += block
        em = np.concatenate(errs_m)
        ev = np.concatenate(errs_v)
        rmse_mean.append(float(np.sqrt((em**2).mean())))
        rmse_var.append(float(np.sqrt((ev**2).mean())))

    rmse_mean = np.array(rmse_mean)
    rmse_var = np.array(rmse_var)
    n_arr = np.array(n_values, dtype=float)
    # Closed form: the standard error of a mean of n iid draws is
    # sd(X)/sqrt(n). That follows from demo 4, not from magic.
    predicted = math.sqrt(TRUE_VAR) / np.sqrt(n_arr)

    print("  reference X: true mean %.1f, true variance %.1f, %d trials per n"
          % (TRUE_MEAN, TRUE_VAR, trials))
    print()
    print("        n   RMSE(sample mean)   sd(X)/sqrt(n)    ratio   RMSE(sample var)")
    print("  -------  -----------------  ---------------  -------  ----------------")
    for i, n in enumerate(n_values):
        print("  %7d  %17.6f  %15.6f  %7.3f  %16.6f"
              % (n, rmse_mean[i], predicted[i], rmse_mean[i] / predicted[i], rmse_var[i]))

    # Fit log10(RMSE) = a + p*log10(n). The slope p IS the convergence rate.
    p_mean, a_mean = np.polyfit(np.log10(n_arr), np.log10(rmse_mean), 1)
    p_var, _ = np.polyfit(np.log10(n_arr), np.log10(rmse_var), 1)
    print()
    print("  fitted exponent for the MEAN     : %.4f   (theory -0.5)" % p_mean)
    print("  fitted exponent for the VARIANCE : %.4f   (theory -0.5)" % p_var)
    print()
    print("  Reading it operationally: to halve the error you need 4x the data.")
    print("  n=100 -> se %.4f ;  n=400 -> se %.4f ;  n=1600 -> se %.4f"
          % (math.sqrt(TRUE_VAR / 100), math.sqrt(TRUE_VAR / 400), math.sqrt(TRUE_VAR / 1600)))
    return {"n": n_arr, "rmse": rmse_mean, "pred": predicted, "slope": float(p_mean)}


# ---------------------------------------------------------------------------
def demo4_variance_of_a_sum():
    """Var(X+Y) = Var X + Var Y + 2 Cov(X,Y), and what independence deletes."""
    print(LINE)
    print("DEMO 4 - Var(X+Y) = Var(X) + Var(Y) + 2*Cov(X,Y)")
    print(LINE)

    rng = np.random.default_rng(SEED + 3)
    n = 400_000
    base = rng.normal(0.0, 2.0, n)  # Var = 4
    noise = rng.normal(0.0, 3.0, n)  # Var = 9

    cases = [
        ("Y independent of X", base, noise.copy()),
        ("Y =  1.5*X + noise", base, 1.5 * base + noise),
        ("Y = -1.5*X + noise", base, -1.5 * base + noise),
    ]

    print("  all estimates use ddof=1, so the identity should hold to ~1e-15")
    print()
    header = "  case                  Var(X)    Var(Y)   Cov(X,Y)   Var(X+Y)  VX+VY+2C    diff"
    print(header)
    print("  " + "-" * (len(header) - 2))
    for name, a, b in cases:
        vx = float(np.var(a, ddof=1))
        vy = float(np.var(b, ddof=1))
        cxy = float(np.cov(a, b, ddof=1)[0, 1])
        lhs = float(np.var(a + b, ddof=1))
        rhs = vx + vy + 2.0 * cxy
        print("  %-18s %9.4f %9.4f %10.4f %10.4f %9.4f %7.1e"
              % (name, vx, vy, cxy, lhs, rhs, abs(lhs - rhs)))

    print()
    print("  and the mirror identity Var(X-Y) = Var(X) + Var(Y) - 2*Cov(X,Y):")
    for name, a, b in cases:
        vx = float(np.var(a, ddof=1))
        vy = float(np.var(b, ddof=1))
        cxy = float(np.cov(a, b, ddof=1)[0, 1])
        lhs = float(np.var(a - b, ddof=1))
        rhs = vx + vy - 2.0 * cxy
        print("    %-18s  Var(X-Y) = %9.4f   vs %9.4f   diff %7.1e"
              % (name, lhs, rhs, abs(lhs - rhs)))

    print()
    print("  CONSEQUENCE - why demo 3 saw n^-0.5:")
    print("  For n INDEPENDENT copies every cross term is 0, so the variances")
    print("  simply add:  Var(sum) = n*Var(X), and Var(mean) = Var(X)/n.")
    # Verify that directly rather than asserting it.
    trials, m = 40_000, 25
    xs = sample_x(rng, (trials, m))
    emp = float(np.var(xs.mean(axis=1), ddof=1))
    print("  simulated Var(mean of %d draws) = %.6f   predicted Var(X)/%d = %.6f"
          % (m, emp, m, TRUE_VAR / m))
    print("  relative gap = %.3f%%" % (100.0 * abs(emp - TRUE_VAR / m) / (TRUE_VAR / m)))
    return None


# ---------------------------------------------------------------------------
def demo5_covariance_matrix():
    """Covariance matrix by hand vs np.cov, then diagonalize it (2.14)."""
    print(LINE)
    print("DEMO 5 - the covariance MATRIX, by hand and by numpy, then diagonalized")
    print(LINE)

    rng = np.random.default_rng(SEED + 4)
    n = 200_000
    f0 = rng.normal(0.0, 2.0, n)  # a feature on a big scale
    f1 = 0.9 * f0 + rng.normal(0.0, 1.0, n)  # correlated with f0
    f2 = -0.4 * f0 + rng.normal(0.0, 0.3, n)  # anti-correlated, small scale
    X = np.column_stack([f0, f1, f2])  # shape (n, 3): rows = samples

    # ---- by hand, straight from Cov(i,j) = E[(Xi-mu_i)(Xj-mu_j)] ---------
    mu = X.mean(axis=0)
    Xc = X - mu  # centre every column: this IS the "subtract the mean" step
    C_hand = (Xc.T @ Xc) / (n - 1)  # ddof=1 to match np.cov's default
    C_np = np.cov(X, rowvar=False)  # rowvar=False: columns are variables

    print("  data: %d samples, 3 features" % n)
    print("  covariance matrix computed by hand ((Xc.T @ Xc)/(n-1)):")
    for row in C_hand:
        print("    [%10.6f %10.6f %10.6f]" % tuple(row))
    print("  max abs diff vs np.cov            = %.3e" % float(np.abs(C_hand - C_np).max()))
    print("  matrix is symmetric, max|C - C.T| = %.3e" % float(np.abs(C_hand - C_hand.T).max()))
    print("  diagonal entries are the variances of each feature:")
    print("    diag(C)          = [%10.6f %10.6f %10.6f]" % tuple(np.diag(C_hand)))
    print("    np.var(ddof=1)   = [%10.6f %10.6f %10.6f]" % tuple(np.var(X, axis=0, ddof=1)))
    print()

    # ---- correlation matrix = covariance with the units divided out ------
    sd = np.sqrt(np.diag(C_hand))
    R_hand = C_hand / np.outer(sd, sd)
    R_np = np.corrcoef(X, rowvar=False)
    print("  correlation matrix (covariance divided by the two sds):")
    for row in R_hand:
        print("    [%10.6f %10.6f %10.6f]" % tuple(row))
    print("  max abs diff vs np.corrcoef       = %.3e" % float(np.abs(R_hand - R_np).max()))
    print("  every diagonal entry is exactly 1, every entry lies in [-1, 1]:")
    print("    min entry %.6f   max entry %.6f" % (R_hand.min(), R_hand.max()))
    print()

    # ---- eigen-decomposition: this is PCA, one topic early (2.14) --------
    evals, evecs = np.linalg.eigh(C_hand)  # eigh: C is symmetric
    order = np.argsort(evals)[::-1]
    evals, evecs = evals[order], evecs[:, order]
    print("  eigenvalues of C (descending)     = [%10.6f %10.6f %10.6f]" % tuple(evals))
    print("  sum of eigenvalues                = %.12f" % float(evals.sum()))
    print("  trace of C (sum of variances)     = %.12f" % float(np.trace(C_hand)))
    print("  abs diff                          = %.3e" % abs(float(evals.sum() - np.trace(C_hand))))
    print("  share of total variance           = [%7.4f %7.4f %7.4f]"
          % tuple(evals / evals.sum()))
    print()
    # Rotate the data into the eigenvector basis and recompute the covariance.
    Z = Xc @ evecs
    C_rot = np.cov(Z, rowvar=False)
    off = C_rot - np.diag(np.diag(C_rot))
    print("  now rotate the data onto the eigenvectors and recompute Cov:")
    for row in C_rot:
        print("    [%12.6f %12.6f %12.6f]" % tuple(row))
    print("  largest OFF-diagonal magnitude    = %.3e" % float(np.abs(off).max()))
    print("  -> in these coordinates the features are UNCORRELATED.")
    print("     That is exactly what PCA (2.14) does: diagonalize this matrix.")
    return None


# ---------------------------------------------------------------------------
def demo6_bessel():
    """Measure the bias of the 1/n variance estimator instead of asserting it."""
    print(LINE)
    print("DEMO 6 - why the denominator is n-1: MEASURE the bias")
    print(LINE)

    rng = np.random.default_rng(SEED + 5)
    trials = 200_000
    print("  true variance of X = %.1f, averaged over %d independent samples per n"
          % (TRUE_VAR, trials))
    print("  'z' = (measured bias) / (Monte-Carlo standard error). |z| under ~3")
    print("  means the residual is indistinguishable from simulation noise.")
    print()
    head = ("      n   mean(/n)  predicted   bias(/n)        z   mean(/(n-1))"
            " bias(/(n-1))      z")
    print(head)
    print("  " + "-" * (len(head) - 2))
    rows = []
    for n in [2, 3, 5, 10, 30, 100]:
        xs = sample_x(rng, (trials, n))
        est_b = xs.var(axis=1, ddof=0)  # divides by n
        est_u = xs.var(axis=1, ddof=1)  # divides by n-1
        v_biased = float(est_b.mean())
        v_unbias = float(est_u.mean())
        # Resolution of this measurement: the standard error of the AVERAGE
        # of `trials` independent estimates. Without this number a small
        # residual cannot be told apart from a small bias.
        se_b = float(est_b.std(ddof=1)) / math.sqrt(trials)
        se_u = float(est_u.std(ddof=1)) / math.sqrt(trials)
        # Theory: E[ (1/n) sum (x - xbar)^2 ] = ((n-1)/n) * sigma^2, because
        # xbar is itself fitted from the same data and sits closer to the
        # sample than the true mean does. The deficit is exactly sigma^2/n.
        pred = (n - 1) / n * TRUE_VAR
        print("  %5d  %9.6f  %9.6f  %9.6f %8.1f  %12.6f %12.6f %6.1f"
              % (n, v_biased, pred, v_biased - TRUE_VAR, (v_biased - TRUE_VAR) / se_b,
                 v_unbias, v_unbias - TRUE_VAR, (v_unbias - TRUE_VAR) / se_u))
        rows.append((n, v_biased, v_unbias))
    print()
    print("  The /n column sits BELOW %.1f every single time, it tracks the" % TRUE_VAR)
    print("  predicted (n-1)/n * sigma^2 column, and its z-scores are in the")
    print("  hundreds. 200,000 trials cannot average that away: it is a bias,")
    print("  not noise. The /(n-1) column's z-scores stay small in both signs.")
    print()
    print("  Practical rule: np.var defaults to ddof=0 (divide by n) and")
    print("  np.cov defaults to ddof=1 (divide by n-1). They disagree by")
    print("  default. On n=5 that is a %.0f%% understatement." % (100.0 / 5))
    return {"rows": rows}


# ---------------------------------------------------------------------------
def demo7_eval_set_size():
    """The bill for demo 3: what a 50-example eval set can and cannot see."""
    print(LINE)
    print("DEMO 7 - what n^-0.5 costs you: a 50-example eval cannot see 3 points")
    print(LINE)

    rng = np.random.default_rng(SEED + 6)
    p_a, p_b = 0.80, 0.83  # B is genuinely better by 3 accuracy points
    trials = 200_000

    # A single graded example is a Bernoulli draw: it scores 1 or 0. Its
    # variance is p*(1-p) -- an expectation/variance fact, nothing more.
    var_a, var_b = p_a * (1 - p_a), p_b * (1 - p_b)
    print("  model A true accuracy %.2f (per-example variance %.4f)" % (p_a, var_a))
    print("  model B true accuracy %.2f (per-example variance %.4f)" % (p_b, var_b))
    print("  true gap %.2f. Each model is scored on its own eval set of n items." % (p_b - p_a))
    print()
    head = ("      n   se(diff)  gap/se  predicted   sim: B<A     ties"
            "  sim + half ties")
    print(head)
    print("  " + "-" * (len(head) - 2))
    for n in [20, 50, 200, 1000, 2000, 5000]:
        # Var of a difference of two INDEPENDENT means: cross term is zero
        # by demo 4, so the variances simply add.
        se = math.sqrt(var_a / n + var_b / n)
        z = (p_b - p_a) / se
        pred_wrong = phi(-z)
        acc_a = rng.binomial(n, p_a, trials) / n
        acc_b = rng.binomial(n, p_b, trials) / n
        wrong = float(np.mean(acc_b < acc_a))
        ties = float(np.mean(acc_b == acc_a))
        # Accuracy on n items is discrete, so exact ties are common at small
        # n; the continuous normal model splits them. Adding half the ties
        # back is the like-for-like comparison.
        print("  %5d  %9.5f  %6.3f  %9.4f  %9.4f  %7.4f  %14.4f"
              % (n, se, z, pred_wrong, wrong, ties, wrong + 0.5 * ties))

    # How many examples to get the answer right 95% of the time?
    z_needed = 1.6449  # one-sided 95%
    n_needed = z_needed**2 * (var_a + var_b) / (p_b - p_a) ** 2
    print()
    print("  n needed for a 95%% chance of ranking them correctly: %.0f examples"
          % math.ceil(n_needed))
    print("  A 50-item eval is off that by a factor of %.0f." % (math.ceil(n_needed) / 50))
    print("  Same arithmetic underwrites drift detection in 7.9: a metric moved")
    print("  by 3 points is only a signal once n makes 3 points bigger than the")
    print("  standard error. Below that it is the eval set breathing.")
    return None


# ---------------------------------------------------------------------------
def make_plot(d2, d3, d6):
    """Four panels. Saved as PNG; the script never opens a window."""
    fig, ax = plt.subplots(2, 2, figsize=(11, 8.5))

    a = ax[0, 0]
    a.scatter(d2["x"], d2["y"], s=3, alpha=0.35, color="#9b2226")
    a.set_title("Y = X^2 : Corr(X,Y) = %.4f\nzero correlation, total dependence" % d2["corr_a"])
    a.set_xlabel("X")
    a.set_ylabel("Y")

    a = ax[0, 1]
    a.scatter(d2["x2"], d2["z"], s=3, alpha=0.35, color="#1b4332")
    a.set_title("X, Y independent : Corr(X,Y) = %.4f\nzero correlation, no dependence" % d2["corr_b"])
    a.set_xlabel("X")
    a.set_ylabel("Y")

    a = ax[1, 0]
    a.loglog(d3["n"], d3["rmse"], "o-", color="#005f73", label="measured RMSE")
    a.loglog(d3["n"], d3["pred"], "--", color="#7f5539", label="sd(X)/sqrt(n)")
    a.set_title("error of the sample mean\nfitted exponent = %.4f" % d3["slope"])
    a.set_xlabel("n")
    a.set_ylabel("RMSE")
    a.legend()
    a.grid(True, which="both", alpha=0.25)

    a = ax[1, 1]
    ns = [r[0] for r in d6["rows"]]
    a.semilogx(ns, [r[1] for r in d6["rows"]], "o-", color="#9b2226", label="divide by n")
    a.semilogx(ns, [r[2] for r in d6["rows"]], "s-", color="#1b4332", label="divide by n-1")
    a.axhline(TRUE_VAR, color="#6b705c", ls=":", label="true variance %.1f" % TRUE_VAR)
    a.set_title("Bessel's correction, measured")
    a.set_xlabel("sample size n")
    a.set_ylabel("average estimate over 200,000 trials")
    a.legend()
    a.grid(True, alpha=0.25)

    fig.tight_layout()
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        "08_expectation_variance_covariance.png")
    fig.savefig(path, dpi=110)
    plt.close(fig)
    return path


def main():
    print("numpy %s  |  seed %d" % (np.__version__, SEED))
    demo1_identity()
    d2 = demo2_zero_cov_not_independence()
    d3 = demo3_convergence_rate()
    demo4_variance_of_a_sum()
    demo5_covariance_matrix()
    d6 = demo6_bessel()
    demo7_eval_set_size()
    print(LINE)
    path = make_plot(d2, d3, d6)
    print("PLOT written: %s" % os.path.basename(path))
    print("  size on disk: %d bytes" % os.path.getsize(path))
    print(LINE)


if __name__ == "__main__":
    main()
