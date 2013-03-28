RDF-to-EJSON
============

Convert RDF into Exhibit JSON

Description
-----------

Subjects from the provided graph are itemized, each considered a separate Exhibit resource.

Property names are constructed from (rdflib.URIRef) predicates using the last non-empty string segment.  For example, "http://example.org/foo/bar" becomes "bar", and "http://example.org/foo/bar#baz" becomes "baz".

When a new property name is determined to conflict with an existing one, the new is modified to include a suffix comprised of a four character partial hash of its full URI, providing repeatability of naming so that your Exhibits won't have to change. For example, the second "name" property may become "name-F029".

The arguments to rdf_to_ejson are;

 * graph; the rdflib.Graph instance comprising the graph to be serialized
 * label_builder; a dict mapping a resource type short name to a function returning the label given the resource as an argument. For example;

    EXAMPLE_LABEL_BUILDER = {
        "Employee": lambda r: " ".join((r.get("lastName"),r.get("firstName")))
    }
 * literal_type_map; a dict mapping from RDF literal types to Exhibit valueTypes. The mapping used by default is provided in DEFAULT_LITERAL_TYPE_MAP

The output is a python data structure suitable for conversion to JSON using your favourite JSON serialization module

Future Work
-----------

 * ASAP; id conflict management
 * key off full URI instead of property short name for label building, literal type map (and innards)
 * owl:sameAs merging
 * default label builder with support for known labels (rdfs, skos)
 * manage (e.g. optionally remove) disconnected resources or subgraphs
