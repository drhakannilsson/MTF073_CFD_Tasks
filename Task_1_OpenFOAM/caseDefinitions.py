"""
caseDefinitions.py - the 40 cases of MTF073 Task 1 (see Task_1_description.pdf).

Each case is a dict with:
  L, H        domain size
  bc          dict boundary number -> boundary condition, where
                ('dirichlet', 'formula')       T = formula (in x, y, L, H, pi)
                ('neumann',)                   dT/dn = 0
                ('convective', h, 'Tinf')      -k dT/dn = h (T - Tinf)
  k           conductivity model (key in K_MODELS)
  b           source model (key in B_MODELS) and its parameters
  probes      points where the temperature is monitored

Boundary numbering (Fig. 1 of the task description) and OpenFOAM patches:
  1 = south (y = 0),  2 = east (x = L),  3 = north (y = H),  4 = west (x = 0)

Formulas are written so that they are valid both as C++ (coded OpenFOAM
code) and as OpenFOAM expressions (setExprBoundaryFields), using the
variables x, y, T, L, H and the constants defined in 'constants'.
Use pi as a variable (it is defined in both languages by t1foam.py).
"""

PATCH_OF_BOUNDARY = {1: 'south', 2: 'east', 3: 'north', 4: 'west'}
BOUNDARY_OF_PATCH = {v: k for k, v in PATCH_OF_BOUNDARY.items()}

# Conductivity models: C++/expression code and human-readable text
K_MODELS = {
    'linearX': {'code': '5.0*(1.0 + 100.0*x/L)',
                'text': 'k = 5(1 + 100x/L)'},
    'region':  {'code': '((x > 0.7 && x < 1.1 && y > 0.3 && y < 0.4) ? 0.01 : 20.0)',
                'text': 'k = 0.01 for 0.7 < x < 1.1 and 0.3 < y < 0.4, k = 20 elsewhere'},
    'T':       {'code': '2.0*(1.0 + 20.0*T/T1)',
                'text': 'k = 2(1 + 20T/T1)'},
    'yT':      {'code': '16.0*(y/H + 30.0*T/T1)',
                'text': 'k = 16(y/H + 30T/T1)'},
}

# Source models (per volume / per area in 2D). 'Su' and 'Sp' give the
# implicit linearization b = Su + Sp*T around the latest temperature T,
# with Sp <= 0.
B_MODELS = {
    'constant':  {'text': 'b = {b}'},
    'quadratic': {'text': 'b = 15(c1 - c2 T^2),  c1 = {c1}, c2 = {c2}'},
}


def _family_A(T_inf1, T2, T3):          # cases 1-5
    return dict(L=1.0, H=0.5,
                bc={1: ('convective', 1000.0, T_inf1),
                    2: ('dirichlet', T2),
                    3: ('dirichlet', T3),
                    4: ('neumann',)},
                k='linearX', b=('constant', {'b': -1.5}), constants={})


def _family_B(T2, T4):                  # cases 6-10
    return dict(L=1.5, H=0.5,
                bc={1: ('convective', 1000.0, '10'),
                    2: ('dirichlet', T2),
                    3: ('neumann',),
                    4: ('dirichlet', T4)},
                k='region', b=('constant', {'b': 0.0}), constants={})


def _family_CD(c1, c2, T3, H, k):       # cases 11-20
    return dict(L=1.0, H=H,
                bc={1: ('dirichlet', '10'),
                    2: ('dirichlet', '20'),
                    3: ('dirichlet', T3),
                    4: ('neumann',)},
                k=k, b=('quadratic', {'c1': c1, 'c2': c2}), constants={'T1': 10.0})


def _family_E(T1, T4, T_inf3):          # cases 21-25
    return dict(L=1.0, H=0.5,
                bc={1: ('dirichlet', T1),
                    2: ('neumann',),
                    3: ('convective', 1000.0, T_inf3),
                    4: ('dirichlet', T4)},
                k='linearX', b=('constant', {'b': -1.5}), constants={})


def _family_F(T1, T_inf3):              # cases 26-30
    return dict(L=1.5, H=0.5,
                bc={1: ('dirichlet', T1),
                    2: ('dirichlet', '10'),
                    3: ('convective', 1000.0, T_inf3),
                    4: ('neumann',)},
                k='region', b=('constant', {'b': 0.0}), constants={})


def _family_GH(c1, c2, T4, H, k):       # cases 31-40
    return dict(L=1.0, H=H,
                bc={1: ('dirichlet', '10'),
                    2: ('dirichlet', '20'),
                    3: ('neumann',),
                    4: ('dirichlet', T4)},
                k=k, b=('quadratic', {'c1': c1, 'c2': c2}), constants={'T1': 10.0})


_A = [('35', '10 + 20*sin(pi*y/H)', '10'),
      ('5', '10 + 5*(1 - y/H) + 15*sin(pi*y/H)', '10'),
      ('25', '15*cos(2*pi*y/H)', '15'),
      ('5', '10 + 5*y/H + 10*sin(pi*y/H)', '15'),
      ('30', '-5*y/H + 15*cos(2*pi*y/H)', '10')]
_B = [('10 + 20*sin(pi*y/H)', '10'),
      ('10 + 20*sin(pi*y/H)', '30'),
      ('5*(y/H - 1) + 15*cos(pi*y/H)', '15'),
      ('5*(y/H - 1) + 15*cos(pi*y/H)', '30'),
      ('10 + 5*sin(pi*y/H)', '20')]
_CD = [(20, 0.2, '20*x/L'),
       (25, 0.1, '10*(1 + 2*x/L)'),
       (25, 0.3, '15 + 5*x/L'),
       (20, 0.4, '5 + 15*x/L'),
       (25, 0.25, '5 + 3*(1 + 5*x/L)')]
_E = [('10', '10 + 20*sin(pi*y/H)', '10'),
      ('15', '10 + 5*(1 - y/H) + 15*sin(pi*y/H)', '10'),
      ('15', '15*cos(2*pi*y/H)', '15'),
      ('10', '10 + 5*y/H + 10*sin(pi*y/H)', '15'),
      ('15', '-5*y/H + 15*cos(2*pi*y/H)', '10')]
_F = [('10 + 20*sin(pi*x/L)', '10'),
      ('10 + 20*sin(pi*x/L)', '30'),
      ('5*(x/L - 1) + 15*cos(pi*x/L)', '15'),
      ('5*(x/L - 1) + 15*cos(pi*x/L)', '30'),
      ('10 + 5*sin(pi*x/L)', '10')]
_GH = [(20, 0.2, '20*y/H'),
       (25, 0.1, '10*(1 + 2*y/H)'),
       (25, 0.3, '15 + 5*y/H'),
       (20, 0.4, '5 + 15*y/H'),
       (25, 0.25, '5 + 3*(1 + 5*y/H)')]

CASES = {}
for n in range(5):
    CASES[1 + n] = _family_A(*_A[n])
    CASES[6 + n] = _family_B(*_B[n])
    CASES[11 + n] = _family_CD(*_CD[n], H=1.0, k='T')
    CASES[16 + n] = _family_CD(*_CD[n], H=2.0, k='yT')
    CASES[21 + n] = _family_E(*_E[n])
    CASES[26 + n] = _family_F(*_F[n])
    CASES[31 + n] = _family_GH(*_GH[n], H=1.0, k='T')
    CASES[36 + n] = _family_GH(*_GH[n], H=2.0, k='yT')

# Default monitoring points (fractions of L and H). They are chosen so that
# they do not coincide with mesh lines of the supplied meshes.
for n, c in CASES.items():
    c['id'] = n
    c['probes'] = [(0.43 * c['L'], 0.43 * c['H']), (0.77 * c['L'], 0.77 * c['H'])]


def get_case(n):
    if n not in CASES:
        raise KeyError(f"Case {n} does not exist (valid: 1-40)")
    return CASES[n]


def describe(c):
    """Human-readable description of a case, as a list of (label, text)."""
    rows = [('Domain', f"L = {c['L']:g}, H = {c['H']:g}")]
    names = {1: 'Boundary 1 (south, y = 0)', 2: 'Boundary 2 (east, x = L)',
             3: 'Boundary 3 (north, y = H)', 4: 'Boundary 4 (west, x = 0)'}
    for b in (1, 2, 3, 4):
        bc = c['bc'][b]
        if bc[0] == 'dirichlet':
            txt = f"Dirichlet: T{b} = {bc[1]}"
        elif bc[0] == 'neumann':
            txt = "Homogeneous Neumann: dT/dn = 0"
        else:
            txt = f"Convective: h = {bc[1]:g}, T_inf,{b} = {bc[2]}"
        rows.append((names[b], txt))
    rows.append(('Conductivity', K_MODELS[c['k']]['text']
                 + (f",  T1 = {c['constants']['T1']:g}" if 'T1' in c['constants'] else '')))
    rows.append(('Source term', B_MODELS[c['b'][0]]['text'].format(**c['b'][1])))
    return rows
