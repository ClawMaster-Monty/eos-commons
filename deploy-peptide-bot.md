# Deploy EOS Peptide Calculator Bot — DigitalOcean

## 1. Create Droplet

1. Go to https://digitalocean.com
2. Click **Create** → **Droplets**
3. Choose: **Ubuntu 22.04 LTS** (Standard, $4/mo)
4. Datacenter: San Francisco or closest to you
5. Authentication: **SSH keys** (recommended) or Password
6. Click **Create Droplet**

## 2. SSH into the Droplet

After it's created, DigitalOcean will email you the IP address. Connect:

```bash
ssh root@YOUR_DROPLET_IP
```

## 3. Install Python and Dependencies

```bash
apt update && apt upgrade -y
apt install python3 python3-pip git -y
pip3 install discord.py python-dotenv requests
```

## 4. Create Bot Directory

```bash
mkdir -p /opt/eos-calc
cd /opt/eos-calc
```

## 5. Upload Bot Files

**Option A: GitHub (recommended)**
```bash
git clone https://github.com/ClawMaster-Monty/eos-commons.git
cp eos-commons/Tools/peptide_calc_bot.py /opt/eos-calc/
```

**Option B: Copy-paste directly**
Paste the contents of `peptide_calc_bot.py` into a file:
```bash
nano /opt/eos-calc/peptide_calc_bot.py
# paste contents, Ctrl+X, Y, Enter
```

## 6. Create .env File

```bash
nano /opt/eos-calc/.env
```

Paste these lines with your actual values:
```
PEPTIDE_BOT_TOKEN=YOUR_BOT_TOKEN_HERE
NOTION_API_KEY=YOUR_NOTION_INTEGRATION_TOKEN
NOTION_DATABASE_ID=395cb9eddf5b800a8571c23fd3e6dc41
```

**To get your Notion API key:**
1. Go to https://www.notion.so/my-integrations
2. Click **+ New integration** → name it "EOS Peptide Calc"
3. Select your workspace
4. Copy the **Internal Integration Token**

**To get the Notion Database ID:**
Already have it: `395cb9eddf5b800a8571c23fd3e6dc41`

Save the file: `Ctrl+X`, `Y`, `Enter`

## 7. Create Systemd Service (so it auto-starts)

```bash
nano /etc/systemd/system/eos-calc.service
```

Paste:
```ini
[Unit]
Description=EOS Peptide Calculator Discord Bot
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/eos-calc
ExecStart=/usr/bin/python3 /opt/eos-calc/peptide_calc_bot.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

Save: `Ctrl+X`, `Y`, `Enter`

## 8. Enable and Start

```bash
systemctl daemon-reload
systemctl enable eos-calc
systemctl start eos-calc
```

## 9. Verify It's Running

```bash
systemctl status eos-calc
```

You should see: `Active: active (running)`

## 10. Test the Bot

Go to your Discord server and try:
- `!calc help`
- `!calc klow standard`
- `!calc list`

## 11. View Logs

```bash
journalctl -u eos-calc -f
```

---

## Troubleshooting

**Bot not responding?**
- Check token is correct in `.env`
- Make sure bot is in the server (use the OAuth2 invite URL from Discord Developer Portal)
- Check logs: `journalctl -u eos-calc -f`

**Notion not logging?**
- Make sure the database is shared with your integration
- Verify the integration has access to the database

**Bot goes offline?**
- `systemctl restart eos-calc`
- If server restarts, systemd starts it automatically
