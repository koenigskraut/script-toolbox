from dataclasses import dataclass


def htoi(h: str) -> int:
    return int(h, 16)


@dataclass(eq=True, frozen=True)
class Color:
    r: int
    g: int
    b: int
    a: float = 1.0

    @classmethod
    def from_hex(cls, code: str, alpha=1.0) -> "Color":
        code = code.strip("#")
        return cls(*map(htoi, [code[0:2], code[2:4], code[4:6]]), a=alpha)

    def to_hex(self) -> str:
        return f"#{self.r:x}{self.g:x}{self.b:x}"

    def over_precise(self, other) -> tuple[float, float, float]:
        r = (other.r * other.a) + (self.r * (1 - other.a))
        g = (other.g * other.a) + (self.g * (1 - other.a))
        b = (other.b * other.a) + (self.b * (1 - other.a))
        return r, g, b

    def over(self, other) -> "Color":
        return Color(*map(round, self.over_precise(other)))


def guess_closure(base: Color, over: Color):
    def guess_color(opacity: int) -> Color | None:
        alpha = opacity / 100
        r = (over.r + base.r * (-1 + alpha)) / alpha
        g = (over.g + base.g * (-1 + alpha)) / alpha
        b = (over.b + base.b * (-1 + alpha)) / alpha
        if any(i < 0 for i in (r, g, b)):
            return None
        return Color(*map(round, [r, g, b]), a=alpha)

    return guess_color


def deviation_closure(base: Color, over: Color):
    def find_deviation(guessed: Color):
        precise = base.over_precise(guessed)
        return (guessed, (over.r - precise[0]) ** 2 + (over.g - precise[1]) ** 2 +
                (over.b - precise[2]) ** 2)

    return find_deviation


if __name__ == "__main__":
    b1, o1 = input().split()
    b2, o2 = input().split()
    base1, over1 = Color.from_hex(b1), Color.from_hex(o1)
    base2, over2 = Color.from_hex(b2), Color.from_hex(o2)

    closure_alpha = guess_closure(base1, over1)
    results_alpha = filter(lambda x: x is not None, map(closure_alpha, range(1, 100)))

    closure_error = deviation_closure(base2, over2)
    results_error = list(map(closure_error, results_alpha))
    results_error.sort(key=lambda r: r[1])
    print(results_error[0][0].to_hex(), results_error[0][0].a)

