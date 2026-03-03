---
name: rabby-wallet-backup
description: Use when the user wants to back up their Rabby wallet address book (named wallet addresses) from the Chrome extension to a local file.
---

# Rabby Wallet Address Book Backup

## Overview

Rabby Wallet stores the address book (named wallet addresses) in a LevelDB database inside Chrome's extension storage. Because Chrome holds a lock on the database, you must copy it first before reading.

## Steps

### 1. Locate the LevelDB directory

The extension ID for Rabby Wallet is `acmacodkjbdgmoleebolmdjonilkdbch`.

```bash
ls ~/Library/Application\ Support/Google/Chrome/Default/Local\ Extension\ Settings/acmacodkjbdgmoleebolmdjonilkdbch/
```

### 2. Copy the database (Chrome holds a lock)

```bash
cp -r ~/Library/Application\ Support/Google/Chrome/Default/Local\ Extension\ Settings/acmacodkjbdgmoleebolmdjonilkdbch /tmp/rabby-db-copy
rm /tmp/rabby-db-copy/LOCK
```

### 3. Set up a Node.js LevelDB reader

```bash
mkdir -p /tmp/leveldb-reader
cd /tmp/leveldb-reader
npm init -y
npm install level
```

### 4. Read and export the address book

```javascript
// /tmp/leveldb-reader/backup.js
const { Level } = require('level')
const fs = require('fs')

async function main() {
  const db = new Level('/tmp/rabby-db-copy', { valueEncoding: 'utf8', keyEncoding: 'utf8' })
  await db.open()

  const raw = await db.get('contactBook')
  const contacts = JSON.parse(raw)
  const entries = Object.values(contacts)

  // JSON backup
  const json = entries.map(e => ({ address: e.address, name: e.name || '' }))
  fs.writeFileSync('/Users/YOUR_USERNAME/Documents/Rabby Backup/wallet-addresses-backup.json', JSON.stringify(json, null, 2))

  // CSV backup
  let csv = 'Name,Address\n'
  for (const e of entries.sort((a, b) => (a.name || '').localeCompare(b.name || ''))) {
    csv += `"${(e.name || '').replace(/,/g, ';')}","${e.address}"\n`
  }
  fs.writeFileSync('/Users/YOUR_USERNAME/Documents/Rabby Backup/wallet-addresses-backup.csv', csv)

  console.log(`Backed up ${entries.length} addresses.`)
  await db.close()
}

main().catch(console.error)
```

```bash
mkdir -p ~/Documents/Rabby\ Backup
node /tmp/leveldb-reader/backup.js
```

### 5. Clean up

```bash
rm -rf /tmp/rabby-db-copy /tmp/leveldb-reader
```

## Output

- `~/Documents/Rabby Backup/wallet-addresses-backup.json` — structured list of `{ name, address }`
- `~/Documents/Rabby Backup/wallet-addresses-backup.csv` — spreadsheet-friendly, sorted by name

## Notes

- The `contactBook` key stores **named/aliased addresses only** — not private keys or seed phrases.
- If Chrome is closed, you can skip the copy step and read directly from the extension settings directory (but you still need to remove or ignore the LOCK file).
- Other Chrome profiles (Profile 1, Profile 2, etc.) have their own extension storage directories — check them if the Default profile is empty.

## Quick Reference

| Step | Command |
|------|---------|
| Find extension dir | `ls ~/Library/.../Local Extension Settings/acmacodkjbdgmoleebolmdjonilkdbch/` |
| Copy DB | `cp -r <dir> /tmp/rabby-db-copy && rm /tmp/rabby-db-copy/LOCK` |
| Install reader | `cd /tmp/leveldb-reader && npm init -y && npm install level` |
| Read key | `db.get('contactBook')` |
| Clean up | `rm -rf /tmp/rabby-db-copy /tmp/leveldb-reader` |
