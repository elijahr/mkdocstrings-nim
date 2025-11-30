## A simple test module for documentation extraction.
##
## This module contains examples of procs, types, and constants.

const
  MaxSize* = 100  ## Maximum allowed size

type
  MyObject* = object
    ## A simple object type.
    name*: string  ## The name field
    value*: int    ## The value field

proc greet*(name: string): string =
  ## Greet someone by name.
  ##
  ## :param name: The name to greet
  ## :returns: A greeting message
  result = "Hello, " & name & "!"

proc add*(a, b: int): int {.inline.} =
  ## Add two integers.
  ##
  ## :param a: First number
  ## :param b: Second number
  ## :returns: Sum of a and b
  result = a + b
