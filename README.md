# 🐝 SwarmSend

**SwarmSend** is a lightweight, configurable bulk email tool designed to send personalized messages (like credentials, notices, or invites) using CSV data. With flexible templating, CC support, and environment-based secrets, it's perfect for organizations looking to streamline communication at scale.

---

## 🚀 Features

- 📧 Bulk Email Sending — Easily send personalized emails to multiple recipients.
- 🧩 Dynamic Subject & Message Templates — Supports {placeholders} in both the subject and body for dynamic content.
- 🧠 Customizable via config.json — Configure batch size, delay between emails, and email templates.
- 📩 Supports Multiple CC Recipients — Add multiple recipients in the CC field for each email.
- 🔒 Environment-Based Credentials — SMTP details loaded securely via the .env file.
- ⏳ Send Delay — Optionally add delays between sending emails to prevent server throttling.
- 📊 Email Sending Logs — Logs sent and failed emails for auditing, with timestamps, success/failure status, and error messages.
- ⚙️ Batch Processing — Process large email lists efficiently by splitting them into batches, optimizing email delivery.
- ⚡ Concurrency Support — Uses multi-threading to send emails concurrently within batches, improving performance.

---

## 📦 Project Structure
swarm-send/
├── config/
│   └── config.json           # Main configuration file
├── data/
│   └── email_list.csv        # List with email contacts
├── src/
│   └── swarm-send.py         # Core logic for sending emails
├── logs/                     # Stores email deliveries log files
│   └── email_log_*.csv       # Logs of email sending attempts (success/failure).
├── .env                      # Environment file for sensitive data like SMTP credentials
├── README.md                 
└── requirements.txt          # Python dependencies for the project

## ⚙️ Requirements
Python 3.9+

## 🛠️ Installation
1. Clone the repository:
git clone https://github.com/moonsglw/swarm-send.git

2. Navigate to the project directory:
cd swarm-send

3. Create a virtual environment (recommended) and activate:
python -m venv venv

4. Install the required dependencies:
pip install -r requirements.txt

## 🔑 Configuration
To get started, you need to configure your SMTP credentials and email settings.

1. Create a .env file in the root directory with the following content:
SMTP_SERVER=smtp.example.com
SMTP_PORT=587
SMTP_USER=your_email@example.com
SMTP_PASSWORD=your_smtp_password

2. Configure the config.json file to set your email templates and CSV file settings:
{
    "subject": "Welcome {{ firstName }} to SwarmSend!",
    "cc": ["another@example.com"],
    "csv_file_path": "email_list.csv",
    "template": "sample_email.html",
    "placeholders": [
        "username",
        "firstName",
        "lastName",
        "password"
    ],
    "delay_seconds": 1,
    "log_file": "email_log.csv",
    "batch_size": 50
}

- subject: can include placeholders, like {firstName}, which will be replaced by data from the CSV file.
- cc: allows you to specify any CC recipients.
- csv_file_path: specifies the path to your email CSV.
- template: html file containing the template for the message body.
- placeholders: column headers from csv to be included in email content.
- delay_seconds: delay time between emails.
- log_file: specifies the path to email log.
- batch_size: specifies the number of recipients to send to batched up

## 📝 Usage
To send emails:

1. Populate email_list.csv with your contents (with column headers)
2. Create your own template html file and paste it in the templates directory
3. Update config.json or just create your own custom config file and paste it in the config folder
4. Run the following command to send the emails:
python src/swarm-send.py

(if using custom config file)
python src/swarm-send.py --config custom_config.json

## 🔍 Logging and Debugging
Logs are stored in the logs/ directory, including both successful and failed email deliveries.
You can configure log levels in the config.json to control verbosity.

## 🛡️ License
SwarmSend is licensed under the MIT License. See the LICENSE file for more details.