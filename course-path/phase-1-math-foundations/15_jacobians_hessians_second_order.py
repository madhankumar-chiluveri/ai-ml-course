"""1.15 - Jacobians, Hessians, and Second-Order Intuition: measured, not asserted.

Six numbered demonstrations that VERIFY the mathematics of vector Jacobians,
second-order Hessian curvature matrices, quadratic Taylor expansions, Newton-Raphson
optimization, the computational intractability of second-order methods for LLMs (N = 10^9+),
and how modern adaptive optimizers (AdamW in 3.5) approximate diagonal curvature in O(N) time.

Requirements : numpy, scipy, matplotlib (Agg backend only - headless).
Safe/offline : no network, no API keys, no external files read. The single file
               written is 15_jacobians_hessians_second_order.png.
Reproducible : every random draw is seeded with SEED = 20260815.

What this proves practically:
 1. The Jacobian J in R^(m x n) contains first partial derivatives for vector-valued
    functions f: R^n -> R^m (e.g. Softmax Jacobian J_ij = s_i(delta_ij - s_j)), while
    the Hessian H in R^(n x n) contains second partial derivatives for scalar losses.
 2. The quadratic Taylor expansion f(x) ~ f(x0) + grad(x0)^T dx + 0.5 dx^T H dx provides
    a local parabolic model of the loss surface with exact curvature matching.
 3. Newton-Raphson optimization (x_{t+1} = x_t - H^(-1) grad f) converges to the exact
    global minimum in exactly ONE step on quadratic losses, where Gradient Descent zig-zags.
 4. For an N-parameter model, the Hessian requires O(N^2) memory and O(N^3) inversion time.
    For a 7B LLM (N = 7 x 10^9), storing the Hessian takes ~196 Exabytes of VRAM,
    proving mathematically why full second-order methods are impossible at LLM scale.
 5. Adaptive first-order optimizers (Adam, AdamW in 3.5) maintain a running average of
    squared gradients v_t = E[g^2] to cheaply approximate diagonal second-order curvature
    in O(N) memory (megabytes, not exabytes).
 6. The Condition Number kappa = lambda_max / lambda_min dictates the convergence speed
    of first-order gradient descent.
"""

import math
import os
import numpy as np

import matplotlib
matplotlib.use("Agg")  # headless: never open a GUI window
import matplotlib.pyplot as plt

SEED = 20260815
LINE = "=" * 70


def demo1_jacobian_vs_hessian():
    """Verify vector Jacobian matrix vs scalar loss Hessian matrix."""
    print(LINE)
    print("DEMO 1 - Jacobian Matrix (Vector Functions) vs. Hessian Matrix (Scalar Losses)")
    print(LINE)

    # 1. Vector function: Softmax s(z): R^3 -> R^3
    z = np.array([2.0, 1.0, 0.1])
    exp_z = np.exp(z - np.max(z))
    s = exp_z / np.sum(exp_z)

    # Analytical Softmax Jacobian: J_ij = s_i * (delta_ij - s_j) = diag(s) - s @ s^T
    J_analytical = np.diag(s) - np.outer(s, s)

    # Numerical Jacobian via finite differences
    eps = 1e-6
    J_numerical = np.zeros((3, 3))
    for j in range(3):
        z_plus = z.copy()
        z_minus = z.copy()
        z_plus[j] += eps
        z_minus[j] -= eps

        s_plus = np.exp(z_plus - np.max(z_plus)) / np.sum(np.exp(z_plus - np.max(z_plus)))
        s_minus = np.exp(z_minus - np.max(z_minus)) / np.sum(np.exp(z_minus - np.max(z_minus)))
        J_numerical[:, j] = (s_plus - s_minus) / (2.0 * eps)

    diff_J = np.max(np.abs(J_analytical - J_numerical))

    # 2. Scalar loss function: f(x, y) = 3*x^2 + 2*y^2 + 2*x*y
    # Hessian: H = [[6, 2], [2, 4]]
    H = np.array([[6.0, 2.0], [2.0, 4.0]])
    eigenvalues_H = np.linalg.eigvalsh(H)

    print("  1. Jacobian of Softmax s(z) [3 inputs -> 3 outputs, shape (3, 3)]:")
    print("     Softmax Probabilities s: %s" % np.round(s, 4))
    print("     Analytical Jacobian Matrix:\n", np.round(J_analytical, 4))
    print("     Max Difference vs Numerical FD: %.2e" % diff_J)
    print()
    print("  2. Hessian of Loss f(x, y) [2 inputs -> 1 scalar loss, shape (2, 2)]:")
    print("     Hessian Matrix:\n", H)
    print("     Eigenvalues of H: %s (Positive Definite -> Local Bowl)" % np.round(eigenvalues_H, 4))
    print()
    print("  SKIP TEST 1 CHECK: Difference between Jacobian and Hessian:")
    print("  - Jacobian J in R^(m x n) is the matrix of FIRST partial derivatives for a")
    print("    vector-valued function f: R^n -> R^m (J_ij = df_i / dx_j).")
    print("  - Hessian H in R^(n x n) is the symmetric matrix of SECOND partial derivatives")
    print("    for a scalar-valued loss function f: R^n -> R (H_ij = d^2 f / (dx_i dx_j)).")


def demo2_quadratic_taylor_approximation():
    """Verify second-order quadratic Taylor approximation against true non-linear loss."""
    print(LINE)
    print("DEMO 2 - Quadratic Taylor Approximation vs. Linear Tangent Plane")
    print(LINE)

    # True non-linear loss function: f(x) = exp(0.5*x) + 0.5*x^2
    # Evaluation point x0 = 1.0, test delta x = 0.4
    x0 = 1.0
    dx = 0.4
    x_test = x0 + dx

    # True value
    f_true = math.exp(0.5 * x_test) + 0.5 * (x_test ** 2)

    # Derivatives at x0:
    # f'(x) = 0.5*exp(0.5*x) + x
    # f''(x) = 0.25*exp(0.5*x) + 1.0
    f0 = math.exp(0.5 * x0) + 0.5 * (x0 ** 2)
    grad0 = 0.5 * math.exp(0.5 * x0) + x0
    hess0 = 0.25 * math.exp(0.5 * x0) + 1.0

    # 1. First-order Taylor (Linear approximation): f(x0) + f'(x0)*dx
    f_linear = f0 + grad0 * dx
    # 2. Second-order Taylor (Quadratic approximation): f(x0) + f'(x0)*dx + 0.5*f''(x0)*dx^2
    f_quadratic = f0 + grad0 * dx + 0.5 * hess0 * (dx ** 2)

    err_linear = abs(f_true - f_linear)
    err_quadratic = abs(f_true - f_quadratic)

    print("  Evaluating f(x) = exp(0.5*x) + 0.5*x^2 at x0 = %.1f + dx = %.1f (x = %.1f):" % (x0, dx, x_test))
    print("    True Loss f(x):                %.8f" % f_true)
    print("    First-Order Linear Model:       %.8f (Error = %.4f)" % (f_linear, err_linear))
    print("    Second-Order Quadratic Model:   %.8f (Error = %.4f)" % (f_quadratic, err_quadratic))
    print("  -> Second-order model captures surface curvature, reducing Taylor error by %.1fx!" %
          (err_linear / max(1e-9, err_quadratic)))


def demo3_newton_raphson_one_step_convergence():
    """Newton-Raphson 1-step exact convergence on quadratic loss vs GD zig-zagging."""
    print(LINE)
    print("DEMO 3 - Newton's Method (1-Step Solution) vs. Gradient Descent")
    print(LINE)

    # Ill-conditioned quadratic loss: f(x, y) = 0.5 * (x, y) @ H @ (x, y)^T
    # H = [[10.0, 2.0], [2.0, 1.0]] -> kappa = 10.43
    H = np.array([[10.0, 2.0],
                  [2.0, 1.0]])
    x0 = np.array([4.0, -8.0])

    # 1. Newton's Method Update: x_newton = x0 - H^(-1) @ grad(x0)
    # Since loss is pure quadratic, grad(x0) = H @ x0
    grad0 = H @ x0
    H_inv = np.linalg.inv(H)
    x_newton = x0 - H_inv @ grad0

    # 2. Gradient Descent with optimal learning rate (lr = 0.15)
    lr = 0.15
    x_gd = x0.copy()
    gd_steps = 0
    while np.linalg.norm(x_gd) > 1e-4 and gd_steps < 100:
        grad_curr = H @ x_gd
        x_gd -= lr * grad_curr
        gd_steps += 1

    print("  Starting point: x0 = %s (Loss = %.2f)" % (x0, 0.5 * x0 @ H @ x0))
    print("  Newton-Raphson Step 1 Position: %s (Loss = %.2e in EXACTLY 1 STEP!)" %
          (np.round(x_newton, 6), 0.5 * x_newton @ H @ x_newton))
    print("  Gradient Descent Steps to reach < 1e-4: %d steps" % gd_steps)
    print("  -> Newton's method inverts the Hessian to jump straight to the bowl minimum in a single step.")


def demo4_computational_cost_llm_scale():
    """Calculate the exact memory and compute explosion of second-order optimization for LLMs."""
    print(LINE)
    print("DEMO 4 - The Computational Wall: Why Full Second-Order Methods Fail for LLMs")
    print(LINE)

    # Compare 3 model scales:
    # 1. Toy MLP: N = 10^5 parameters
    # 2. ResNet-50: N = 2.5 x 10^7 parameters
    # 3. Llama-3-8B: N = 8 x 10^9 parameters
    models = [
        ("Small MLP", 100_000),
        ("ResNet-50", 25_000_000),
        ("Llama-3-8B", 8_000_000_000),
    ]

    print("  Parameter Count (N) | Gradient Memory (FP32) | Hessian Matrix Memory (FP32) | Inversion FLOPs O(N^3)")
    print("  -------------------|------------------------|------------------------------|-----------------------")

    for name, N in models:
        grad_bytes = N * 4  # 4 bytes per float32
        hess_bytes = (N ** 2) * 4

        # Format memory
        def fmt_bytes(b):
            if b < 1e6:
                return "%.1f KB" % (b / 1e3)
            elif b < 1e9:
                return "%.1f MB" % (b / 1e6)
            elif b < 1e12:
                return "%.1f GB" % (b / 1e9)
            elif b < 1e15:
                return "%.1f TB" % (b / 1e12)
            elif b < 1e18:
                return "%.1f PB" % (b / 1e15)
            else:
                return "%.1f Exabytes" % (b / 1e18)

        flops_inv = (N ** 3)
        print("  %-18s | %22s | %28s | ~10^%d FLOPs" %
              ("%s (%.0e)" % (name, N), fmt_bytes(grad_bytes), fmt_bytes(hess_bytes), math.log10(flops_inv)))

    print()
    print("  SKIP TEST 2 CHECK: Why full second-order optimization is infeasible for LLMs:")
    print("  1. Memory Wall: Storing the Hessian requires O(N^2) memory. For an 8B model,")
    print("     H in R^(8B x 8B) requires ~256 Exabytes of VRAM (more than all GPUs on Earth combined).")
    print("  2. Compute Wall: Inverting the Hessian requires O(N^3) operations (~5 x 10^29 FLOPs).")
    print("  3. Non-Convexity: In deep networks, the Hessian is indefinite; direct inversion H^(-1) grad")
    print("     can step uphill toward saddle points or local maxima!")


def demo5_adam_diagonal_curvature_approximation():
    """How Adam / AdamW approximates diagonal second-order curvature in O(N) space (3.5)."""
    print(LINE)
    print("DEMO 5 - AdamW as an O(N) Diagonal Curvature Approximation (3.5)")
    print(LINE)

    # Diagonal Hessian with anisotropic scales: H = diag([100.0, 1.0])
    # Parameter 1 is steep (H_11 = 100), Parameter 2 is flat (H_22 = 1)
    H_diag = np.array([100.0, 1.0])
    w = np.array([5.0, 5.0])

    # 1. True Newton Step (Diagonal): w_new = w - H^(-1) * grad = w - grad / H_diag
    grad = H_diag * w
    w_newton = w - grad / H_diag

    # 2. AdamW Step: m_t = beta1*m + (1-beta1)*g, v_t = beta2*v + (1-beta2)*g^2
    # Update step: delta_w = - lr * m_t / (sqrt(v_t) + eps)
    # Notice that sqrt(v_t) scales roughly proportional to |g| ~ H_ii * |w_i|,
    # dividing out the steepness of each coordinate independently!
    v_t = grad ** 2
    adam_step = grad / (np.sqrt(v_t) + 1e-8)

    print("  Anisotropic Loss Surface: H_11 = 100.0 (Steep), H_22 = 1.0 (Flat):")
    print("    Raw Gradient Vector:           grad = %s" % grad)
    print("    Newton Exact Step Direction:   -H^(-1) grad = %s" % (-grad / H_diag))
    print("    Adam Normalized Step (O(N)):   -grad / sqrt(v) = %s" % (-adam_step))
    print()
    print("  KEY INSIGHT: AdamW's second moment (v_t) acts as a diagonal Hessian approximation,")
    print("  automatically taking smaller steps in steep directions and larger steps in flat directions,")
    print("  achieving second-order conditioning benefits with pure O(N) memory and compute!")


def demo6_condition_number_and_convergence():
    """Condition number kappa = lambda_max / lambda_min and GD slowdown."""
    print(LINE)
    print("DEMO 6 - Condition Number (kappa) & Gradient Descent Slowdown")
    print(LINE)

    # Compare Well-Conditioned (kappa = 1.0) vs Ill-Conditioned (kappa = 50.0)
    for kappa in [1.0, 10.0, 50.0]:
        H = np.array([[kappa, 0.0], [0.0, 1.0]])
        x = np.array([1.0, 1.0])
        lr = 1.0 / kappa  # Optimal conservative step size

        steps = 0
        while np.linalg.norm(x) > 0.05 and steps < 200:
            grad = H @ x
            x -= lr * grad
            steps += 1

        rate = (kappa - 1.0) / (kappa + 1.0)
        print("  Condition Number kappa = %4.1f (lambda_max=%.1f, lambda_min=1.0):" % (kappa, kappa))
        print("    Theoretical Contraction Rate per Step: (kappa-1)/(kappa+1) = %.4f" % rate)
        print("    Steps to Converge to ||x|| < 0.05:     %d steps" % steps)
        print()


def make_plot():
    """Generate 15_jacobians_hessians_second_order.png."""
    fig, axes = plt.subplots(2, 2, figsize=(13, 10))

    # Subplot 1: Quadratic vs Linear Taylor Approximation
    x_grid = np.linspace(-0.5, 2.5, 200)
    f_true_curve = np.exp(0.5 * x_grid) + 0.5 * (x_grid ** 2)

    x0 = 1.0
    f0 = math.exp(0.5 * x0) + 0.5 * (x0 ** 2)
    g0 = 0.5 * math.exp(0.5 * x0) + x0
    h0 = 0.25 * math.exp(0.5 * x0) + 1.0

    f_lin_curve = f0 + g0 * (x_grid - x0)
    f_quad_curve = f0 + g0 * (x_grid - x0) + 0.5 * h0 * ((x_grid - x0) ** 2)

    ax1 = axes[0, 0]
    ax1.plot(x_grid, f_true_curve, color="black", lw=2.5, label="True Loss $f(x) = e^{0.5x} + 0.5x^2$")
    ax1.plot(x_grid, f_lin_curve, color="#d90429", lw=2, linestyle="--", label="1st-Order Linear (Tangent)")
    ax1.plot(x_grid, f_quad_curve, color="#0077b6", lw=2.2, linestyle="-.", label="2nd-Order Quadratic (Hessian)")
    ax1.plot(x0, f0, "ro", markersize=8, label="Taylor Expansion Point $x_0 = 1.0$")

    ax1.set_xlabel("Parameter $x$", fontsize=11)
    ax1.set_ylabel("Loss Value", fontsize=11)
    ax1.set_title("1. Taylor Approximations: Linear vs. Quadratic", fontsize=12, fontweight="bold")
    ax1.set_ylim(-1, 8)
    ax1.legend(loc="upper left", framealpha=0.9)
    ax1.grid(True, alpha=0.3)

    # Subplot 2: Newton 1-Step vs GD Trajectory
    x_s = np.linspace(-5, 5, 100)
    y_s = np.linspace(-9, 5, 100)
    X_S, Y_S = np.meshgrid(x_s, y_s)
    H_quad = np.array([[10.0, 2.0], [2.0, 1.0]])
    Z_quad = 5.0 * (X_S ** 2) + 2.0 * X_S * Y_S + 0.5 * (Y_S ** 2)

    ax2 = axes[0, 1]
    ax2.contour(X_S, Y_S, Z_quad, levels=20, cmap="viridis")

    # Newton step
    x_init = np.array([4.0, -8.0])
    ax2.plot(x_init[0], x_init[1], "go", markersize=8, label="Start $(4.0, -8.0)$")
    ax2.plot([x_init[0], 0], [x_init[1], 0], color="#0077b6", lw=2.5, marker="s", label="Newton 1-Step Jump")

    # GD path
    pos = x_init.copy()
    gd_p = [pos.copy()]
    for _ in range(12):
        pos -= 0.15 * (H_quad @ pos)
        gd_p.append(pos.copy())
    gd_p = np.array(gd_p)
    ax2.plot(gd_p[:, 0], gd_p[:, 1], "r--o", lw=1.5, markersize=3, label="Gradient Descent (Zig-Zag)")

    ax2.plot(0, 0, "k*", markersize=12, label="Optimum $(0, 0)$")
    ax2.set_xlabel("Dimension $x$", fontsize=11)
    ax2.set_ylabel("Dimension $y$", fontsize=11)
    ax2.set_title("2. Optimization: Newton 1-Step vs. GD Zig-Zag", fontsize=12, fontweight="bold")
    ax2.legend(loc="lower left", framealpha=0.9, fontsize=9)

    # Subplot 3: Memory Scaling Curve (O(N) vs O(N^2))
    params_n = np.logspace(3, 9, 7)  # 1K to 1B
    mem_grad = params_n * 4 / 1e9    # GB
    mem_hess = (params_n ** 2) * 4 / 1e9  # GB

    ax3 = axes[1, 0]
    ax3.plot(params_n, mem_grad, color="#2b9348", lw=2.5, marker="o", label=r"1st-Order Gradient Memory $\mathcal{O}(N)$")
    ax3.plot(params_n, mem_hess, color="#d90429", lw=2.5, marker="s", label=r"2nd-Order Hessian Memory $\mathcal{O}(N^2)$")
    ax3.axhline(80, color="gray", linestyle=":", lw=1.5, label="Single GPU VRAM Limit (80 GB)")

    ax3.set_xscale("log")
    ax3.set_yscale("log")
    ax3.set_xlabel("Parameter Count $N$", fontsize=11)
    ax3.set_ylabel("Memory Required (GB, Log Scale)", fontsize=11)
    ax3.set_title(r"3. The Memory Wall: Gradient $\mathcal{O}(N)$ vs. Hessian $\mathcal{O}(N^2)$", fontsize=12, fontweight="bold")
    ax3.legend(loc="upper left", framealpha=0.9)
    ax3.grid(True, alpha=0.3)

    # Subplot 4: Softmax Jacobian Heatmap
    z_soft = np.array([2.5, 1.2, 0.4, -0.8])
    exp_s = np.exp(z_soft - np.max(z_soft))
    s_probs = exp_s / np.sum(exp_s)
    J_soft = np.diag(s_probs) - np.outer(s_probs, s_probs)

    ax4 = axes[1, 1]
    im = ax4.imshow(J_soft, cmap="coolwarm", aspect="auto")
    fig.colorbar(im, ax=ax4, label="Jacobian Derivative $\\partial s_i / \\partial z_j$")
    for i in range(4):
        for j in range(4):
            ax4.text(j, i, "%.3f" % J_soft[i, j], ha="center", va="center",
                     color="white" if abs(J_soft[i, j]) > 0.08 else "black", fontsize=9, fontweight="bold")

    ax4.set_xticks(range(4))
    ax4.set_yticks(range(4))
    ax4.set_xticklabels(["$z_0$", "$z_1$", "$z_2$", "$z_3$"])
    ax4.set_yticklabels(["$s_0$", "$s_1$", "$s_2$", "$s_3$"])
    ax4.set_title("4. Softmax Vector Jacobian Matrix $J_{ij}$", fontsize=12, fontweight="bold")

    plt.tight_layout()
    plot_path = os.path.join(os.path.dirname(__file__), "15_jacobians_hessians_second_order.png")
    plt.savefig(plot_path, dpi=150)
    plt.close()
    print("PLOT written: 15_jacobians_hessians_second_order.png")


def main():
    print("numpy %s  |  seed %d" % (np.__version__, SEED))
    demo1_jacobian_vs_hessian()
    demo2_quadratic_taylor_approximation()
    demo3_newton_raphson_one_step_convergence()
    demo4_computational_cost_llm_scale()
    demo5_adam_diagonal_curvature_approximation()
    demo6_condition_number_and_convergence()
    make_plot()


if __name__ == "__main__":
    main()
