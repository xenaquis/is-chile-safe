#!/usr/bin/env bash
# .github/scripts/fetch-lint-tools.sh — download actionlint + shellcheck into a
# deterministic, gitignored .tools/ directory, verifying SHA-256 against pinned
# checksums. F-85: the session-scoped scratchpad glob used during planning does
# not exist in the executor's or CI's session — this script replaces it with a
# location that is identical every time, on every machine.
# Idempotent: skips the download when both binaries are already present and
# executable.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
TOOLS_DIR="$ROOT/.tools"
mkdir -p "$TOOLS_DIR"

ACTIONLINT_VERSION="1.7.7"
SHELLCHECK_VERSION="0.11.0"

os="$(uname -s)"
case "$os" in
  Linux)
    ACTIONLINT_URL="https://github.com/rhysd/actionlint/releases/download/v${ACTIONLINT_VERSION}/actionlint_${ACTIONLINT_VERSION}_linux_amd64.tar.gz"
    ACTIONLINT_SHA256="023070a287cd8cccd71515fedc843f1985bf96c436b7effaecce67290e7e0757"
    SHELLCHECK_URL="https://github.com/koalaman/shellcheck/releases/download/v${SHELLCHECK_VERSION}/shellcheck-v${SHELLCHECK_VERSION}.linux.x86_64.tar.xz"
    SHELLCHECK_SHA256="8c3be12b05d5c177a04c29e3c78ce89ac86f1595681cab149b65b97c4e227198"
    ACTIONLINT_BIN="$TOOLS_DIR/actionlint"
    SHELLCHECK_BIN="$TOOLS_DIR/shellcheck"
    ;;
  MINGW*|MSYS*|CYGWIN*)
    ACTIONLINT_URL="https://github.com/rhysd/actionlint/releases/download/v${ACTIONLINT_VERSION}/actionlint_${ACTIONLINT_VERSION}_windows_amd64.zip"
    ACTIONLINT_SHA256="7f12f1801bca3d480d67aaf7774f4c2a6359a3ca8eebe382c95c10c9704aa731"
    SHELLCHECK_URL="https://github.com/koalaman/shellcheck/releases/download/v${SHELLCHECK_VERSION}/shellcheck-v${SHELLCHECK_VERSION}.zip"
    SHELLCHECK_SHA256="8a4e35ab0b331c85d73567b12f2a444df187f483e5079ceffa6bda1faa2e740e"
    ACTIONLINT_BIN="$TOOLS_DIR/actionlint.exe"
    SHELLCHECK_BIN="$TOOLS_DIR/shellcheck.exe"
    ;;
  *)
    echo "::error::fetch-lint-tools.sh: unsupported OS '$os' — only Linux (CI) and Windows/git-bash (local) are pinned"
    exit 1
    ;;
esac

if [ -x "$ACTIONLINT_BIN" ] && [ -x "$SHELLCHECK_BIN" ]; then
  echo "lint tools already present and executable in $TOOLS_DIR — skipping download"
  echo "ACTIONLINT_BIN=$ACTIONLINT_BIN"
  echo "SHELLCHECK_BIN=$SHELLCHECK_BIN"
  exit 0
fi

verify_sha256() {
  local file="$1" expected="$2" actual
  actual="$(sha256sum "$file" | cut -d' ' -f1)"
  if [ "$actual" != "$expected" ]; then
    echo "::error::SHA-256 mismatch for $file: expected $expected, got $actual — refusing to install a tampered or corrupted binary"
    exit 1
  fi
}

tmpdir="$(mktemp -d)"
trap 'rm -rf "$tmpdir"' EXIT

echo "downloading actionlint v${ACTIONLINT_VERSION} for $os..."
curl -sL --fail -o "$tmpdir/actionlint.pkg" "$ACTIONLINT_URL"
verify_sha256 "$tmpdir/actionlint.pkg" "$ACTIONLINT_SHA256"

echo "downloading shellcheck v${SHELLCHECK_VERSION} for $os..."
curl -sL --fail -o "$tmpdir/shellcheck.pkg" "$SHELLCHECK_URL"
verify_sha256 "$tmpdir/shellcheck.pkg" "$SHELLCHECK_SHA256"

case "$os" in
  Linux)
    tar -xzf "$tmpdir/actionlint.pkg" -C "$tmpdir" actionlint
    mv "$tmpdir/actionlint" "$ACTIONLINT_BIN"
    tar -xJf "$tmpdir/shellcheck.pkg" -C "$tmpdir"
    mv "$tmpdir/shellcheck-v${SHELLCHECK_VERSION}/shellcheck" "$SHELLCHECK_BIN"
    ;;
  MINGW*|MSYS*|CYGWIN*)
    unzip -oq "$tmpdir/actionlint.pkg" -d "$tmpdir/al" actionlint.exe
    mv "$tmpdir/al/actionlint.exe" "$ACTIONLINT_BIN"
    unzip -oq "$tmpdir/shellcheck.pkg" -d "$tmpdir/sc" shellcheck.exe
    mv "$tmpdir/sc/shellcheck.exe" "$SHELLCHECK_BIN"
    ;;
esac

chmod +x "$ACTIONLINT_BIN" "$SHELLCHECK_BIN"

[ -x "$ACTIONLINT_BIN" ] || { echo "::error::actionlint install failed, not executable at $ACTIONLINT_BIN"; exit 1; }
[ -x "$SHELLCHECK_BIN" ] || { echo "::error::shellcheck install failed, not executable at $SHELLCHECK_BIN"; exit 1; }

echo "lint tools installed and SHA-256-verified in $TOOLS_DIR"
echo "ACTIONLINT_BIN=$ACTIONLINT_BIN"
echo "SHELLCHECK_BIN=$SHELLCHECK_BIN"
