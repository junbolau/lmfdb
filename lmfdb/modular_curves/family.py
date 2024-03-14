
from sage.misc.lazy_attribute import lazy_attribute
from lmfdb.modular_curves.web_curve import get_bread

def ModCurveFamily(name):
    if name == "X0N":
        return X0N()
    elif name == "X1N":
        return X1N()
    elif name == "XN":
        return XN()
    raise ValueError("Invalid name")

class ModCurveFamily_base():
    @lazy_attribute
    def bread(self):
        return get_bread([(f"${self.name}$", " ")])

    @lazy_attribute
    def title(self):
        return f"Modular curve family ${self.name}$"

class X0N(ModCurveFamily_base):
    name = "X_0(N)"
    sl2level = "N"
    index = "N+1"
    psl2index = "N^2+1"
    genus = "1 + "
    nu2 = "0"
    nu3 = "0"
    cusps = "N/2"
    rational_cusps = "1"
    moduli_description = r"$X_0(N)$ is the modular curve $X_H$ for $H\le \GL_2(\widehat\Z)$ the inverse image of $\begin{pmatrix} \ast & \ast \\ 0 & \ast \end{pmatrix} \subset \GL_2(\Z/N\Z)$. As a moduli space it parameterizes pairs $(E,C)$, where $E$ is an elliptic curve over $k$, and $C$ is a $\Gal_k$-stable cyclic subgroup of $E[N](\overline{k})$ of order $N$ that is the kernel of a rational isogeny $E\to E'$ of degree $N$."
    genus_formula = r"The genus of $X_0(N)$ is blah"

    @lazy_attribute
    def cusps_display(self):
        return self.cusps

    @lazy_attribute
    def cusps_width_display(self):
        return "unknown"

    @lazy_attribute
    def cusps_orbits_display(self):
        return "one is rational"

    elliptic_points = "There are no elliptic points, unless N=1, in which case there are 2"

    @lazy_attribute
    def properties(self):
        return [("Level", "$N$"),
                ("Index", str(self.index)),
                ("Genus", str(self.genus))]

class X1N(ModCurveFamily_base):
    name = "X_1(N)"
    sl2level = "N"
    index = "N+1"
    psl2index = "N^2+1"
    genus = "1/N"
    nu2 = "0"
    nu3 = "0"
    cusps = "N/2"
    rational_cusps = "1"
    moduli_description = r"$X_1(N)$ is the modular curve $X_H$ for $H\le \GL_2(\widehat\Z)$ the inverse image of $\begin{pmatrix} 1 & * \\ 0 & * \end{pmatrix} < \GL_2(\Z/N\Z)$. As a moduli space it parameterizes pairs $(E,P)$, where $E$ is an elliptic curve over $k$, and $P \in EN$ is a point of exact order $N$."
    genus_formula = r"The genus of $X_1(N)$ is blah"

    @lazy_attribute
    def cusps_display(self):
        return self.cusps

    @lazy_attribute
    def cusps_width_display(self):
        return "unknown"

    @lazy_attribute
    def cusps_orbits_display(self):
        return "one is rational"

    elliptic_points = "There are no elliptic points, unless N=1, in which case there are 2"

    @lazy_attribute
    def properties(self):
        return [("Level", "$N$"),
                ("Index", str(self.index)),
                ("Genus", str(self.genus))]


class XN(ModCurveFamily_base):
    name = "X(N)"
    sl2level = "N"
    index = "N+1"
    psl2index = "N^2+1"
    genus = "1/N"
    nu2 = "0"
    nu3 = "0"
    cusps = "N/2"
    rational_cusps = "1"
    moduli_description = r"$X(N)$ is the modular curve $X_H$ for $H\le \GL_2(\widehat\Z)$ the inverse image of the trivial subgroup of $\GL_2(\Z/N\Z)$. As a moduli space it parameterizes triples $(E,P,Q)$, where $E$ is an elliptic curve over $k$, and $P,Q \in E(k)$ form a basis for $EN$. There are other variants. The canonical field of definition of $X(N)$ is $\Q(\zeta_N)$, which means that the database of modular curves $X_H/\Q$ only includes $X(N)$ for $N\le 2$."
    genus_formula = r"The genus of $X(N)$ is blah"

    @lazy_attribute
    def cusps_display(self):
        return self.cusps

    @lazy_attribute
    def cusps_width_display(self):
        return "unknown"

    @lazy_attribute
    def cusps_orbits_display(self):
        return "one is rational"

    elliptic_points = "There are no elliptic points, unless N=1, in which case there are 2"

    @lazy_attribute
    def properties(self):
        return [("Level", "$N$"),
                ("Index", str(self.index)),
                ("Genus", str(self.genus))]
