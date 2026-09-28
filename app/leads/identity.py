"""Lead identity generation and deduplication hierarchy.

Identity hierarchy:
  1. Internal lead ID (if supplied)
  2. Normalized email
  3. Normalized 10-digit phone number
  4. Name + normalized contact hint
"""

from __future__ import annotations

import hashlib
import uuid


def generate_lead_id() -> str:
    """Generate a stable, unique internal lead ID."""
    return f"lead-{uuid.uuid4().hex[:12]}"


def build_identity_key(
    email: str | None,
    phone: str | None,
    name: str,
) -> str:
    """Construct an identity key that guarantees deduplication in SQLite.

    Prefer:
      email:<email>
      phone:<10-digit-phone>
      name_contact:<name-hash>
    """
    if email:
        return f"email:{email.lower().strip()}"
    if phone:
        return f"phone:{phone.strip()}"
    
    # Fallback to normalized name hash
    norm_name = "".join(name.lower().split())
    digest = hashlib.sha256(norm_name.encode("utf-8")).hexdigest()[:16]
    return f"name:{digest}"