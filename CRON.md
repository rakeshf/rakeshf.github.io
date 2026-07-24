# Installing the update cronjob

1. Make the helper script executable:

```
chmod +x scripts/update_data.sh
```

2. Edit `deploy/update-data.cron` and replace `/absolute/path/to/repo` with the absolute path to this repository on the server (for example `/home/ubuntu/rakeshf.github.io`).

3. Install the crontab (as the user who should run the jobs):

```
crontab deploy/update-data.cron
```

Or edit the current user's crontab manually with `crontab -e` and paste the single cron line from `deploy/update-data.cron`.

4. Logs:

- Job wrapper log: `logs/scripts/cron_wrapper.log`
- Detailed script output: `logs/scripts/update_data.log`

5. Test manually before installing:

```
/usr/bin/env bash scripts/update_data.sh
```

Notes:
- Adjust the schedule in `deploy/update-data.cron` as required. Use `crontab.guru` to help craft schedules.
- If your scripts require a virtualenv or specific environment variables, modify `scripts/update_data.sh` to activate the environment before running the Python scripts.

**GitHub Actions**

You can run the update on GitHub using the scheduled workflow at `.github/workflows/update-data.yml`. It runs every 30 minutes on working days (Monday–Friday) between 09:15 and 15:15 Asia/Kolkata (IST) and can also be triggered manually via `workflow_dispatch`.

Notes:
- The workflow checks out the repository, runs `scripts/update_data.sh`, and commits any changed files back to the repo using the default `GITHUB_TOKEN`.
- The workflow schedule is specified in UTC (GitHub Actions). The IST window 09:15–15:15 corresponds to 03:45–09:45 UTC. The cron entries used are:
  - `45 3 * * 1-5`        (03:45 UTC => 09:15 IST)
  - `15,45 4-8 * * 1-5`  (04:15–08:45 UTC => 09:45–14:15 IST)
  - `15,45 9 * * 1-5`    (09:15,09:45 UTC => 14:45,15:15 IST)
- Weekly cleanup runs from `.github/workflows/weekly-data-cleanup.yml` every Monday at 08:30 IST (`0 3 * * 1` UTC). It deletes generated files in `data/` and recreates `data/index.json` as an empty list.
- Darvas Box and Golden Cross data refresh runs from `.github/workflows/update-screeners.yml` daily at 14:00 IST (`30 8 * * *` UTC). It regenerates `data/darvas_breakouts.json` and `data/golden_cross.json`.
- If your scripts require dependencies or a virtual environment, update the workflow to install them (for example, add `pip install -r requirements.txt`).
- GitHub Actions runs on UTC for scheduled cron triggers.
