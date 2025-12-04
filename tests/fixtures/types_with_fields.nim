## Test module with various type definitions for field extraction testing.

type
  SimpleObject* = object
    ## A simple object with public fields.
    x*: int      ## X coordinate
    y*: int      ## Y coordinate
    z: float     ## Z coordinate (private)

type
  RefCounter* = ref object
    ## A reference-counted counter.
    count*: int  ## Current count value
    max: int     ## Maximum allowed (private)

type
  Color* = enum
    ## Basic colors.
    Red = 0,     ## The color red
    Green = 1,   ## The color green
    Blue = 2     ## The color blue

type
  NodeKind* = enum
    nkInt, nkFloat, nkString

type
  Node* = object
    ## A variant object for AST nodes.
    case kind*: NodeKind  ## The node kind
    of nkInt:
      intVal*: int        ## Integer value
    of nkFloat:
      floatVal*: float    ## Float value
    of nkString:
      strVal*: string     ## String value

type
  Empty* = object
    ## An empty object with no fields.

type
  Generic*[T] = object
    ## A generic container.
    value*: T    ## The contained value
    count*: int  ## Item count
