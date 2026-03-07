---
name: openclaw-vm-wireguard-vpn
description: Use when an openclaw VM is getting HTTP 403 errors from Anthropic API due to geographic IP restrictions, or when setting up ProtonVPN WireGuard on an Ubuntu VM running openclaw in Docker so API traffic routes through a non-restricted region.
---

# OpenClaw VM: ProtonVPN WireGuard Setup

## Overview

Anthropic blocks API access from certain regions (HK, some Asian IPs). The fix is routing Docker container traffic through ProtonVPN WireGuard with `Table = off` to avoid breaking SSH and LAN connectivity.

**Why not Cloudflare WARP:** WARP routes through the nearest Cloudflare PoP — for a HK VM this stays in Asia and doesn't bypass the geo-block. ProtonVPN has explicit US servers.

## Prerequisites

- Ubuntu 22.04+ VM
- ProtonVPN free account (proton.me) — US-FREE servers are sufficient
- Root/sudo access
- WireGuard config file from ProtonVPN dashboard (`.conf` format, not `.ovpn`)

## Step 1 — Install WireGuard

```bash
sudo apt-get install -y wireguard
```

## Step 2 — Get ProtonVPN WireGuard Config

1. Log in to proton.me → VPN → Downloads → WireGuard configuration
2. Select a **US-FREE** server
3. Download the `.conf` file (open the file and note the endpoint IP)

## Step 3 — Create WireGuard Config with `Table = off`

Copy to `/etc/wireguard/proton.conf` — **critical**: use `Table = off` and manual route rules to avoid breaking SSH:

```ini
[Interface]
PrivateKey = <your-private-key>
Address = <tunnel-ip>/32
Table = off
PostUp = ip route add <endpoint-ip>/32 via <lan-gateway> dev <lan-iface>; ip route add default dev %i
PreDown = ip route del default dev %i; ip route del <endpoint-ip>/32 via <lan-gateway> dev <lan-iface>

[Peer]
PublicKey = <server-public-key>
AllowedIPs = 0.0.0.0/0
Endpoint = <endpoint-ip>:<port>
PersistentKeepalive = 25
```

Replace:
- `<endpoint-ip>` — the VPN server IP from `Endpoint =` line (e.g. `37.19.199.149`)
- `<lan-gateway>` — your LAN gateway (e.g. `192.168.50.1` — find with `ip route show default`)
- `<lan-iface>` — your LAN interface (e.g. `ens3` — find with `ip route show default`)

**Why `Table = off`:** Without it, WireGuard replaces the routing table entirely. The `ip route add` in PostUp sets only two routes: one host route to the VPN endpoint (so the tunnel can reach the internet), plus a default route through the tunnel for everything else — SSH and LAN stay on the original path.

## Step 4 — Remove IPv6 (if needed)

If WireGuard fails to start, remove IPv6 parts:
- Remove any `Address` line with `::` (e.g. `2a07:b944::.../128`)
- Remove `::/0` from `AllowedIPs`

Verify kernel IPv6 tunnel support: `modprobe ip6_tunnel` — if it fails, IPv6 tunneling is unsupported.

## Step 5 — Bring Up and Test

```bash
# Start WireGuard
sudo wg-quick up proton

# Verify tunnel is up
sudo wg show

# Verify default route goes through proton interface
ip route show default

# Verify Docker containers exit through VPN
docker exec openclaw-gateway curl -s https://ipinfo.io/ip
# Should return a ProtonVPN US IP, not your local IP
```

## Step 6 — Enable Auto-Start on Boot

```bash
# Enable WireGuard service
sudo systemctl enable wg-quick@proton

# Make Docker start AFTER WireGuard (so containers get the VPN route at boot)
sudo mkdir -p /etc/systemd/system/docker.service.d
cat << 'EOF' | sudo tee /etc/systemd/system/docker.service.d/wg-before-docker.conf
[Unit]
After=wg-quick@proton.service
Wants=wg-quick@proton.service
EOF
sudo systemctl daemon-reload
```

## Verification

```bash
# Check services
sudo systemctl status wg-quick@proton

# Check external IP seen by Docker
docker exec openclaw-gateway curl -s https://ipinfo.io/json | python3 -m json.tool
# country should be "US"
```

## Common Mistakes

| Mistake | Symptom | Fix |
|---------|---------|-----|
| No `Table = off` | SSH drops immediately after `wg-quick up` | Bring down: `sudo wg-quick down proton` (use Synology console if SSH is gone) |
| Forgot endpoint host route in PostUp | Tunnel can't reach VPN server | Add `ip route add <endpoint-ip>/32 via <lan-gateway> dev <lan-iface>` |
| IPv6 in config but kernel lacks support | `wg-quick up` fails | Remove `2a07::/128` address and `::/0` from AllowedIPs |
| Cloudflare WARP nftables conflict | `table inet cloudflare-warp` blocks SSH | Stop/disable WARP: `sudo systemctl stop warp-svc && sudo systemctl disable warp-svc` |
| Running `sudo nft flush ruleset` | Docker loses internet (no NAT rules) | **NEVER do this.** Docker creates its rules in nftables; flushing breaks Docker networking. Recovery: `sudo systemctl restart docker`, then `docker network connect openclaw_default openclaw-gateway` |
| Interface already exists on retry | `wg-quick up` fails: "already exists" | `sudo ip link delete proton` then retry |
| Docker not restarted after WireGuard | Containers use old routes | `cd ~/openclaw && docker compose restart` |

## Recovery: If SSH Drops

1. Access VM via Synology Virtual Machine Manager console (or physical access)
2. `sudo wg-quick down proton` — removes VPN routes, restores normal routing
3. Fix the config and retry

## Updating the VPN Server

ProtonVPN free servers rotate. To switch:
1. Download new `.conf` from ProtonVPN dashboard
2. `sudo wg-quick down proton`
3. Replace `/etc/wireguard/proton.conf`
4. `sudo wg-quick up proton`
5. Verify with `docker exec openclaw-gateway curl -s https://ipinfo.io/ip`
