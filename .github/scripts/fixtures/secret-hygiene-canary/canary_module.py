"""canary_module.py (SEC-05, FM-06)

Deliberately DIRTY fixture -- committed on purpose. Exhibits the
botocore-DEBUG log-hygiene risk shape (shape 4) check-secret-hygiene.sh
must detect. Never fix this line; the gate's own canary pass depends on it
staying exactly as written. Excluded from the real-tree pipeline/*.py scan
by directory path, scanned first as its own pass.
"""
import logging

logging.basicConfig(level=logging.DEBUG)
