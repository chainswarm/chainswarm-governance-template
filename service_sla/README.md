Put one JSON per epoch to enable the Service Miner slice.

Example file name: `service_sla/2025-W33.json`

```json
{
  "hotkey": "5F...service",
  "service_score": 0.96,  // 0..1; must be >= validator threshold (default 0.8)
  "budget": 0.075         // target share (fraction of total emissions)
}
```

If absent or score < threshold, the Service Miner gets 0 for that week.
