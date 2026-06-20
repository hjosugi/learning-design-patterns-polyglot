from __future__ import annotations

from collections.abc import Callable

DiscountStrategy = Callable[[int], int]


def no_discount(cents: int) -> int:
    return cents


def seasonal_discount(cents: int) -> int:
    return round(cents * 0.9)


def vip_discount(cents: int) -> int:
    return round(cents * 0.8)


def checkout(total_cents: int, strategy: DiscountStrategy) -> int:
    if total_cents < 0:
        raise ValueError("total must be positive")
    return strategy(total_cents)


if __name__ == "__main__":
    for name, strategy in {
        "none": no_discount,
        "seasonal": seasonal_discount,
        "vip": vip_discount,
    }.items():
        print(f"{name}: {checkout(12_500, strategy)}")

