"""
Regression lineaire simple from scratch.
Reference : Joel Grus, "Data Science From Scratch", chapitre 14.

IMPORTANT : N'importez pas numpy ou scipy pour ces fonctions.
"""

try:
    from analysis.stats import mean, variance, covariance, correlation, standard_deviation
except ModuleNotFoundError:
    from stats import mean, variance, covariance, correlation, standard_deviation


def predict(alpha: float, beta: float, x_i: float) -> float:
    """Predit y pour une valeur x : y = alpha + beta * x."""
    return alpha + beta * x_i


def error(alpha: float, beta: float, x_i: float, y_i: float) -> float:
    """Calcule l'erreur de prediction pour un point."""
    return y_i - predict(alpha, beta, x_i)


def sum_of_sqerrors(alpha: float, beta: float, x: list, y: list) -> float:
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

def total_sum_of_squares(y):
    """the total squared variation of y_i's from their mean"""
    y_mean = mean(y)
    return sum((y_i - y_mean) ** 2 for y_i in y)


def r_squared(alpha: float, beta: float, x: list, y: list) -> float:
    """
    Coefficient de determination R².
    R² = 1 - (SS_res / SS_tot)
    1.0 = ajustement parfait, 0.0 = le modele n'explique rien.
    """
    return 1.0 - (sum_of_sqerrors(alpha, beta, x, y) /
                total_sum_of_squares(y))
