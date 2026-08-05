#!/usr/bin/env bash
# canary-script.sh (SEC-05, FM-06)
#
# Deliberately DIRTY fixture — committed on purpose. Exhibits the bare
# xtrace/command-echo risk shape (shape 2) check-secret-hygiene.sh must
# detect. Never fix this line; the gate's own canary pass depends on it
# staying exactly as written. Excluded from the real-tree scan by directory
# path, scanned first as its own pass.
set -x
echo "canary script body — not executed by any real workflow"
