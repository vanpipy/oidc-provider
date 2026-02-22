def normalize_scope(scope: str | None) -> str:
  if not scope:
    return "openid"
  parts = [p for p in scope.split() if p]
  if "openid" not in parts:
    parts.append("openid")
  seen = set()
  normalized = []
  for p in parts:
    if p not in seen:
      seen.add(p)
      normalized.append(p)
  return " ".join(normalized)

