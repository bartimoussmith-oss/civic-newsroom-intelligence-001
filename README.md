# Civic Newsroom intelligence data host 001

Dedicated public host for generated retrieval indexes and explicitly unreviewed analytical candidates from 6,065 public normalized representations. Source records stay in civic-newsroom-data-001. The website stays in civic-newsroom.

## Publication contract

A committed intelligence-publication.json is the release descriptor. Its immutable base URL and collection hash identify the generated collection. collection.json hashes files.json; files.json specifies the parts, encodings, lengths and encoded/decoded SHA-256 hashes for each logical file. Verify and concatenate parts, decode gzip only when specified, and verify the decoded logical hash before parsing. Logical .jsonl.gz files retain their original gzip format after reconstruction. Concatenate the database parts listed in collection.json and decompress the resulting gzip stream; database_sha256 identifies the SQLite file. The dedicated host enforces 45 MiB physical files and 512 MiB of derived generations. Existing generations are never deleted or overwritten to make room; allocate a new approved host if the cumulative budget is exhausted. This does not change the main repository's 256 MiB budget.

## Reproducibility and status

The workflow pins engine/packaging code at 18efc5218131792fb311493d4678b700c4d8d71a and source data at 2465245db04551c42f748a85fc151b869d246649, dataset build-40279333802. source-publication.json is a snapshot of the source descriptor fields needed for integrity verification, restored only in the runner's local checkout. All source bytes, record count, SQLite integrity, logical reconstruction and representative evidence retrieval are checked before publication. Status is recorded in status/build.json. No publication descriptor means no successful data release is claimed.

The host workflow runs on its own code changes or manual dispatch. Its scoped Actions token writes only to this repository. It neither edits source repositories nor changes Pages settings or website data pointers. Website integration is a separate reviewed change after a verified data publication.

These are generated representations and literal analytical candidates, not independent-source certification, semantic search, verified entities, verified obligations, legal findings or complete historical coverage. A successful workflow does not establish Google indexing or AI Mode inclusion.
