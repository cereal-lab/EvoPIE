# pylint: disable=no-member
# pylint: disable=E1101
# helper method to use instead of directly calling bleach.clean
import bleach
from bleach_allowlist import generally_xss_safe, print_attrs, standard_styles

RICH_HTML_FIELDS = {
    ("Course", "description"),
    ("Distractor", "answer"),
    ("Distractor", "justification"),
    ("InvalidatedDistractor", "answer"),
    ("InvalidatedDistractor", "comment"),
    ("InvalidatedDistractor", "justification"),
    ("Justification", "justification"),
    ("Question", "answer"),
    ("Question", "stem"),
    ("Quiz", "description"),
}

def _model_name(model):
    return model if isinstance(model, str) else model.__name__

def prepare_field_value(model, field, value):
    """Prepare a submitted value according to the model field policy."""
    if (_model_name(model), field) in RICH_HTML_FIELDS:
        return bleach.clean(
            value,
            tags=generally_xss_safe,
            attributes=print_attrs,
            styles=standard_styles,
        )
    return bleach.clean(value, tags=[], attributes={}, strip=True)

def groupby(iterable, key=lambda x: x):
    '''from iterable creates list of pairs group_key:list of elements with the key.
        Note that iterable.groupby groups only adjacent elements. This method is equiv of itertools.groupby(sorted)
    '''
    res = {}
    for el in iterable:
        k = key(el)
        if k not in res:
            res[k] = []
        res[k].append(el)
    return res.items()

def unpack_key(key, knows):
    ''' Allows to flatten 'sid': [1,2,3] to several records with 'sid': 1, 'sid':2, 'sid': 3
        It does same for qid and did 
    '''
    return [k2 for k in knows 
                for ks in [[{**k, key: i} for i in k[key]] 
                            if type(k.get(key, "*")) == list else 
                            [{**k, key: i} for i in range(k[key]["range"][0], k[key]["range"][1] + 1)] #NOTE: json "range":[2,3] is mapped to call range(2,4)
                            if type(k.get(key, "*")) == dict and "range" in k[key] else
                            [{**k, key: i} for r in k[key]["ranges"] for rg in [r if type(r) == list else [r, r]] for i in range(rg[0], rg[1] + 1)]
                            if type(k.get(key, "*")) == dict and "ranges" in k[key] else
                            [k]] 
                for k2 in ks]    

def find_median(sorted_list):
    if len(sorted_list) == 0: return None, []
    indices = []

    list_size = len(sorted_list)
    median = 0

    if list_size % 2 == 0:
        indices.append(int(list_size / 2) - 1)  # -1 because index starts from 0
        indices.append(int(list_size / 2))

        median = (sorted_list[indices[0]] + sorted_list[indices[1]]) / 2
    else:
        indices.append(int(list_size / 2))

        median = sorted_list[indices[0]]

    return median, indices    

def param_to_dict(n, v, d = {}, type_converters = {}, delim = '_'):
    '''
    Converts flat dict to tree using delim as edge in hierarchy
    Example: a.b.0.test --> {"a":{"b":{"0":{"test":...}}}} 
    '''
    cur = d     
    converter = type_converters
    path = n.split(delim)
    for path_elem in path[:-1]:
        converter = converter.get(path_elem, converter.get("*", {}))
        cur = cur.setdefault(path_elem, {})        
    converter = converter.get(path[-1], converter.get("*", {}))
    cur[path[-1]] = converter(v) if callable(converter) else v
    return d