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

You can run the update on GitHub using a scheduled workflow. A sample workflow has been added at `.github/workflows/update-data.yml`. It runs every 15 minutes on working days (Monday–Friday) between 09:15 and 15:00 Asia/Kolkata (IST) by default and can also be triggered manually via `workflow_dispatch`.

Notes:
- The workflow checks out the repository, runs `scripts/update_data.sh`, and commits any changed files back to the repo using the default `GITHUB_TOKEN`.
- The workflow schedule is specified in UTC (GitHub Actions). The IST window 09:15–15:00 corresponds to 03:45–09:30 UTC. The cron entries used are:
  - `45 3 * * 1-5`        (03:45 UTC => 09:15 IST)
  - `*/15 4-8 * * 1-5`   (04:00–08:59 UTC => 09:30–14:59 IST)
  - `0,15,30 9 * * 1-5`  (09:00,09:15,09:30 UTC => 14:30,14:45,15:00 IST)
- If your scripts require dependencies or a virtual environment, update the workflow to install them (for example, add `pip install -r requirements.txt`).
- GitHub Actions runs on UTC for scheduled cron triggers.

