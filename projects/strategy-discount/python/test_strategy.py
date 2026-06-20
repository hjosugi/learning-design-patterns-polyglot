from strategy import checkout, no_discount, seasonal_discount, vip_discount


def test_checkout_strategies() -> None:
    assert checkout(12_500, no_discount) == 12_500
    assert checkout(12_500, seasonal_discount) == 11_250
    assert checkout(12_500, vip_discount) == 10_000


def test_negative_total_is_rejected() -> None:
    try:
        checkout(-1, no_discount)
    except ValueError as exc:
        assert "positive" in str(exc)
    else:
        raise AssertionError("expected ValueError")


if __name__ == "__main__":
    test_checkout_strategies()
    test_negative_total_is_rejected()
    print("ok")

