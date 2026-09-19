# 🌦️ Germany Weather Reporter & Email Dispatcher

An automated Python tool that fetches live weather forecasts for Germany (or any city) using the [Open-Meteo API](https://open-meteo.com) and automatically sends formatted HTML and plain-text weather reports to your inbox via Gmail SMTP.

---

## ✨ Features

- **🇩🇪 Germany Overview**: Displays current weather for 8 major German cities (Berlin, Munich, Hamburg, Frankfurt, Cologne, Stuttgart, Düsseldorf, Leipzig) with parallel multi-threading for fast response times.
- **🔍 Custom City Search**: Lookup any city in Germany or worldwide by passing it as a command line argument (e.g., `python germany.py Berlin`).
- **📧 Automated Email Reports**: Sends a responsive HTML email table and plain-text summary via SMTP.
- **🛡️ Secure Configuration**: Supports `.env` files to prevent credentials from being exposed.
- **🪟 Cross-Platform Console**: Handles UTF-8 console output for emojis and special characters on Windows and Linux.
- **⏰ Scheduled GitHub Actions (IST)**: Automated daily reports at 08:00 AM IST via GitHub Actions.

---

## 🚀 Getting Started

### 1. Prerequisites
Make sure you have Python 3.7+ installed.

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure Credentials
Copy the example environment file:
```bash
cp .env.example .env
```
Open `.env` and fill in your details:
```ini
SENDER_EMAIL=your_email@gmail.com
SENDER_PASSWORD=your_16_digit_app_password
RECEIVER_EMAIL=recipient_email@gmail.com
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
```

> **Note on Gmail:** You need a 16-character [Google App Password](https://myaccount.google.com/apppasswords) with 2-Step Verification enabled.

---

## 💻 Usage

### Run Germany Overview:
```bash
python germany.py
```

### Search a Specific City:
```bash
python germany.py Munich
```
or
```bash
python germany.py "Frankfurt am Main"
```
