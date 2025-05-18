import pandas as pd
import smtplib
import json
import time
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
from tqdm import tqdm
import os
import re
import argparse
from jinja2 import Template
import concurrent.futures
import glob
from email.mime.application import MIMEApplication


# Load environment variables from .env file
load_dotenv()

def load_config(config_path):
    """Load configuration from a JSON file."""
    with open(config_path, "r") as f:
        return json.load(f)

def load_email_list_data(filepath):
    """Load email list data from a CSV file."""
    return pd.read_csv(filepath, dtype=str)

def is_valid_email(email):
    """Simple regex to validate email format."""
    return bool(re.match(r"[^@]+@[^@]+\.[^@]+", email))

def get_attachment_files(prefix, attachment_dir, allow_multiple_attachments):
    """Return matching .zip files from attachment_dir that start with prefix."""
    pattern = os.path.join(attachment_dir, f"{prefix}*.zip")
    matches = sorted(glob.glob(pattern))  # Sorted for consistent ordering
    if not allow_multiple_attachments and matches:
        return [matches[0]]
    return matches

# def send_email(smtp_server, smtp_port, sender_email, sender_password, recipient_email, cc_emails, subject, body):
#     """Send email using the SMTP server."""
#     msg = MIMEMultipart()
#     msg['From'] = sender_email
#     msg['To'] = recipient_email
#     msg['Subject'] = subject

#     if cc_emails:
#         msg['Cc'] = ", ".join(cc_emails)

#     msg.attach(MIMEText(body, 'html'))

#     recipients = [recipient_email] + cc_emails if cc_emails else [recipient_email]

#     with smtplib.SMTP(smtp_server, smtp_port, timeout=10) as server:
#         server.starttls()
#         server.login(sender_email, sender_password)
#         server.sendmail(sender_email, recipients, msg.as_string())

def send_email(smtp_server, smtp_port, sender_email, sender_password, recipient_email, cc_emails, subject, body, attachments=None):
    """Send email with optional attachments using the SMTP server."""
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = recipient_email
    msg['Subject'] = subject

    if cc_emails:
        msg['Cc'] = ", ".join(cc_emails)

    msg.attach(MIMEText(body, 'html'))

    # Attach files
    if attachments:
        for filepath in attachments:
            try:
                with open(filepath, "rb") as f:
                    part = MIMEApplication(f.read(), Name=os.path.basename(filepath))
                    part['Content-Disposition'] = f'attachment; filename="{os.path.basename(filepath)}"'
                    msg.attach(part)
            except Exception as e:
                print(f"Failed to attach file {filepath}: {e}")
                raise

    recipients = [recipient_email] + cc_emails if cc_emails else [recipient_email]

    with smtplib.SMTP(smtp_server, smtp_port, timeout=10) as server:
        server.starttls()
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, recipients, msg.as_string())


# def send_email_in_batch(smtp_server, smtp_port, sender_email, sender_password, recipients, cc_emails, subject, body):
#     """Send emails concurrently using multiple threads."""
#     with concurrent.futures.ThreadPoolExecutor() as executor:
#         futures = []
#         for recipient in recipients:
#             futures.append(executor.submit(send_email, smtp_server, smtp_port, sender_email, sender_password, recipient, cc_emails, subject, body))
        
#         # Wait for all futures to complete
#         concurrent.futures.wait(futures)
#         #print(f"Sent emails to {len(recipients)} recipients concurrently.")

# def retry_send_email(smtp_server, smtp_port, sender_email, sender_password, recipients, cc_emails, subject, body, retries=3, delay=5):
#     """Retry email sending logic."""
#     attempt = 0
#     while attempt < retries:
#         try:
#             send_email_in_batch(smtp_server, smtp_port, sender_email, sender_password, recipients, cc_emails, subject, body)
#             return
#         except Exception as e:
#             attempt += 1
#             print(f"Error sending email: {e}. Retrying... {attempt}/{retries}")
#             time.sleep(delay)
    
#     print(f"Failed to send email to {recipients} after {retries} attempts.")

def send_email_in_batch(smtp_server, smtp_port, sender_email, sender_password, recipients, cc_emails, subject, body, attachments=None):
    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = []
        for recipient in recipients:
            futures.append(executor.submit(send_email, smtp_server, smtp_port, sender_email, sender_password, recipient, cc_emails, subject, body, attachments))
        concurrent.futures.wait(futures)

def retry_send_email(smtp_server, smtp_port, sender_email, sender_password, recipients, cc_emails, subject, body, retries=3, delay=5, attachments=None):
    attempt = 0
    while attempt < retries:
        try:
            send_email_in_batch(smtp_server, smtp_port, sender_email, sender_password, recipients, cc_emails, subject, body, attachments)
            return
        except Exception as e:
            attempt += 1
            print(f"Error sending email: {e}. Retrying... {attempt}/{retries}")
            time.sleep(delay)
    print(f"Failed to send email to {recipients} after {retries} attempts.")


def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="SwarmSend - A Bulk Email Tool")
    parser.add_argument(
        '--config',
        type=str,
        default='config.json',
        help='Path to the configuration file'
    )
    return parser.parse_args()

def render_template(template_str, context):
    """Render a Jinja2 template with the given context."""
    template = Template(template_str)
    return template.render(**context)

def load_template(template_dir, template_filename):
    """Load the HTML template file content."""
    template_path = os.path.join(template_dir, template_filename)
    with open(template_path, 'r', encoding='utf-8') as f:
        return f.read()

def main():
    """Main function to load config and run the script."""
    args = parse_args()

    script_dir = os.path.dirname(os.path.abspath(__file__))
    config_dir = os.path.join(script_dir, '..', 'config')
    data_dir = os.path.join(script_dir, '..', 'data')
    logs_dir = os.path.join(script_dir, '..', 'logs')
    templates_dir = os.path.join(script_dir, '..', 'templates')

    config_path = os.path.join(config_dir, args.config)

    try:
        config = load_config(config_path)
    except FileNotFoundError:
        print(f"Error: Configuration file '{args.config}' not found.")
        return
    except json.JSONDecodeError:
        print(f"Error: Failed to parse '{args.config}' as JSON.")
        return

    smtp_server = os.getenv("SMTP_SERVER")
    smtp_port = int(os.getenv("SMTP_PORT"))
    sender_email = os.getenv("SMTP_USER")
    sender_password = os.getenv("SMTP_PASSWORD")

    file_path = os.path.join(data_dir, config["csv_file_path"])
    df = load_email_list_data(file_path)

    subject_template = config["subject"]
    message_template_filename = config["template"]  # Get the template filename from config
    cc_emails = config.get("cc", [])
    placeholders = config.get("placeholders", [])

    if isinstance(cc_emails, str):
        cc_emails = [cc_emails]

    delay_seconds = config.get("delay_seconds", 0)
    log_file = config.get("log_file", "email_log.csv")
    batch_size = config.get("batch_size", 50)  # Get batch size from config

    # Load selected email template
    try:
        message_template = load_template(templates_dir, message_template_filename)
    except FileNotFoundError:
        print(f"Error: Template file '{message_template_filename}' not found in templates directory.")
        return

    if not os.path.exists(logs_dir):
        os.makedirs(logs_dir)

    log = []

    # Loop through list and send emails in batches
    for batch_start in tqdm(range(0, len(df), batch_size), desc="Sending emails in batches"):
        batch_end = min(batch_start + batch_size, len(df))
        batch = df.iloc[batch_start:batch_end]

        recipients = batch['email'].tolist()

        # Skip invalid emails
        valid_recipients = [email for email in recipients if is_valid_email(email)]

        if not valid_recipients:
            continue

        # Loop through batch to create and send emails
        for _, row in batch.iterrows():
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            email_addr = row.get('email', 'UNKNOWN')

            if any(pd.isna(row.get(field)) for field in placeholders):
                log.append({
                    "timestamp": timestamp,
                    "email": email_addr,
                    "status": "Skipped",
                    "error_message": "Missing required fields"
                })
                continue

            try:
                context = row.to_dict()

                subject = render_template(subject_template, context)
                message = render_template(message_template, context)

                #retry_send_email(smtp_server, smtp_port, sender_email, sender_password, [email_addr], cc_emails, subject, message)
                
                attachments_cfg = config.get("attachments", {})
                attachments = []
                if attachments_cfg.get("enabled", False):
                    attachment_dir = os.path.join(data_dir, attachments_cfg.get("directory", "attachments"))
                    allow_multiple = attachments_cfg.get("allow_multiple", False)
                    #prefix = row.get("attachment_prefix", row.get("district", ""))  # fallback to 'district' column
                    prefix_key = attachments_cfg.get("use_prefix_from", "attachment_prefix")
                    prefix = row.get(prefix_key, "")
                    attachments = get_attachment_files(prefix, attachment_dir, allow_multiple)

                    # Skip if no attachment found
                    if not attachments:
                        log.append({
                            "timestamp": timestamp,
                            "email": email_addr,
                            "status": "Skipped",
                            "error_message": f"No attachment found for prefix '{prefix}'"
                        })
                        continue


                # Now pass attachments to send_email (via retry_send_email)
                retry_send_email(smtp_server, smtp_port, sender_email, sender_password, [email_addr], cc_emails, subject, message, attachments=attachments)

                log.append({
                    "timestamp": timestamp,
                    "email": email_addr,
                    "status": "Success",
                    "error_message": ""
                })
            except Exception as e:
                log.append({
                    "timestamp": timestamp,
                    "email": email_addr,
                    "status": "Failed",
                    "error_message": str(e)
                })

            if delay_seconds > 0:
                time.sleep(delay_seconds)

    timestamp_str = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    log_filename = f"email_log_{timestamp_str}.csv"
    log_path = os.path.join(logs_dir, log_filename)
    pd.DataFrame(log).to_csv(log_path, index=False)
    print(f"📄 Log saved to {log_path}")

if __name__ == "__main__":
    main()
