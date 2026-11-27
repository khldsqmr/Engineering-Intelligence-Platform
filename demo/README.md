# EIP Demonstration Snapshot

This directory contains a bundled historical dataset derived
from public Apache Airflow GitHub activity.

- `snapshot.json.gz`: compressed analytical snapshot.
- `manifest.json`: provenance, coverage, record counts,
  checksum and pseudonymization metadata.

The snapshot contains derived Gold records, ingestion
metadata and historical AI intelligence executions.

Raw Bronze observations and Silver records are excluded.
Contributor identifiers are pseudonymized, but retained
public PR identifiers prevent complete anonymization.

Historical AI outputs retain their original evaluation
records, including approved and rejected executions.

The default Docker deployment restores this snapshot
automatically into a dedicated persistent database.

Manual initialization from the repository root:

```bash
python -m backend.pipelines.demo_bootstrap --database data/eip_demo.db
```

The initializer validates snapshot integrity and preserves
an existing valid database.

See the root NOTES.md for design decisions and limitations.
