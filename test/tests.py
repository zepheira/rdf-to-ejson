from rdf_to_ejson import convert
import rdflib
from StringIO import StringIO
import simplejson as json

# deep_eq from https://gist.github.com/samuraisam/901117
import datetime, time, functools, operator, types
 
default_fudge = datetime.timedelta(seconds=0, microseconds=0, days=0)
 
def deep_eq(_v1, _v2, datetime_fudge=default_fudge, _assert=False):
  """
  Tests for deep equality between two python data structures recursing 
  into sub-structures if necessary. Works with all python types including
  iterators and generators. This function was dreampt up to test API responses
  but could be used for anything. Be careful. With deeply nested structures
  you may blow the stack.
  
  Options:
            datetime_fudge => this is a datetime.timedelta object which, when
                              comparing dates, will accept values that differ
                              by the number of seconds specified
            _assert        => passing yes for this will raise an assertion error
                              when values do not match, instead of returning 
                              false (very useful in combination with pdb)
  """
  _deep_eq = functools.partial(deep_eq, datetime_fudge=datetime_fudge, 
                               _assert=_assert)
  
  def _check_assert(R, a, b, reason=''):
    if _assert and not R:
      assert 0, "an assertion has failed in deep_eq (%s) %s != %s" % (
        reason, str(a), str(b))
    return R
  
  def _deep_dict_eq(d1, d2):
    k1, k2 = (sorted(d1.keys()), sorted(d2.keys()))
    if k1 != k2: # keys should be exactly equal
      return _check_assert(False, k1, k2, "keys")
    
    return _check_assert(operator.eq(sum(_deep_eq(d1[k], d2[k]) 
                                       for k in k1), 
                                     len(k1)), d1, d2, "dictionaries")
  
  def _deep_iter_eq(l1, l2):
    if len(l1) != len(l2):
      return _check_assert(False, l1, l2, "lengths")
    return _check_assert(operator.eq(sum(_deep_eq(v1, v2) 
                                      for v1, v2 in zip(l1, l2)), 
                                     len(l1)), l1, l2, "iterables")
  
  def op(a, b):
    _op = operator.eq
    if type(a) == datetime.datetime and type(b) == datetime.datetime:
      s = datetime_fudge.seconds
      t1, t2 = (time.mktime(a.timetuple()), time.mktime(b.timetuple()))
      l = t1 - t2
      l = -l if l > 0 else l
      return _check_assert((-s if s > 0 else s) <= l, a, b, "dates")
    return _check_assert(_op(a, b), a, b, "values")
 
  c1, c2 = (_v1, _v2)
  
  # guard against strings because they are iterable and their
  # elements yield iterables infinitely. 
  # I N C E P T I O N
  for t in types.StringTypes:
    if isinstance(_v1, t):
      break
  else:
    if isinstance(_v1, types.DictType):
      op = _deep_dict_eq
    else:
      try:
        c1, c2 = (list(iter(_v1)), list(iter(_v2)))
      except TypeError:
        c1, c2 = _v1, _v2
      else:
        op = _deep_iter_eq
  
  return op(c1, c2)

#####################################
# TESTS START HERE

# Label builder for all these tests
LABEL_BUILDER = {
    "Employee": lambda r: " ".join((r.get("lastName"),r.get("firstName"))),
    "Customer": lambda r: r.get("name"),
    "Location": lambda r: r.get("address"),
}

TESTS = [] # list of (format, input, expected output) tuples

#
# valueType=item detection for two linked resources
#
TESTS.append(( "turtle",
"""
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix type: <http://example.com/types/> .
@prefix customer: <http://example.com/customers/> .
@prefix props: <http://example.com/props/> .
@prefix location: <http://example.com/location/> .

customer:99999 rdf:type type:Customer ;
  props:name "John Smith" ;
  props:location location:88888 .

location:88888 rdf:type type:Location ;
  rdf:type type:Location ;
  props:address "99 River Lane" .
""",
{
    "items": [
        {
            "label": "John Smith",
            "type": "Customer",
            "id": "99999",
            "name": "John Smith",
            "location": "88888"
        },
        {
            "label": "99 River Lane",
            "type": "Location",
            "id": "88888",
            "address": "99 River Lane"
        }
    ],
    "properties": {
        "type": {
            "uri": "http://www.w3.org/1999/02/22-rdf-syntax-ns#type"
        },
        "location": {
            "valueType": "item",
            "uri": "http://example.com/props/location"
        },
        "name": {
            "uri": "http://example.com/props/name"
        },
        "address": {
            "uri": "http://example.com/props/address"
        }
    },
    "types": {
        "Customer": {
            "uri": "http://example.com/types/Customer"
        },
        "Location": {
            "uri": "http://example.com/types/Location"
        }
    }
}
))

def test_all():
    for t in TESTS:
        graph = rdflib.Graph()
        graph.load(StringIO(t[1]),format=t[0])

        output = convert(graph,label_builder=LABEL_BUILDER)
        assert deep_eq(t[2],output), "Converted output was:\n"+json.dumps(output,indent=4)
