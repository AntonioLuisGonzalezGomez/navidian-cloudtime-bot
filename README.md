## Navidian CloudTime Bot

Automated time tracking bot for **Navidian CloudTime**, using **Selenium**, **Docker**, and **cron/manual scheduling**.
Designed for both automated and manual operation with holiday-aware scheduling.

## Features

- Automated daily check-in/check-out on Navidian CloudTime

- Supports telework marking

- Automatic pause/resume after ~4 hours of work

- Dockerized execution using a Selenium Grid (Selenoid)

- Randomized start delay to mimic human behavior

- Holiday-aware execution (customizable list)

- Manual execution via SSH aliases

- Logs all actions with timestamps

- Configurable via environment variables

## Architecture
```
[navidian_bot.py] ---> [Selenium Grid (Selenoid)] ---> [Navidian Web CloudTime]
       ^
       |
  Dockerized bot
       |
   VNC / Remote Debug
```

- The bot runs inside a Docker container (`navidian-bot`)
- Uses Selenoid for browser automation (Chrome/Firefox)
- Can be scheduled via cron or executed manually via SSH

## Installation

1. Clone the repository:

```
   git clone https://github.com/yourusername/navidian-cloudtime-bot.git
   cd navidian-cloudtime-bot`
```
2. Copy .env.example to .env and configure your credentials:

```
   cp .env.example .env`
```

- NAVIDIAN_USER → your Navidian CloudTime username

- NAVIDIAN_PASSWORD → your password

- NAVIDIAN_TELEWORK → y/n (mark telework)

- NAVIDIAN_COMPENSATION → minutes to adjust

- NAVIDIAN_PAUSE → y/n (enable automatic pause)

3. Start Selenoid and the bot:

```
   docker compose up -d selenoid selenoid-ui navidian-bot
```

## Automated Execution (Cron)

The ficharDelayed.sh script accepts the following parameters:

```
ficharDelayed.sh <USER> <PASSWORD> <TELEWORK> [COMPENSATION] [PAUSE]

- <USER> → your Navidian username
- <PASSWORD> → your password
- <TELEWORK> → y if working remotely, n if on-site
- [COMPENSATION] → minutes to adjust the workday (optional)
- [PAUSE] → y/n to enable automatic pause (optional)
````

Example per-day configuration

```
# Monday, Thursday, Friday: remote work
0 8 * * 1,4,5 /omv/scripts/ficharDelayed.sh 33333333A PASSWORD y >> /omv/scripts/cron_logs.txt 2>&1

# Tuesday: on-site work
0 8 * * 2 /omv/scripts/ficharDelayed.sh 33333333A PASSWORD n >> /omv/scripts/cron_logs.txt 2>&1

# Wednesday (optional): choose remote or on-site as needed
0 8 * * 3 /omv/scripts/ficharDelayed.sh 33333333A PASSWORD y >> /omv/scripts/cron_logs.txt 2>&1
```


- Each line corresponds to a **specific day of the week** and can pass a different `<TELEWORK>` value.

- The script includes a **random delay** and a **holiday check**, so it runs safely and automatically.

- Logs are written to `cron_logs.txt` for tracking.


## Manual Execution (SSH Aliases)

Add to your `.bashrc` (or `.zshrc`) as examples:

```
alias navidian-start="ssh user@server docker compose run --rm navidian-bot"
alias navidian-stop="ssh user@server docker stop navidian-bot"
alias navidian-logs="ssh user@server docker logs -f navidian-bot"
alias navidian-logfile="ssh user@server cat /path/to/navidian_logs.txt"
```

- Allows manual start/stop, real-time log viewing, and log inspection.

- Useful for debugging or emergency interventions.

## License

This project is released under the MIT License.
See LICENSE for details.

## Disclaimer

- This tool is provided as-is for educational or internal automation purposes.

- Use at your own risk.

- Respect your company's policies and terms of service of Navidian CloudTime.