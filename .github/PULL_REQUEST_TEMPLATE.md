### Requirement
R-ID: R-00001

### Miner Identity
- GitHub: @your-handle
- Hotkey (SS58): `5F...`
- Nonce (hex, 32 bytes): `0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef`
- Signature (ed25519 over `nonce || hotkey` base64): `...`

> **Note:** You must have a merged file in `registry/miners/` mapping your GitHub to this hotkey before Sunday 18:00 (Warsaw) or you won’t receive emissions.

### Checklist
- [ ] CI green
- [ ] Acceptance checks pass
- [ ] Tests added/updated
- [ ] Lint/static clean
