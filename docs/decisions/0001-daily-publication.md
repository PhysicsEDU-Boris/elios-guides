# 0001 — Daily guide publication

Accepted, 8 November 2026. Owner authorized the daily feed and backend setup.

Keep the existing Gemini → Claude/Figma → export pipeline. Research runs daily at 03:00 WIB;
the owner confirmed the existing Claude task already runs daily at 05:00 WIB.
GitHub Pages serves public static assets; no Firebase write credential or new server is needed.

Successful exports invoke a reusable publishing workflow. Publishing revalidates content and sources,
rejects examples, empty fact-checks, mismatched languages, symlinks, invalid PDFs and covers, then copies
only EN/ID JSON, PDF and PNG assets. It never runs issue-supplied code. The published branch preserves
archive files and the newest 365 catalogue entries without merging PRs or changing main.
Research reads that archive so publication is not dependent on guide PR merges.

Use GitHub Actions Pages deployment with serialized publication and no cancellation mid-deploy.
A failed run retains the last live deployment. A daily 08:00 WIB check reports a missing issue via
Actions failure notifications. Human review can still reject educational quality missed by automated checks.
Asset hashes invalidate corrected PDF caches while issue dates keep progress stable.

The default-branch schedules require owner merge of the automation PR. Existing account secrets,
Claude/Figma scheduling and GitHub notification preferences are not stored in the repository.
