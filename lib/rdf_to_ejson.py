import simplejson
import httplib2
import rdflib
import hashlib
import sys, os

__version__ = "0.2"

_RDF_TYPE = u"http://www.w3.org/1999/02/22-rdf-syntax-ns#type"
_RDFS_LABEL = "label" # "http://www.w3.org/2000/01/rdf-schema#label"
_SKOS_PREFLABEL = "prefLabel" # "http://www.w3.org/2004/02/skos/core#prefLabel"

# Converts rdflib URIRefs to Exhibit property names. Assumes unique names.
# NOTE that for consistent naming, an rdflib Graph needs to return the
# triples in a consistent order, otherwise the "winner" (who gets to use
# the unhyphenated short name) will vary between runs. Not sure what
# rdflib guarantees here but works so far.
PROP_TRANSLATE = lambda x: os.path.basename(x.rstrip("/")).rpartition("#")[2]

# Track the properties and types for inclusion in output
_EXHIBIT_PROPS = {}
_EXHIBIT_TYPES = {}

# Example label builder for an "Employee" resource type
EXAMPLE_LABEL_BUILDER = {
    "Employee": lambda r: " ".join((r.get("lastName"),r.get("firstName")))
}

# Mapping from XSD type to Exhibit valueType. Augment as required
DEFAULT_LITERAL_TYPE_MAP = {
    "http://www.w3.org/2001/XMLSchema#decimal": "number",
    "http://www.w3.org/2001/XMLSchema#integer": "number",
    "http://www.w3.org/2001/XMLSchema#boolean": "boolean",
    "http://www.w3.org/2001/XMLSchema#dateTime": "date",
    "http://www.w3.org/2001/XMLSchema#string": "text",
}

def _add_property(_p,p,_o,used,is_item=False):
    """
    Add a new property to the dict of existing properties, performing
    conflict detection and correction.
    """
    orig_p = p
    if p in used:
        if not used[p] == unicode(_p):
            p = _rename_property(p,unicode(_p))

    prop = {
        "uri": unicode(_p)
    }
    if is_item:
        prop["valueType"] = "item"
    else:
        if hasattr(_o,"datatype"):
            #print >> sys.stderr,repr((_o,_o.datatype))
            vt = DEFAULT_LITERAL_TYPE_MAP.get(str(_o.datatype))
            if vt:
                prop["valueType"] = vt

    used[p] = unicode(_p)
    _EXHIBIT_PROPS[p] = prop

    return p

def _add_type(_p,p,used):
    """
    Add new exhibit type in a similar way to properties
    """
    orig_p = p
    if p in used:
        if not used[p] == unicode(_p):
            p = _rename_property(p,unicode(_p))

    prop = {
        "uri": unicode(_p)
    }

    used[p] = unicode(_p)
    _EXHIBIT_TYPES[p] = prop

    return p

def _rename_property(p,_p):
    """
    Return a new short name for p based on the original p as well as
    part of a hash of the full URI of the property (for repeatability)
    """
    return "%s-%s"%(p,hashlib.md5(_p).hexdigest().upper()[:4])

def convert(graph,label_builder={},literal_type_map=DEFAULT_LITERAL_TYPE_MAP):
    """
    Convert RDF into Exhibit JSON... well actually just a Python data structure
    that can be serialized to JSON, in case you need to manipulate it prior to
    that step.

    Arguments:
    graph -- the source, an rdflib.Graph instance
    label_builder -- dict mapping a type short name to a function returning the label
        given the resource as an argument. See SAMPLE_LABEL_BUILDER above.
    literal_type_map -- dict mapping from any source literal type to an Exhibit valueType
    """

    used_props = {}
    used_types = {}

    # Build resources in a dict keyed by their short name ...
    keyed_resources = {}
    for (_s,_p,_o) in graph:
        (s,p,o) = PROP_TRANSLATE(unicode(_s)), PROP_TRANSLATE(unicode(_p)), unicode(_o)

        # Looks up whether the object is used as a subject in the graph and so
        # needs to be typed as an Exhibit item
        try:
            graph.triples((_o,None,None)).next()
            is_item = True
        except StopIteration:
            is_item = False

        p = _add_property(_p,p,_o,used_props,is_item)

        if s not in keyed_resources:
            keyed_resources[s] = { "id": s }

        new_o = PROP_TRANSLATE(o)
        if unicode(_p) == _RDF_TYPE:
            new_o = _add_type(o,new_o,used_types)

        # Check for existing properties of this resource, and if a dup,
        # create or update value as a list
        if p in keyed_resources[s]:
            if isinstance(keyed_resources[s][p],list):
                keyed_resources[s][p].append(new_o)
            else:
                keyed_resources[s][p] = [keyed_resources[s][p], new_o]
        else:
            keyed_resources[s][p] = new_o

    # Second pass for label extraction
    resources = keyed_resources.values()
    for r in resources:

        # FIXME use of short name as key makes label detection ambiguous.
        # May want to 
        if "label" in r:
            label = r["label"]
        else:
            label = None
            rtype = r.get("type")
            if rtype:
                if isinstance(rtype,list):
                    rtype = rtype[0] # FIXME pick first non-null label?
                label_func = label_builder.get(rtype)
                if label_func:
                    label = label_func(r)

            if isinstance(label,list): label = label[0]

        r["label"] = label or r["id"]

    return {"items": resources,
            "types": _EXHIBIT_TYPES,
            "properties": _EXHIBIT_PROPS}

if __name__ == "__main__":
    graph = rdflib.Graph()
    graph.load(sys.argv[1],format=sys.argv[2])
    exhibit = convert(graph)

    print simplejson.dumps(exhibit,indent=4)
