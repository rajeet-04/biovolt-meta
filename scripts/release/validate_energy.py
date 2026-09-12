def integrate(samples: list[tuple[int, float | None]], gap_ms: int = 2500) -> float:
    total = 0.0
    for (previous_uptime, previous_power), (uptime, power) in zip(
        samples, samples[1:], strict=False
    ):
        delta = uptime - previous_uptime
        if delta <= 0 or delta > gap_ms or previous_power is None or power is None:
            continue
        total += (previous_power + power) / 2 * delta / 1_000_000
    return total
