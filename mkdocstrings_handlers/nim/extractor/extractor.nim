## AST extraction logic for nimdocinfo
import std/[json, strutils, sequtils, os]
import compiler/[ast, parser, idents, options, pathutils, lineinfos, msgs, renderer, llstream]

type
  DocEntry* = object
    name*: string
    kind*: string
    line*: int
    signature*: string
    params*: seq[tuple[name, typ: string]]
    returns*: string
    pragmas*: seq[string]
    raises*: seq[string]
    doc*: string
    exported*: bool  ## True if symbol has * (public API)

  ModuleDoc* = object
    module*: string
    file*: string
    doc*: string
    entries*: seq[DocEntry]

proc extractDocComment(n: PNode): string =
  ## Extract doc comment from a node
  if n == nil:
    return ""
  if n.comment.len > 0:
    return n.comment.strip
  return ""

proc extractPragmas(n: PNode): seq[string] =
  ## Extract pragma names from a pragma node
  result = @[]
  if n == nil or n.kind != nkPragma:
    return
  for child in n:
    if child.kind == nkIdent:
      result.add($child.ident.s)
    elif child.kind == nkExprColonExpr and child[0].kind == nkIdent:
      result.add($child[0].ident.s)

proc extractRaises(n: PNode): seq[string] =
  ## Extract exception types from raises pragma
  ## e.g., {.raises: [ValueError, IOError].}
  result = @[]
  if n == nil or n.kind != nkPragma:
    return
  for child in n:
    if child.kind == nkExprColonExpr and child.len >= 2:
      if child[0].kind == nkIdent and $child[0].ident.s == "raises":
        let bracket = child[1]
        if bracket.kind == nkBracket:
          for exc in bracket:
            if exc.kind == nkIdent:
              result.add($exc.ident.s)
            elif exc.kind == nkDotExpr:
              # Handle qualified names like system.Exception
              result.add($exc)

proc extractParams(n: PNode): seq[tuple[name, typ: string]] =
  ## Extract parameter list from formal params
  result = @[]
  if n == nil or n.kind != nkFormalParams:
    return
  # Skip first child (return type)
  for i in 1..<n.len:
    let param = n[i]
    if param.kind == nkIdentDefs:
      let typNode = param[^2]
      let typStr = if typNode.kind == nkEmpty: "auto" else: $typNode
      # All names except last two (type and default)
      for j in 0..<param.len - 2:
        if param[j].kind == nkIdent:
          result.add(($param[j].ident.s, typStr))

proc extractReturnType(n: PNode): string =
  ## Extract return type from formal params
  if n == nil or n.kind != nkFormalParams or n.len == 0:
    return ""
  let retNode = n[0]
  if retNode.kind == nkEmpty:
    return ""
  return $retNode

const
  # Nim AST indices for routine (proc/func/etc) nodes
  routineNameIdx = 0
  routinePatternIdx = 1
  routineGenericParamsIdx = 2
  routineParamsIdx = 3
  routinePragmasIdx = 4
  routineBodyIdx = 6

proc renderSignature(n: PNode, kind: string, name: string): string =
  ## Render full signature as string
  result = kind & " " & name
  if n.len > routineParamsIdx and n[routineParamsIdx].kind == nkFormalParams:
    let params = n[routineParamsIdx]
    var paramStrs: seq[string] = @[]
    for i in 1..<params.len:
      paramStrs.add($params[i])
    result &= "(" & paramStrs.join("; ") & ")"
    let ret = extractReturnType(n[routineParamsIdx])
    if ret.len > 0:
      result &= ": " & ret

proc isExported(n: PNode): bool =
  ## Check if a name node represents an exported symbol (has *)
  n.kind == nkPostfix

proc extractName(n: PNode): string =
  ## Extract name from a name node (handles postfix for exported symbols)
  if n.kind == nkIdent:
    return $n.ident.s
  elif n.kind == nkPostfix and n.len >= 2 and n[1].kind == nkIdent:
    return $n[1].ident.s
  elif n.kind == nkPostfix and n.len >= 2 and n[1].kind == nkAccQuoted:
    # Handle quoted operators like `+`*
    if n[1].len > 0 and n[1][0].kind == nkIdent:
      return $n[1][0].ident.s
  return ""

proc extractProcDoc(n: PNode): string =
  ## Extract doc comment from a proc definition
  ## The doc comment can be on the proc node itself or on the first statement in the body
  result = extractDocComment(n)
  if result.len == 0 and n.len > routineBodyIdx:
    let body = n[routineBodyIdx]
    if body != nil and body.kind == nkStmtList and body.len > 0:
      # Check if first statement has a comment
      result = extractDocComment(body[0])
      if result.len == 0 and body[0].kind == nkCommentStmt:
        result = body[0].comment.strip

proc extractProc(n: PNode, kind: string): DocEntry =
  ## Extract documentation from a proc/func/etc definition
  result.name = extractName(n[routineNameIdx])
  result.kind = kind
  result.line = n.info.line.int
  result.doc = extractProcDoc(n)
  result.exported = isExported(n[routineNameIdx])

  if n.len > routineParamsIdx:
    result.params = extractParams(n[routineParamsIdx])
    result.returns = extractReturnType(n[routineParamsIdx])

  # Extract pragmas at the correct index
  if n.len > routinePragmasIdx and n[routinePragmasIdx].kind == nkPragma:
    result.pragmas = extractPragmas(n[routinePragmasIdx])
    result.raises = extractRaises(n[routinePragmasIdx])

  result.signature = renderSignature(n, kind, result.name)

proc extractType(n: PNode): DocEntry =
  ## Extract documentation from a type definition
  result.kind = "type"
  result.doc = extractDocComment(n)
  result.line = n.info.line.int
  result.name = extractName(n[0])
  result.exported = isExported(n[0])
  result.signature = "type " & result.name

proc extractConst(n: PNode): DocEntry =
  ## Extract documentation from a const definition
  result.kind = "const"
  result.doc = extractDocComment(n)
  result.line = n.info.line.int
  result.name = extractName(n[0])
  result.exported = isExported(n[0])
  result.signature = "const " & result.name

proc walkAst(n: PNode, entries: var seq[DocEntry]) =
  ## Walk AST and collect documentation entries
  if n == nil:
    return

  case n.kind
  of nkProcDef:
    entries.add extractProc(n, "proc")
  of nkFuncDef:
    entries.add extractProc(n, "func")
  of nkIteratorDef:
    entries.add extractProc(n, "iterator")
  of nkTemplateDef:
    entries.add extractProc(n, "template")
  of nkMacroDef:
    entries.add extractProc(n, "macro")
  of nkTypeDef:
    entries.add extractType(n)
  of nkConstDef:
    entries.add extractConst(n)
  else:
    for child in n:
      walkAst(child, entries)

proc extractModule*(filepath: string): ModuleDoc =
  ## Extract all documentation from a Nim source file
  result.file = filepath
  result.module = filepath.splitFile.name
  result.entries = @[]

  # Parse the file
  var conf = newConfigRef()
  conf.verbosity = 0

  let fileIdx = fileInfoIdx(conf, AbsoluteFile(filepath))
  var parser: Parser

  let source = readFile(filepath)
  openParser(parser, fileIdx, llStreamOpen(source), newIdentCache(), conf)

  let ast = parseAll(parser)
  closeParser(parser)

  # Extract module doc comment
  if ast.len > 0 and ast[0].comment.len > 0:
    result.doc = ast[0].comment.strip

  walkAst(ast, result.entries)

proc toJson*(doc: ModuleDoc): JsonNode =
  ## Convert module documentation to JSON
  result = %*{
    "module": doc.module,
    "file": doc.file,
    "doc": doc.doc,
    "entries": []
  }

  for entry in doc.entries:
    var entryJson = %*{
      "name": entry.name,
      "kind": entry.kind,
      "line": entry.line,
      "signature": entry.signature,
      "doc": entry.doc,
      "exported": entry.exported
    }

    if entry.params.len > 0:
      entryJson["params"] = %entry.params.mapIt(%*{"name": it.name, "type": it.typ})

    if entry.returns.len > 0:
      entryJson["returns"] = %entry.returns

    if entry.pragmas.len > 0:
      entryJson["pragmas"] = %entry.pragmas

    if entry.raises.len > 0:
      entryJson["raises"] = %entry.raises

    result["entries"].add entryJson
