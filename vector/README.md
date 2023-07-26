# SVG Path to Polygon

## Basic math

An SVG path is constructed from *line* and *curve* commands.
To transform a path into a polygon we only need to work with *curve* commands.
There are three of them, and we will focus on the most common and challenging one — cubic Bézier curve.

A cubic Bézier curve can be defined as

$$ B(t) = (1-t)^3 P_0 + 3(1-t)^2 t P_1 + 3(1-t) t^2 P_2 + t^3 P_3, \quad 0 \le t \le 1  $$  

where $P_0$, $P_1$, $P_2$ and $P_3$ are *control points*.

Let's find first and second derivatives for $B(t)$ (we'll need them later).
First, let's express $B(t)$ in terms of t:

$$ B(t) = (-P_0 + 3 P_1 - 3 P_2 + P_3) t^3 + (3 P_0 - 6 P_1 + 3 P_2) t^2 + (-3 P_0 + 3 P_1) t + P_0 $$  

So, as we can see

$$ B(t) = a t^3 + b t^2 + c t + d $$

where

$$ a = -P_0 + 3 (P_1 - P_2) + P_3 $$

$$ b = 3 (P_0 - 2 P_1 + P_2) $$

$$ c = 3 (-P_0 + P_1) $$

$$ d = P_0 $$

Now if we reuse these variables, derivatives simply become:

$$ B'(t) = 3at^2 + 2bt + c $$

$$ B''(t) = 6at + 2b $$

## Tangent

Let's recall the geometric meaning of a derivative from the school course.
Its value $f'(t)$ at some point $t$ is a slope coefficient for tangent line at that point.
Here's a simple SVG path with four cubic Bézier curves and highlighted control points:
<p align="center" >
<img src="https://github.com/koenigskraut/script-toolbox/raw/master/vector/files/1_basic.svg" alt="" width="100%"/>
</p>
We'll focus on the first segment:
<p align="center" >
<img src="https://github.com/koenigskraut/script-toolbox/raw/master/vector/files/2_first_segment.svg" alt="" width="50%"/>
</p>
First, let's check our equations. Since we do not multiply our points, we can express them as complex numbers:

$$ P_0=10+15 i, \quad P_1=20+5 i, \quad P_2=30+5 i, \quad P_3=40+15 i $$

$$ a = 0 $$

$$ b = 30i $$

$$ c = 30-30i $$

$$ d = 10+15i $$

And if we use $t = 0.5$ we should get a point in the middle of our curve with $X$ coordinate (real part) of $25$. Let's calculate and mark it on our image:

$$ B(0.5) = 0 \cdot 0.5^3 + 30i \cdot 0.5^2 + (30-30i) \space 0.5 + (10+15i) = 25+7.5i $$

<p align="center" >
<img src="https://github.com/koenigskraut/script-toolbox/raw/master/vector/files/3_calculated_point.svg" alt="" width="50%"/>
</p>

Seems right. Now we'll pick a less boring point $t=0.32$ and find a derivative for it:

$$ B'(t) = 3at^2 + 2bt + c $$

$$ B'(0.32) = 3 \cdot 0 \cdot 0.32^2 + 2 \cdot 30i \cdot 0.32 + (30-30i) = 30-10.8i $$

Wait, it has two parts? Isn't it suppose to be a slope of a line? Right, it's a parametric derivative! Actually we should've calculated two derivatives, $\frac{dx}{dt}$ and $\frac{dy}{dt}$, and then to find the actual derivative $\frac{dy}{dx}$ divide them one by another.
Since our parametric equations are identical, we just plug in points and do not multiply them, we can calculate both derivatives at once using complex numbers and then divide imaginary part ($Y$ component) by real one ($X$ component).
So the actual derivative value at $t = 0.32$ is

$$ \frac{-10.8}{30} = -0.36 $$

Actual point on our curve at $t = 0.32$ is $B(0.32) \approx 19.6+8.47i$. Using point-slope form of a line

$$y - y_1 = m(x - x_1)$$

, where $(x_1,y_1)$ is a given point and $m$ is a slope, let's write a proper line equation:

$$ y - 8.47 = -0.36 (x - 19.6) $$

$$ y = -0.36x + 15.53 $$

With $x = 0$ we get the second point of our tangent $(0,15.53)$, mark it on our image and draw a line through it and $(19.6,8.47)$:
<p align="center" >
<img src="https://github.com/koenigskraut/script-toolbox/raw/master/vector/files/4_tangent.svg" alt="" width="50%"/>
</p>

## Normal

Second thing that we would need after tangent is normal — line that is perpendicular to our curve at a given point.

<p align="center" >
<img src="https://github.com/koenigskraut/script-toolbox/raw/master/vector/files/5_normal.svg" alt="" width="50%"/>
</p>

We would exploit dot product property being equal to zero when the multiplied vectors are perpendicular.
First, recall what happens, when we plug some $t$ in our parametric function $B(t)$? We get a point on our Bézier curve.
And how do we make a vector from two points? By subtracting their coordinates. So $B(t) - P_a$ for a given scalar $t$ and point $P_a$ is some vector based on points $P_a$ and $B(t)$.
Turns out that the derivative of a parametric function produces the coordinates of a tangent vector $\overrightarrow{T}$.
All we need is to find a $t$ corresponding to a point $P_b$, such that $\overrightarrow{P_a P_b} \cdot \overrightarrow{T} = 0$.

Dot product can be calculated as:

$$a \cdot b = a_x b_x + a_y b_y$$

That means, we can write a simple equation:

$$ (B_x(t) - x_a) \cdot B_x'(t) + (B_y(t) - y_a) \cdot B_y'(t) = 0 $$

where $B_x(t)$ and $B_y(t)$ are separate parametric functions for $y$ and $x$, $B_x'(t)$ and $B_y'(t)$ are their derivatives, $x_a$ and $y_a$ are coordinates of a point $P_a$ outside our curve.
When solved, it will produce $t$, that corresponds to a point $P_b$ on our curve, producing line $P_a P_b$ perpendicular to our curve tangent at point $P_b$.

As already shown above, we choose the point $P_a(12,\space 3)$ and now want to find a normal through it.

$$ B(t) = a t^3 + b t^2 + c t + d $$

$$ B'(t) = 3at^2 + 2bt + c $$

$$ a = 0, \quad b = 30i, \quad c = 30-30i, \quad d = 10+15i $$

$$ B_x'(t) = 30, \quad B_y'(t) = 60t-30 $$

$$ B_x(t) = 30t+10, \quad B_y(t) = 30t^2-30t+15 $$

$$ x_a = 12, \quad x_b = 3 $$

So our equation will be:

$$ (30t+10 - 12) \cdot 30 + (30t^2-30t+15 - 3) \cdot (60t - 30) = 0 $$

$$ 30 t^3 - 45 t^2 + 42 t - 7 = 0, \quad t \in [0;1] $$

$$ t \approx 0.206 $$

$$ B(0.206) \approx 16.18+10.09i $$

<p align="center" >
<img src="https://github.com/koenigskraut/script-toolbox/raw/master/vector/files/6_normal_points.svg" alt="" width="57%"/>
</p>

## Convex vs concave Bézier curve

Next thing that we need is to determine if current segment of Bézier curve is convex or not. Let's expand the scope of our analysis to the next segment:

<p align="center" >
<img src="https://github.com/koenigskraut/script-toolbox/raw/master/vector/files/7_convex_concave.svg" alt="" width="75%"/>
</p>

Let's formally define what is a purely convex/concave Bézier curve and what isn't.
The curve is convex if it is located strictly on the one side of any tangent.
For our purposes we can say that our curve is convex at some point $P$ if the tangent is *outside* our path and concave otherwise:

<p align="center" >
<img src="https://github.com/koenigskraut/script-toolbox/raw/master/vector/files/8_convex_concave_tangent.svg" alt="" width="100%"/>
</p>

## The Algorithm

What we are interested in is some iterative algorithm, that embeds a Bézier curve into a polygon. Each iteration should approximate the shape of our curve more and more but with an important condition: polygon must **never** cut off part of a curve.
Since it's just a fun experiment, we won't bother with the most optimal and beautiful solution and just stick to one that works.

### Convex curve

The first idea is this:
1. find a maximum;
2. draw tangent through it;
3. intersect it with lines $P_0 P_1$ and $P_2 P_3$ (which are tangents for start and end points $P_0$ and $P_3$);
4. the resulting trapezoid is our polygon approximation.

<p align="center" >
<img src="https://github.com/koenigskraut/script-toolbox/raw/master/vector/files/9_algorithm_convex.svg" alt="" width="100%"/>
</p>

### Concave curve

But wait, the algorithm above only works for a convex curve! Indeed, for a concave one we should come up with something else. For example:
1. find a local minimum and draw tangent through it;
2. intersect it with lines $P_0 P_1$ and $P_2 P_3$ (which are tangents for start and end points $P_0$ and $P_3$);
3. find normals $O_1 N_1$ and $O_1 N_2$ for the intersection points;
4. the resulting trapezoid $P_0 N_1 N_2 P_3$ is our polygon approximation.

<p align="center" >
<img src="https://raw.githubusercontent.com/koenigskraut/script-toolbox/4b08fb9d7563f244c6083d4d85060322479ad502/vector/files/10_algorithm_concave.svg" alt="" width="100%"/>
</p>

### Inflecting curve

Now when we covered purely convex and concave curves, we should recall the full example:

<p align="center" >
<img src="https://github.com/koenigskraut/script-toolbox/raw/master/vector/files/1_basic.svg" alt="" width="100%"/>
</p>

What about two rightmost segments? They are neither convex nor concave ones!
Segment #3 is convex at the beginning and then after an *inflection point* $B_1$ it becomes concave. The opposite is true for the segment #4 and inflection point $B_2$.
<p align="center" >
<img src="https://github.com/koenigskraut/script-toolbox/raw/master/vector/files/11_inflecting_curves.svg" alt="" width="75%"/>
</p>
We'll use divide and conquer strategy to deal with them. First, let's break our segments in two by inflection point. One part will be convex and another concave.
<p align="center" >
<img src="https://github.com/koenigskraut/script-toolbox/raw/master/vector/files/12_inflecting_curves_breakdown.svg" alt="" width="75%"/>
</p>

For the convex one we'll use the convex curve algorithm:
1. find a local maximum;
2. draw tangent through it;
3. intersect it with tangents in start and end points (in our case end is an inflection point);
4. the resulting trapezoid is our polygon approximation.

<p align="center" >
<img src="https://github.com/koenigskraut/script-toolbox/raw/master/vector/files/13_inflecting_convex.svg" alt="" width="100%"/>
</p>

And for the concave one we'll use the respective concave curve algorithm:
1. find a local minimum and draw tangent through it;
2. intersect it with tangents in start and end points (in our case start is an inflection point);
3. find normals $O_1 N_1$ and $O_1 N_2$ for intersection points;
4. the resulting trapezoid $B_1 N_1 N_2 P_3$ is our polygon approximation.

<p align="center" >
<img src="https://github.com/koenigskraut/script-toolbox/raw/master/vector/files/14_inflecting_concave.svg" alt="" width="100%"/>
</p>

## Result

Let's again recall our example:
<p align="center" >
<img src="https://github.com/koenigskraut/script-toolbox/raw/master/vector/files/15_basic_pure.svg" alt="" width="100%"/>
</p>
And finally reveal the result of our approximation:
<p align="center" >
<img src="https://github.com/koenigskraut/script-toolbox/raw/master/vector/files/16_basic_approx.svg" alt="" width="100%"/>
</p>

As we can see, the number of vertices varies between the segments and the approximation of an inflecting curve turns out to be more precise than purely convex/concave one.
It is not a big deal though, since the algorithms above can be just thought of as the initial step of The Real Algorithm.
The real one should be iterative since we could want to approximate our path more and more accurate.
So, the simplest way I can think of to iterate over what we have at hand is as follows:
1. underlying curve segment is convex:
   1. plot normals $V_i N_i$ through every vertex $V_i$ other than $P_0$ and $P_3$ (start and end);
   2. cut off corners of our polygon with tangents at every point $N_i$;
   3. the resulting polygon is our new approximation.
   <p align="center" >
    <img src="https://github.com/koenigskraut/script-toolbox/raw/master/vector/files/17_convex_iterative.svg" alt="" width="100%"/>
    </p>
2. underlying curve segment is concave:
   1. plot tangents $t_i$ through every vertex including $P0$ and $P3$ (start and end);
   2. for every tangent intersection $O_i$ plot normal $O_i N_i$;
   3. $P_0$, $N_1$, $V_1$, ... $V_i$, $N_i$, $P_3$ are our new polygon approximation vertices.
   <p align="center" >
    <img src="https://github.com/koenigskraut/script-toolbox/raw/master/vector/files/18_concave_iterative.svg" alt="" width="100%"/>
    </p>

