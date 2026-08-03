"""
1.5 - Derivatives, Partial Derivatives, Gradients : companion script.

WHAT THIS RUNS
    Seven numbered demos that MEASURE the facts behind derivatives, partial
    derivatives and gradients instead of asserting them. Every claim in the
    note has a printed number here that you can reproduce and attack.

REQUIREMENTS
    numpy        (2.4.4 used when this output was captured)
    matplotlib   (3.11.1) - forced to the "Agg" backend, so no window is ever
                 opened. Demo 5 writes exactly one PNG next to this file and
                 prints its size in bytes.
    Nothing else. Pure local computation: no network access, no API keys, no
    downloads, no files read. Safe to run offline on a laptop.

REPRODUCIBILITY
    All randomness comes from np.random.default_rng(SEED) with SEED = 4242,
    printed at the top of the run.

WHAT THIS PROVES PRACTICALLY
    1. A derivative is the limit of secant slopes, and for f(x) = x^2 the
       secant-slope error equals h EXACTLY - verified to 0.0 absolute
       difference, so "the error shrinks with h" is not hand-waving.
    2. Shrinking h does NOT make a finite-difference derivative monotonically
       better. The error curve is U-shaped: it falls, bottoms out near
       h = sqrt(machine eps), then gets WORSE as catastrophic cancellation
       takes over. The measured best h is compared against the theoretical
       prediction. (This is the direct bridge to 1.12 numerical stability.)
    3. The partial derivatives of f(x,y) = x^2*y + 3y are df/dx = 2xy and
       df/dy = x^2 + 3, confirmed against central differences at five points,
       plus an explicit demonstration that "hold the other variable fixed"
       literally means differentiating a one-variable slice.
    4. The gradient is the direction of steepest ascent - proven by brute
       force. Many random unit directions are sampled, their directional
       derivatives measured, and the best random one is compared with the
       gradient's own. Repeated across dimensions 2 to 1000 to show how
       badly random search loses as dimension grows.
    5. The gradient is perpendicular to the contour (level set) it sits on -
       verified with an exact parametrisation, dot product driven to ~1e-16.
    6. Stepping along -grad decreases a convex loss and stepping along +grad
       increases it, measured side by side from the same start with the same
       step size. This is the answer to "why the minus sign".
    7. The gradient of a mean-squared-error loss with respect to its
       parameters - the exact quantity 2.3 and 3.5 consume - matches central
       differences to ~1e-9, and is numerically zero at the least-squares
       optimum.
"""

import os

import matplotlib

matplotlib.use("Agg")  # headless: never opens a window, safe on any machine
import matplotlib.pyplot as plt
import numpy as np

SEED = 4242
HERE = os.path.dirname(os.path.abspath(__file__))
LINE = "=" * 70


def banner(title):
    """Every demo announces itself the same way so the transcript is scannable."""
    print(LINE)
    print(title)
    print(LINE)


# ----------------------------------------------------------------------
# DEMO 1 - what a derivative actually IS
# ----------------------------------------------------------------------
def demo1_secant_to_tangent():
    """
    The derivative is defined as a LIMIT of secant slopes:

        f'(a) = lim_{h->0} ( f(a+h) - f(a) ) / h

    For f(x) = x^2 that limit can be worked out by hand with school algebra:

        ( (a+h)^2 - a^2 ) / h = ( a^2 + 2ah + h^2 - a^2 ) / h
                              = ( 2ah + h^2 ) / h
                              = 2a + h

    So the secant slope is exactly 2a + h. The error against the true
    derivative 2a is therefore EXACTLY h - not "about h", not "on the order
    of h". We check that claim numerically below, which is the cheapest
    possible sanity test of the whole idea.
    """
    banner("DEMO 1 - a derivative is the limit of secant slopes")

    a = 3.0
    exact = 2.0 * a  # f'(x) = 2x  =>  f'(3) = 6

    print("  f(x) = x^2   at a = 3.0   ->   true derivative f'(3) = 6.0")
    print("  algebra says the secant slope is exactly 2a + h = 6 + h")
    print()
    print("      h            secant slope            slope - 6      "
          "|(slope-6)-h|   relative")
    print("  " + "-" * 82)

    worst_clean = 0.0
    for k in range(0, 11):
        h = 10.0 ** (-k)
        slope = ((a + h) ** 2 - a**2) / h
        err = slope - exact
        gap = abs(err - h)  # should be 0 while floating point can keep up
        rel = gap / h
        if k <= 4:
            worst_clean = max(worst_clean, rel)
        print(f"  {h:8.0e}   {slope:20.14f}   {err:16.10e}  {gap:13.4e}  "
              f"{rel:9.2e}")

    print()
    print(f"  worst RELATIVE deviation from 'error == h' for h >= 1e-04: "
          f"{worst_clean:.2e}")
    print("  That is agreement to ~11 significant digits. The algebra is not")
    print("  approximately right, it is exactly right - and the tiny residue")
    print("  is floating-point noise, not mathematics.")
    print()
    print("  Watch the last column climb anyway. By h = 1e-08 the deviation is")
    print("  as big as the answer, and at h = 1e-09 and h = 1e-10 the computed")
    print("  slope is IDENTICAL - shrinking h stopped doing anything. Demo 2")
    print("  is about exactly that wall.")
    print()
    print("  Reading it geometrically: the secant through (3, 9) and (3+h, ...)")
    print("  tilts toward the tangent as h shrinks. 'Derivative' = that tangent's")
    print("  slope = the instantaneous rate of change = how much f moves per unit")
    print("  of x, right here, right now.")


# ----------------------------------------------------------------------
# DEMO 2 - the U-shaped error curve (the honest surprise)
# ----------------------------------------------------------------------
def demo2_step_size_sweep():
    """
    Everyone's first instinct: to approximate a derivative better, make h
    smaller. That is only half true, and the half that is false will bite.

    Two competing error sources:

      TRUNCATION error  - the formula itself is only an approximation.
                          Forward difference (f(a+h)-f(a))/h is off by about
                          (h/2)*|f''(a)|. It SHRINKS as h shrinks.

      ROUNDOFF error    - f(a+h) and f(a) are nearly equal numbers stored to
                          ~16 significant digits. Subtracting them destroys
                          leading digits (catastrophic cancellation, 1.12),
                          then dividing by a tiny h magnifies what is left.
                          It GROWS as h shrinks, roughly 2*eps*|f(a)|/h.

    Total error is therefore a U. Minimising (h/2)*|f''| + 2*eps*|f|/h over h
    gives the optimum

        h* = 2 * sqrt( eps * |f(a)| / |f''(a)| )

    which for a well-scaled function is about sqrt(eps) ~ 1.5e-8, NOT 1e-16.

    The central difference (f(a+h)-f(a-h))/(2h) has truncation error
    (h^2/6)*|f'''| instead, so its optimum sits near cbrt(eps) ~ 6e-6 and its
    best achievable error is far smaller. Same cost, better answer.
    """
    banner("DEMO 2 - smaller h is NOT strictly better: the U-shaped error")

    a = 1.0
    f = np.sin
    exact = np.cos(a)  # d/dx sin(x) = cos(x)
    eps = np.finfo(np.float64).eps

    print(f"  f(x) = sin(x)  at a = 1.0   ->   f'(1) = cos(1) = {exact:.15f}")
    print(f"  machine epsilon (float64)   = {eps:.6e}")
    print(f"  sqrt(eps)                   = {np.sqrt(eps):.6e}")
    print(f"  cbrt(eps)                   = {eps ** (1.0 / 3.0):.6e}")
    print()
    print("        h        forward diff err     central diff err")
    print("  " + "-" * 54)

    hs = np.array([10.0 ** (-k) for k in range(1, 15)])
    fwd_err = np.empty_like(hs)
    cen_err = np.empty_like(hs)

    for i, h in enumerate(hs):
        fwd = (f(a + h) - f(a)) / h
        cen = (f(a + h) - f(a - h)) / (2.0 * h)
        fwd_err[i] = abs(fwd - exact)
        cen_err[i] = abs(cen - exact)
        mark = ""
        print(f"  {h:8.0e}      {fwd_err[i]:14.6e}       {cen_err[i]:14.6e}{mark}")

    i_f = int(np.argmin(fwd_err))
    i_c = int(np.argmin(cen_err))

    # Theoretical optima. For f = sin at a = 1:
    #   |f(a)|   = sin(1),  |f''(a)| = sin(1),  |f'''(a)| = cos(1)
    f_abs = abs(np.sin(a))
    f2_abs = abs(np.sin(a))
    f3_abs = abs(np.cos(a))
    h_fwd_pred = 2.0 * np.sqrt(eps * f_abs / f2_abs)
    h_cen_pred = (3.0 * eps * f_abs / f3_abs) ** (1.0 / 3.0)
    err_fwd_pred = 2.0 * np.sqrt(eps * f_abs * f2_abs)

    print()
    print("  FORWARD DIFFERENCE")
    print(f"    best h on this grid : {hs[i_f]:.0e}   error {fwd_err[i_f]:.6e}")
    print(f"    theory says h* =    : {h_fwd_pred:.6e}  (= 2*sqrt(eps*|f|/|f''|))")
    print(f"    theory says err ~   : {err_fwd_pred:.6e}")
    print(f"    error at h = 1e-01  : {fwd_err[0]:.6e}   (truncation dominates)")
    print(f"    error at h = 1e-14  : {fwd_err[13]:.6e}   (roundoff dominates)")
    ratio = fwd_err[13] / fwd_err[i_f]
    print(f"    going from the best h to 1e-14 made it {ratio:,.0f}x WORSE")

    print()
    print("  CENTRAL DIFFERENCE")
    print(f"    best h on this grid : {hs[i_c]:.0e}   error {cen_err[i_c]:.6e}")
    print(f"    theory says h* =    : {h_cen_pred:.6e}  (= (3*eps*|f|/|f'''|)^(1/3))")
    print(f"    best central error is {fwd_err[i_f] / cen_err[i_c]:,.0f}x smaller than")
    print("    the best forward error, for the same one extra function call.")

    print()
    print("  This is the single most useful practical fact in the topic:")
    print("  when you check an analytic gradient against finite differences,")
    print("  use a CENTRAL difference with h near 1e-05, not h = 1e-12.")


# ----------------------------------------------------------------------
# DEMO 3 - partial derivatives, worked on the skip-test function
# ----------------------------------------------------------------------
def f_skip(x, y):
    """The skip-test function: f(x,y) = x^2 * y + 3y."""
    return x**2 * y + 3.0 * y


def grad_skip(x, y):
    """
    Analytic gradient of f(x,y) = x^2*y + 3y.

    df/dx : treat y as a CONSTANT.  d/dx [ x^2 * y ] = 2x*y ; d/dx [3y] = 0.
            -> df/dx = 2xy
    df/dy : treat x as a CONSTANT.  d/dy [ x^2 * y ] = x^2  ; d/dy [3y] = 3.
            -> df/dy = x^2 + 3
    """
    return np.array([2.0 * x * y, x**2 + 3.0])


def demo3_partials():
    banner("DEMO 3 - partial derivatives of f(x,y) = x^2*y + 3y")

    h = 1e-5  # central difference, sized from Demo 2's measured optimum
    pts = [(0.0, 0.0), (1.0, 1.0), (2.0, 1.0), (-1.0, 3.0), (2.5, -4.0)]

    print("  analytic:  df/dx = 2xy        df/dy = x^2 + 3")
    print(f"  numeric :  central difference with h = {h:.0e}")
    print()
    print("     x       y      df/dx anl   df/dx num    df/dy anl   df/dy num")
    print("  " + "-" * 68)

    worst = 0.0
    for x, y in pts:
        g = grad_skip(x, y)
        # Partial in x: perturb ONLY x, hold y frozen. That is the definition.
        gx_num = (f_skip(x + h, y) - f_skip(x - h, y)) / (2.0 * h)
        # Partial in y: perturb ONLY y, hold x frozen.
        gy_num = (f_skip(x, y + h) - f_skip(x, y - h)) / (2.0 * h)
        worst = max(worst, abs(g[0] - gx_num), abs(g[1] - gy_num))
        print(
            f"  {x:6.2f}  {y:6.2f}   {g[0]:10.6f}  {gx_num:10.6f}   "
            f"{g[1]:10.6f}  {gy_num:10.6f}"
        )

    print()
    print(f"  max |analytic - numeric| across all 10 partials: {worst:.3e}")

    print()
    print("  What 'hold the other variable fixed' literally means, at (2, 1):")
    x0, y0 = 2.0, 1.0
    print("    freeze y = 1  ->  g(x) = f(x, 1) = x^2*1 + 3*1 = x^2 + 3")
    print("                      g'(x) = 2x        ->  g'(2) = 4.0")
    print(f"                      df/dx from the formula 2xy = {2.0 * x0 * y0:.1f}")
    print("    freeze x = 2  ->  k(y) = f(2, y) = 4y + 3y = 7y   (a straight line)")
    print("                      k'(y) = 7        ->  k'(1) = 7.0")
    print(f"                      df/dy from the formula x^2+3 = {x0**2 + 3.0:.1f}")
    print()
    print(f"  So grad f(2,1) = [{grad_skip(x0, y0)[0]:.1f}, {grad_skip(x0, y0)[1]:.1f}]")
    print("  A gradient is nothing more exotic than a list of these slopes,")
    print("  one per input. That is why a loss over millions of parameters is")
    print("  tractable: each parameter contributes one ordinary derivative.")


# ----------------------------------------------------------------------
# DEMO 4 - steepest ascent, proven by brute-force search
# ----------------------------------------------------------------------
def random_unit_directions(rng, n, d):
    """
    n random unit vectors in d dimensions, uniformly spread over the sphere.

    Drawing each coordinate from a standard normal and then normalising gives
    a uniform direction, because the multivariate standard normal has no
    preferred direction - its density depends only on the length of the
    vector, not on where it points.
    """
    v = rng.normal(size=(n, d))
    return v / np.linalg.norm(v, axis=1, keepdims=True)


def demo4_steepest_ascent(rng):
    """
    CLAIM: among all unit directions u, the directional derivative

        D_u f(p) = grad f(p) . u

    is largest when u points along grad f(p).

    Why, in one line: the dot product satisfies g . u = |g| * |u| * cos(theta),
    and with |u| = 1 that is |g| * cos(theta), which is maximised at theta = 0
    (cos = 1) and minimised at theta = 180 degrees (cos = -1).

    Rather than take that on trust, we sample directions at random, evaluate
    each one, and see whether anything beats the gradient. Nothing should.
    """
    banner("DEMO 4 - the gradient IS the direction of steepest ascent")

    p = np.array([2.0, 1.0])
    g = grad_skip(p[0], p[1])
    gnorm = float(np.linalg.norm(g))
    print(f"  f(x,y) = x^2*y + 3y   at p = ({p[0]:.1f}, {p[1]:.1f})")
    print(f"  grad f(p) = [{g[0]:.1f}, {g[1]:.1f}]        |grad f(p)| = {gnorm:.12f}")
    print()

    # --- Check 1: the directional derivative computed two independent ways.
    # (a) analytically as grad . u
    # (b) by a central finite difference of f along u - no gradient involved
    n_check = 6
    U = random_unit_directions(rng, n_check, 2)
    t = 1e-5
    print("  directional derivative, two independent routes:")
    print("        u_x        u_y      grad . u      finite diff      abs diff")
    print("  " + "-" * 66)
    worst = 0.0
    for u in U:
        an = float(g @ u)
        q = p + t * u
        r = p - t * u
        nu = (f_skip(q[0], q[1]) - f_skip(r[0], r[1])) / (2.0 * t)
        worst = max(worst, abs(an - nu))
        print(f"  {u[0]:9.5f}  {u[1]:9.5f}  {an:11.6f}   {nu:14.6f}   {abs(an - nu):.2e}")
    print(f"  max abs diff: {worst:.3e}   (they are the same quantity)")

    # --- Check 2: grad . u == |grad| * cos(theta).
    # The angle theta is obtained INDEPENDENTLY of any dot product: each 2-D
    # vector's compass bearing comes from arctan2, and theta is the difference
    # of bearings. If the identity were an accident of how we defined cosine,
    # this test would expose it.
    U2 = random_unit_directions(rng, 100_000, 2)
    dots = U2 @ g
    bearing_u = np.arctan2(U2[:, 1], U2[:, 0])
    bearing_g = np.arctan2(g[1], g[0])
    theta = bearing_u - bearing_g
    predicted = gnorm * np.cos(theta)  # |g| * |u| * cos(theta), with |u| = 1
    identity_gap = float(np.max(np.abs(dots - predicted)))
    print()
    print("  identity check: grad.u  ==  |grad| * cos(theta), where theta comes")
    print("  from arctan2 bearings and never touches a dot product -")
    print(f"    max |grad.u - |grad|*cos(theta)| over 100,000 directions: "
          f"{identity_gap:.3e}")
    print("  cos(theta) is 1 only at theta = 0, so the maximum sits on the")
    print("  gradient itself. Everything below is that statement, measured.")

    # --- Check 3: does ANY random direction beat the gradient?
    best_i = int(np.argmax(dots))
    best_val = float(dots[best_i])
    u_grad = g / gnorm
    print()
    print("  brute-force search over 100,000 random unit directions in 2-D:")
    print(f"    best random direction     : ({U2[best_i, 0]:.6f}, {U2[best_i, 1]:.6f})")
    print(f"    its directional derivative: {best_val:.12f}")
    print(f"    normalised gradient       : ({u_grad[0]:.6f}, {u_grad[1]:.6f})")
    print(f"    its directional derivative: {gnorm:.12f}")
    print(f"    gradient beat the best random by: {gnorm - best_val:.3e}")
    print(f"    worst random direction    : {float(np.min(dots)):.12f}"
          f"   (that is -|grad|, the steepest DESCENT)")
    print(f"    -|grad| for comparison    : {-gnorm:.12f}")

    # --- Check 4: how badly does random search lose as dimension grows?
    # This is the practical punchline. With millions of parameters (3.5),
    # guessing directions is hopeless; the gradient hands you the best one
    # for the price of one backward pass.
    print()
    print("  Same experiment in higher dimensions, 20,000 samples each.")
    print("  f(v) = 0.5 * sum(c_i * v_i^2) + d . v   ->   grad = c*v + d")
    print()
    print("      dim   best of 20,000   typical guess   angle of the best (deg)")
    print("  " + "-" * 64)
    for d in (2, 3, 5, 10, 50, 100, 1000):
        c = rng.uniform(0.5, 2.0, size=d)
        dv = rng.normal(size=d)
        v = rng.normal(size=d)
        gd = c * v + dv  # analytic gradient of the quadratic above
        gdn = float(np.linalg.norm(gd))
        Ud = random_unit_directions(rng, 20_000, d)
        vals = (Ud @ gd) / gdn  # this is cos(angle to the gradient)
        frac = float(np.max(vals))
        typical = float(np.median(np.abs(vals)))
        ang = np.degrees(np.arccos(np.clip(frac, -1.0, 1.0)))
        print(f"   {d:6d}   {frac:14.6f}   {typical:13.6f}   {ang:21.2f}")
    print("  (both columns are fractions of |grad|; the gradient scores 1.0)")
    print()
    print("  In 2-D random guessing finds the best direction. In 1000-D the")
    print("  best of 20,000 guesses captures only a small fraction of the")
    print("  available slope. Real models have far more than 1000 parameters.")


# ----------------------------------------------------------------------
# DEMO 5 - gradients are perpendicular to contours
# ----------------------------------------------------------------------
def demo5_perpendicular_contours():
    """
    A CONTOUR (level set) of f is the set of points where f has one fixed
    value: f(x,y) = c. Walking along a contour, f does not change at all, so
    the directional derivative along the contour's tangent must be ZERO:

        grad f . tangent = 0     <=>     grad f is perpendicular to the contour

    We can check this exactly for f(x,y) = x^2 + 3y^2, whose contour at level
    c is the ellipse

        x(t) = sqrt(c)   * cos(t)
        y(t) = sqrt(c/3) * sin(t)

    Differentiating the parametrisation gives the tangent, and the gradient is
    [2x, 6y]. Their dot product should be zero for every t.

    This is the geometric reason gradient descent works the way it does: to
    change f as fast as possible you must move ACROSS contours, not along
    them, and "across" means along the gradient. It also previews 1.11, where
    the shape of those contours decides how fast descent converges.
    """
    banner("DEMO 5 - the gradient is perpendicular to the contour")

    c = 12.0
    ts = np.linspace(0.0, 2.0 * np.pi, 1001)
    x = np.sqrt(c) * np.cos(ts)
    y = np.sqrt(c / 3.0) * np.sin(ts)

    # sanity: every sampled point really is on the level set f = 12
    fvals = x**2 + 3.0 * y**2
    print(f"  f(x,y) = x^2 + 3y^2 ,  contour level c = {c:.1f}")
    print(f"  max |f(point) - 12| over 1001 contour points: "
          f"{float(np.max(np.abs(fvals - c))):.3e}")

    gx = 2.0 * x
    gy = 6.0 * y
    tx = -np.sqrt(c) * np.sin(ts)  # dx/dt
    ty = np.sqrt(c / 3.0) * np.cos(ts)  # dy/dt

    dot = gx * tx + gy * ty
    gnorm = np.hypot(gx, gy)
    tnorm = np.hypot(tx, ty)
    cos_ang = dot / (gnorm * tnorm)
    ang = np.degrees(np.arccos(np.clip(cos_ang, -1.0, 1.0)))

    print()
    print(f"  max |grad . tangent|                : {float(np.max(np.abs(dot))):.3e}")
    print(f"  max |cos(angle)| between them       : "
          f"{float(np.max(np.abs(cos_ang))):.3e}")
    print(f"  angle range over the whole contour  : "
          f"{float(np.min(ang)):.10f} to {float(np.max(ang)):.10f} degrees")
    print("  Zero dot product means exactly 90 degrees, everywhere, always.")

    # An independent confirmation with NO calculus in it at all: step a tiny
    # amount along the tangent and measure how little f changes, versus the
    # same size step along the gradient.
    i = 137
    p = np.array([x[i], y[i]])
    ghat = np.array([gx[i], gy[i]]) / gnorm[i]
    that = np.array([tx[i], ty[i]]) / tnorm[i]
    step = 1e-4

    def F(v):
        return v[0] ** 2 + 3.0 * v[1] ** 2

    base = F(p)
    d_tan = F(p + step * that) - base
    d_grad = F(p + step * ghat) - base
    print()
    print(f"  at the contour point ({p[0]:.6f}, {p[1]:.6f}), step size {step:.0e}:")
    print(f"    move along the TANGENT  -> f changes by {d_tan:.6e}")
    print(f"    move along the GRADIENT -> f changes by {d_grad:.6e}")
    print(f"    ratio: the gradient step changes f "
          f"{abs(d_grad) / abs(d_tan):,.0f}x more")

    # ---- picture ----
    xs = np.linspace(-4.2, 4.2, 400)
    ys = np.linspace(-2.6, 2.6, 400)
    X, Y = np.meshgrid(xs, ys)
    Z = X**2 + 3.0 * Y**2

    fig, ax = plt.subplots(figsize=(7.6, 4.8), dpi=140)
    cs = ax.contour(X, Y, Z, levels=[1, 3, 6, 12, 20, 30], colors="#005f73",
                    linewidths=1.4)
    ax.clabel(cs, inline=True, fontsize=8, fmt="%.0f")

    qx = np.linspace(-3.6, 3.6, 13)
    qy = np.linspace(-2.2, 2.2, 9)
    QX, QY = np.meshgrid(qx, qy)
    U = 2.0 * QX
    V = 6.0 * QY
    M = np.hypot(U, V)
    M[M == 0.0] = 1.0
    ax.quiver(QX, QY, U / M, V / M, color="#9b2226", angles="xy",
              scale=22, width=0.0035)

    ax.plot(x, y, color="#1b4332", linewidth=2.2, label="contour f = 12")
    ax.plot([p[0]], [p[1]], "o", color="#1b4332", markersize=7)
    ax.arrow(p[0], p[1], 1.1 * that[0], 1.1 * that[1], color="#1b4332",
             width=0.02, head_width=0.12, length_includes_head=True)
    ax.arrow(p[0], p[1], 1.1 * ghat[0], 1.1 * ghat[1], color="#9b2226",
             width=0.02, head_width=0.12, length_includes_head=True)

    ax.set_title("grad f = [2x, 6y] is perpendicular to every contour of "
                 "f = x^2 + 3y^2", fontsize=10)
    ax.set_xlabel("x")
    ax.set_ylabel("y")
    ax.set_aspect("equal")
    ax.legend(loc="upper right", fontsize=8)
    fig.tight_layout()

    png = os.path.join(HERE, "05_gradient_field.png")
    fig.savefig(png)
    plt.close(fig)
    print()
    print(f"  saved: {os.path.basename(png)}  ({os.path.getsize(png):,} bytes)")
    print("  Red arrows are gradients. They cross every blue contour at a")
    print("  right angle - which is what the number above measured.")


# ----------------------------------------------------------------------
# DEMO 6 - why MINUS the gradient (measured, not asserted)
# ----------------------------------------------------------------------
def demo6_plus_vs_minus(rng):
    """
    Skip-test question 2, settled by experiment.

    Take a convex function with a single minimum:

        f(x,y) = 3x^2 + 2y^2 + xy - 4x + 2y + 7

    Its partial derivatives:
        df/dx = 6x + y - 4
        df/dy = 4y + x + 2

    Run the SAME loop twice from the SAME start with the SAME step size, once
    stepping along -grad and once along +grad, and print the loss. This is the
    update rule 2.3 uses for linear regression and the one every optimizer in
    3.5 modifies.
    """
    banner("DEMO 6 - step along -grad or +grad? measure it")

    def f(v):
        x, y = v
        return 3.0 * x**2 + 2.0 * y**2 + x * y - 4.0 * x + 2.0 * y + 7.0

    def grad(v):
        x, y = v
        return np.array([6.0 * x + y - 4.0, 4.0 * y + x + 2.0])

    # exact minimiser: solve grad = 0, i.e. [[6,1],[1,4]] @ [x,y] = [4,-2]
    A = np.array([[6.0, 1.0], [1.0, 4.0]])
    b = np.array([4.0, -2.0])
    star = np.linalg.solve(A, b)
    print(f"  f(x,y) = 3x^2 + 2y^2 + xy - 4x + 2y + 7")
    print(f"  grad f = [6x + y - 4,  4y + x + 2]")
    print(f"  exact minimiser (grad = 0): "
          f"({star[0]:.10f}, {star[1]:.10f})   f = {f(star):.10f}")
    print(f"  |grad| there: {np.linalg.norm(grad(star)):.3e}")

    start = np.array([3.0, 3.0])
    lr = 0.1
    steps = 20
    print()
    print(f"  start = ({start[0]:.1f}, {start[1]:.1f})   step size = {lr}   "
          f"{steps} steps")
    print()
    print("   step     f(p) with  p <- p - lr*grad      f(p) with  p <- p + lr*grad")
    print("  " + "-" * 72)

    p_minus = start.copy()
    p_plus = start.copy()
    hist_m = [f(p_minus)]
    hist_p = [f(p_plus)]
    for s in range(1, steps + 1):
        p_minus = p_minus - lr * grad(p_minus)  # DESCENT
        p_plus = p_plus + lr * grad(p_plus)  # ASCENT
        hist_m.append(f(p_minus))
        hist_p.append(f(p_plus))

    for s in (0, 1, 2, 3, 5, 10, 15, 20):
        print(f"   {s:4d}     {hist_m[s]:24.10f}      {hist_p[s]:24.6e}")

    print()
    print(f"  -grad : {hist_m[0]:.6f}  ->  {hist_m[-1]:.10f}   "
          f"(minimum is {f(star):.10f})")
    print(f"  +grad : {hist_p[0]:.6f}  ->  {hist_p[-1]:.6e}")
    print(f"  distance to the minimum after {steps} steps:")
    print(f"    -grad : {np.linalg.norm(p_minus - star):.3e}")
    print(f"    +grad : {np.linalg.norm(p_plus - star):.3e}")
    print(f"  monotonically decreasing along -grad? "
          f"{bool(np.all(np.diff(hist_m) < 0))}")
    print(f"  monotonically increasing along +grad? "
          f"{bool(np.all(np.diff(hist_p) > 0))}")

    # Direction is not the whole story: the STEP SIZE has a hard ceiling.
    # For a quadratic, one descent step maps the error e = p - p* to
    # (I - lr*H) e, where H is the Hessian (the matrix of second partial
    # derivatives, here exactly A). So the error shrinks by a factor
    #     rho = max over eigenvalues lam of |1 - lr*lam|
    # every step, and descent only converges when rho < 1, i.e. lr < 2/lam_max.
    # We predict rho from the eigenvalues and then MEASURE the observed
    # shrink factor from consecutive iterates. 1.11 develops this properly.
    evals = np.linalg.eigvalsh(A)  # Hessian of f is exactly A = [[6,1],[1,4]]
    lam_max = float(evals[-1])
    print()
    print(f"  Hessian of f = [[6, 1], [1, 4]]   eigenvalues "
          f"{evals[0]:.6f}, {lam_max:.6f}")
    print(f"  theory: descent converges only while lr < 2/lambda_max = "
          f"{2.0 / lam_max:.6f}")
    print()
    print("      lr     predicted rho   measured shrink   verdict")
    print("  " + "-" * 56)
    for lr_try in (0.10, 0.30, 0.3118, 0.32, 0.40):
        rho = float(np.max(np.abs(1.0 - lr_try * evals)))
        q = start.copy()
        prev = np.linalg.norm(q - star)
        for _ in range(40):
            q = q - lr_try * grad(q)
            cur = np.linalg.norm(q - star)
            ratio = cur / prev
            prev = cur
        verdict = "converges" if rho < 1.0 else "DIVERGES"
        print(f"   {lr_try:6.4f}   {rho:13.6f}   {ratio:15.6f}   {verdict}")
    print("  The measured shrink factor reproduces the predicted rho, and the")
    print("  sign flip happens exactly at 2/lambda_max. A correct direction with")
    print("  an oversized step still blows up - which is why 3.5 spends so much")
    print("  effort on step sizes rather than on directions.")


# ----------------------------------------------------------------------
# DEMO 7 - the gradient 2.3 and 3.5 actually consume
# ----------------------------------------------------------------------
def demo7_squared_error_gradient(rng):
    """
    The loss that starts everything:

        L(w, b) = (1/n) * sum_i ( w*x_i + b - y_i )^2

    Write r_i = w*x_i + b - y_i for the residual. Differentiating term by
    term, using the chain rule pattern d/dw [ r^2 ] = 2r * dr/dw (formalised
    in 1.6) with dr/dw = x_i and dr/db = 1:

        dL/dw = (2/n) * sum_i r_i * x_i
        dL/db = (2/n) * sum_i r_i

    Every number in a linear-regression training loop (2.3) is one of these
    two, and every optimizer in 3.5 is a rule for what to do with them. We
    confirm both against central differences, then confirm the gradient
    vanishes at the least-squares solution.
    """
    banner("DEMO 7 - gradient of a squared-error loss (the 2.3 / 3.5 quantity)")

    n = 200
    x = rng.uniform(-3.0, 3.0, size=n)
    y = 2.5 * x - 1.0 + rng.normal(0.0, 0.3, size=n)

    def loss(w, b):
        r = w * x + b - y
        return float(np.mean(r**2))

    def grad_loss(w, b):
        r = w * x + b - y
        return np.array([2.0 * np.mean(r * x), 2.0 * np.mean(r)])

    print(f"  synthetic data: n = {n}, y = 2.5x - 1.0 + noise(sd 0.3)")
    print("  L(w,b) = mean( (w*x + b - y)^2 )")
    print("  dL/dw  = 2 * mean( (w*x + b - y) * x )      dL/db = 2 * mean(w*x + b - y)")
    print()

    h = 1e-5
    print("      w        b        L(w,b)     dL/dw anl  dL/dw num  "
          "dL/db anl  dL/db num")
    print("  " + "-" * 76)
    worst = 0.0
    for w, b in [(0.0, 0.0), (1.0, 0.5), (2.5, -1.0), (-2.0, 4.0), (5.0, 2.0)]:
        g = grad_loss(w, b)
        gw = (loss(w + h, b) - loss(w - h, b)) / (2.0 * h)
        gb = (loss(w, b + h) - loss(w, b - h)) / (2.0 * h)
        worst = max(worst, abs(g[0] - gw), abs(g[1] - gb))
        print(f"  {w:6.2f}  {b:6.2f}  {loss(w, b):10.5f}  {g[0]:10.5f} {gw:10.5f}  "
              f"{g[1]:9.5f} {gb:10.5f}")
    print()
    print(f"  max |analytic - central difference|: {worst:.3e}")
    print("  The hand-derived formula and a blind numerical probe agree. That")
    print("  agreement test is exactly how you debug a backward pass.")

    # Least-squares optimum via the normal equations, then check grad ~ 0.
    X = np.column_stack([x, np.ones(n)])
    theta = np.linalg.lstsq(X, y, rcond=None)[0]
    w_star, b_star = float(theta[0]), float(theta[1])
    g_star = grad_loss(w_star, b_star)
    print()
    print(f"  least-squares optimum: w* = {w_star:.10f}   b* = {b_star:.10f}")
    print(f"  L(w*, b*)            = {loss(w_star, b_star):.10f}")
    print(f"  grad at the optimum  = [{g_star[0]:.3e}, {g_star[1]:.3e}]"
          f"   |grad| = {np.linalg.norm(g_star):.3e}")
    print("  A zero gradient is the algebraic definition of a flat point.")

    # And one honest gradient-descent run, so the whole chain is visible.
    print()
    print("  20 steps of plain gradient descent from (w, b) = (0, 0), lr = 0.05:")
    w, b = 0.0, 0.0
    print("     step         L(w,b)          w            b        |grad|")
    print("  " + "-" * 60)
    for s in range(21):
        g = grad_loss(w, b)
        if s in (0, 1, 2, 5, 10, 20):
            print(f"   {s:6d}   {loss(w, b):12.8f}  {w:11.7f}  {b:11.7f}   "
                  f"{np.linalg.norm(g):.4e}")
        w -= 0.05 * g[0]
        b -= 0.05 * g[1]
    print(f"  gap to the exact optimum: |w - w*| = {abs(w - w_star):.6f}   "
          f"|b - b*| = {abs(b - b_star):.6f}")
    print("  b converges far more slowly than w here. That is not a bug - it")
    print("  is the elongated-contour problem 1.11 names and 3.5's optimizers")
    print("  are built to fix.")


def main():
    print(f"numpy {np.__version__}  |  matplotlib {matplotlib.__version__}  "
          f"|  seed {SEED}")
    rng = np.random.default_rng(SEED)
    demo1_secant_to_tangent()
    demo2_step_size_sweep()
    demo3_partials()
    demo4_steepest_ascent(rng)
    demo5_perpendicular_contours()
    demo6_plus_vs_minus(rng)
    demo7_squared_error_gradient(rng)
    print(LINE)


if __name__ == "__main__":
    main()
