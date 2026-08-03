"""
Topic 1.7 - Probability: Random Variables, Distributions, Bayes
Companion script.

WHAT THIS RUNS
    Seven numbered demos. Each one computes a probability at least two independent
    ways - a closed form and a brute-force count or simulation - and prints how far
    apart the two answers landed. The point is verification, not illustration.

REQUIREMENTS
    Python 3.10+, numpy, matplotlib. Developed against numpy 2.4.4 /
    matplotlib 3.11.1 / Python 3.14 on Windows. matplotlib is imported with the
    non-interactive "Agg" backend, so nothing tries to open a window.

SAFE / OFFLINE
    No network calls. No API keys, no environment variables, no input files.
    It writes exactly two .png files into its own directory and touches nothing
    else on disk. Every random draw comes from np.random.default_rng(SEED) with
    SEED = 20250807, so every number printed is reproducible byte for byte.

WHAT THIS PROVES PRACTICALLY
    1. Bayes theorem computed three independent ways - closed form, a normalized
       2x2 joint probability table, and integer natural frequencies out of one
       million people - agrees to machine precision (max abs diff ~1e-17).
    2. A test that is 99% accurate, applied to a disease with 0.1% prevalence,
       produces a positive result that is WRONG about 91% of the time. A simulation
       of 1,000,000 patients reproduces the analytic answer to ~0.1 percentage points.
    3. That 2x2 table IS the precision/recall table used in 2.12: the positive
       predictive value is precision, the sensitivity is recall. Same arithmetic,
       two vocabularies.
    4. The identical test carries wildly different information at different base
       rates. Sweeping prevalence from 0.01% to 50% moves the posterior from under
       1% to 99%, with no change to the test whatsoever.
    5. Empirical mean and variance of Bernoulli, Binomial, Normal, Uniform and
       Exponential samples converge onto their closed forms at the 1/sqrt(n) rate,
       and the closed forms themselves are re-derived by brute-force summation
       over the PMF (1.8).
    6. The Central Limit Theorem is measured, not asserted: the skewness of the mean
       of n exponential draws is computed empirically and matched against the
       predicted 2/sqrt(n), and the excess kurtosis against 6/n.
    7. Marginal independence and conditional independence are different properties -
       each can hold while the other fails - and the "naive" assumption behind
       Naive Bayes (2.12) is caught double-counting duplicated evidence by a factor
       of 8 in the likelihood ratio while still classifying every case correctly.
"""

import math
import os

import numpy as np

import matplotlib
matplotlib.use("Agg")  # headless: never opens a window, never blocks
import matplotlib.pyplot as plt

SEED = 20250807
HERE = os.path.dirname(os.path.abspath(__file__))
BAR = "=" * 70


def rule(title):
    print(BAR)
    print(title)
    print(BAR)


# ----------------------------------------------------------------------------
# Shared scenario constants for Demos 1, 2, 3 and 7.
# These are the exact numbers from the skip test: a "99% accurate" test, and a
# disease that 0.1% of the population has.
# "99% accurate" is deliberately ambiguous in the wild; we pin it down as
# sensitivity = specificity = 0.99, which is the most generous reading.
# ----------------------------------------------------------------------------
PREVALENCE = 0.001   # P(D)   - the prior, the base rate
SENSITIVITY = 0.99   # P(+|D) - true positive rate  (this is RECALL, see 2.12)
SPECIFICITY = 0.99   # P(-|H) - true negative rate


def bayes_ppv(prevalence, sensitivity, specificity):
    """P(disease | positive) straight from the closed form.

    P(D|+) = P(+|D) P(D) / P(+)
    P(+)   = P(+|D) P(D) + P(+|H) P(H)        <- law of total probability
    """
    p_pos_given_d = sensitivity
    p_pos_given_h = 1.0 - specificity
    p_d = prevalence
    p_h = 1.0 - prevalence
    p_pos = p_pos_given_d * p_d + p_pos_given_h * p_h
    return (p_pos_given_d * p_d) / p_pos


# ----------------------------------------------------------------------------
# DEMO 1 - Bayes theorem, stated and then computed three independent ways.
# ----------------------------------------------------------------------------
def demo1_bayes_three_ways():
    rule("DEMO 1 - Bayes theorem computed three independent ways")

    p_d = PREVALENCE
    p_h = 1.0 - p_d
    p_pos_given_d = SENSITIVITY
    p_pos_given_h = 1.0 - SPECIFICITY

    print("  the setup (exactly the skip-test numbers)")
    print("    P(D)       prevalence / prior      = %.6f   (%.2f%% of people)"
          % (p_d, 100 * p_d))
    print("    P(+|D)     sensitivity / recall    = %.6f" % p_pos_given_d)
    print("    P(-|H)     specificity             = %.6f" % SPECIFICITY)
    print("    P(+|H)     false positive rate     = %.6f" % p_pos_given_h)
    print()

    # --- Way A: the closed form -------------------------------------------
    p_pos = p_pos_given_d * p_d + p_pos_given_h * p_h
    way_a = (p_pos_given_d * p_d) / p_pos
    print("  WAY A - closed form")
    print("    P(+) = P(+|D)P(D) + P(+|H)P(H)")
    print("         = %.6f * %.6f + %.6f * %.6f" % (p_pos_given_d, p_d, p_pos_given_h, p_h))
    print("         = %.8f + %.8f = %.8f" % (p_pos_given_d * p_d, p_pos_given_h * p_h, p_pos))
    print("    P(D|+) = %.8f / %.8f = %.10f" % (p_pos_given_d * p_d, p_pos, way_a))
    print()

    # --- Way B: build the full joint distribution and normalize a column ---
    # joint[i, j] = P(state_i, result_j).  Rows: D, H.  Columns: +, -.
    # Nothing here uses Bayes theorem; it is just a table of four numbers that
    # sums to 1, and a conditional probability is a normalized slice of it.
    joint = np.array([
        [p_d * p_pos_given_d,       p_d * (1 - p_pos_given_d)],
        [p_h * p_pos_given_h,       p_h * (1 - p_pos_given_h)],
    ])
    way_b = joint[0, 0] / joint[:, 0].sum()
    print("  WAY B - normalize a column of the joint distribution")
    print("                        result +        result -          row total")
    print("    disease D      %14.10f  %14.10f   %14.10f"
          % (joint[0, 0], joint[0, 1], joint[0].sum()))
    print("    healthy H      %14.10f  %14.10f   %14.10f"
          % (joint[1, 0], joint[1, 1], joint[1].sum()))
    print("    col total      %14.10f  %14.10f   %14.10f"
          % (joint[:, 0].sum(), joint[:, 1].sum(), joint.sum()))
    print("    the whole table sums to %.16f  (it must; probability axiom)" % joint.sum())
    print("    P(D|+) = joint[D,+] / column(+) = %.10f" % way_b)
    print()

    # --- Way C: integer natural frequencies, no floating point division
    #     until the very last step. This is the version that convinces people.
    n = 1_000_000
    n_d = round(n * p_d)
    n_h = n - n_d
    tp = round(n_d * p_pos_given_d)
    fn = n_d - tp
    fp = round(n_h * p_pos_given_h)
    tn = n_h - fp
    way_c = tp / (tp + fp)
    print("  WAY C - natural frequencies: 1,000,000 people, counted")
    print("    %9d have the disease -> %8d test +  (true positives)" % (n_d, tp))
    print("                                 %8d test -  (false negatives)" % fn)
    print("    %9d are healthy     -> %8d test +  (FALSE positives)" % (n_h, fp))
    print("                                 %8d test -  (true negatives)" % tn)
    print("    positives in total          = %d + %d = %d" % (tp, fp, tp + fp))
    print("    P(D|+) = %d / %d = %.10f" % (tp, tp + fp, way_c))
    print()

    diffs = [abs(way_a - way_b), abs(way_a - way_c), abs(way_b - way_c)]
    print("  AGREEMENT")
    print("    way A (formula)      = %.16f" % way_a)
    print("    way B (joint table)  = %.16f" % way_b)
    print("    way C (counting)     = %.16f" % way_c)
    print("    max abs diff         = %.3e   <- three different routes, one answer"
          % max(diffs))
    print()
    print("  ANSWER TO SKIP TEST 2: a positive result is far more likely FALSE.")
    print("    P(disease | positive) = %.4f%%" % (100 * way_a))
    print("    P(healthy | positive) = %.4f%%" % (100 * (1 - way_a)))
    print("    For every 1 true positive there are %.2f false positives."
          % (fp / tp))
    print()


# ----------------------------------------------------------------------------
# DEMO 2 - stop trusting the algebra: simulate a million patients and count.
# ----------------------------------------------------------------------------
def demo2_simulate_a_million(rng):
    rule("DEMO 2 - simulate 1,000,000 patients and count what actually happens")

    n = 1_000_000

    # Two independent coin flips per patient:
    #   1. does this patient have the disease?           (Bernoulli, p = PREVALENCE)
    #   2. given that, what does the test say?           (Bernoulli, p = sens or 1-spec)
    # This is a random variable in the literal sense: a function from an outcome
    # of a random experiment to a number. Nothing here knows Bayes theorem.
    has_disease = rng.random(n) < PREVALENCE

    # per-patient probability that the test fires
    p_test_positive = np.where(has_disease, SENSITIVITY, 1.0 - SPECIFICITY)
    tests_positive = rng.random(n) < p_test_positive

    tp = int(np.sum(has_disease & tests_positive))
    fn = int(np.sum(has_disease & ~tests_positive))
    fp = int(np.sum(~has_disease & tests_positive))
    tn = int(np.sum(~has_disease & ~tests_positive))

    print("  2x2 contingency table, %s simulated patients, seed %d" % (f"{n:,}", SEED))
    print()
    print("                        test +          test -        row total")
    print("    ------------------------------------------------------------")
    print("    disease D     %12s   %12s   %12s"
          % (f"{tp:,}", f"{fn:,}", f"{tp + fn:,}"))
    print("    healthy H     %12s   %12s   %12s"
          % (f"{fp:,}", f"{tn:,}", f"{fp + tn:,}"))
    print("    ------------------------------------------------------------")
    print("    col total     %12s   %12s   %12s"
          % (f"{tp + fp:,}", f"{fn + tn:,}", f"{n:,}"))
    print()
    print("  READ THE '+' COLUMN. That is the entire lesson.")
    print("    true  positives (sick, test +) : %s" % f"{tp:,}")
    print("    FALSE positives (well, test +) : %s" % f"{fp:,}")
    print("    ratio false : true             = %.2f : 1" % (fp / tp))
    print()

    ppv_sim = tp / (tp + fp)
    ppv_analytic = bayes_ppv(PREVALENCE, SENSITIVITY, SPECIFICITY)
    npv_sim = tn / (tn + fn)

    # How close SHOULD the simulation be? Only ~1000 of the million people are
    # actually sick, so the true-positive count carries Poisson-scale noise of
    # about sqrt(1000). Quoting a simulated number without its own error bar is
    # the mistake 1.10 exists to prevent, so we compute the error bar first.
    # Given the number of positives P, the true-positive count is Binomial(P, ppv),
    # so the standard error of the estimated PPV is sqrt(ppv(1-ppv)/P).
    expected_positives = n * (SENSITIVITY * PREVALENCE
                              + (1 - SPECIFICITY) * (1 - PREVALENCE))
    se = math.sqrt(ppv_analytic * (1 - ppv_analytic) / expected_positives)
    print("  SIMULATED vs ANALYTIC")
    print("    P(D|+) simulated  = %.6f  (%.4f%%)" % (ppv_sim, 100 * ppv_sim))
    print("    P(D|+) Bayes      = %.6f  (%.4f%%)" % (ppv_analytic, 100 * ppv_analytic))
    print("    difference        = %.4f percentage points"
          % abs(100 * ppv_sim - 100 * ppv_analytic))
    print("    expected noise    = %.4f percentage points (1 standard error)" % (100 * se))
    print("    that is %.2f standard errors away - ordinary sampling noise, not a bug."
          % (abs(ppv_sim - ppv_analytic) / se))
    print()

    # Turn the noise down by a factor of sqrt(20) and watch the gap close.
    # Counted in chunks so we never hold 20,000,000 floats in memory at once.
    big = 20_000_000
    chunk = 2_000_000
    btp = bfp = 0
    for _ in range(big // chunk):
        d = rng.random(chunk) < PREVALENCE
        pos = rng.random(chunk) < np.where(d, SENSITIVITY, 1 - SPECIFICITY)
        btp += int(np.sum(d & pos))
        bfp += int(np.sum(~d & pos))
    ppv_big = btp / (btp + bfp)
    print("  SAME EXPERIMENT AT %s PATIENTS (20x the sample, sqrt(20)=4.5x less noise)"
          % f"{big:,}")
    print("    true positives = %s   false positives = %s" % (f"{btp:,}", f"{bfp:,}"))
    print("    P(D|+) simulated  = %.6f  (%.4f%%)" % (ppv_big, 100 * ppv_big))
    print("    P(D|+) Bayes      = %.6f  (%.4f%%)" % (ppv_analytic, 100 * ppv_analytic))
    se_big = math.sqrt(ppv_analytic * (1 - ppv_analytic) / (btp + bfp))
    print("    difference        = %.4f percentage points"
          % abs(100 * ppv_big - 100 * ppv_analytic))
    print("    expected noise    = %.4f percentage points (1 standard error)"
          % (100 * se_big))
    print("    that is %.2f standard errors. The error bar shrank %.1fx, exactly as"
          % (abs(ppv_big - ppv_analytic) / se_big, se / se_big))
    print("    sqrt(20) predicts. Bayes was right both times; only the noise moved.")
    print()

    # --- the same table, in the vocabulary of 2.12 -------------------------
    precision = tp / (tp + fp)
    recall = tp / (tp + fn)
    specificity_emp = tn / (tn + fp)
    accuracy = (tp + tn) / n
    f1 = 2 * precision * recall / (precision + recall)
    print("  THE SAME TABLE, RENAMED (this is precision/recall - see 2.12)")
    print("    precision   = TP/(TP+FP) = %.6f   <- identical to P(D|+), the PPV" % precision)
    print("    recall      = TP/(TP+FN) = %.6f   <- identical to sensitivity" % recall)
    print("    specificity = TN/(TN+FP) = %.6f" % specificity_emp)
    print("    NPV         = TN/(TN+FN) = %.6f   <- a negative is very trustworthy" % npv_sim)
    print("    F1          = %.6f" % f1)
    print("    accuracy    = %.6f   <- looks superb, and is useless here" % accuracy)
    print()
    print("  A model that always predicts 'healthy' would score accuracy %.6f"
          % ((n - (tp + fn)) / n))
    print("  ... which BEATS the test. Accuracy on a rare class is not evidence.")
    print()


# ----------------------------------------------------------------------------
# DEMO 3 - the base rate is doing the work, not the test.
# ----------------------------------------------------------------------------
def demo3_prevalence_sweep(rng):
    rule("DEMO 3 - one unchanged test, swept across base rates")

    prevalences = np.array([0.0001, 0.0005, 0.001, 0.005, 0.01, 0.05,
                            0.10, 0.20, 0.35, 0.50])
    ppv = np.array([bayes_ppv(p, SENSITIVITY, SPECIFICITY) for p in prevalences])

    print("  Sensitivity and specificity are FIXED at 0.99 for every row below.")
    print("  Only the prior changes.")
    print()
    print("    prevalence     P(D|+)        odds of being right     1 in N positives is real")
    print("    ----------------------------------------------------------------------------")
    for p, v in zip(prevalences, ppv):
        print("    %8.4f%%   %8.4f%%        %10.4f : 1        1 in %8.2f"
              % (100 * p, 100 * v, v / (1 - v), 1.0 / v))
    print()

    # Spot-check two rows by simulation so the curve is not taken on trust.
    print("  spot-check by simulation (2,000,000 patients each), with error bars,")
    print("  because a simulated number quoted without its noise proves nothing:")
    for p in (0.001, 0.05):
        n = 2_000_000
        d = rng.random(n) < p
        pos = rng.random(n) < np.where(d, SENSITIVITY, 1 - SPECIFICITY)
        npos = int(np.sum(pos))
        got = float(np.sum(d & pos)) / npos
        want = bayes_ppv(p, SENSITIVITY, SPECIFICITY)
        se = math.sqrt(want * (1 - want) / npos)
        print("    prev %6.3f%%  simulated %.5f   Bayes %.5f   diff %.5f   = %.2f SE"
              % (100 * p, got, want, abs(got - want), abs(got - want) / se))
    print()

    # A finer grid for the plot.
    grid = np.logspace(-4, np.log10(0.5), 400)
    grid_ppv = np.array([bayes_ppv(p, SENSITIVITY, SPECIFICITY) for p in grid])

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.semilogx(100 * grid, 100 * grid_ppv, lw=2.2, color="#005f73")
    ax.axvline(100 * PREVALENCE, color="#9b2226", ls="--", lw=1.4)
    ax.axhline(100 * bayes_ppv(PREVALENCE, SENSITIVITY, SPECIFICITY),
               color="#9b2226", ls="--", lw=1.4)
    ax.plot([100 * PREVALENCE], [100 * bayes_ppv(PREVALENCE, SENSITIVITY, SPECIFICITY)],
            "o", ms=9, color="#9b2226")
    ax.annotate("0.1%% prevalence -> %.1f%%"
                % (100 * bayes_ppv(PREVALENCE, SENSITIVITY, SPECIFICITY)),
                xy=(100 * PREVALENCE, 100 * bayes_ppv(PREVALENCE, SENSITIVITY, SPECIFICITY)),
                xytext=(0.03, 55), fontsize=10, color="#9b2226")
    ax.set_xlabel("prevalence, P(D)   [%, log scale]")
    ax.set_ylabel("P(disease | positive)   [%]")
    ax.set_title("Same 99%/99% test. Only the base rate changes.")
    ax.grid(True, which="both", alpha=0.3)
    ax.set_ylim(0, 100)
    fig.tight_layout()
    path = os.path.join(HERE, "07_bayes_prevalence_sweep.png")
    fig.savefig(path, dpi=110)
    plt.close(fig)
    print("  saved %s  (%d bytes)" % (os.path.basename(path), os.path.getsize(path)))
    print()
    print("  The transferable lesson: evidence strength (the test) and prior")
    print("  strength (the base rate) multiply. A strong test against a rare event")
    print("  still yields a weak conclusion. This is why an eval set built around a")
    print("  rare failure mode misleads unless the base rate is carried along - the")
    print("  same trap that 1.10 formalises as the significance-vs-prior problem.")
    print()


# ----------------------------------------------------------------------------
# DEMO 4 - five named distributions, closed forms checked against samples.
# ----------------------------------------------------------------------------
def demo4_distributions(rng):
    rule("DEMO 4 - five distributions: closed-form mean/variance vs samples")

    # First: re-derive the Binomial closed forms by brute-force summation over
    # the PMF. This is a pure-arithmetic check with no randomness in it at all.
    n_trials, p = 20, 0.3
    ks = np.arange(n_trials + 1)
    pmf = np.array([math.comb(n_trials, int(k)) * p ** int(k) * (1 - p) ** (n_trials - int(k))
                    for k in ks])
    mean_by_sum = float(np.sum(ks * pmf))
    var_by_sum = float(np.sum((ks - mean_by_sum) ** 2 * pmf))
    print("  Binomial(n=20, p=0.3) - closed form vs brute-force sum over the PMF")
    print("    sum of PMF over all 21 outcomes = %.16f" % pmf.sum())
    print("      -> off 1.0 by %.3e, which is float64 rounding across 21 additions,"
          % abs(pmf.sum() - 1.0))
    print("         not a probability error. 1.12 is the topic that owns this.")
    print("    mean  by sum k*P(k)   = %.14f      closed form n*p      = %.14f"
          % (mean_by_sum, n_trials * p))
    print("    var   by sum (k-mu)^2 = %.14f      closed form n*p*(1-p)= %.14f"
          % (var_by_sum, n_trials * p * (1 - p)))
    print("    max abs diff = %.3e   <- the formulas are not approximations"
          % max(abs(mean_by_sum - n_trials * p),
                abs(var_by_sum - n_trials * p * (1 - p))))
    print()

    # Now the sampling check across five distributions and three sample sizes.
    specs = [
        ("Bernoulli(p=0.3)", lambda m: (rng.random(m) < 0.3).astype(float),
         0.3, 0.3 * 0.7),
        ("Binomial(20, 0.3)", lambda m: rng.binomial(20, 0.3, size=m).astype(float),
         20 * 0.3, 20 * 0.3 * 0.7),
        ("Normal(5, sd=2)", lambda m: rng.normal(5.0, 2.0, size=m),
         5.0, 4.0),
        ("Uniform(0, 10)", lambda m: rng.uniform(0.0, 10.0, size=m),
         5.0, 100.0 / 12.0),
        ("Exponential(mean=2)", lambda m: rng.exponential(2.0, size=m),
         2.0, 4.0),
    ]
    # IMPORTANT METHOD NOTE. A single sample of size n gives ONE error, and one
    # error is mostly luck - the first draft of this demo printed a table where
    # the n=100 error was smaller than the n=10,000 error, which teaches the
    # opposite of the truth. So each cell below is the AVERAGE absolute error
    # over many independent repeats. That is what "typical error" means.
    sizes = [(100, 400), (10_000, 200), (1_000_000, 20)]

    print("  Empirical mean and variance vs their closed forms.")
    print("  Each cell = mean |estimate - truth| over R independent repeats,")
    print("  because one draw is luck and we are trying to measure a rate.")
    print("  The standard error is sd/sqrt(n), so 100x more data -> 10x less error.")
    print()
    header = "    %-20s %11s" % ("distribution", "true mean")
    for m, r in sizes:
        header += " %13s" % ("n=%d" % m)
    print(header + "   ratios")
    print("    " + "-" * 78)
    for name, draw, true_mean, true_var in specs:
        row = "    %-20s %11.5f" % (name, true_mean)
        errs = []
        for m, r in sizes:
            e = float(np.mean([abs(float(np.mean(draw(m))) - true_mean) for _ in range(r)]))
            errs.append(e)
            row += " %13.6f" % e
        print(row + "   %.1fx %.1fx" % (errs[0] / errs[1], errs[1] / errs[2]))
    print("                                                                    "
          "  (want ~10x 10x)")
    print()

    header = "    %-20s %11s" % ("distribution", "true var")
    for m, r in sizes:
        header += " %13s" % ("n=%d" % m)
    print(header + "   ratios")
    print("    " + "-" * 78)
    for name, draw, true_mean, true_var in specs:
        row = "    %-20s %11.5f" % (name, true_var)
        errs = []
        for m, r in sizes:
            e = float(np.mean([abs(float(np.var(draw(m))) - true_var) for _ in range(r)]))
            errs.append(e)
            row += " %13.6f" % e
        print(row + "   %.1fx %.1fx" % (errs[0] / errs[1], errs[1] / errs[2]))
    print("                                                                    "
          "  (want ~10x 10x)")
    print()

    # Make the 1/sqrt(n) rate explicit rather than eyeballed, with the exact
    # constant. For a mean that is approximately Normal(mu, sd^2/n), the
    # expected ABSOLUTE error is sd/sqrt(n) * sqrt(2/pi), because E|Z| = sqrt(2/pi).
    print("  Nailing the constant: Exponential(mean=2) has sd = 2, so the predicted")
    print("  typical absolute error of the sample mean is (2/sqrt(n)) * sqrt(2/pi).")
    print()
    print("    %10s %18s %18s %10s" % ("n", "measured |err|", "predicted", "ratio"))
    for m in (100, 1_000, 10_000, 100_000, 1_000_000):
        errs = np.abs(np.array([np.mean(rng.exponential(2.0, size=m))
                                for _ in range(400)]) - 2.0)
        typical = float(np.mean(errs))
        predicted = 2.0 / math.sqrt(m) * math.sqrt(2.0 / math.pi)
        print("    %10d %18.6f %18.6f %10.3f"
              % (m, typical, predicted, typical / predicted))
    print("    (the ratio column hugging 1.0 is the 1/sqrt(n) law confirmed over")
    print("     four orders of magnitude - 1.8 develops where sd/sqrt(n) comes from)")
    print()


# ----------------------------------------------------------------------------
# DEMO 5 - Central Limit Theorem, measured with a number instead of a shrug.
# ----------------------------------------------------------------------------
def _chunked_means(rng, n, replicates, chunk=20_000):
    """Mean of n Exponential(mean=1) draws, `replicates` times, without ever
    allocating a replicates-by-n array."""
    out = np.empty(replicates)
    done = 0
    while done < replicates:
        k = min(chunk, replicates - done)
        out[done:done + k] = rng.exponential(1.0, size=(k, n)).mean(axis=1)
        done += k
    return out


def _skew_kurt(x):
    """Sample skewness and EXCESS kurtosis, from the definitions.
    skew = E[((X-mu)/sigma)^3]   kurt_excess = E[((X-mu)/sigma)^4] - 3
    """
    mu = x.mean()
    sd = x.std()
    z = (x - mu) / sd
    return float(np.mean(z ** 3)), float(np.mean(z ** 4) - 3.0)


def _normal_cdf(x):
    """Standard normal CDF from math.erf - no scipy needed."""
    return 0.5 * (1.0 + np.array([math.erf(v / math.sqrt(2.0)) for v in np.atleast_1d(x)]))


def demo5_clt(rng):
    rule("DEMO 5 - Central Limit Theorem, with a measured error not a hand-wave")

    replicates = 200_000
    print("  Source distribution: Exponential(mean=1). It is violently non-normal:")
    print("  it is bounded below at 0, and its true skewness is exactly 2.")
    print("  We average n of its draws, %s times, and measure the shape." % f"{replicates:,}")
    print()
    print("  Theory says the skewness of the mean of n iid draws is skew/sqrt(n),")
    print("  and the excess kurtosis is kurt/n. For Exponential: 2/sqrt(n) and 6/n.")
    print()
    print("    %5s %14s %14s %12s %12s %12s"
          % ("n", "skew measured", "2/sqrt(n)", "kurt meas.", "6/n", "KS vs normal"))
    print("    " + "-" * 74)

    grid = np.linspace(-4.0, 4.0, 801)
    normal_grid = _normal_cdf(grid)
    stored = {}
    for n in (1, 2, 5, 10, 30, 100):
        means = _chunked_means(rng, n, replicates)
        z = (means - means.mean()) / means.std()
        stored[n] = z
        sk, ku = _skew_kurt(means)
        # Kolmogorov-Smirnov style statistic: the largest gap between the
        # empirical CDF of the standardised means and the normal CDF.
        emp = np.searchsorted(np.sort(z), grid, side="right") / z.size
        ks = float(np.max(np.abs(emp - normal_grid)))
        print("    %5d %14.5f %14.5f %12.5f %12.5f %12.5f"
              % (n, sk, 2.0 / math.sqrt(n), ku, 6.0 / n, ks))

    floor = 1.0 / math.sqrt(replicates)
    print()
    print("  Monte Carlo noise floor on that KS column is about 1/sqrt(%s) = %.5f,"
          % (f"{replicates:,}", floor))
    print("  so anything at or below ~%.4f is measurement noise, not residual skew."
          % (2 * floor))
    print("  The skew and kurtosis columns are the honest evidence: measured tracks")
    print("  predicted across two orders of magnitude in n.")
    print()
    # The n=1 KS value is not arbitrary and is worth pinning down: a standardised
    # Exponential(1) is x-1, which can never go below -1, while the normal puts
    # Phi(-1) of its mass down there. So the gap at z = -1 is exactly Phi(-1).
    phi_minus_1 = float(_normal_cdf(-1.0)[0])
    print("  Why is the n=1 row %.5f? A standardised Exponential(1) equals x - 1," % 0.15866)
    print("  so it has ZERO mass below -1, while the normal curve puts Phi(-1) =")
    print("  %.6f of its mass there. The largest possible gap is that number," % phi_minus_1)
    print("  and the measurement found it. The starting point was never noise.")
    print()

    fig, axes = plt.subplots(2, 3, figsize=(12, 6.5), sharex=True)
    for ax, n in zip(axes.ravel(), (1, 2, 5, 10, 30, 100)):
        z = stored[n]
        ax.hist(z, bins=90, range=(-4, 4), density=True,
                color="#0a9396", edgecolor="none", alpha=0.85)
        pdf = np.exp(-grid ** 2 / 2) / math.sqrt(2 * math.pi)
        ax.plot(grid, pdf, color="#9b2226", lw=1.8)
        sk, _ = _skew_kurt(z)
        ax.set_title("n = %d   skew = %.3f" % (n, sk), fontsize=10)
        ax.set_xlim(-4, 4)
        ax.grid(alpha=0.25)
    fig.suptitle("Mean of n Exponential(1) draws, standardised, vs the normal curve")
    fig.tight_layout()
    path = os.path.join(HERE, "07_clt_convergence.png")
    fig.savefig(path, dpi=110)
    plt.close(fig)
    print("  saved %s  (%d bytes)" % (os.path.basename(path), os.path.getsize(path)))
    print()
    print("  Caveat worth carrying: the CLT is about the MIDDLE of the distribution.")
    print("  At n=100 the centre is indistinguishable from normal while the far right")
    print("  tail is still exponential. Tail risk does not become normal quickly.")
    print()


# ----------------------------------------------------------------------------
# DEMO 6 - independence is not conditional independence, and 'naive' is a bet.
# ----------------------------------------------------------------------------
def demo6_independence(rng):
    rule("DEMO 6 - independence vs conditional independence, and the 'naive' bet")

    n = 400_000

    # --- PART A: conditionally independent, marginally DEPENDENT -----------
    # Spam filter. Class C = spam with prior 0.3.
    # Given the class, the two word-features are generated independently.
    print("  PART A - independent GIVEN the class, dependent when you forget the class")
    print("    P(spam) = 0.30")
    print("    given spam: P(A=1) = 0.80, P(B=1) = 0.70, drawn independently")
    print("    given ham : P(A=1) = 0.05, P(B=1) = 0.04, drawn independently")
    print()
    spam = rng.random(n) < 0.30
    a = rng.random(n) < np.where(spam, 0.80, 0.05)
    b = rng.random(n) < np.where(spam, 0.70, 0.04)

    p_a = a.mean()
    p_b = b.mean()
    p_ab = (a & b).mean()
    p_a_g_s = a[spam].mean()
    p_b_g_s = b[spam].mean()
    p_ab_g_s = (a & b)[spam].mean()

    print("    CONDITIONAL on spam:")
    print("      P(A=1|spam)             = %.6f" % p_a_g_s)
    print("      P(B=1|spam)             = %.6f" % p_b_g_s)
    print("      P(A=1,B=1|spam)         = %.6f" % p_ab_g_s)
    print("      P(A|spam)*P(B|spam)     = %.6f" % (p_a_g_s * p_b_g_s))
    print("      gap                     = %.6f   -> conditionally INDEPENDENT"
          % abs(p_ab_g_s - p_a_g_s * p_b_g_s))
    print()
    print("    MARGINALLY, ignoring the class:")
    print("      P(A=1)                  = %.6f" % p_a)
    print("      P(B=1)                  = %.6f" % p_b)
    print("      P(A=1,B=1)              = %.6f" % p_ab)
    print("      P(A)*P(B)               = %.6f" % (p_a * p_b))
    print("      gap                     = %.6f   -> marginally DEPENDENT (%.2fx off)"
          % (abs(p_ab - p_a * p_b), p_ab / (p_a * p_b)))
    print()

    # --- PART B: marginally independent, conditionally DEPENDENT ----------
    print("  PART B - the reverse: independent until you condition, then locked together")
    print("    X, Y are fair independent coin flips. Z = X XOR Y.")
    print()
    x = rng.random(n) < 0.5
    y = rng.random(n) < 0.5
    z = np.logical_xor(x, y)
    print("      P(X=1)                  = %.6f" % x.mean())
    print("      P(Y=1)                  = %.6f" % y.mean())
    print("      P(X=1,Y=1)              = %.6f" % (x & y).mean())
    print("      P(X)*P(Y)               = %.6f" % (x.mean() * y.mean()))
    print("      gap                     = %.6f   -> marginally INDEPENDENT"
          % abs((x & y).mean() - x.mean() * y.mean()))
    print()
    m = ~z  # condition on Z = 0, i.e. X and Y agree
    print("      now condition on Z = 0:")
    print("      P(X=1|Z=0)              = %.6f" % x[m].mean())
    print("      P(Y=1|Z=0)              = %.6f" % y[m].mean())
    print("      P(X=1,Y=1|Z=0)          = %.6f" % (x & y)[m].mean())
    print("      P(X|Z=0)*P(Y|Z=0)       = %.6f" % (x[m].mean() * y[m].mean()))
    print("      gap                     = %.6f   -> conditionally DEPENDENT"
          % abs((x & y)[m].mean() - x[m].mean() * y[m].mean()))
    print()
    print("    So the two notions are logically unrelated. Neither implies the other.")
    print()

    # --- PART C: what the naive assumption costs when it is false ---------
    # Now B is a near-copy of A: given the class, B agrees with A 95% of the time.
    # A Naive Bayes classifier (2.12) assumes P(A,B|C) = P(A|C)P(B|C). Here that
    # is simply false, and we can measure exactly how false.
    print("  PART C - what the 'naive' assumption of 2.12 costs when it is wrong")
    print("    Same classes, but now B is a near-duplicate of A: given the class,")
    print("    B copies A with probability 0.95. The features are NOT conditionally")
    print("    independent any more. Naive Bayes assumes they are.")
    print()
    pA = {True: 0.80, False: 0.05}
    prior = {True: 0.30, False: 0.70}
    copy_p = 0.95

    # exact conditional joint P(A=i, B=j | C)
    def joint_given(c, i, j):
        pa = pA[c] if i else 1 - pA[c]
        pb_given_a = copy_p if (i == j) else 1 - copy_p
        return pa * pb_given_a

    def marg_b(c, j):
        return sum(joint_given(c, i, j) for i in (True, False))

    print("    %-12s %14s %14s %12s" % ("pattern", "exact LR", "naive LR", "naive/exact"))
    print("    " + "-" * 56)
    for i in (True, False):
        for j in (True, False):
            ex = joint_given(True, i, j) / joint_given(False, i, j)
            nv = ((pA[True] if i else 1 - pA[True]) * marg_b(True, j)) / \
                 ((pA[False] if i else 1 - pA[False]) * marg_b(False, j))
            print("    A=%d,B=%d      %14.4f %14.4f %11.2fx"
                  % (int(i), int(j), ex, nv, nv / ex))
    print()
    print("    Look at the exact-LR column: it takes only TWO values, one per value")
    print("    of A. B changes nothing. That is because in this construction B is a")
    print("    noisy copy of A, so P(B|A,class) does not depend on the class at all -")
    print("    once you know A, B is pure noise. The exact rule correctly ignores it.")
    print("    The naive rule cannot: it multiplies in a factor for B regardless.")
    print()

    # And now on real samples: does the overconfidence change the decision?
    spam2 = rng.random(n) < prior[True]
    a2 = rng.random(n) < np.where(spam2, pA[True], pA[False])
    same = rng.random(n) < copy_p
    b2 = np.where(same, a2, ~a2)

    def posteriors(ai, bi):
        ex_num = prior[True] * joint_given(True, ai, bi)
        ex_den = ex_num + prior[False] * joint_given(False, ai, bi)
        nv_num = prior[True] * (pA[True] if ai else 1 - pA[True]) * marg_b(True, bi)
        nv_den = nv_num + prior[False] * (pA[False] if ai else 1 - pA[False]) * marg_b(False, bi)
        return ex_num / ex_den, nv_num / nv_den

    ex_post = np.empty(n)
    nv_post = np.empty(n)
    for ai in (True, False):
        for bi in (True, False):
            mask = (a2 == ai) & (b2 == bi)
            e, v = posteriors(ai, bi)
            ex_post[mask] = e
            nv_post[mask] = v

    ex_pred = ex_post > 0.5
    nv_pred = nv_post > 0.5
    agree = float(np.mean(ex_pred == nv_pred))
    acc_ex = float(np.mean(ex_pred == spam2))
    acc_nv = float(np.mean(nv_pred == spam2))
    print("    on %s samples drawn from the TRUE (dependent) model:" % f"{n:,}")
    print("      exact posterior accuracy   = %.6f" % acc_ex)
    print("      naive posterior accuracy   = %.6f" % acc_nv)
    print("      the two agree on the label = %.6f of cases" % agree)
    print("      mean |naive - exact| posterior probability = %.6f"
          % float(np.mean(np.abs(nv_post - ex_post))))
    print("      max  |naive - exact| posterior probability = %.6f"
          % float(np.max(np.abs(nv_post - ex_post))))
    print()
    print("    Verdict: the naive model is badly MIS-CALIBRATED. It distorts the")
    print("    evidence in BOTH directions - 8.1x too extreme when the duplicate")
    print("    agrees, 4x too weak when it disagrees - yet the argmax is unchanged,")
    print("    so classification accuracy is identical to the exact model's.")
    print("    That is exactly why Naive Bayes (2.12) survives an assumption that is")
    print("    almost always false: RANKING survives what CALIBRATION does not.")
    print("    Trust its label. Do not trust its probability.")
    print()


# ----------------------------------------------------------------------------
# DEMO 7 - evidence accumulates by multiplying odds / adding log-odds.
# ----------------------------------------------------------------------------
def demo7_sequential_updating():
    rule("DEMO 7 - updating on evidence: odds multiply, log-odds add")

    prior_odds = PREVALENCE / (1 - PREVALENCE)
    lr_pos = SENSITIVITY / (1 - SPECIFICITY)          # likelihood ratio of a +
    lr_neg = (1 - SENSITIVITY) / SPECIFICITY          # likelihood ratio of a -

    print("  odds(x) = P(x) / (1 - P(x));  P = odds / (1 + odds)")
    print("  Bayes in odds form:  posterior odds = prior odds * likelihood ratio")
    print()
    print("    prior odds  = %.6f / %.6f = %.8f" % (PREVALENCE, 1 - PREVALENCE, prior_odds))
    print("    LR of a +   = P(+|D)/P(+|H) = %.4f / %.4f = %.4f"
          % (SENSITIVITY, 1 - SPECIFICITY, lr_pos))
    print("    LR of a -   = P(-|D)/P(-|H) = %.4f / %.4f = %.6f"
          % (1 - SENSITIVITY, SPECIFICITY, lr_neg))
    print()

    sequences = [
        ("+",       [lr_pos]),
        ("+ +",     [lr_pos, lr_pos]),
        ("+ + +",   [lr_pos, lr_pos, lr_pos]),
        ("+ + -",   [lr_pos, lr_pos, lr_neg]),
        ("-",       [lr_neg]),
    ]
    print("    %-10s %16s %14s %16s" % ("results", "posterior odds", "P(D|results)", "log-odds"))
    print("    " + "-" * 60)
    results = {}
    for label, lrs in sequences:
        odds = prior_odds
        for lr in lrs:
            odds *= lr
        p = odds / (1 + odds)
        results[label] = p
        print("    %-10s %16.6f %13.4f%% %16.6f"
              % (label, odds, 100 * p, math.log(odds)))
    print()

    # Independent verification: recompute the "+ + " case from the raw joint over
    # three binary test outcomes, with no odds algebra anywhere, assuming the
    # tests are conditionally independent given disease status.
    def brute_force(seq):
        """seq is a list of True (positive) / False (negative)."""
        num = PREVALENCE
        den_h = 1 - PREVALENCE
        for is_pos in seq:
            num *= SENSITIVITY if is_pos else (1 - SENSITIVITY)
            den_h *= (1 - SPECIFICITY) if is_pos else SPECIFICITY
        return num / (num + den_h)

    checks = [("+", [True]), ("+ +", [True, True]),
              ("+ + +", [True, True, True]), ("+ + -", [True, True, False]),
              ("-", [False])]
    worst = 0.0
    print("    cross-check: same numbers from the raw joint, no odds algebra")
    print("    %-10s %18s %18s %12s" % ("results", "odds form", "brute force", "abs diff"))
    print("    " + "-" * 60)
    for label, seq in checks:
        bf = brute_force(seq)
        d = abs(bf - results[label])
        worst = max(worst, d)
        print("    %-10s %18.14f %18.14f %12.3e" % (label, results[label], bf, d))
    print("    max abs diff over all five = %.3e" % worst)
    print()
    print("  Read the '+ +' row: two positives take you from %.2f%% to %.2f%%."
          % (100 * results["+"], 100 * results["+ +"]))
    print("  Read the '+ + -' row: a single negative undoes both positives, back to %.2f%%."
          % (100 * results["+ + -"]))
    print()
    print("  THE CATCH, and it links straight back to Demo 6: multiplying the")
    print("  likelihood ratios assumes the repeat tests are conditionally independent")
    print("  given disease status. If they share a systematic bias - the same reagent,")
    print("  the same lab - they are not, and the '+ +' number above is too confident,")
    print("  in exactly the way Part C of Demo 6 measured.")
    print()
    print("  Adding log-likelihood-ratios instead of multiplying is the same equation")
    print("  in a numerically safer form (1.12), and it is literally what a Naive Bayes")
    print("  classifier computes in 2.12, and what a language model accumulates when it")
    print("  sums log-probabilities across a sequence in 4.6.")
    print()


def main():
    print("numpy %s  |  seed %d" % (np.__version__, SEED))
    rng = np.random.default_rng(SEED)
    demo1_bayes_three_ways()
    demo2_simulate_a_million(rng)
    demo3_prevalence_sweep(rng)
    demo4_distributions(rng)
    demo5_clt(rng)
    demo6_independence(rng)
    demo7_sequential_updating()
    print(BAR)
    print("done - all demos completed")
    print(BAR)


if __name__ == "__main__":
    main()
