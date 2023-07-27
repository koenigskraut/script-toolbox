import math
import sys
from typing import Callable, Optional, Any

import svgpathtools
from svgpathtools import svg2paths
from dataclasses import dataclass, astuple
import scipy.optimize as opt

numeric = float | complex


def assert_args(*args):
    if not all(isinstance(i, float) for i in args) and not all(isinstance(i, complex) for i in args):
        raise TypeError("mismatched arguments types")


def orelse(v: Any, default: Any) -> Any:
    return v if v is not None else default


@dataclass
class Line:
    a: float
    b: float
    c: float
    points: tuple[complex, complex]

    @staticmethod
    def from_points(p1: complex, p2: complex) -> "Line":
        a = (p1.imag - p2.imag)
        b = (p2.real - p1.real)
        c = (p1.real * p2.imag - p2.real * p1.imag)
        return Line(a, b, -c, (p1, p2))

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
    coefficients: list[numeric]
    representation: str = ""

    def __post_init__(self):
        if self.representation:
            return
        assert_args(*self.coefficients)
        t_pow = ["t³", "t²", "t", ""]
        if isinstance(self.coefficients[0], float):
            for i, k in enumerate(self.coefficients):
                if k == 0:
                    continue
                plus = "+" if k > 0 and self.representation else ""
                self.representation += f"{plus}{k}{t_pow[i]}"
        else:
            for i, k in enumerate(self.coefficients):
                if k == 0:
                    continue
                plus = "+" if self.representation else ""
                self.representation += f"{plus}{k}{t_pow[i]}"
        self.representation = self.representation if self.representation else "NULL"

    def __str__(self):
        return self.representation

    def __call__(self, *args, **kwargs):
        return self.body(*args, **kwargs)


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
        return PrintableFunction(lambda t: 3 * a * t ** 2 + 2 * b * t + c, [type(a)(0), 3 * a, 2 * b, c])

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
        return PrintableFunction(lambda t: 6 * a * t + 2 * b, [type(a)(0), type(a)(0), 6 * a, 2 * b])

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

    def is_convex_at(self, t) -> bool:
        val = self.derivative_x(t) * self.second_derivative_y(t) - self.derivative_y(t) * self.second_derivative_x(t)
        return val > 0

    def tangent_at(self, t: float) -> Line:
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

    def inflection_point(self) -> Optional[float]:
        c_a = 3 * (self.b.real * self.a.imag - self.b.imag * self.a.real)
        c_b = 3 * (self.c.real * self.a.imag - self.c.imag * self.a.real)
        c_c = self.c.real * self.b.imag - self.c.imag * self.b.real
        if (raw := solve_quadratic(c_a, c_b, c_c)) is None:
            return None
        results = list(filter(lambda t: t is not None and 0 < t < 1, raw))
        if len(results) > 1:
            print("Two points!", results, self)
        return results[0] if results else None

    def critical_points(self) -> Optional[list[float]]:
        ks = [3 * self.a, 2 * self.b, self.c]
        base_cond = lambda t: t is not None and 0 < t < 1
        x_cond = lambda t: base_cond(t)  # and self.derivative_y(t) != 0
        y_cond = lambda t: base_cond(t)  # and self.derivative_x(t) != 0
        critical_x = list(filter(x_cond, orelse(solve_quadratic(*(k.real for k in ks)), [])))
        critical_y = list(filter(y_cond, orelse(solve_quadratic(*(k.imag for k in ks)), [])))
        results = [i for i in critical_x if self.derivative_y(i) != 0]
        results += [i for i in critical_y if self.derivative_x(i) != 0]
        return results


@dataclass
class Polygon:
    a: complex
    b: complex
    c: complex
    d: complex

    @staticmethod
    def from_lines(side_1: Line, side_2: Line, base: Line, start: complex, end: complex) -> Optional["Polygon"]:
        p1 = side_1.intersect(base)
        p2 = side_2.intersect(base)
        if p1 is None or p2 is None:
            return None
        return Polygon(start, p1, p2, end)


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


def solve_convex(curve: MyCubicBezier, t: float, inflection_t=None) -> Optional[list[complex]]:
    p0, p1, p2, p3 = curve.control_points
    tangent_line = curve.tangent_at(t)
    polygon: tuple[complex, complex, complex, complex]
    line1: Line
    line2: Line
    if inflection_t is None:
        line1, line2 = Line.from_points(p0, p1), Line.from_points(p2, p3)
        start, end = p0, p3
    else:
        inflection_point = curve.equation(inflection_t)
        if t < inflection_t:
            line1, line2 = Line.from_points(p0, p1), curve.tangent_at(inflection_t)
            start, end = p0, inflection_point
        else:
            line1, line2 = curve.tangent_at(inflection_t), Line.from_points(p2, p3)
            start, end = inflection_point, p3
    tr = Polygon.from_lines(line1, line2, tangent_line, start, end)
    if tr is None:
        tangent_line = curve.tangent_at(0.5)
        tr = Polygon.from_lines(line1, line2, tangent_line, start, end)
        if tr is None:
            return [start, end]
    polygon = astuple(tr)
    if inflection_t is None:
        normal_eq1 = curve.normal(polygon[1])
        normal_eq2 = curve.normal(polygon[2])
        n1 = opt.root_scalar(normal_eq1, x0=0, x1=1).root
        n2 = opt.root_scalar(normal_eq2, x0=0, x1=1).root
        poly1 = Polygon.from_lines(line1, tangent_line, curve.tangent_at(n1), start, polygon[2])
        poly2 = Polygon.from_lines(tangent_line, line2, curve.tangent_at(n2), polygon[1], end)
        poly1_tuple = [start, polygon[2]] if poly1 is None else list(astuple(poly1))
        poly2_tuple = [polygon[1], end] if poly2 is None else list(astuple(poly2))
        polygon = poly1_tuple[:-1] + poly2_tuple[1:]
    return polygon


def solve_concave(curve: MyCubicBezier, t: float, inflection_t=None) -> list[complex]:
    p0, p1, p2, p3 = curve.control_points
    tangent_line = curve.tangent_at(t)
    polygon: tuple[complex, complex, complex, complex]
    line1: Line
    line2: Line
    if inflection_t is None:
        line1, line2 = Line.from_points(p0, p1), Line.from_points(p2, p3)
        start, end = p0, p3
    else:
        inflection_point = curve.equation(inflection_t)
        if t < inflection_t:
            line1, line2 = Line.from_points(p0, p1), curve.tangent_at(inflection_t)
            start, end = p0, inflection_point
        else:
            line1, line2 = curve.tangent_at(inflection_t), Line.from_points(p2, p3)
            start, end = inflection_point, p3

    tr = Polygon.from_lines(line1, line2, tangent_line, start, end)
    if tr is None or tr.b is None or tr.c is None:
        return [start, end]
    normal_eq1 = curve.normal(tr.b)
    normal_eq2 = curve.normal(tr.c)
    n1 = curve.equation(nt1 := opt.root_scalar(normal_eq1, x0=0, x1=1).root)
    n2 = curve.equation(nt2 := opt.root_scalar(normal_eq2, x0=0, x1=1).root)
    polygon = (start, n1, n2, end)
    if inflection_t is None:
        t1 = curve.tangent_at(nt1)
        t2 = curve.tangent_at(nt2)
        o1 = line1.intersect(t1)
        o2 = t1.intersect(t2)
        o3 = t2.intersect(line2)
        normal_eq1 = curve.normal(o1)
        normal_eq2 = curve.normal(o2)
        normal_eq3 = curve.normal(o3)

        nn1 = curve.equation(opt.root_scalar(normal_eq1, x0=0, x1=1).root)
        nn2 = curve.equation(opt.root_scalar(normal_eq2, x0=0, x1=1).root)
        nn3 = curve.equation(opt.root_scalar(normal_eq3, x0=0, x1=1).root)
        polygon = [start, nn1, n1, nn2, n2, nn3, end]
    return polygon


def parse_svg(filename: str):
    a, _ = svg2paths(filename)
    curve = a[0]
    final_polyline = []
    # print(len(curve))
    for pick in curve:
        if isinstance(pick, svgpathtools.Line):
            final_polyline.append(pick.end)
            continue
        my_bezier = MyCubicBezier.from_points(*pick)
        inflection_point = my_bezier.inflection_point()
        critical_points = my_bezier.critical_points()
        if not critical_points:
            critical_points = [0.5]
        for t in critical_points:
            is_convex = my_bezier.is_convex_at(t)
            if is_convex:
                # print(f'	<circle fill="#FF0000" cx="{point.real}" cy="{point.imag}" r="1"/>')
                polygon = solve_convex(my_bezier, t, inflection_point)
            else:
                # print(f'	<circle fill="#0000FF" cx="{point.real}" cy="{point.imag}" r="1"/>')
                polygon = solve_concave(my_bezier, t, inflection_point)
            if final_polyline:
                final_polyline += polygon[1:]
            else:
                final_polyline += polygon

    print(f'<path xmlns="http://www.w3.org/2000/svg" fill="#0000FF" opacity="0.5" d="M {final_polyline[0].real} '
          f'{final_polyline[0].imag} L ', end="")
    for fp in final_polyline:
        if fp is not None:
            print(f"{fp.real:.2f} {fp.imag:.2f}", end=" ")
    print('Z "/>')


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("provide just svg filename as first argument")
        sys.exit(1)
    parse_svg(sys.argv[1])
