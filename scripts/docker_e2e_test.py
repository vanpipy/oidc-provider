import os
import subprocess
import sys
import time
from urllib.request import urlopen


def _wait_for_server_ready(base_url: str, timeout_seconds: float = 30.0) -> None:
  deadline = time.time() + timeout_seconds
  url = f"{base_url}/.well-known/openid-configuration"
  last_error: Exception | None = None
  while time.time() < deadline:
    try:
      response = urlopen(url, timeout=1.0)
      if response.getcode() < 500:
        return
      last_error = RuntimeError(f"unexpected status {response.getcode()}")
    except Exception as exc:
      last_error = exc
    time.sleep(0.5)
  if last_error is None:
    last_error = RuntimeError("server did not become ready in time")
  raise last_error


def main() -> None:
  image = os.getenv("OIDC_IMAGE", "oidc-provider")
  container_name = os.getenv("OIDC_CONTAINER_NAME", "oidc-provider-e2e")
  base_url = os.getenv("E2E_BASE_URL", "http://127.0.0.1:8001")
  port_mapping = os.getenv("E2E_PORT_MAPPING", "8001:8000")

  run_args = [
    "docker",
    "run",
    "--rm",
    "-d",
    "--name",
    container_name,
    "-p",
    port_mapping,
    "-e",
    "DATABASE_URL=sqlite:////app/app.db",
    "-e",
    f"OIDC_ISSUER_URL={base_url}",
    image,
  ]

  container_started = False
  try:
    subprocess.check_call(run_args)
    container_started = True
    subprocess.check_call(
      [
        "docker",
        "exec",
        container_name,
        "python",
        "-m",
        "app.cli",
        "seed_demo",
      ]
    )
    _wait_for_server_ready(base_url)
    os.environ["E2E_MODE"] = "external"
    os.environ["E2E_BASE_URL"] = base_url
    import pytest

    exit_code = pytest.main(["-q", "e2e"])
    raise SystemExit(exit_code)
  finally:
    if container_started:
      try:
        subprocess.run(
          ["docker", "stop", container_name],
          check=True,
          stdout=subprocess.PIPE,
          stderr=subprocess.PIPE,
          text=True,
        )
      except subprocess.CalledProcessError as exc:
        print(f"failed to stop container {container_name}: {exc}", file=sys.stderr)


if __name__ == "__main__":
  main()
