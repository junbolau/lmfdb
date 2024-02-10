# -*- coding: utf-8 -*-
# See genus2_curves/web_g2c.py
# See templates/space.html for how functions are called

from lmfdb import db
from sage.all import ZZ
from sage.databases.cremona import cremona_letter_code
from lmfdb.number_fields.web_number_field import nf_display_knowl, cyclolookup, rcyclolookup
from lmfdb.characters.TinyConrey import ConreyCharacter
from lmfdb.utils import (
    display_knowl, web_latex, coeff_to_power_series,
    web_latex_factored_integer, prop_int_pretty)
from flask import url_for
import re
NEWLABEL_RE = re.compile(r"^([0-9]+)\.([0-9]+)\.([a-z]+)$")
OLDLABEL_RE = re.compile(r"^([0-9]+)\.([0-9]+)\.([0-9]+)$")
GAMMA1_RE = re.compile(r"^([0-9]+)\.([0-9]+)$")
def valid_label(label):
    return NEWLABEL_RE.match(label) or OLDLABEL_RE.match(label)
def valid_gamma1(label):
    return GAMMA1_RE.match(label)

def get_bread(**kwds):
    # Should be called with either search=True or an initial segment of the links below
    links = [('level', 'Level %s', 'cmf.by_url_level'),
             ('weight', 'Weight %s', 'cmf.by_url_full_gammma1_space_label'),
             ('char_orbit_label', 'Character orbit %s', 'cmf.by_url_space_label'),
             ('hecke_orbit', 'Newform orbit %s', 'cmf.by_url_newform_label'),
             ('embedding_label', 'Embedding %s', 'cmf.by_url_newform_conrey5')]
    bread = [('Modular forms', url_for('modular_forms')),
             ('Classical', url_for("cmf.index"))]
    if 'other' in kwds:
        if isinstance(kwds['other'], str):
            return bread + [(kwds['other'], ' ')]
        else:
            return bread + kwds['other']
    url_kwds = {}
    for key, display, link in links:
        if key not in kwds:
            return bread
        url_kwds[key] = kwds[key]
        bread.append((display % kwds[key], url_for(link, **url_kwds)))
    return bread
def get_search_bread():
    return get_bread(other='Search results')
def get_dim_bread():
    return get_bread(other='Dimension table')

def newform_search_link(text, title=None, **kwd):
    query = '&'.join('%s=%s'%(key, val) for key, val in kwd.items())
    link = "%s?%s"%(url_for('.index'), query)
    return "<a href='%s'%s>%s</a>"%(link, "" if title is None else " title='%s'"%title, text)

def cyc_display(m, d, real_sub):
    r"""
    Used to display cyclotomic fields and their real subfields.

    INPUT:

    - ``m`` -- the order of the root of unity generating the field.
    - ``d`` -- the degree of the cyclotomic field over Q
    - ``real_sub`` -- whether to display the real subfield instead.

    OUTPUT:

    A string or knowl showing the cyclotomic field Q(\zeta_m) or Q(\zeta_m)^+.
    """
    if d == 1:
        name = r'\(\Q\)'
    elif m == 4:
        name = r'\(\Q(i)\)'
    elif real_sub:
        name = r'\(\Q(\zeta_{%s})^+\)' % m
    else:
        name = r'\(\Q(\zeta_{%s})\)' % m
    if d < 24:
        if real_sub:
            label = rcyclolookup[m]
        else:
            label = cyclolookup[m]
        return nf_display_knowl(label, name=name)
    else:
        return name

def ALdim_table(al_dims, level, weight):
    def sign_char(x): return "-" if x else "+"
    def url_sign_char(x): return "-" if x else "%2B"
    primes = ZZ(level).prime_divisors()
    num_primes = len(primes)
    header = [r'<th>\(%s\)</th>'%p for p in primes]
    if num_primes > 1:
        header.append(r"<th class='right'>%s</th>"%(display_knowl('cmf.fricke', title='Fricke').replace('"',"'")))
    header.append('<th>Dim</th>')
    rows = []
    fricke = [0,0]
    for i, dim in enumerate(al_dims):
        if dim == 0:
            continue
        b = list(reversed(ZZ(i).bits()))
        b = [0 for j in range(num_primes-len(b))] + b
        row = [r'<td>\(%s\)</td>'%sign_char(x) for x in b]
        sign = sum(b) % 2
        if num_primes > 1:
            row.append(r"<td class='right'>$%s$</td>"%sign_char(sign))
        query = {'level':level, 'weight':weight, 'char_order':1, 'atkin_lehner_string':"".join(map(url_sign_char,b))}
        link = newform_search_link(r'\(%s\)'%dim, **query)
        row.append(r'<td>%s</td>'%(link))
        fricke[sign] += dim
        if i == len(al_dims) - 1 and num_primes > 1:
            tr = "<tr class='endsection'>"
        else:
            tr = "<tr>"
        rows.append(tr + ''.join(row) + '</tr>')
    if num_primes > 1:
        plus_knowl = display_knowl('cmf.plus_space',title='Plus space').replace('"',"'")
        plus_link = newform_search_link(r'\(%s\)'%fricke[0], level=level, weight=weight, char_order=1, fricke_eigenval=1)
        minus_knowl = display_knowl('cmf.minus_space',title='Minus space').replace('"',"'")
        minus_link = newform_search_link(r'\(%s\)'%fricke[1], level=level, weight=weight, char_order=1, fricke_eigenval=-1)
        rows.append(r"<tr><td colspan='%s'>%s</td><td class='right'>\(+\)</td><td>%s</td></tr>"%(num_primes, plus_knowl, plus_link))
        rows.append(r"<tr><td colspan='%s'>%s</td><td class='right'>\(-\)</td><td>%s</td></tr>"%(num_primes, minus_knowl, minus_link))
    return ("<table class='ntdata'><thead><tr>%s</tr></thead><tbody>%s</tbody></table>" %
            (''.join(header), ''.join(rows)))

def common_latex(level, weight, conrey=None, S="S", t=0, typ="", symbolic_chi=False):
    # symbolic_chi is currently ignored: we always use a symbolic chi
    if conrey is None:
        char = ""
    #elif symbolic_chi is True:
    #    char = r", \chi"
    #elif symbolic_chi:
    #    char = ", " + symbolic_chi
    elif conrey == 1:
        char = ""
    else:
        #char = r", [\chi_{{{level}}}({conrey}, \cdot)]".format(level=level, conrey=conrey)
        char = r", [\chi]"
    if typ:
        typ = r"^{\mathrm{%s}}"%(typ)
    if char:
        ans = r"{S}_{{{k}}}{typ}({N}{char})"
    else:
        ans = r"{S}_{{{k}}}{typ}(\Gamma_{t}({N}){char})"
    return ans.format(S=S, k=weight, typ=typ, t=t, N=level, char=char)

def convert_spacelabel_from_conrey(spacelabel_conrey):
    """
    Returns the label for a space specified using a Conrey index
    e.g. 23.2.22 -> 23.2.b (because 23.b is the character orbit label of the Conrey character 23.22)
    """
    N, k, n = map(int, spacelabel_conrey.split('.'))
    try:
        return db.mf_newspaces.lucky({'conrey_index': ConreyCharacter(N,n).min_conrey_conj, 'level': N, 'weight': k}, projection='label')
    except AssertionError: # N and n not relatively prime
        pass


def trace_expansion_generic(space, prec_max=10):
    prec = min(len(space.traces)+1, prec_max)
    return web_latex(coeff_to_power_series([0] + space.traces[:prec-1],prec=prec),enclose=True)


class DimGrid():
    def __init__(self, grid=None):
        if grid is None:
            self._grid = {'M':{'all':0,'new':0,'old':0},
                          'S':{'all':0,'new':0,'old':0},
                          'E':{'all':0,'new':0,'old':0}}
        else:
            self._grid = grid

    def __getitem__(self, X):
        return self._grid[X]

    def __add__(self, other):
        if isinstance(other,int) and other == 0: # So that we can do sum(grids)
            return self
        elif isinstance(other,DimGrid):
            grid = {}
            for X in ['M','S','E']:
                grid[X] = {}
                for typ in ['all','new','old']:
                    grid[X][typ] = self._grid[X][typ] + other._grid[X][typ]
            return DimGrid(grid)
        else:
            raise TypeError

    def __mul__(self, other):
        if isinstance(other, int):
            grid = {}
            for X in ['M','S','E']:
                grid[X] = {}
                for typ in ['all','new','old']:
                    grid[X][typ] = other * self._grid[X][typ]
            return DimGrid(grid)
        else:
            raise TypeError

    def __radd__(self, other):
        return self.__add__(other)

    def __rmul__(self, other):
        return self.__mul__(other)

    @staticmethod
    def from_db(data):
        grid = {'M':{'all':data['mf_dim'],
                     'new':data['dim']+data['eis_new_dim'],
                     'old':data['mf_dim']-data['dim']-data['eis_new_dim']},
                'S':{'all':data['cusp_dim'],
                     'new':data['dim'],
                     'old':data['cusp_dim']-data['dim']},
                'E':{'all':data['eis_dim'],
                     'new':data['eis_new_dim'],
                     'old':data['eis_dim']-data['eis_new_dim']}}
        return DimGrid(grid)

class WebNewformSpace():
    def __init__(self, data):
        self.__dict__.update(data)
        self.factored_level = web_latex_factored_integer(self.level, equals=True)
        self.has_projective_image_types = all(typ+'_dim' in data for typ in ('dihedral','a4','s4','a5'))
        # The following can be removed once we change the behavior of lucky to include Nones
        self.num_forms = data.get('num_forms')
        self.trace_bound = data.get('trace_bound')
        self.has_trace_form = (data.get('traces') is not None)
        self.char_conrey = self.conrey_index
        self.char_conrey_str = r'\chi_{%s}(%s,\cdot)' % (self.level, self.char_conrey)
        self.newforms = list(db.mf_newforms.search({'space_label':self.label}, projection=2))
        oldspaces = db.mf_subspaces.search({'label':self.label, 'sub_level':{'$ne':self.level}}, ['sub_level', 'sub_char_orbit_index', 'sub_conrey_index', 'sub_mult'])
        self.oldspaces = [(old['sub_level'], old['sub_char_orbit_index'], old['sub_conrey_index'], old['sub_mult']) for old in oldspaces]
        self.dim_grid = DimGrid.from_db(data)
        self.plot = db.mf_newspace_portraits.lookup(self.label, projection="portrait")

        # Properties
        self.properties = [('Label',self.label)]
        if self.plot is not None and self.dim > 0:
            self.properties += [(None, '<img src="{0}" width="200" height="200"/>'.format(self.plot))]
        self.properties +=[
            ('Level', prop_int_pretty(self.level)),
            ('Weight', prop_int_pretty(self.weight)),
            ('Character orbit', '%s.%s' % (self.level, self.char_orbit_label)),
            ('Rep. character', '$%s$' % self.char_conrey_str),
            ('Character field',r'$\Q%s$' % ('' if self.char_degree==1 else r'(\zeta_{%s})' % self.char_order)),
            ('Dimension', prop_int_pretty(self.dim)),
        ]
        if self.num_forms is not None:
            self.properties.append(('Newform subspaces', prop_int_pretty(self.num_forms)))
        self.properties.append(('Sturm bound', prop_int_pretty(self.sturm_bound)))
        if data.get('trace_bound') is not None:
            self.properties.append(('Trace bound', prop_int_pretty(self.trace_bound)))
        # Work around search results not including None
        if data.get('num_forms') is None:
            self.num_forms = None

        # Breadcrumbs
        self.bread = get_bread(level=self.level, weight=self.weight, char_orbit_label=self.char_orbit_label)

        # Downloads
        self.downloads = [
            ('Trace form to text', url_for('cmf.download_traces', label=self.label)),
            ('All stored data to text', url_for('.download_newspace', label=self.label)),
            ('Underlying data', url_for('.mf_data', label=self.label)),
        ]

        if self.conrey_index == 1:
            self.trivial_character = True
            character_str = "trivial character"
            if self.dim == 0:
                self.dim_str = r"\(%s\)"%(self.dim)
            else:
                self.minus_dim = self.dim - self.plus_dim
                self.dim_str = r"\(%s + %s\)"%(self.plus_dim, self.minus_dim)
        else:
            self.trivial_character = False
            character_str = r"Character {level}.{orbit_label}".format(level=self.level, orbit_label=self.char_orbit_label)
            self.dim_str = r"\(%s\)"%(self.dim)
        self.title = r"Space of modular forms of level %s, weight %s, and %s"%(self.level, self.weight, character_str)
        gamma1_link = '/ModularForm/GL2/Q/holomorphic/%d/%d' % (self.level, self.weight)
        self.friends = [('Newspace %d.%d' % (self.level, self.weight), gamma1_link)]

    @staticmethod
    def by_label(label):
        """
        Searches for a specific modular forms space by its label.
        Constructs the WebNewformSpace object if the space is found, raises an error otherwise
        """
        if not valid_label(label):
            raise ValueError("Invalid modular forms space label %s." % label)
        data = db.mf_newspaces.lookup(label)
        if data is None:
            raise ValueError("Space %s not found" % label)
        return WebNewformSpace(data)

    @property
    def char_orbit_link(self):
        label = '%s.%s' % (self.level, self.char_orbit_label)
        return display_knowl('character.dirichlet.orbit_data', title=label, kwargs={'label':label})

    def display_character(self):
        if self.char_order == 1:
            ord_deg = " (trivial)"
        else:
            ord_knowl = display_knowl('character.dirichlet.order', title='order')
            deg_knowl = display_knowl('character.dirichlet.degree', title='degree')
            ord_deg = r" (of %s \(%d\) and %s \(%d\))" % (ord_knowl, self.char_order, deg_knowl, self.char_degree)
        return self.char_orbit_link + ord_deg

    def _vec(self):
        return [self.level, self.weight, self.conrey_index]

    def mf_latex(self):
        return common_latex(*(self._vec() + ["M"]))

    def eis_latex(self):
        return common_latex(*(self._vec() + ["E"]))

    def eis_new_latex(self):
        return common_latex(*(self._vec() + ["E",0,"new"]))

    def eis_old_latex(self):
        return common_latex(*(self._vec() + ["E",0,"old"]))

    def cusp_latex(self):
        return common_latex(*(self._vec() + ["S"]))

    def cusp_latex_symbolic(self):
        return common_latex(*(self._vec() + ["S"]), symbolic_chi=True)

    def new_latex(self):
        return common_latex(*(self._vec() + ["S",0,"new"]))

    def old_latex(self):
        return common_latex(*(self._vec() + ["S",0,"old"]))

    def old_latex_symbolic(self):
        return common_latex(*(self._vec() + ["S",0,"old"]), symbolic_chi=True)

    def subspace_latex(self, new=False):
        return common_latex("M", self.weight, self.conrey_index, "S", 0, "new" if new else "", symbolic_chi=True)

    def oldspace_decomposition(self):
        # Returns a latex string giving the decomposition of the old part.  These come from levels M dividing N, with the conductor of the character dividing M.
        template = r"<a href={url}>\({old}\)</a>\(^{{\oplus {mult}}}\)"
        return r"\(\oplus\)".join(template.format(old=common_latex(N, self.weight, conrey, typ="new"),
                                                  url=url_for(".by_url_space_label",level=N,weight=self.weight,char_orbit_label=cremona_letter_code(i-1)),
                                                  mult=mult)
                                  for N, i, conrey, mult in self.oldspaces)

    def ALdim_table(self):
        return ALdim_table(self.ALdims, self.level, self.weight)

    def trace_expansion(self, prec_max=10):
        return trace_expansion_generic(self, prec_max)

    def hecke_cutter_display(self):
        return ", ".join(r"\(%d\)" % p for p in self.hecke_cutter_primes)

    def display_character_field(self):
        return cyc_display(self.char_order, self.char_degree, False)

class WebGamma1Space():
    def __init__(self, level, weight):
        data = db.mf_gamma1.lucky({'level':level,'weight':weight})
        if data is None:
            raise ValueError("Space not in database")
        self.__dict__.update(data)
        self.weight_parity = -1 if (self.weight % 2) == 1 else 1
        self.factored_level = web_latex_factored_integer(self.level, equals=True)
        self.has_projective_image_types = all(typ+'_dim' in data for typ in ('dihedral','a4','s4','a5'))
        # The following can be removed once we change the behavior of lucky to include Nones
        self.num_forms = data.get('num_forms')
        self.num_spaces = data.get('num_spaces')
        self.trace_bound = data.get('trace_bound')
        self.has_trace_form = (data.get('traces') is not None)
        # by default we sort on char_orbit_index
        newspaces = list(db.mf_newspaces.search({'level':level, 'weight':weight, 'char_parity': self.weight_parity}))
        oldspaces = db.mf_gamma1_subspaces.search({'level':level, 'sub_level':{'$ne':level}, 'weight':weight}, ['sub_level','sub_mult'])
        self.oldspaces = [(old['sub_level'],old['sub_mult']) for old in oldspaces]
        self.dim_grid = DimGrid.from_db(data)
        self.decomp = []
        newforms = list(db.mf_newforms.search({'level':level, 'weight':weight}, ['label', 'space_label', 'dim', 'level', 'char_orbit_label', 'hecke_orbit', 'char_degree']))
        self.has_uncomputed_char = False
        for space in newspaces:
            if space.get('num_forms') is None:
                self.decomp.append((space, None))
                self.has_uncomputed_char = True
            else:
                self.decomp.append((space, [form for form in newforms if form['space_label'] == space['label']]))
        self.plot = db.mf_gamma1_portraits.lookup(self.label, projection="portrait")
        self.properties = [('Label',self.label),]
        if self.plot is not None and self.dim > 0:
            self.properties += [(None, '<a href="{0}"><img src="{0}" width="200" height="200"/></a>'.format(self.plot))]
        self.properties +=[
            ('Level',str(self.level)),
            ('Weight',str(self.weight)),
            ('Dimension',str(self.dim))
        ]
        if self.num_spaces is not None:
            self.properties.append(('Nonzero newspaces',str(self.num_spaces)))
        if self.num_forms is not None:
            self.properties.append(('Newform subspaces',str(self.num_forms)))
        self.properties.append(('Sturm bound',str(self.sturm_bound)))
        if self.trace_bound is not None:
            self.properties.append(('Trace bound',str(self.trace_bound)))
        self.bread = get_bread(level=self.level, weight=self.weight)
        # Downloads
        self.downloads = [
            ('Trace form to text', url_for('cmf.download_traces', label=self.label)),
            ('All stored data to text', url_for('cmf.download_full_space', label=self.label)),
            ('Underlying data', url_for('.mf_data', label=self.label)),
        ]
        self.title = r"Space of modular forms of level %s and weight %s"%(self.level, self.weight)
        self.friends = []

    @staticmethod
    def by_label(label):
        match = valid_gamma1(label)
        if not match:
            raise ValueError("Invalid modular forms space label %s." % label)
        level, weight = map(int, match.groups())
        return WebGamma1Space(level, weight)

    def _vec(self):
        return [self.level, self.weight, None]

    def mf_latex(self):
        return common_latex(*(self._vec() + ["M",1]))

    def eis_latex(self):
        return common_latex(*(self._vec() + ["E",1]))

    def eis_new_latex(self):
        return common_latex(*(self._vec() + ["E",1,"new"]))

    def eis_old_latex(self):
        return common_latex(*(self._vec() + ["E",1,"old"]))

    def cusp_latex(self):
        return common_latex(*(self._vec() + ["S",1]))

    def new_latex(self):
        return common_latex(*(self._vec() + ["S",1,"new"]))

    def subspace_latex(self, new=False):
        return common_latex("M", self.weight, None, "S", 1, "new" if new else "")

    def summand_latex(self,symbolic_chi=True):
        return common_latex(self.level, self.weight, 1, "S", 0, "new", symbolic_chi=symbolic_chi)

    def old_latex(self):
        return common_latex(*(self._vec() + ["S",1,"old"]))

    def header_latex(self):
        return r'\(' + common_latex(*(self._vec() + ["S",0,"new",True])) + r'\)'

    def _link(self, N, i=None, form=None, typ="new", label=True):
        if form is not None:
            form = cremona_letter_code(form - 1)
        if label:
            if i is None:
                name = "{N}.{k}".format(N=N, k=self.weight)
            elif form is None:
                name = "{N}.{k}.{i}".format(N=N, k=self.weight, i=i)
            else:
                name = "{N}.{k}.{i}.{f}".format(N=N, k=self.weight, i=i, f=form)
        else:
            t = 1 if i is None else 0
            name = r"\(%s\)" % common_latex(N, self.weight, i, t=t, typ=typ)
        if i is None:
            url = url_for(".by_url_full_gammma1_space_label",
                          level=N, weight=self.weight)
        elif form is None:
            url = url_for(".by_url_space_label",
                          level=N, weight=self.weight, char_orbit_label=i)
        else:
            url = url_for(".by_url_newform_label",
                          level=N, weight=self.weight, char_orbit_label=i, hecke_orbit=form)
        return r"<a href={url}>{name}</a>".format(url=url, name=name)

    def oldspace_decomposition(self):
        template = r"{link}\(^{{\oplus {mult}}}\)"
        return r"\(\oplus\)".join(template.format(link=self._link(N, label=False),
                                                  mult=mult)
                                  for N, mult in self.oldspaces)

    def decomposition(self):
        # returns a list of 6-tuples chi_rep, num_chi, space, firstform, firstdim, forms
        ans = []
        for i, (space, forms) in enumerate(self.decomp):
            rowtype = "oddrow" if i%2 else "evenrow"
            chi_str = r"\chi_{%s}(%s, \cdot)" % (space['level'], space['conrey_index'])
            chi_rep = '<a href="' + url_for('characters.render_Dirichletwebpage',
                                             modulus=space['level'],
                                             orbit_label=space['char_orbit_label'])
            chi_rep += r'">\({}\)</a>'.format(chi_str)

            num_chi = space['char_degree']
            link = self._link(space['level'], space['char_orbit_label'])
            if forms is None:
                ans.append((rowtype, chi_rep, num_chi, link, "n/a", space['dim'], []))
            elif not forms:
                ans.append((rowtype, chi_rep, num_chi, link, "None", space['dim'], []))
            else:
                dims = [form['dim'] for form in forms]
                forms = [self._link(form['level'], form['char_orbit_label'], form['hecke_orbit']) for form in forms]
                ans.append((rowtype, chi_rep, num_chi, link, forms[0], dims[0], list(zip(forms[1:], dims[1:]))))
        return ans

    def trace_expansion(self, prec_max=10):
        return trace_expansion_generic(self, prec_max)
