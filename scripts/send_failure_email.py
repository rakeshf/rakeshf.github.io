import os
import smtplib
import ssl
from email.message import EmailMessage


required_settings = (
    "ALERT_SMTP_HOST",
    "ALERT_SMTP_PORT",
    "ALERT_SMTP_USERNAME",
    "ALERT_SMTP_PASSWORD",
    "ALERT_EMAIL_TO",
)
missing_settings = [name for name in required_settings if not os.environ.get(name)]
if missing_settings:
    raise SystemExit(
        "Failure email not sent; configure GitHub Actions secrets: "
        + ", ".join(missing_settings)
    )

repository = os.environ["GITHUB_REPOSITORY"]
run_url = (
    f"{os.environ['GITHUB_SERVER_URL']}/{repository}/actions/runs/"
    f"{os.environ['GITHUB_RUN_ID']}"
)

message = EmailMessage()
message["Subject"] = f"Market data workflow failed: {repository}"
message["From"] = os.environ["ALERT_SMTP_USERNAME"]
message["To"] = os.environ["ALERT_EMAIL_TO"]
message.set_content(
    "The market-data workflow failed while generating data, updating index.json, "
    "committing the output, or deploying the site.\n\n"
    f"Workflow: {os.environ['GITHUB_WORKFLOW']}\n"
    f"Event: {os.environ['GITHUB_EVENT_NAME']}\n"
    f"Branch: {os.environ['GITHUB_REF_NAME']}\n"
    f"Commit: {os.environ['GITHUB_SHA']}\n"
    f"Run: {run_url}\n"
)

with smtplib.SMTP(
    os.environ["ALERT_SMTP_HOST"],
    int(os.environ["ALERT_SMTP_PORT"]),
    timeout=30,
) as server:
    server.starttls(context=ssl.create_default_context())
    server.login(
        os.environ["ALERT_SMTP_USERNAME"],
        os.environ["ALERT_SMTP_PASSWORD"],
    )
    server.send_message(message)