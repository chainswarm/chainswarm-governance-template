# Bittensor KOTH — GitHub-first Monorepo

**Simple rules:**
- Owner writes requirements (`requirements/R-#####.yaml`).
- Miners register once in `registry/miners/*.yaml` (GitHub ↔ hotkey).
- Miners open **one PR per requirement per epoch** and paste hotkey + signature in the PR.
- Only **merged PRs** count for that epoch.
- Validators are “dumb”: they verify CI artifacts and compute weights weekly.

**Epoch clock (Europe/Warsaw):**
- Build: Mon 00:00 → Fri 18:00
- Freeze: Fri 18:00 (any push after rolls to next epoch)
- Snapshot: Sun 18:00
- Weight compute: Sun 18:10

**Service Miner (optional):**
- A fixed small slice for infra uptime (SLA), published in `service_sla/{epoch}.json`.

Repos with topic `koth-enabled` are scanned by governance (this monorepo should have it).
