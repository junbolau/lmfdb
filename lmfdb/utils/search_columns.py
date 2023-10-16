from .web_display import display_knowl
from lmfdb.utils import pol_to_html, coeff_to_poly

template_sage = r'''
def make_cell_{column}(rec):
    return {constructor_function}
'''

template_magma = r'''
define make_cell_{column}(rec) in Magma, and
    return {constructor_function}
'''

template_gp = r'''
define make_cell_{column}(rec) in gp, and
    return {constructor_function}
'''

default_template = {'sage' : template_sage,\
            'magma' : template_magma,\
            'gp' : template_gp }

def tf(val, language):
    if language == 'sage':
        return 'True' if val else 'False'
    elif language == 'magma':
        return 'true' if val else 'false'
    elif language in ['pari', 'gp']:
        return '1' if val else '0'
    raise NotImplementedError('{language = } is not recognized')

def get_default_func(default, name):
    def f(info):
        if "hidecol" in info and name in info["hidecol"].split("."):
            return False
        if "showcol" in info and name in info["showcol"].split("."):
            return True
        sort_order = info.get('sort_order', '')
        if (sort_order and sort_order == name
                and "search_array" in info
                and info["search_array"].sorts is not None):
            return True
        if isinstance(default, bool):
            return default
        return default(info)
    return f


class SearchCol:
    def __init__(self, name, knowl, title, default=False, align="left",
                 contingent=None, short_title=None, **kwds):
        # Both contingent and default can be functions that take info
        # as an input (if default is a boolean it's translated to the
        # constant function with that value)
        # If contingent is false, then that column doesn't even show
        # up on the list of possible columns
        # If default is false, then that column is included in the
        # selector but not displayed by default
        assert "," not in name
        self.name = name
        self.knowl = knowl
        self.title = title
        if short_title is None:
            short_title = None if title is None else title.lower()
        self.short_title = short_title
        self.default = get_default_func(default, name)
        self.orig = [name]
        self.height = 1
        self.contingent = contingent
        fundict = {}
        fundict['sage'] = lambda x : x
        fundict['magma'] = lambda x : x
        fundict['gp'] = lambda x : x
        self.constructor_function = fundict
        self.th_class = self.td_class = f"col-{name}"
        if align == "left":
            self.th_style = self.td_style = ""
        else:
            self.th_style = self.td_style = f"text-align:{align};"
        self.th_content = self.td_content = ""
        self.inline = kwds.pop("inline", True)
        self.is_string = kwds.pop("is_string", True)
        self.cell_function_name = kwds.pop("cell_function_name", None)
        self.download_col = kwds.pop("download_col", None)
        if not self.inline and self.cell_function_name is None:
            self.cell_function_name = f"process_{name}"

        for key, val in kwds.items():
            assert hasattr(self, key) and key.startswith("th_") or key.startswith("td_")
            setattr(self, key, getattr(self, key) + val)

    def _get(self, rec, name=None):
        # We support dictionaries as well as classes like
        # AbvarFq_isoclass that are created in a postprocess step
        if name is None:
            name = self.name
            orig = self.orig[0]
        else:
            orig = name
        if isinstance(rec, dict):
            return rec.get(orig, "")
        val = getattr(rec, name)
        return val() if callable(val) else val

    def get(self, rec):
        # This function is used by the front-end display code, while the underlying _get method
        # is used for downloading.  The difference shows up for Floats, where we want the full
        # precision in the downloaded file
        return self._get(rec)

    def display(self, rec):
        # default behavior is to just use the string representation of rec
        return str(self.get(rec))

    def display_knowl(self):
        if self.knowl:
            return display_knowl(self.knowl, self.title)
        return self.title

    def show(self, info, rank=None):
        if (self.contingent is None or self.contingent(info)) and (rank is None or rank == 0):
            yield self

    def download(self, rec, language, name=None):
        if self.download_col is not None:
            name = self.download_col
        s = self._get(rec, name=name)
        if self.is_string:
            return '"{0}"'.format(s)
        else:
            return s

class SpacerCol(SearchCol):
    def __init__(self, name, **kwds):
        super().__init__(name, None, None, **kwds)
        self.orig = []

    def display(self, rec):
        return ""

    def display_knowl(self):
        return ""


class MathCol(SearchCol):
    def __init__(self, name, knowl, title, default=False, align="center", orig=None, **kwds):
        kwds.setdefault('is_string', False)
        super().__init__(name, knowl, title, default, align, **kwds)
        self.orig = [orig if (orig is not None) else name]

    def display(self, rec):
        val = self.get(rec)
        return f"${val}$" if val is not None else ""

class FloatCol(MathCol):
    def __init__(self, name, knowl, title, prec=3, default=False, align="center", **kwds):
        kwds.setdefault('is_string', False)
        super().__init__(name, knowl, title, default, align, **kwds)
        self.prec = prec

    def get(self, rec):
        val = self._get(rec)
        # We mix string processing directives so that we can use variable precision
        return f"%.{self.prec}f" % val

class CheckCol(SearchCol):
    def __init__(self, name, knowl, title, default=False, align="center", **kwds):
        kwds.setdefault('is_string', False)
        super().__init__(name, knowl, title, default, align, **kwds)

    def display(self, rec):
        val = self.get(rec)
        return "&#x2713;" if val else ("?" if val is None else "")

class CheckMaybeCol(SearchCol):
    def __init__(self, name, knowl, title, default=False, align="center", **kwds):
        kwds.setdefault('is_string', False)
        super().__init__(name, knowl, title, default, align, **kwds)

    def display(self, rec):
        if self.get(rec) > 0:
            return "&#x2713;"
        return "" if self.get(rec) < 0 else "not computed"

    def download(self, rec, language, name=None):
        ans = self.get(rec)
        if ans == 0:
            return "not computed"
        else:
            return (ans > 0)

class LinkCol(SearchCol):
    def __init__(self, name, knowl, title, url_for, default=False, align="left", **kwds):
        super().__init__(name, knowl, title, default, align, **kwds)
        self.url_for = url_for

    def display(self, rec):
        link = self.get(rec)
        if link is None:
            return ""
        return f'<a href="{self.url_for(link)}">{link}</a>'


class ProcessedCol(SearchCol):
    def __init__(self, name, knowl, title, func, default=False, orig=None,
                 mathmode=False, align="left", apply_download=False, **kwds):
        super().__init__(name, knowl, title, default, align, **kwds)
        self.func = func
        self.orig = [orig if (orig is not None) else name]
        self.mathmode = mathmode
        self.apply_download = apply_download

    def display(self, rec):
        s = str(self.func(self.get(rec)))
        if s and self.mathmode:
            s = f"${s}$"
        return s

    def download(self, rec, lang, name=None):
        if self.download_col is not None:
            name = self.download_col
        s = self._get(rec, name=name)
        if self.apply_download:
            s = self.func(s)
        if self.is_string:
            return '"{0}"'.format(s)
        else:
            return s

class ProcessedLinkCol(SearchCol):
    def __init__(self, name, knowl, title, url_func, disp_func, default=False,
                 orig=None, align="left", **kwds):
        super().__init__(name, knowl, title, default, align, **kwds)
        self.url_func = url_func
        self.disp_func = disp_func
        self.orig = [orig if (orig is not None) else name]

    def display(self, rec):
        x = self.get(rec)
        url = self.url_func(x)
        disp = self.disp_func(x)
        return f'<a href="{url}">{disp}</a>'


class MultiProcessedCol(SearchCol):
    def __init__(self, name, knowl, title, inputs, func, default=False,
                 mathmode=False, align="left", apply_download=True, **kwds):
        super().__init__(name, knowl, title, default, align, **kwds)
        self.func = func
        self.orig = inputs
        self.mathmode = mathmode
        self.apply_download = apply_download

    def display(self, rec):
        s = self.func(*[rec.get(col) for col in self.orig])
        if s != "" and self.mathmode:
            s = f"${s}$"
        return s

    def download(self, rec, language, name=None):
        if self.download_col is None:
            data = [rec.get(col) for col in self.orig]
            if self.apply_download:
                return self.func(*data)
        else:
            data = self._get(rec, name=self.download_col)
        return data

class ContingentCol(ProcessedCol):
    def __init__(self, name, knowl, title, func, contingent=lambda info: True,
                 default=False, orig=None, mathmode=False, align="center",
                 **kwds):
        super().__init__(name, knowl, title, func, default, orig, mathmode, align, **kwds)
        self.contingent = contingent

    def show(self, info, rank=None):
        if self.contingent(info) and (rank is None or rank == 0):
            yield self


class ColGroup(SearchCol):
    # See classical modular forms for an example

    def __init__(self, name, knowl, title, subcols,
                 contingent=lambda info: True, default=False, orig=None,
                 align="center", **kwds):
        super().__init__(name, knowl, title, default, align, **kwds)
        self.subcols = subcols
        self.contingent = contingent
        if orig is None:
            orig = sum([sub.orig for sub in subcols], [])
        self.orig = orig
        self.height = 2

    def show(self, info, rank=None):
        if self.contingent(info):
            if callable(self.subcols):
                subcols = self.subcols(info)
            else:
                subcols = self.subcols
            n = 0
            for sub in subcols:
                if sub.name != self.name and "colgroup" not in sub.th_class:
                    sub.th_class += f" colgroup-{self.name}"
                if sub.default(info):
                    n += 1
            self.th_content = f" colspan={n}"
            if rank == 0:
                yield self
            else:
                yield from subcols

    def download(self, rec, language):
        return [sub.get(rec) for sub in self.subcols]


class SearchColumns:
    above_results = ""  # Can add text above the Results (1-50 of ...) if desired
    above_table = ""  # Can add text above the results table if desired
    dummy_download = False  # change this to include dummy_download_search_results.html instead
    below_download = ""  # Can add text above the bottom download links

    def __init__(self, columns, db_cols=None, tr_class=None):
        """
        INPUT:

        - ``columns`` -- a list of SearchCol objects
        """
        self.maxheight = maxheight = max(C.height for C in columns)
        if maxheight > 1:
            for C in columns:
                if C.height == 1:
                    # columns that have height > 1 are responsible for
                    # setting th_content on their own
                    C.th_content += fr" rowspan={maxheight}"
        self.columns = columns
        if db_cols is None:
            db_cols = sorted(set(sum([C.orig for C in columns], [])))
        self.db_cols = db_cols
        if tr_class is None:
            tr_class = ["" for _ in range(maxheight)]
        self.tr_class = tr_class

    def columns_shown(self, info, rank=None):
        # By default, this doesn't depend on info
        # rank is None in the body of the table, and 0..(maxrank-1) in the header
        for C in self.columns:
            yield from C.show(info, rank)



# The following column types are used to control download behavior

class PolynomialCol(SearchCol):
    def __init__(self, name, knowl, title, default=False, orig=None,
                 mathmode=False, align="left", **kwds):
        super().__init__(name, knowl, title, default, align, **kwds)
        self.cell_function_name = f'process_{name}'
        self.orig = [orig if (orig is not None) else name]
        self.mathmode = mathmode

    def cell_function_body(self, lang):
        if lang.name == 'sage':
            return "return QQ['x'](x)"
        elif lang.name == 'magma':
            return "return ZZx![c : c in x];"
        elif lang.name == 'gp':
            return "Pol(Vecrev(x))"
        else:
            raise NotImplementedError('Language not supported yet')

    def display(self, rec):
        return pol_to_html(str(coeff_to_poly(self.get(rec))))

    def download(self, rec, lang):
        return self.get(rec)

class ListCol(ProcessedCol):
    def download(self, rec, lang):
        s = self.func(self.get(rec)).replace('"','')
        return s

class FinGroupCol(ProcessedCol):
    def download(self, rec, lang):
        return self.get(rec)

class NonMaxPrimesCol(ProcessedCol):
    def download(self, rec, lang):
        s = self.get(rec)
        if s is None or s == "":
            return lang.to_lang([])
        else:
            return s

