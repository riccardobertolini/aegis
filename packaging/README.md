# Aegis Packaging

Tools for building offline/air-gapped installer bundles.

## Scripts (to be implemented in later phases)

- `build_wheelhouse.sh` — download all Python wheels on a connected machine
- `build_node_offline.sh` — package node_modules for offline install
- `bundle.sh` — assemble full distributable archive
- `install.sh` — offline installer for target machine

## Assumptions

- Target OS: Linux x86_64 (primary), Windows 10+ (secondary)
- Python 3.11+ must be pre-installed on target machine
- Node 18+ must be pre-installed on target machine (or bundled)
