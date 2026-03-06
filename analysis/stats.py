"""
Fonctions statistiques from scratch.
Reference : Joel Grus, "Data Science From Scratch", chapitre 5.

IMPORTANT : N'importez pas numpy, pandas ou statistics pour ces fonctions.
Implementez-les avec du Python pur (listes, boucles, math).
"""

import math


def mean(xs: list[float]) -> float:
    """Retourne la moyenne d'une liste de nombres."""
    return sum(xs) / len(xs)
    raise NotImplementedError("Implementez mean() - voir Grus ch.5")

def de_mean(xs: list[float]) -> list[float]:
    """translate x by subtracting its mean (so the result has mean 0)"""
    x_bar = mean(xs)
    return [x_i - x_bar for x_i in xs]


def median(xs: list[float]) -> float:
    """Retourne la mediane d'une liste de nombres."""
    xs_sorted = sorted(xs)
    n=len(xs_sorted)
    mid = n//2
    if n%2==1:
        return xs_sorted[mid]
    else:
        return (xs_sorted[mid-1]+xs_sorted[mid])/2
    raise NotImplementedError("Implementez median() - voir Grus ch.5")

def sum_of_squares(xs: list[float]) -> float:
    """Retourne la somme des carrés d'une liste de nombres."""
    return sum(x**2 for x in xs)
    raise NotImplementedError("Implementez sum_of_squares() - voir Grus ch.5")

def variance(xs: list[float]) -> float:
    """Retourne la variance d'une liste de nombres."""
    n=len(xs)
    deviation=de_mean(xs)
    return sum_of_squares(deviation) / (n - 1)
    raise NotImplementedError("Implementez variance() - voir Grus ch.5")


def standard_deviation(xs: list[float]) -> float:
    """Retourne l'ecart-type d'une liste de nombres."""
    return math.sqrt(variance(xs))
    raise NotImplementedError("Implementez standard_deviation() - voir Grus ch.5")


def covariance(xs: list[float], ys: list[float]) -> float:
    """Retourne la covariance entre deux series."""
    assert len(xs) == len(ys) #les listes doivent avoir la meme longueur
    n=len(xs)
    return sum(x*y for x,y in zip(de_mean(xs), de_mean(ys))) / (n - 1)
    raise NotImplementedError("Implementez covariance() - voir Grus ch.5")


def correlation(xs: list[float], ys: list[float]) -> float:
    """
    Retourne le coefficient de correlation de Pearson entre deux series.
    Retourne 0 si l'une des series a un ecart-type nul.
    """
    assert len(xs) == len(ys)
    stdev_x = standard_deviation(xs)
    stdev_y = standard_deviation(ys)
    if stdev_x > 0 and stdev_y > 0:
        return covariance(xs, ys) / (stdev_x * stdev_y)
    else:
        return 0
    raise NotImplementedError("Implementez correlation() - voir Grus ch.5")

if __name__ == "__main__":
    xs = [1, 2, 3, 4, 5]
    ys = [2, 4, 6, 8, 10]

    print("Test mean:")
    print(mean(xs))  # attendu: 3

    print("\nTest median:")
    print(median(xs))  # attendu: 3

    print("\nTest de_mean:")
    print(de_mean(xs))  # attendu: [-2, -1, 0, 1, 2]

    print("\nTest sum_of_squares:")
    print(sum_of_squares(xs))  # attendu: 55

    print("\nTest variance:")
    print(variance(xs))  # attendu: 2.5

    print("\nTest standard_deviation:")
    print(standard_deviation(xs))  # attendu: ~1.5811

    print("\nTest covariance:")
    print(covariance(xs, ys))  # attendu: 5.0

    print("\nTest correlation:")
    print(correlation(xs, ys))  # attendu: 1.0