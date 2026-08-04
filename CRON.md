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

You can run the update on GitHub using the scheduled workflow at `.github/workflows/update-data.yml`. It runs 5 times on working days (Monday-Friday) during Indian market hours and can also be triggered manually via `workflow_dispatch`.

Notes:
- The workflow checks out the repository, runs `scripts/update_data.sh`, and commits any changed files back to the repo using the default `GITHUB_TOKEN`. This frequent workflow only runs `scripts/screener.py`, which generates timestamped files like `data/2026-07-07T13-38-33.json` and updates `data/index.json`.
- If one or more symbols fail during a run, `scripts/screener.py` skips those symbols and still writes JSON for the successful symbols. The workflow fails only when no symbol data can be generated.
- The workflow schedule is specified in UTC (GitHub Actions). The cron entries intentionally avoid top-of-hour times because GitHub scheduled workflows can be delayed or skipped when many repositories run at the same minute. The cron entries used are:
  - `5 4,9 * * 1-5` (04:05,09:05 UTC => 09:35,14:35 IST)
  - `10 5 * * 1-5` (05:10 UTC => 10:40 IST)
  - `15 6 * * 1-5` (06:15 UTC => 11:45 IST)
  - `35 7 * * 1-5` (07:35 UTC => 13:05 IST)
- Monthly cleanup runs from `.github/workflows/monthly-data-cleanup.yml` on the first day of each month at 08:30 IST (`0 3 1 * *` UTC). It deletes generated files in `data/` and recreates `data/index.json` as an empty list.
- Darvas Box and Golden Cross data refresh runs from `.github/workflows/update-screeners.yml` daily at 14:00 IST (`30 8 * * *` UTC). It regenerates `data/darvas_breakouts.json` and `data/golden_cross.json`.
- If your scripts require dependencies or a virtual environment, update the workflow to install them (for example, add `pip install -r requirements.txt`).
- GitHub Actions runs on UTC for scheduled cron triggers.
