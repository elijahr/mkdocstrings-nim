## A sample library for testing mkdocstrings-nim.
##
## This module demonstrates documentation generation.

const
  Version* = "1.0.0"  ## Library version

type
  Config* = object
    ## Configuration settings.
    name*: string  ## Config name
    debug*: bool   ## Debug mode flag

proc initialize*(cfg: Config): bool =
  ## Initialize the library with given config.
  ##
  ## :param cfg: Configuration to use
  ## :returns: True if successful
  result = true

proc process*(data: string; count: int = 1): seq[string] {.inline.} =
  ## Process data and return results.
  ##
  ## :param data: Input data to process
  ## :param count: Number of times to process
  ## :returns: Processed results
  ## :raises ValueError: If data is empty
  result = @[data]
