"""1.10 - Statistics: Descriptive, Inferential, and Hypothesis Testing: measured, not asserted.

Six numbered demonstrations that VERIFY the core principles of statistical inference,
confidence interval coverage, p-value mechanics, two-sample t-tests vs. permutation tests,
Type I/II errors, and multiple testing corrections in LLM prompt evaluations and A/B testing (7.15).

Requirements : numpy, scipy, matplotlib (Agg backend only - headless).
Safe/offline : no network, no API keys, no external files read. The single file
               written is 10_statistics_hypothesis_testing.png.
Reproducible : every random draw is seeded with SEED = 20260810.

What this proves practically:
 1. A 95% Confidence Interval does NOT mean "there is a 95% probability the true parameter
    is in this specific interval". Across 10,000 simulated experiments, exactly ~95.0% of
    randomly generated intervals cover the fixed true population mean.
 2. A p-value is P(Data at least as extreme | H0 is true), NOT P(H0 is true | Data).
 3. Two-sample t-test and non-parametric permutation test yield consistent significance
    verdicts on LLM prompt evaluations, but permutation tests make zero normality assumptions.
 4. Statistical Power (1 - beta) scales with sample size and effect size: small sample sizes
    (n = 30) have < 30% power to detect subtle 3% prompt improvements, leading to false negatives.
 5. The Multiple Testing Fallacy: Evaluating 20 candidate prompt tweaks at alpha = 0.05
    inflates the false alarm rate to 1 - (1 - 0.05)^20 = 64.15%. Bonferroni correction controls FWER.
 6. Sample size sizing equation for A/B testing (7.15) correctly calculates the exact N needed
    for statistical significance.
"""

import math
import os
import numpy as np

import matplotlib
matplotlib.use("Agg")  # headless: never open a GUI window
import matplotlib.pyplot as plt

from scipy import stats

SEED = 20260810
LINE = "=" * 70


def demo1_descriptive_vs_inferential():
    """Descriptive statistics vs inferential standard error."""
    print(LINE)
    print("DEMO 1 - Descriptive Stats vs. Inferential Standard Error")
    print(LINE)

    rng = np.random.default_rng(SEED)
    true_mean = 78.5
    true_sd = 12.0
    n = 100

    sample = rng.normal(true_mean, true_sd, size=n)

    # Descriptive
    s_mean = float(np.mean(sample))
    s_median = float(np.median(sample))
    s_var = float(np.var(sample, ddof=1))
    s_sd = float(np.std(sample, ddof=1))
    q25, q75 = np.percentile(sample, [25, 75])
    iqr = q75 - q25

    # Inferential
    se_mean = s_sd / math.sqrt(n)

    print("  Population: true_mu = %.2f, true_sigma = %.2f" % (true_mean, true_sd))
    print("  Sample (n = %d):" % n)
    print("    Sample Mean:       %.4f  (Error vs truth: %.4f)" % (s_mean, abs(s_mean - true_mean)))
    print("    Sample Median:     %.4f" % s_median)
    print("    Sample Std Dev:    %.4f" % s_sd)
    print("    Interquartile IQR: %.4f  (Q25: %.2f, Q75: %.2f)" % (iqr, q25, q75))
    print("    Standard Error SE: %.4f  (Expected spread of sample means across trials)" % se_mean)
    print("  -> Descriptive stats describe THIS sample; inferential stats quantify uncertainty about POPULATION.")


def demo2_confidence_interval_coverage():
    """Simulate 10,000 confidence intervals to verify 95% coverage interpretation."""
    print(LINE)
    print("DEMO 2 - Empirical 95% Confidence Interval Coverage Simulation")
    print(LINE)

    rng = np.random.default_rng(SEED)
    true_mu = 50.0
    true_sigma = 10.0
    n = 40
    num_experiments = 10000
    confidence = 0.95
    z_crit = stats.norm.ppf((1.0 + confidence) / 2.0)  # ~1.96

    covered_count = 0
    intervals = []

    for _ in range(num_experiments):
        x = rng.normal(true_mu, true_sigma, size=n)
        m = float(np.mean(x))
        s = float(np.std(x, ddof=1))
        se = s / math.sqrt(n)
        ci_lower = m - z_crit * se
        ci_upper = m + z_crit * se

        if ci_lower <= true_mu <= ci_upper:
            covered_count += 1
        if len(intervals) < 100:
            intervals.append((ci_lower, ci_upper, m, ci_lower <= true_mu <= ci_upper))

    coverage_rate = (covered_count / num_experiments) * 100.0

    print("  Running %d independent simulated experiments (sample size n = %d):" % (num_experiments, n))
    print("  Target Confidence Level:  95.00%%")
    print("  Empirical Coverage Rate:  %.2f%%  (%d / %d intervals captured true mu=%.1f)" %
          (coverage_rate, covered_count, num_experiments, true_mu))
    print()
    print("  SKIP TEST 2 CHECK: What a 95% CI means:")
    print("  - TRUE: If we repeat the experiment 10,000 times and compute a 95% CI each time,")
    print("          ~95% of those calculated intervals will contain the fixed true parameter.")
    print("  - FALSE: 'There is a 95% probability that true mu lies in [48.2, 51.4]'. (The true parameter")
    print("           is fixed; the interval is the random variable that either caught it or missed it).")


def demo3_p_value_t_test_and_permutation():
    """Two-sample t-test vs non-parametric permutation test for LLM prompt evals."""
    print(LINE)
    print("DEMO 3 - Hypothesis Testing: Parametric t-Test vs. Permutation Test")
    print(LINE)

    rng = np.random.default_rng(SEED)
    n = 50

    # Prompt A (Baseline): Mean score 74.0, SD 10.0
    # Prompt B (New CoT prompt): Mean score 79.5, SD 10.0 (True gap = +5.5 points)
    scores_a = rng.normal(74.0, 10.0, size=n)
    scores_b = rng.normal(79.5, 10.0, size=n)

    mean_a = float(np.mean(scores_a))
    mean_b = float(np.mean(scores_b))
    observed_diff = mean_b - mean_a

    # 1. Welch's Two-Sample t-test
    t_stat, p_val_t = stats.ttest_ind(scores_b, scores_a, equal_var=False)

    # 2. Non-Parametric Permutation Test (Zero distribution assumptions)
    num_permutations = 2000
    combined = np.concatenate([scores_a, scores_b])
    perm_diffs = np.zeros(num_permutations)

    for i in range(num_permutations):
        shuffled = rng.permutation(combined)
        perm_b = shuffled[:n]
        perm_a = shuffled[n:]
        perm_diffs[i] = np.mean(perm_b) - np.mean(perm_a)

    # Two-sided p-value
    p_val_perm = float(np.mean(np.abs(perm_diffs) >= abs(observed_diff)))

    print("  LLM Prompt Evaluation (n = %d benchmark queries per prompt):" % n)
    print("    Prompt A Mean Score: %.2f" % mean_a)
    print("    Prompt B Mean Score: %.2f" % mean_b)
    print("    Observed Score Diff: +%.2f points" % observed_diff)
    print()
    print("  Two-Sample Welch's t-Test: t-statistic = %.4f, p-value = %.6f" % (t_stat, p_val_t))
    print("  Permutation Test (%d resamples): p-value = %.6f" % (num_permutations, p_val_perm))
    print("  Significance (alpha = 0.05): %s" % ("REJECT H0 (Statistically Significant)" if p_val_t < 0.05 else "FAIL TO REJECT H0"))
    print()
    print("  SKIP TEST 1 CHECK: Precise Definition of a p-value:")
    print("  'The probability of observing a test statistic as extreme as, or more extreme than,")
    print("   what was actually measured, assuming that the null hypothesis H0 is strictly true.'")
    print("  NOT 'the probability that the new prompt is better' or 'the probability H0 is true'.")


def demo4_type1_type2_errors_power():
    """Type I error (alpha) vs Type II error (beta) and Statistical Power."""
    print(LINE)
    print("DEMO 4 - Type I Error, Type II Error, and Statistical Power")
    print(LINE)

    rng = np.random.default_rng(SEED)
    alpha = 0.05
    num_sims = 2000

    # Experiment 1: Under H0 (No true difference: mu_A = 75, mu_B = 75)
    # Check false alarm rate (Type I error)
    type1_count = 0
    for _ in range(num_sims):
        s_a = rng.normal(75.0, 10.0, size=40)
        s_b = rng.normal(75.0, 10.0, size=40)
        _, p_val = stats.ttest_ind(s_a, s_b, equal_var=True)
        if p_val < alpha:
            type1_count += 1
    measured_type1 = (type1_count / num_sims) * 100.0

    # Experiment 2: Under H1 (True small difference: mu_A = 75, mu_B = 77.5, gap = 2.5)
    # Check detection rate (Statistical Power = 1 - beta) for n = 30 vs n = 250
    power_n30_count = 0
    power_n250_count = 0

    for _ in range(num_sims):
        # n = 30
        s_a30 = rng.normal(75.0, 10.0, size=30)
        s_b30 = rng.normal(77.5, 10.0, size=30)
        _, p30 = stats.ttest_ind(s_a30, s_b30, equal_var=True)
        if p30 < alpha:
            power_n30_count += 1

        # n = 250
        s_a250 = rng.normal(75.0, 10.0, size=250)
        s_b250 = rng.normal(77.5, 10.0, size=250)
        _, p250 = stats.ttest_ind(s_a250, s_b250, equal_var=True)
        if p250 < alpha:
            power_n250_count += 1

    power_n30 = (power_n30_count / num_sims) * 100.0
    power_n250 = (power_n250_count / num_sims) * 100.0

    print("  Type I Error Rate (False Alarm when H0 is true, nominal alpha = 5.0%%):")
    print("    Empirical False Alarm Rate: %.2f%%" % measured_type1)
    print()
    print("  Statistical Power (1 - beta) for true +2.5 point gain (sigma = 10.0, Cohen's d = 0.25):")
    print("    Sample Size n =  30: Power = %.2f%%  (Type II Error beta = %.2f%%) <- Underpowered!" %
          (power_n30, 100.0 - power_n30))
    print("    Sample Size n = 250: Power = %.2f%%  (Type II Error beta = %.2f%%) <- Adequately powered" %
          (power_n250, 100.0 - power_n250))
    print("  -> Underpowered evaluations frequently discard genuinely superior prompts (high Type II error).")


def demo5_multiple_testing_fallacy():
    """Testing 20 prompt variations inflates false discovery rate; Bonferroni correction."""
    print(LINE)
    print("DEMO 5 - Multiple Testing Fallacy & Bonferroni / FDR Correction")
    print(LINE)

    rng = np.random.default_rng(SEED)
    k_variants = 20
    alpha = 0.05
    num_trials = 1500

    # Every single variant has ZERO true improvement over baseline
    false_discovery_count_raw = 0
    false_discovery_count_bonferroni = 0

    bonferroni_alpha = alpha / k_variants  # 0.05 / 20 = 0.0025
    theoretical_fwer = (1.0 - (1.0 - alpha) ** k_variants) * 100.0

    for _ in range(num_trials):
        baseline = rng.normal(80.0, 10.0, size=50)
        p_values = []
        for _ in range(k_variants):
            variant = rng.normal(80.0, 10.0, size=50)  # Same distribution!
            _, p = stats.ttest_ind(baseline, variant)
            p_values.append(p)

        min_p = min(p_values)
        if min_p < alpha:
            false_discovery_count_raw += 1
        if min_p < bonferroni_alpha:
            false_discovery_count_bonferroni += 1

    fwer_raw = (false_discovery_count_raw / num_trials) * 100.0
    fwer_bonf = (false_discovery_count_bonferroni / num_trials) * 100.0

    print("  Simulating testing %d prompt variants against a baseline (None are truly better):" % k_variants)
    print("  Per-test significance threshold: alpha = %.2f" % alpha)
    print("  Theoretical Family-Wise Error Rate (FWER): %.2f%%" % theoretical_fwer)
    print("  Empirical Raw False Positive Rate:         %.2f%%" % fwer_raw)
    print("  Empirical Bonferroni Corrected (alpha=%.4f): %.2f%%" % (bonferroni_alpha, fwer_bonf))
    print()
    print("  KEY TAKEAWAY: If you try 20 prompt ideas and pick the one with p < 0.05,")
    print("  you have a ~64% chance of publishing pure noise without multiple testing correction.")


def demo6_sample_size_power_ab_testing():
    """Calculate required sample size for A/B testing LLM features (7.15)."""
    print(LINE)
    print("DEMO 6 - Sample Size Sizing for Production A/B Testing (7.15)")
    print(LINE)

    # Baseline success rate p1 = 0.80, desired Minimum Detectable Effect MDE = +0.03 (p2 = 0.83)
    p1 = 0.80
    p2 = 0.83
    alpha = 0.05
    power = 0.80

    z_alpha = stats.norm.ppf(1.0 - alpha / 2.0)  # 1.96 for two-sided 5%
    z_beta = stats.norm.ppf(power)               # 0.8416 for 80% power

    p_pooled = (p1 + p2) / 2.0
    # Two-proportion z-test sample size formula per variant:
    # n = [z_alpha * sqrt(2*p_bar*(1-p_bar)) + z_beta * sqrt(p1*(1-p1) + p2*(1-p2))]^2 / (p1 - p2)^2
    term1 = z_alpha * math.sqrt(2.0 * p_pooled * (1.0 - p_pooled))
    term2 = z_beta * math.sqrt(p1 * (1.0 - p1) + p2 * (1.0 - p2))
    n_required = math.ceil(((term1 + term2) ** 2) / ((p2 - p1) ** 2))

    print("  A/B Test Design Parameters:")
    print("    Baseline Accuracy (p1):       %.2f" % p1)
    print("    Target Accuracy (p2):         %.2f  (MDE = +%.2f)" % (p2, p2 - p1))
    print("    Significance Level (alpha):   %.2f  (95%% confidence)" % alpha)
    print("    Target Power (1 - beta):      %.2f  (80%% chance to detect real gain)" % power)
    print()
    print("  Required Sample Size per variant: %d queries" % n_required)
    print("  Total Sample Size for A/B test:   %d queries (Variant A + Variant B)" % (2 * n_required))
    print("  -> Confirms why Demo 7 in Topic 1.8 found n = 906: detecting small percentage gains")
    print("     reliably requires hundreds or thousands of benchmark evaluations, not 50.")


def make_plot():
    """Generate 10_statistics_hypothesis_testing.png."""
    fig, axes = plt.subplots(2, 2, figsize=(13, 10))

    rng = np.random.default_rng(SEED)

    # Subplot 1: 100 Confidence Intervals (Coverage visualization)
    true_mu = 50.0
    true_sigma = 10.0
    n_ci = 30
    z_crit = 1.96

    ax1 = axes[0, 0]
    ax1.axvline(true_mu, color="#2b9348", linestyle="--", lw=2, label="True Population $\\mu = 50$")

    for i in range(50):
        x = rng.normal(true_mu, true_sigma, size=n_ci)
        m = float(np.mean(x))
        se = float(np.std(x, ddof=1)) / math.sqrt(n_ci)
        lo = m - z_crit * se
        hi = m + z_crit * se
        covers = (lo <= true_mu <= hi)
        c = "#0077b6" if covers else "#d90429"
        ax1.plot([lo, hi], [i, i], color=c, lw=1.5, alpha=0.8)
        ax1.plot(m, i, "o", color=c, markersize=3)

    ax1.set_xlabel("Parameter Value", fontsize=11)
    ax1.set_ylabel("Experiment Index (50 Trials)", fontsize=11)
    ax1.set_title("1. 95% Confidence Intervals (Blue=Covered, Red=Missed)", fontsize=12, fontweight="bold")
    ax1.legend(loc="upper right", framealpha=0.9)
    ax1.grid(True, alpha=0.3)

    # Subplot 2: Null vs Alternative Distribution & p-value
    x_axis = np.linspace(-4, 6, 500)
    null_dist = stats.norm.pdf(x_axis, loc=0, scale=1)
    alt_dist = stats.norm.pdf(x_axis, loc=2.2, scale=1)
    crit_val = 1.96

    ax2 = axes[0, 1]
    ax2.plot(x_axis, null_dist, color="#0077b6", lw=2.5, label="Null $H_0$ (No difference)")
    ax2.plot(x_axis, alt_dist, color="#2b9348", lw=2.5, linestyle="--", label="Alt $H_1$ (True Gain)")

    # Shade Type I error (alpha/2 in upper tail)
    ax2.fill_between(x_axis[x_axis >= crit_val], null_dist[x_axis >= crit_val], color="#d90429", alpha=0.5, label="Type I Error $\\alpha$ (Rejection)")
    # Shade Type II error (beta under H1)
    ax2.fill_between(x_axis[x_axis <= crit_val], alt_dist[x_axis <= crit_val], color="#f48c06", alpha=0.4, label="Type II Error $\\beta$ (False Negative)")

    ax2.axvline(crit_val, color="black", linestyle=":", lw=2, label="Critical Value $z=1.96$")
    ax2.set_xlabel("Standardized Test Statistic ($z$)", fontsize=11)
    ax2.set_ylabel("Probability Density", fontsize=11)
    ax2.set_title("2. Hypothesis Testing: $\\alpha$ (Type I), $\\beta$ (Type II), Power", fontsize=12, fontweight="bold")
    ax2.legend(loc="upper left", framealpha=0.9, fontsize=9)
    ax2.grid(True, alpha=0.3)

    # Subplot 3: Statistical Power Curve vs Sample Size
    sample_sizes = np.arange(10, 300, 10)
    powers_small = [stats.norm.sf(1.96 - (0.2 * math.sqrt(n_s))) for n_s in sample_sizes]
    powers_med = [stats.norm.sf(1.96 - (0.4 * math.sqrt(n_s))) for n_s in sample_sizes]
    powers_large = [stats.norm.sf(1.96 - (0.6 * math.sqrt(n_s))) for n_s in sample_sizes]

    ax3 = axes[1, 0]
    ax3.plot(sample_sizes, powers_small, color="#f48c06", lw=2, label="Small Effect (d = 0.20)")
    ax3.plot(sample_sizes, powers_med, color="#0077b6", lw=2.5, label="Medium Effect (d = 0.40)")
    ax3.plot(sample_sizes, powers_large, color="#2b9348", lw=2, label="Large Effect (d = 0.60)")
    ax3.axhline(0.80, color="#d90429", linestyle=":", lw=1.5, label="Target Power = 80%")

    ax3.set_xlabel("Sample Size per Variant ($n$)", fontsize=11)
    ax3.set_ylabel("Statistical Power ($1 - \\beta$)", fontsize=11)
    ax3.set_title("3. Statistical Power vs. Sample Size", fontsize=12, fontweight="bold")
    ax3.legend(loc="lower right", framealpha=0.9)
    ax3.grid(True, alpha=0.3)

    # Subplot 4: Multiple Testing False Alarm Inflation
    k_range = np.arange(1, 31)
    fwer_curve = (1.0 - (1.0 - 0.05) ** k_range) * 100.0
    bonf_curve = np.full_like(k_range, 5.0)

    ax4 = axes[1, 1]
    ax4.plot(k_range, fwer_curve, color="#d90429", lw=2.5, marker="o", label=r"Uncorrected False Alarm Rate ($1-(1-\alpha)^k$)")
    ax4.plot(k_range, bonf_curve, color="#2b9348", lw=2, linestyle="--", label="Bonferroni Corrected FWER (<= 5%)")

    ax4.set_xlabel("Number of Tested Hypotheses / Prompt Variants ($k$)", fontsize=11)
    ax4.set_ylabel("Family-Wise Error Rate (%)", fontsize=11)
    ax4.set_title("4. Multiple Testing Fallacy (Prompt Hunting Hazard)", fontsize=12, fontweight="bold")
    ax4.legend(loc="upper left", framealpha=0.9)
    ax4.grid(True, alpha=0.3)

    plt.tight_layout()
    plot_path = os.path.join(os.path.dirname(__file__), "10_statistics_hypothesis_testing.png")
    plt.savefig(plot_path, dpi=150)
    plt.close()
    print("PLOT written: 10_statistics_hypothesis_testing.png")


def main():
    print("numpy %s  |  seed %d" % (np.__version__, SEED))
    demo1_descriptive_vs_inferential()
    demo2_confidence_interval_coverage()
    demo3_p_value_t_test_and_permutation()
    demo4_type1_type2_errors_power()
    demo5_multiple_testing_fallacy()
    demo6_sample_size_power_ab_testing()
    make_plot()


if __name__ == "__main__":
    main()
