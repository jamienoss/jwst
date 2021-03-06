# Licensed under a 3-clause BSD style license - see LICENSE.rst

from collections import OrderedDict

from asdf import AsdfFile
from asdf import schema as asdf_schema

from jwst.transforms.jwextension import JWSTExtension
from gwcs.extension import GWCSExtension

# return_result included for backward compatibility
def find_fits_keyword(schema, keyword, return_result=False):
    """
    Utility function to find a reference to a FITS keyword in a given
    schema.  This is intended for interactive use, and not for use
    within library code.

    Parameters
    ----------
    schema : JSON schema fragment
        The schema in which to search.

    keyword : str
        A FITS keyword name

    Returns
    -------
    locations : list of str
    """
    def find_fits_keyword(subschema, path, combiner, ctx, recurse):
        if len(path) and path[0] == 'extra_fits':
            return True
        if subschema.get('fits_keyword') == keyword:
            results.append('.'.join(path))

    results = []
    walk_schema(schema, find_fits_keyword, results)

    return results

def build_fits_dict(schema):
    """
    Utility function to create a dict that maps FITS keywords to their
    metadata attribute in a input schema.

    Parameters
    ----------
    schema : JSON schema fragment
        The schema in which to search.

    Returns
    -------
    results : dict
        Dictionary with FITS keywords as keys and schema metadata
        attributes as values

    """
    def build_fits_dict(subschema, path, combiner, ctx, recurse):
        if len(path) and path[0] == 'extra_fits':
            return True
        kw = subschema.get('fits_keyword')
        if kw is not None:
            results[kw] = '.'.join(path)

    results = {}
    walk_schema(schema, build_fits_dict, results)

    return results


def build_schema2fits_dict(schema):
    """
    Utility function to create a dict that maps metadata attributes to thier
    FITS keyword and FITS HDU locations (if any).

    Parameters
    ----------
    schema : JSON schema fragment
        The schema in which to search.

    Returns
    -------
    results : dict
        Dictionary with schema metadata path as keys and a tuple of FITS
        keyword and FITS HDU as values.

    """
    def build_schema_dict(subschema, path, combiner, ctx, recurse):
        if len(path) and path[0] == 'extra_fits':
            return True
        kw = subschema.get('fits_keyword')
        hdu = subschema.get('fits_hdu')
        if kw is not None:
            results['.'.join(path)] = (kw, hdu)

    results = {}
    walk_schema(schema, build_schema_dict, results)

    return results


class SearchSchemaResults(list):
    def __repr__(self):
        import textwrap

        result = []
        for path, description in self:
            result.append(path)
            result.append(
                textwrap.fill(
                    description, initial_indent='    ',
                    subsequent_indent='    '))
        return '\n'.join(result)


def search_schema(schema, substring):
    """
    Utility function to search the metadata schema for a particular
    phrase.

    This is intended for interactive use, and not for use within
    library code.

    The searching is case insensitive.

    Parameters
    ----------
    schema : JSON schema fragment
        The schema in which to search.

    substring : str
        The substring to search for.

    Returns
    -------
    locations : list of tuples
    """
    substring = substring.lower()

    def find_substring(subschema, path, combiner, ctx, recurse):
        matches = False
        for param in ('title', 'description'):
            if substring in schema.get(param, '').lower():
                matches = True
                break

        if substring in '.'.join(path).lower():
            matches = True

        if matches:
            description = '\n\n'.join([
                schema.get('title', ''),
                schema.get('description', '')]).strip()
            results.append(('.'.join(path), description))

    results = SearchSchemaResults()
    walk_schema(schema, find_substring, results)
    results.sort()
    return results


def walk_schema(schema, callback, ctx={}):
    """
    Walks a JSON schema tree in breadth-first order, calling a
    callback function at each entry.

    Parameters
    ----------
    schema : JSON schema

    callback : callable
        The callback receives the following arguments at each entry:

        - subschema: The subschema for the entry
        - path: A list of strings defining the path to the entry
        - combiner: The current combiner in effect, will be 'allOf',
          'anyOf', 'oneOf', 'not' or None
        - ctx: An arbitrary context object, usually a dictionary
        - recurse: A function to call to recurse deeper on a node.

        If the callback returns `True`, the subschema will not be
        further recursed.

    ctx : object, optional
        An arbitrary context object
    """
    def recurse(schema, path, combiner, ctx):
        if callback(schema, path, combiner, ctx, recurse):
            return

        for c in ['allOf', 'not']:
            for sub in schema.get(c, []):
                recurse(sub, path, c, ctx)

        for c in ['anyOf', 'oneOf']:
            for i, sub in enumerate(schema.get(c, [])):
                recurse(sub, path + [c], c, ctx)

        if schema.get('type') == 'object':
            for key, val in schema.get('properties', {}).items():
                recurse(val, path + [key], combiner, ctx)

        if schema.get('type') == 'array':
            items = schema.get('items', {})
            if isinstance(items, list):
                for i, item in enumerate(items):
                    recurse(item, path + [i], combiner, ctx)
            elif len(items):
                recurse(items, path + ['items'], combiner, ctx)

    recurse(schema, [], None, ctx)


def merge_property_trees(schema):
    """
    Recursively merges property trees that are governed by the "allOf" combiner.

    The main purpose of this function is to allow multiple subschemas to be
    combined into a single schema. All of the properties at each level of each
    subschema are merged together to form a single coherent tree.

    This allows datamodel schemas to be more modular, since various components
    can be represented in individual files and then referenced elsewhere. They
    are then combined by this function into a single schema data structure.
    """
    newschema = OrderedDict()

    def add_entry(path, schema, combiner):
        # TODO: Simplify?
        cursor = newschema
        for i in range(len(path)):
            part = path[i]
            if part == combiner:
                cursor = cursor.setdefault(combiner, [])
                return
            elif isinstance(part, int):
                cursor = cursor.setdefault('items', [])
                while len(cursor) <= part:
                    cursor.append({})
                cursor = cursor[part]
            elif part == 'items':
                cursor = cursor.setdefault('items', OrderedDict())
            else:
                cursor = cursor.setdefault('properties', OrderedDict())
                if i < len(path) - 1 and isinstance(path[i + 1], int):
                    cursor = cursor.setdefault(part, [])
                else:
                    cursor = cursor.setdefault(part, OrderedDict())

        cursor.update(schema)

    def callback(schema, path, combiner, ctx, recurse):
        type = schema.get('type')
        schema = OrderedDict(schema)
        if type == 'object':
            del schema['properties']
        elif type == 'array':
            del schema['items']
        if 'allOf' in schema:
            del schema['allOf']

        add_entry(path, schema, combiner)

    walk_schema(schema, callback)

    return newschema

def read_schema(schema_file, extensions=None):
    """
    Read a schema file from disk in order to pass it as an argument
    to a new datamodel.
    """
    def get_resolver(asdf_file):
        extensions = asdf_file._extensions
        def asdf_file_resolver(uri):
            return extensions._url_mapping(extensions._tag_mapping(uri))
        return asdf_file_resolver

    default_extensions = [GWCSExtension(), JWSTExtension()]

    if extensions is None:
        extensions = default_extensions[:]
    else:
        extensions.extend(default_extensions)
    asdf_file = AsdfFile(extensions=extensions)

    if hasattr(asdf_file, 'resolver'):
        file_resolver = asdf_file.resolver
    else:
        file_resolver = get_resolver(asdf_file)

    schema = asdf_schema.load_schema(schema_file,
                                     resolver=file_resolver,
                                     resolve_references=True)

    schema = merge_property_trees(schema)
    return schema
