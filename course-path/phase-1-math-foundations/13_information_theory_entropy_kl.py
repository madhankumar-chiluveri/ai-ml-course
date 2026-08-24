"""1.13 - Information Theory: Entropy, KL Divergence, Perplexity: measured, not asserted.

Six numbered demonstrations that VERIFY the core theorems of information theory,
Shannon entropy bounds, Gibbs' inequality, asymmetric KL divergence (Forward vs. Reverse KL),
LLM perplexity calculations, temperature scaling dynamics, and Decision Tree information gain.

Requirements : numpy, scipy, matplotlib (Agg backend only - headless).
Safe/offline : no network, no API keys, no external files read. The single file
               written is 13_information_theory_entropy_kl.png.
Reproducible : every random draw is seeded with SEED = 20260813.

What this proves practically:
 1. Shannon Entropy H(P) measures average surprisal: uniform distribution maximizes entropy
    at log2(K) bits, while a deterministic distribution has exactly 0 bits of entropy.
 2. Cross-Entropy splits cleanly into H(P, Q) = H(P) + D_KL(P || Q). By Gibbs' inequality,
    D_KL >= 0 always, so H(P, Q) >= H(P) with equality if and only if Q = P.
 3. KL Divergence is strictly ASYMMETRIC: D_KL(P || Q) != D_KL(Q || P). Forward KL is
    zero-avoiding (mode-covering), while Reverse KL is zero-forcing (mode-seeking in VAEs/DPO).
 4. Language Model Perplexity (PPL) is exactly the exponentiated Cross-Entropy loss:
    PPL = exp(NLL) = exp(H(P, Q)). A uniform random guess over vocabulary V has PPL = V.
 5. Temperature scaling T during LLM generation (4.6) smoothly interpolates entropy from
    0 (greedy argmax, T -> 0) to ln(V) (pure noise, T -> inf).
 6. Information Gain in Decision Trees (2.9) is Shannon mutual information I(X; Y) = H(Y) - H(Y|X).
"""

import math
import os
import numpy as np

import matplotlib
matplotlib.use("Agg")  # headless: never open a GUI window
import matplotlib.pyplot as plt

SEED = 20260813
LINE = "=" * 70


def demo1_entropy_and_surprisal():
    """Self-information, Shannon Entropy, and maximum entropy bounds."""
    print(LINE)
    print("DEMO 1 - Shannon Entropy & Maximum Entropy Bounds")
    print(LINE)

    # 4-state discrete systems
    # 1. Deterministic: [1, 0, 0, 0]
    p_det = np.array([1.0, 0.0, 0.0, 0.0])
    # 2. Skewed: [0.7, 0.15, 0.1, 0.05]
    p_skew = np.array([0.70, 0.15, 0.10, 0.05])
    # 3. Uniform: [0.25, 0.25, 0.25, 0.25]
    p_unif = np.array([0.25, 0.25, 0.25, 0.25])

    def calc_entropy(p):
        p_safe = p[p > 0]
        return -np.sum(p_safe * np.log2(p_safe))

    h_det = max(0.0, calc_entropy(p_det))
    h_skew = calc_entropy(p_skew)
    h_unif = calc_entropy(p_unif)
    h_max = math.log2(4.0)

    print("  4-Outcome Discrete Distributions (Base-2 bits):")
    print("    Deterministic [1.0, 0, 0, 0]:        H(P) = %.4f bits  (Zero uncertainty)" % h_det)
    print("    Skewed [0.70, 0.15, 0.10, 0.05]:     H(P) = %.4f bits" % h_skew)
    print("    Uniform [0.25, 0.25, 0.25, 0.25]:    H(P) = %.4f bits  (Max possible = log2(4) = %.4f)" % (h_unif, h_max))
    print()
    print("  -> Entropy measures average information/unpredictability.")
    print("  -> Maximum entropy theorem: on a discrete space of size K, H(P) <= log2(K).")


def demo2_cross_entropy_kl_decomposition():
    """Decomposition: H(P, Q) = H(P) + D_KL(P || Q) and Gibbs' Inequality."""
    print(LINE)
    print("DEMO 2 - Cross-Entropy Decomposition & Gibbs' Inequality")
    print(LINE)

    # True distribution P
    P = np.array([0.40, 0.35, 0.15, 0.10])
    # Imperfect model distribution Q
    Q = np.array([0.25, 0.25, 0.25, 0.25])

    eps = 1e-15
    # Entropy H(P) (nats)
    H_P = -np.sum(P * np.log(P + eps))
    # Cross-Entropy H(P, Q) (nats)
    H_PQ = -np.sum(P * np.log(Q + eps))
    # KL Divergence D_KL(P || Q)
    KL_PQ = np.sum(P * np.log((P + eps) / (Q + eps)))

    diff = abs(H_PQ - (H_P + KL_PQ))

    print("  True Distribution P:  %s" % P)
    print("  Model Distribution Q: %s" % Q)
    print()
    print("  Entropy of Truth H(P):                 %.8f nats" % H_P)
    print("  KL Divergence D_KL(P || Q):            %.8f nats" % KL_PQ)
    print("  Sum H(P) + D_KL(P || Q):               %.8f nats" % (H_P + KL_PQ))
    print("  Cross-Entropy Loss H(P, Q):            %.8f nats" % H_PQ)
    print("  Decomposition Difference:              %.3e" % diff)
    print()
    print("  Gibbs' Inequality Check: D_KL(P || Q) >= 0 is %.8f >= 0 -> H(P, Q) >= H(P)." % KL_PQ)
    print("  -> Optimizing Cross-Entropy Loss H(P, Q) is mathematically identical to minimizing KL Divergence!")


def demo3_asymmetric_kl_divergence():
    """Forward KL vs Reverse KL (Mode-Covering vs Mode-Seeking in RLHF/DPO)."""
    print(LINE)
    print("DEMO 3 - Asymmetry of KL Divergence: Forward vs. Reverse KL")
    print(LINE)

    # Two discrete distributions
    P = np.array([0.90, 0.09, 0.01])
    Q = np.array([0.33, 0.33, 0.34])

    eps = 1e-15
    kl_forward = float(np.sum(P * np.log((P + eps) / (Q + eps))))  # D_KL(P || Q)
    kl_reverse = float(np.sum(Q * np.log((Q + eps) / (P + eps))))  # D_KL(Q || P)

    print("  Distribution P: %s" % P)
    print("  Distribution Q: %s" % Q)
    print("    Forward KL  D_KL(P || Q) = sum P * ln(P / Q) = %.6f nats" % kl_forward)
    print("    Reverse KL  D_KL(Q || P) = sum Q * ln(Q / P) = %.6f nats" % kl_reverse)
    print("    Ratio D_KL(Q || P) / D_KL(P || Q) = %.2f" % (kl_reverse / kl_forward))
    print()
    print("  SKIP TEST 1 CHECK: Why KL Divergence is NOT Symmetric:")
    print("  D_KL(P || Q) = sum P(x) ln[ P(x) / Q(x) ] != sum Q(x) ln[ Q(x) / P(x) ] = D_KL(Q || P)")
    print("  - Forward KL D_KL(P || Q) is 'Zero-Avoiding' (Mode-Covering): if P(x) > 0, Q(x) CANNOT be 0,")
    print("    forcing Q to spread out and cover all modes of P (Standard Supervised MLE).")
    print("  - Reverse KL D_KL(Q || P) is 'Zero-Forcing' (Mode-Seeking): if P(x) == 0, Q(x) MUST be 0,")
    print("    forcing Q to lock tightly onto a single high-probability mode (Used in VAEs, RLHF, and DPO in 4.11).")


def demo4_llm_cross_entropy_and_perplexity():
    """Relationship between Cross-Entropy Loss and Perplexity."""
    print(LINE)
    print("DEMO 4 - LLM Next-Token Cross-Entropy & Perplexity (PPL)")
    print(LINE)

    V = 32000  # Typical Llama/Mistral vocab size

    # Case 1: Perfect model predicting true token with probability 1.0
    loss_perfect = max(0.0, -math.log(1.0))
    ppl_perfect = math.exp(loss_perfect)

    # Case 2: Good language model (e.g. Llama-3-70B on benchmark text, Loss = 1.60 nats)
    loss_good = 1.6094379  # ln(5.0)
    ppl_good = math.exp(loss_good)

    # Case 3: Untrained Uniform Random Guessing (Loss = ln(V))
    loss_random = math.log(V)
    ppl_random = math.exp(loss_random)

    print("  LLM Vocabulary Size V = %d tokens:" % V)
    print("    Case 1 (Perfect Predictor):  Loss = %.4f nats -> Perplexity PPL = %.4f" % (loss_perfect, ppl_perfect))
    print("    Case 2 (Good Model):         Loss = %.4f nats -> Perplexity PPL = %.4f" % (loss_good, ppl_good))
    print("    Case 3 (Random Model):       Loss = %.4f nats -> Perplexity PPL = %.4f (= Vocab Size V)" %
          (loss_random, ppl_random))
    print()
    print("  SKIP TEST 2 CHECK: Relationship between Cross-Entropy Loss and Perplexity:")
    print("  Perplexity is the exponentiation of the Cross-Entropy loss:")
    print("    PPL = exp( Cross-Entropy Loss ) = exp( - (1/N) sum ln P(token_t | context) )")
    print("  Intuition: A model with PPL = 5.0 is, on average, as confused as choosing uniformly")
    print("  among 5 equally likely candidate words at each step.")


def demo5_temperature_scaling_entropy():
    """Effect of temperature scaling on softmax distribution entropy (Phase 4.6)."""
    print(LINE)
    print("DEMO 5 - Temperature Scaling & Softmax Output Entropy (4.6)")
    print(LINE)

    logits = np.array([3.5, 1.2, 0.8, -0.5, -1.0])
    temperatures = [0.2, 0.7, 1.0, 2.0, 10.0]

    print("  Raw Model Logits: %s" % logits)
    print()
    print("   Temperature T | Softmax Distribution                     | Entropy H(Q) (nats)")
    print("  ---------------|------------------------------------------|--------------------")

    for T in temperatures:
        scaled_logits = logits / T
        shift_z = scaled_logits - np.max(scaled_logits)
        probs = np.exp(shift_z) / np.sum(np.exp(shift_z))
        eps = 1e-15
        ent = -np.sum(probs * np.log(probs + eps))
        prob_str = "[" + ", ".join(["%.3f" % p for p in probs]) + "]"
        print("  %14.1f | %-40s | %18.4f" % (T, prob_str, ent))

    print()
    print("  -> Low Temperature (T -> 0): Distribution collapses to one-hot greedy argmax (Entropy -> 0).")
    print("  -> High Temperature (T -> inf): Distribution flattens to uniform noise (Entropy -> ln(K) = %.4f)." % math.log(len(logits)))


def demo6_decision_tree_information_gain():
    """Information Gain in Decision Tree Splits (2.9) using Shannon Entropy."""
    print(LINE)
    print("DEMO 6 - Information Gain & Mutual Information in Decision Trees (2.9)")
    print(LINE)

    # Parent Node: 14 instances (9 Yes [1], 5 No [0])
    # Target: PlayTennis?
    p_parent = np.array([9.0 / 14.0, 5.0 / 14.0])
    H_parent = -np.sum(p_parent * np.log2(p_parent))

    # Feature Split: 'Wind' (Weak: 8 instances [6 Yes, 2 No], Strong: 6 instances [3 Yes, 3 No])
    p_weak = np.array([6.0 / 8.0, 2.0 / 8.0])
    p_strong = np.array([3.0 / 6.0, 3.0 / 6.0])

    H_weak = -np.sum(p_weak * np.log2(p_weak))
    H_strong = -np.sum(p_strong * np.log2(p_strong))

    # Conditional Entropy H(Parent | Wind)
    H_cond = (8.0 / 14.0) * H_weak + (6.0 / 14.0) * H_strong

    # Information Gain: IG = H(Parent) - H(Parent | Wind)
    IG = H_parent - H_cond

    print("  Parent Node Entropy H(Y):                 %.4f bits" % H_parent)
    print("  Child Left (Weak Wind, n=8) Entropy:      %.4f bits" % H_weak)
    print("  Child Right (Strong Wind, n=6) Entropy:    %.4f bits" % H_strong)
    print("  Weighted Conditional Entropy H(Y | Wind):  %.4f bits" % H_cond)
    print("  Information Gain IG(Y, Wind):             %.4f bits" % IG)
    print("  -> Decision trees (2.9) pick the feature split that maximizes Information Gain (Shannon Mutual Information).")


def make_plot():
    """Generate 13_information_theory_entropy_kl.png."""
    fig, axes = plt.subplots(2, 2, figsize=(13, 10))

    # Subplot 1: Bernoulli Shannon Entropy vs p
    p_vals = np.linspace(0.001, 0.999, 300)
    ent_vals = - (p_vals * np.log2(p_vals) + (1.0 - p_vals) * np.log2(1.0 - p_vals))

    ax1 = axes[0, 0]
    ax1.plot(p_vals, ent_vals, color="#0077b6", lw=2.5)
    ax1.plot(0.5, 1.0, "ro", markersize=8, label="Max Entropy at $p=0.50$ (1.0 bit)")
    ax1.set_xlabel("Bernoulli Parameter $p = P(X = 1)$", fontsize=11)
    ax1.set_ylabel("Shannon Entropy $H(p)$ (Bits)", fontsize=11)
    ax1.set_title("1. Shannon Entropy of Binary Source ($H_{max} = 1.0$ bit)", fontsize=12, fontweight="bold")
    ax1.legend(loc="lower center", framealpha=0.9)
    ax1.grid(True, alpha=0.3)

    # Subplot 2: Forward vs Reverse KL (Bimodal Truth P vs Unimodal Fit Q)
    x_axis = np.linspace(-6, 6, 400)
    # Bimodal P: 0.5*N(-2, 0.6^2) + 0.5*N(2, 0.6^2)
    p_true_pdf = 0.5 * (1.0 / (0.6 * math.sqrt(2 * math.pi))) * np.exp(-0.5 * ((x_axis + 2) / 0.6) ** 2) + \
                 0.5 * (1.0 / (0.6 * math.sqrt(2 * math.pi))) * np.exp(-0.5 * ((x_axis - 2) / 0.6) ** 2)

    # Forward KL (Mode Covering): Q_fwd = N(0, 2.1^2)
    q_fwd_pdf = (1.0 / (2.1 * math.sqrt(2 * math.pi))) * np.exp(-0.5 * (x_axis / 2.1) ** 2)
    # Reverse KL (Mode Seeking): Q_rev = N(-2, 0.6^2)
    q_rev_pdf = (1.0 / (0.6 * math.sqrt(2 * math.pi))) * np.exp(-0.5 * ((x_axis + 2) / 0.6) ** 2)

    ax2 = axes[0, 1]
    ax2.plot(x_axis, p_true_pdf, color="black", lw=2.5, label="Bimodal Truth $P(x)$")
    ax2.plot(x_axis, q_fwd_pdf, color="#0077b6", lw=2.2, linestyle="--", label="Forward KL $D_{KL}(P||Q)$ (Mode-Covering)")
    ax2.plot(x_axis, q_rev_pdf, color="#d90429", lw=2.2, linestyle="-.", label="Reverse KL $D_{KL}(Q||P)$ (Mode-Seeking / DPO)")

    ax2.set_xlabel("Feature Coordinate $x$", fontsize=11)
    ax2.set_ylabel("Probability Density", fontsize=11)
    ax2.set_title("2. Asymmetry: Forward vs. Reverse KL", fontsize=12, fontweight="bold")
    ax2.legend(loc="upper right", framealpha=0.9, fontsize=9)
    ax2.grid(True, alpha=0.3)

    # Subplot 3: Cross-Entropy Loss vs Perplexity
    ce_loss_range = np.linspace(0.0, 5.0, 300)
    ppl_range = np.exp(ce_loss_range)

    ax3 = axes[1, 0]
    ax3.plot(ce_loss_range, ppl_range, color="#2b9348", lw=2.5)
    ax3.plot(1.609, 5.0, "ro", markersize=7, label="Loss = 1.61 $\\to$ PPL = 5.0 tokens")
    ax3.plot(3.0, math.exp(3.0), "bo", markersize=7, label="Loss = 3.00 $\\to$ PPL = 20.08 tokens")

    ax3.set_xlabel("Cross-Entropy Loss $-\\frac{1}{N} \\sum \\ln P(w_t)$ (nats)", fontsize=11)
    ax3.set_ylabel("Perplexity $\\text{PPL} = e^{\\text{Loss}}$", fontsize=11)
    ax3.set_title("3. Cross-Entropy Loss vs. Language Model Perplexity", fontsize=12, fontweight="bold")
    ax3.legend(loc="upper left", framealpha=0.9)
    ax3.grid(True, alpha=0.3)

    # Subplot 4: Softmax Temperature Scaling on Logits
    logits = np.array([3.5, 1.2, 0.8, -0.5, -1.0])
    vocab_labels = ["Token 1", "Token 2", "Token 3", "Token 4", "Token 5"]
    temps = [0.3, 1.0, 3.0]
    colors = ["#d90429", "#0077b6", "#2b9348"]

    ax4 = axes[1, 1]
    x_pos = np.arange(len(logits))
    width = 0.25

    for idx, (T, c) in enumerate(zip(temps, colors)):
        scaled_z = logits / T
        p = np.exp(scaled_z - np.max(scaled_z)) / np.sum(np.exp(scaled_z - np.max(scaled_z)))
        ax4.bar(x_pos + idx * width, p, width=width, color=c, label="T = %.1f" % T, edgecolor="black")

    ax4.set_xticks(x_pos + width)
    ax4.set_xticklabels(vocab_labels, fontsize=10)
    ax4.set_ylabel("Softmax Probability", fontsize=11)
    ax4.set_title("4. Temperature Scaling: Greedy (T=0.3) vs. Uniform (T=3.0)", fontsize=12, fontweight="bold")
    ax4.legend(loc="upper right", framealpha=0.9)
    ax4.grid(True, axis="y", alpha=0.3)

    plt.tight_layout()
    plot_path = os.path.join(os.path.dirname(__file__), "13_information_theory_entropy_kl.png")
    plt.savefig(plot_path, dpi=150)
    plt.close()
    print("PLOT written: 13_information_theory_entropy_kl.png")


def main():
    print("numpy %s  |  seed %d" % (np.__version__, SEED))
    demo1_entropy_and_surprisal()
    demo2_cross_entropy_kl_decomposition()
    demo3_asymmetric_kl_divergence()
    demo4_llm_cross_entropy_and_perplexity()
    demo5_temperature_scaling_entropy()
    demo6_decision_tree_information_gain()
    make_plot()


if __name__ == "__main__":
    main()
