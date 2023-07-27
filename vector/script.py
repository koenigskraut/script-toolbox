import math
from typing import Callable
from enum import Enum

import svgpathtools
from svgpathtools import svg2paths
from dataclasses import dataclass
import scipy.optimize as opt

numeric = float | complex


def assert_args(*args):
    if not all(isinstance(i, float) for i in args) and not all(isinstance(i, complex) for i in args):
        raise TypeError("mismatched arguments types")


@dataclass
class Line:
    a: float
    b: float
    c: float

    @staticmethod
    def from_points(p1: complex, p2: complex) -> "Line":
        a = (p1.imag - p2.imag)
        b = (p2.real - p1.real)
        c = (p1.real * p2.imag - p2.real * p1.imag)
        return Line(a, b, -c)

    def intersect(self, another) -> complex | None:
        d = self.a * another.b - self.b * another.a
        d_x = self.c * another.b - self.b * another.c
        d_y = self.a * another.c - self.c * another.a
        if d != 0:
            x = d_x / d
            y = d_y / d
            return complex(x, y)
        else:
            return None


@dataclass
class PrintableFunction:
    body: Callable
    representation: str | list[numeric]

    def __post_init__(self):
        if isinstance(self.representation, str):
            return
        assert_args(*self.representation)
        str_repr: str = ""
        t_pow = ["t³", "t²", "t", ""][4 - len(self.representation):]
        if isinstance(self.representation[0], float):
            for i, k in enumerate(self.representation):
                if k == 0:
                    continue
                plus = "+" if k > 0 and str_repr else ""
                str_repr += f"{plus}{k}{t_pow[i]}"
        else:
            for i, k in enumerate(self.representation):
                if k == 0:
                    continue
                plus = "+" if str_repr else ""
                str_repr += f"{plus}{k}{t_pow[i]}"
        self.representation = str_repr if str_repr else "NULL"

    def __str__(self):
        return self.representation

    def __call__(self, *args, **kwargs):
        return self.body(*args, **kwargs)


class Direction(Enum):
    HORIZONTAL = 1
    VERTICAL = 2


@dataclass
class MyCubicBezier:
    a: complex
    b: complex
    c: complex
    d: complex
    control_points: tuple[complex, complex, complex, complex]

    @staticmethod
    def from_points(p0: complex, p1: complex, p2: complex, p3: complex) -> "MyCubicBezier":
        a = -p0 + 3 * (p1 - p2) + p3
        b = 3 * (p0 - 2 * p1 + p2)
        c = 3 * (p1 - p0)
        d = p0
        return MyCubicBezier(a, b, c, d, (p0, p1, p2, p3))

    @staticmethod
    def __get_equation(a: numeric, b: numeric, c: numeric, d: numeric) -> PrintableFunction:
        return PrintableFunction(lambda t: a * t ** 3 + b * t ** 2 + c * t + d, [a, b, c, d])

    @property
    def equation(self) -> PrintableFunction:
        return self.__get_equation(self.a, self.b, self.c, self.d)

    @property
    def equation_x(self) -> PrintableFunction:
        return self.__get_equation(*(i.real for i in (self.a, self.b, self.c, self.d)))

    @property
    def equation_y(self) -> PrintableFunction:
        return self.__get_equation(*(i.imag for i in (self.a, self.b, self.c, self.d)))

    @staticmethod
    def __get_derivative(a: numeric, b: numeric, c: numeric) -> PrintableFunction:
        return PrintableFunction(lambda t: 3 * a * t ** 2 + 2 * b * t + c, [a, b, c])

    @property
    def derivative(self) -> PrintableFunction:
        return self.__get_derivative(self.a, self.b, self.c)

    @property
    def derivative_x(self) -> PrintableFunction:
        return self.__get_derivative(*(i.real for i in (self.a, self.b, self.c)))

    @property
    def derivative_y(self) -> PrintableFunction:
        return self.__get_derivative(*(i.imag for i in (self.a, self.b, self.c)))

    @staticmethod
    def __get_second_derivative(a: numeric, b: numeric) -> PrintableFunction:
        return PrintableFunction(lambda t: 6 * a * t + 2 * b, [a, b])

    @property
    def second_derivative(self) -> PrintableFunction:
        return self.__get_second_derivative(self.a, self.b)

    @property
    def second_derivative_x(self) -> PrintableFunction:
        return self.__get_second_derivative(self.a.real, self.b.real)

    @property
    def second_derivative_y(self) -> PrintableFunction:
        return self.__get_second_derivative(self.a.imag, self.b.imag)

    def normal(self, point):
        return lambda t: (self.equation_x(t) - point.real) * self.derivative_x(t) + \
                         (self.equation_y(t) - point.imag) * self.derivative_y(t)

    def direction(self) -> Direction:
        return Direction.HORIZONTAL if self.a.imag != 0 or self.b.imag != 0 else Direction.VERTICAL

    def is_convex(self, t) -> bool:
        val = self.derivative_x(t)*self.second_derivative_y(t) - self.derivative_y(t)*self.second_derivative_x(t)
        return val > 0

    def tangent_at_t(self, t: float) -> Line:
        point = self.equation(t)
        diff_complex = self.derivative(t)
        tangent_line: Line
        if diff_complex.imag != 0 and diff_complex.real != 0:
            slope = diff_complex.imag / diff_complex.real
            tan = tangent(point, slope)
            tangent_line = Line.from_points(complex(0, tan(0)), point)
        elif diff_complex.imag == 0:
            tangent_line = Line.from_points(complex(0, point.imag), point)
        else:
            tangent_line = Line.from_points(complex(point.real, 0), point)
        return tangent_line


def solve_linear(k, b) -> float | None:
    if k == 0:
        return None
    return -b / k


def solve_quadratic(a, b, c):
    if a == 0:
        return [solve_linear(b, c)]
    d = b ** 2 - 4 * a * c
    if d < 0:
        return None
    d = math.sqrt(d)
    result = [(-b + d) / (2 * a), (-b - d) / (2 * a)]
    if result[0] > result[1]:
        result[0], result[1] = result[1], result[0]
    return result


def tangent(point: complex, slope: float):
    return lambda x: slope * (x - point.real) + point.imag


class ResultAxis(Enum):
    X_AXIS = 1
    Y_AXIS = 2


def trapezoid(side1: Line, side2: Line, base: Line, start: complex, end: complex):
    p1 = side1.intersect(base)
    p2 = side2.intersect(base)
    return start, p1, p2, end


def solve_convex(curve: MyCubicBezier, t: float, with_inflection: bool) -> tuple[complex, complex, complex, complex]:
    p0, p1, p2, p3 = curve.control_points
    tangent_line = curve.tangent_at_t(t)
    polygon: tuple[complex, complex, complex, complex]
    line1: Line
    line2: Line
    if not with_inflection:
        line1, line2 = Line.from_points(p0, p1), Line.from_points(p2, p3)
        start, end = p0, p3
    else:
        inflection_t = solve_linear(6 * curve.a, 2 * curve.b).real
        inflection_point = curve.equation(inflection_t)
        if t < inflection_t:
            line1, line2 = Line.from_points(p0, p1), curve.tangent_at_t(inflection_t)
            start, end = p0, inflection_point
        else:
            line1, line2 = curve.tangent_at_t(inflection_t), Line.from_points(p2, p3)
            start, end = inflection_point, p3
    polygon = trapezoid(line1, line2, tangent_line, start, end)
    if not with_inflection:
        normal_eq1 = curve.normal(polygon[1])
        normal_eq2 = curve.normal(polygon[2])
        n1 = opt.fsolve(normal_eq1, [0.5])[0]
        n2 = opt.fsolve(normal_eq2, [0.5])[0]
        poly1 = trapezoid(line1, tangent_line, curve.tangent_at_t(n1), start, polygon[2])
        poly2 = trapezoid(tangent_line, line2, curve.tangent_at_t(n2), polygon[1], end)
        polygon = poly1[:3] + poly2[1:]
    return polygon


def solve_concave(curve: MyCubicBezier, t: float, with_inflection: bool) -> tuple[complex, complex, complex, complex]:
    p0, p1, p2, p3 = curve.control_points
    tangent_line = curve.tangent_at_t(t)
    polygon: tuple[complex, complex, complex, complex]
    line1: Line
    line2: Line
    if not with_inflection:
        line1, line2 = Line.from_points(p0, p1), Line.from_points(p2, p3)
        start, end = p0, p3
    else:
        inflection_t = solve_linear(6 * curve.a, 2 * curve.b).real
        inflection_point = curve.equation(inflection_t)
        if t < inflection_t:
            line1, line2 = Line.from_points(p0, p1), curve.tangent_at_t(inflection_t)
            start, end = p0, inflection_point
        else:
            line1, line2 = curve.tangent_at_t(inflection_t), Line.from_points(p2, p3)
            start, end = inflection_point, p3
    _, o1, o2, _ = trapezoid(line1, line2, tangent_line, start, end)
    if o1 is None or o2 is None:
        return start, o1, o2, end
    normal_eq1 = curve.normal(o1)
    normal_eq2 = curve.normal(o2)
    n1 = curve.equation(nt1 := opt.fsolve(normal_eq1, [0.5])[0])
    n2 = curve.equation(nt2 := opt.fsolve(normal_eq2, [0.5])[0])
    polygon = (start, n1, n2, end)
    if not with_inflection:
        t1 = curve.tangent_at_t(nt1)
        t2 = curve.tangent_at_t(nt2)
        o1 = line1.intersect(t1)
        o2 = t1.intersect(t2)
        o3 = t2.intersect(line2)
        normal_eq1 = curve.normal(o1)
        normal_eq2 = curve.normal(o2)
        normal_eq3 = curve.normal(o3)
        nn1 = curve.equation(opt.fsolve(normal_eq1, [0.5])[0])
        nn2 = curve.equation(opt.fsolve(normal_eq2, [0.5])[0])
        nn3 = curve.equation(opt.fsolve(normal_eq3, [0.5])[0])
        polygon = (start, nn1, n1, nn2, n2, nn3, end)
    return polygon


def parse_svg(filename: str):
    a, _ = svg2paths(filename)
    curve = a[0]
    final_polyline = []
    print(len(curve))
    for i in range(0, len(curve)):
        pick = curve[i]
        if isinstance(pick, svgpathtools.Line):
            final_polyline.append(pick.end)
            continue
        my_bezier = MyCubicBezier.from_points(*pick)

        eq = my_bezier.equation
        diff = my_bezier.derivative

        extr_real = solve_quadratic(3 * my_bezier.a.real, 2 * my_bezier.b.real, my_bezier.c.real)
        extr_imag = solve_quadratic(3 * my_bezier.a.imag, 2 * my_bezier.b.imag, my_bezier.c.imag)
        extr_real = [] if extr_real is None else extr_real
        extr_imag = [] if extr_imag is None else extr_imag
        if not extr_real and not extr_imag:
            final_polyline.append(pick.end)
            continue

        critical_points = [i for i in extr_real if i is not None and 0 <= i <= 1] + \
                          [i for i in extr_imag if i is not None and 0 <= i <= 1]
        if not critical_points:
            critical_points = [0.5]

        for t in critical_points:
            is_convex = my_bezier.is_convex(t)
            point = my_bezier.equation(t)
            if is_convex:
                print(f'	<circle fill="#FF0000" cx="{point.real}" cy="{point.imag}" r="1"/>')
                polygon = solve_convex(my_bezier, t, len(critical_points) > 1)
            else:
                print(f'	<circle fill="#0000FF" cx="{point.real}" cy="{point.imag}" r="1"/>')
                polygon = solve_concave(my_bezier, t, len(critical_points) > 1)
            if final_polyline:
                final_polyline += polygon[1:]
            else:
                final_polyline += polygon

    print(f'<path xmlns="http://www.w3.org/2000/svg" fill="#0000FF" opacity="0.5" d="M {final_polyline[0].real} {final_polyline[0].imag} L ', end="")
    for fp in final_polyline:
        if fp is not None:
            print(f"{fp.real:.2f} {fp.imag:.2f}", end=" ")
    print('Z "/>')


if __name__ == "__main__":
    # if len(sys.argv) == 1:
    #     print("provide svg filename as first argument")
    #     sys.exit(1)
    parse_svg("files/example-full.svg")
