"""
SSL Certificate Verification Helper for NinjaOne API & OAuth.

- Injects native Windows Certificate Store via `truststore` (supports corporate SSL inspection / local CAs)
- Provides configurable SSL verification (supports disabling verification for debugging or enterprise proxy MITM)
"""

from __future__ import annotations

import os
import urllib3

# Automatically inject Windows Certificate Store into Python standard ssl library
try:
    import truststore
    truststore.inject_into_ssl()
except Exception:
    pass


def get_ssl_verify() -> bool | str:
    """
    Returns the `verify` argument for requests:
    - False: SSL verification explicitly disabled in .env / settings
    - str: Path to a custom enterprise CA bundle file
    - True: Standard verification (utilizing Windows truststore / certifi)
    """
    verify_env = os.getenv("NINJA_SSL_VERIFY", "true").strip()
    if verify_env.lower() in ("false", "0", "no", "off", "disable", "disabled"):
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        return False
    elif os.path.exists(verify_env):
        return verify_env
    return True
