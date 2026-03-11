"""
Regression lineaire simple from scratch.
Reference : Joel Grus, "Data Science From Scratch", chapitre 14.

IMPORTANT : N'importez pas numpy ou scipy pour ces fonctions.
"""

import random
from pathlib import Path
from collections.abc import Callable, Iterator, Sequence
from typing import TypeVar
import pandas as pd

try:
    from analysis.stats import mean, variance, covariance, correlation, standard_deviation
except ModuleNotFoundError:
    from stats import mean, variance, covariance, correlation, standard_deviation


T = TypeVar("T")


def predict(alpha: float, beta: float, x_i: float) -> float:
    """Predit y pour une valeur x : y = alpha + beta * x."""
    return alpha + beta * x_i


def error(alpha: float, beta: float, x_i: float, y_i: float) -> float:
    """Calcule l'erreur de prediction pour un point."""
    return y_i - predict(alpha, beta, x_i)


def sum_of_sqerrors(alpha: float, beta: float, x: Sequence[float], y: Sequence[float]) -> float:
    """Somme des erreurs au carre sur tous les points."""
    return sum(error(alpha, beta, x_i, y_i) ** 2 for x_i, y_i in zip(x, y))



def least_squares_fit(x: list[float], y: list[float]) -> tuple[float, float]:
    """
    Trouve alpha et beta qui minimisent la somme des erreurs au carre.
    Retourne (alpha, beta) tels que y ≈ alpha + beta * x.
    """
    beta = correlation(x, y) * standard_deviation(y) / standard_deviation(x)
    alpha = mean(y) - beta * mean(x)
    return alpha, beta

def total_sum_of_squares(y: Sequence[float]) -> float:
    """the total squared variation of y_i's from their mean"""
    y_mean = mean(y)
    return sum((y_i - y_mean) ** 2 for y_i in y)


def r_squared(alpha: float, beta: float, x: Sequence[float], y: Sequence[float]) -> float:
    """
    Coefficient de determination R².
    R² = 1 - (SS_res / SS_tot)
    1.0 = ajustement parfait, 0.0 = le modele n'explique rien.
    """
    return 1.0 - (sum_of_sqerrors(alpha, beta, x, y) /
                total_sum_of_squares(y))

def squared_error(x_i: float, y_i: float, theta: Sequence[float]) -> float:
    alpha, beta = theta
    return error(alpha, beta, x_i, y_i) ** 2


def squared_error_gradient(x_i: float, y_i: float, theta: Sequence[float]) -> list[float]:
    alpha, beta = theta
    return [-2 * error(alpha, beta, x_i, y_i), # alpha partial derivative
    -2 * error(alpha, beta, x_i, y_i) * x_i] # beta partial derivative


def in_random_order(data: Sequence[T]) -> Iterator[T]:
    """generator that returns the elements of data in random order"""
    indexes = [i for i, _ in enumerate(data)]
    random.shuffle(indexes)
    for i in indexes:
        yield data[i]


def vector_subtract(v: Sequence[float], w: Sequence[float]) -> list[float]:
    """subtracts corresponding elements"""
    return [v_i - w_i
    for v_i, w_i in zip(v, w)]

def scalar_multiply(c: float, v: Sequence[float]) -> list[float]:
    """c is a number, v is a vector"""
    return [c * v_i for v_i in v]


def minimize_stochastic(
    target_fn: Callable[[float, float, Sequence[float]], float],
    gradient_fn: Callable[[float, float, Sequence[float]], list[float]],
    x: Sequence[float],
    y: Sequence[float],
    theta_0: Sequence[float],
    alpha_0: float = 0.01,
) -> list[float]:
    data: list[tuple[float, float]] = list(zip(x, y))
    theta = list(theta_0) # initial guess
    alpha = alpha_0 # initial step size
    min_theta: list[float] | None = None
    min_value = float("inf") # the minimum so far
    iterations_with_no_improvement = 0
    # if we ever go 100 iterations with no improvement, stop
    while iterations_with_no_improvement < 100:
        value = sum( target_fn(x_i, y_i, theta) for x_i, y_i in data )
        if value < min_value:
            # if we've found a new minimum, remember it
            # and go back to the original step size
            min_theta, min_value = theta, value
            iterations_with_no_improvement = 0
            alpha = alpha_0
        else:
            # otherwise we're not improving, so try shrinking the step size
            iterations_with_no_improvement += 1
            alpha *= 0.9
            # and take a gradient step for each of the data points
        for x_i, y_i in in_random_order(data):
            gradient_i = gradient_fn(x_i, y_i, theta)
            theta = vector_subtract(theta, scalar_multiply(alpha, gradient_i))
    return min_theta if min_theta is not None else theta


def fit_linear_regression_sgd(
    x: Sequence[float],
    y: Sequence[float],
    alpha_0: float = 0.01,
    seed: int = 0,
) -> tuple[float, float]:
    """
    Fit y = alpha + beta * x with SGD using standardized x.

    Standardizing x avoids unstable steps when x has large values,
    then coefficients are converted back to the original x scale.
    """
    if len(x) != len(y):
        raise ValueError("x and y must have the same length")
    if len(x) < 2:
        raise ValueError("Need at least 2 points to fit regression")

    x_mean = mean(x)
    x_std = standard_deviation(x)
    if x_std == 0:
        raise ValueError("x has zero variance, slope is undefined")

    x_scaled = [(x_i - x_mean) / x_std for x_i in x]

    random.seed(seed)
    theta_0 = [random.random(), random.random()]
    alpha_scaled, beta_scaled = minimize_stochastic(
        squared_error,
        squared_error_gradient,
        x_scaled,
        y,
        theta_0,
        alpha_0,
    )

    beta = beta_scaled / x_std
    alpha = alpha_scaled - beta * x_mean
    return alpha, beta



project_root = Path(__file__).resolve().parents[1]


def main() -> None:
    df = pd.read_csv(project_root / "data" / "dvf_toulon.csv")

    prix_vente_list = df["prix_vente"].tolist()
    surface_m2_list = df["surface_m2"].tolist()

    alpha_closed, beta_closed = least_squares_fit(surface_m2_list, prix_vente_list)
    alpha_sgd, beta_sgd = fit_linear_regression_sgd(surface_m2_list, prix_vente_list, alpha_0=0.01, seed=0)

    print(f"Closed-form   -> alpha = {alpha_closed:.4f}, beta = {beta_closed:.4f}")
    print(f"SGD (scaled)  -> alpha = {alpha_sgd:.4f}, beta = {beta_sgd:.4f}")
    print(f"R2 (closed-form) = {r_squared(alpha_closed, beta_closed, surface_m2_list, prix_vente_list):.4f}")
    print(f"R2 (SGD)         = {r_squared(alpha_sgd, beta_sgd, surface_m2_list, prix_vente_list):.4f}")
    print(f"Prediction 113m2 (closed-form): {predict(alpha_closed, beta_closed, 113):.2f}")
    print(f"Prediction 113m2 (SGD):         {predict(alpha_sgd, beta_sgd, 113):.2f}")


if __name__ == "__main__":
    main()