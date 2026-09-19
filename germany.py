import os
import smtplib
import sys
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import requests

# Fix Windows console UTF-8 output
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# Load .env configuration if present
_env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
if os.path.exists(_env_path):
    with open(_env_path, "r", encoding="utf-8") as _f:
        for _line in _f:
            _line = _line.strip()
            if _line and not _line.startswith("#") and "=" in _line:
                _k, _v = _line.split("=", 1)
                os.environ.setdefault(_k.strip(), _v.strip().strip("\"'"))

# ==============================================================================
# EMAIL CONFIGURATION (Gmail)
# Credentials are read from .env file or environment variables to protect secrets
# ==============================================================================
SENDER_EMAIL = os.getenv("SENDER_EMAIL", "your_email@gmail.com")
SENDER_PASSWORD = os.getenv("SENDER_PASSWORD", "your_app_password_here")
RECEIVER_EMAIL = os.getenv("RECEIVER_EMAIL", "receiver_email@example.com")

SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))

# ==============================================================================
# WEATHER DATA CONFIGURATION
# ==============================================================================
WMO_WEATHER_CODES = {
    0: ("Clear sky", "☀️"),
    1: ("Mainly clear", "🌤️"),
    2: ("Partly cloudy", "⛅"),
    3: ("Overcast", "☁️"),
    45: ("Fog", "🌫️"),
    48: ("Depositing rime fog", "🌫️"),
    51: ("Light drizzle", "🌦️"),
    53: ("Moderate drizzle", "🌦️"),
    55: ("Dense drizzle", "🌧️"),
    61: ("Slight rain", "🌦️"),
    63: ("Moderate rain", "🌧️"),
    65: ("Heavy rain", "🌧️"),
    71: ("Slight snow fall", "🌨️"),
    73: ("Moderate snow fall", "🌨️"),
    75: ("Heavy snow fall", "❄️"),
    77: ("Snow grains", "❄️"),
    80: ("Slight rain showers", "🌦️"),
    81: ("Moderate rain showers", "🌧️"),
    82: ("Violent rain showers", "⛈️"),
    85: ("Slight snow showers", "🌨️"),
    86: ("Heavy snow showers", "❄️"),
    95: ("Thunderstorm", "⛈️"),
    96: ("Thunderstorm with slight hail", "⛈️"),
    99: ("Thunderstorm with heavy hail", "⛈️"),
}

GERMAN_CITIES = {
    "Berlin (Capital)": {"lat": 52.5200, "lon": 13.4050},
    "Munich": {"lat": 48.1351, "lon": 11.5820},
    "Hamburg": {"lat": 53.5511, "lon": 9.9937},
    "Frankfurt": {"lat": 50.1109, "lon": 8.6821},
    "Cologne": {"lat": 50.9375, "lon": 6.9603},
    "Stuttgart": {"lat": 48.7758, "lon": 9.1829},
    "Düsseldorf": {"lat": 51.2277, "lon": 6.7735},
    "Leipzig": {"lat": 51.3397, "lon": 12.3731},
}


def get_weather_description(code):
    return WMO_WEATHER_CODES.get(code, ("Unknown", "🌡️"))


def fetch_weather(lat, lon):
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "current": "temperature_2m,relative_humidity_2m,apparent_temperature,precipitation,weather_code,wind_speed_10m",
        "timezone": "auto",
    }
    response = requests.get(url, params=params, timeout=10)
    response.raise_for_status()
    return response.json()


def search_city(city_name):
    url = "https://geocoding-api.open-meteo.com/v1/search"
    params = {
        "name": city_name,
        "count": 5,
        "language": "en",
        "format": "json",
    }
    response = requests.get(url, params=params, timeout=10)
    response.raise_for_status()
    data = response.json()
    results = data.get("results", [])

    for result in results:
        if result.get("country_code", "").upper() == "DE":
            return result
    return results[0] if results else None


# ==============================================================================
# EMAIL GENERATION & SENDING
# ==============================================================================
def send_weather_email(subject, html_body, text_body):
    # Check if credentials are still placeholder
    is_placeholder = (
        not SENDER_EMAIL
        or not RECEIVER_EMAIL
        or not SENDER_PASSWORD
        or "your_email" in SENDER_EMAIL
        or "receiver_email" in RECEIVER_EMAIL
        or "your_app_password" in SENDER_PASSWORD
    )

    if is_placeholder:
        print("\n" + "!" * 72)
        print("  [!] EMAIL NOT SENT: Sender / Receiver credentials are not configured!")
        print("  " + "-" * 68)
        print("  To send weather emails directly to your inbox, open 'germany.py'")
        print("  and set your credentials at lines 20-22:")
        print(f"    SENDER_EMAIL    = \"your_actual_email@gmail.com\"")
        print(f"    SENDER_PASSWORD = \"your_16_digit_app_password\"")
        print(f"    RECEIVER_EMAIL  = \"your_recipient_email@gmail.com\"")
        print("  " + "-" * 68)
        print("  Note: For Gmail, use an App Password (not your normal password):")
        print("        https://myaccount.google.com/apppasswords")
        print("!" * 72 + "\n")
        return False

    print(f"\nDispatching weather report email to '{RECEIVER_EMAIL}'...")
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = SENDER_EMAIL
        msg["To"] = RECEIVER_EMAIL

        part_text = MIMEText(text_body, "plain", "utf-8")
        part_html = MIMEText(html_body, "html", "utf-8")
        msg.attach(part_text)
        msg.attach(part_html)

        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT, timeout=15) as server:
            server.starttls()
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.sendmail(SENDER_EMAIL, RECEIVER_EMAIL, msg.as_string())

        print(f"  [✓] SUCCESS: Weather report email delivered to {RECEIVER_EMAIL}!\n")
        return True
    except smtplib.SMTPAuthenticationError:
        print("\n" + "!" * 72)
        print("  [✗] AUTHENTICATION FAILED: Incorrect email address or App Password.")
        print("  For Gmail:")
        print("    1. Enable 2-Step Verification on your Google Account.")
        print("    2. Generate an App Password: https://myaccount.google.com/apppasswords")
        print("    3. Paste the 16-letter code into SENDER_PASSWORD.")
        print("!" * 72 + "\n")
        return False
    except Exception as e:
        print(f"\n  [✗] Failed to send email: {e}\n")
        return False


def build_html_overview(data_list):
    timestamp = datetime.now().strftime("%A, %d %B %Y - %H:%M")
    rows = ""
    for item in data_list:
        rows += f"""
        <tr style="border-bottom: 1px solid #e5e7eb;">
            <td style="padding: 12px 14px; font-weight: 600; color: #111827;">{item['city']}</td>
            <td style="padding: 12px 14px; color: #374151;">{item['emoji']} {item['condition']}</td>
            <td style="padding: 12px 14px; font-weight: 700; color: #2563eb;">{item['temp']}</td>
            <td style="padding: 12px 14px; color: #6b7280;">{item['feels_like']}</td>
            <td style="padding: 12px 14px; color: #6b7280;">{item['humidity']}</td>
            <td style="padding: 12px 14px; color: #6b7280;">{item['wind']}</td>
        </tr>
        """

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #f3f4f6; margin: 0; padding: 24px; }}
            .card {{ max-width: 680px; margin: 0 auto; background: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1); }}
            .header {{ background: linear-gradient(135deg, #1e3a8a, #2563eb); color: white; padding: 26px 20px; text-align: center; }}
            .header h1 {{ margin: 0 0 6px 0; font-size: 24px; }}
            .header p {{ margin: 0; opacity: 0.9; font-size: 14px; }}
            .content {{ padding: 20px; overflow-x: auto; }}
            table {{ width: 100%; border-collapse: collapse; text-align: left; font-size: 14px; }}
            th {{ background-color: #f8fafc; padding: 12px 14px; color: #64748b; font-weight: 600; text-transform: uppercase; font-size: 11px; letter-spacing: 0.05em; }}
            .footer {{ text-align: center; font-size: 12px; color: #9ca3af; padding: 16px; border-top: 1px solid #f3f4f6; }}
        </style>
    </head>
    <body>
        <div class="card">
            <div class="header">
                <h1>🇩🇪 Germany Weather Overview</h1>
                <p>{timestamp}</p>
            </div>
            <div class="content">
                <table>
                    <thead>
                        <tr>
                            <th>City</th>
                            <th>Condition</th>
                            <th>Temp</th>
                            <th>Feels</th>
                            <th>Humidity</th>
                            <th>Wind</th>
                        </tr>
                    </thead>
                    <tbody>
                        {rows}
                    </tbody>
                </table>
            </div>
            <div class="footer">
                Automated Weather Report via Open-Meteo API
            </div>
        </div>
    </body>
    </html>
    """


def build_html_single_city(data):
    timestamp = datetime.now().strftime("%A, %d %B %Y - %H:%M")
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #f3f4f6; margin: 0; padding: 24px; }}
            .card {{ max-width: 480px; margin: 0 auto; background: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1); }}
            .header {{ background: linear-gradient(135deg, #1e3a8a, #2563eb); color: white; padding: 24px; text-align: center; }}
            .header h1 {{ margin: 0 0 4px 0; font-size: 22px; }}
            .header p {{ margin: 0; opacity: 0.9; font-size: 13px; }}
            .temp-box {{ text-align: center; padding: 24px 16px; background-color: #f8fafc; border-bottom: 1px solid #e2e8f0; }}
            .temp {{ font-size: 46px; font-weight: 800; color: #1e293b; margin: 0; }}
            .condition {{ font-size: 17px; color: #475569; margin-top: 6px; }}
            .stats {{ width: 100%; padding: 16px 20px; box-sizing: border-box; }}
            .stat-row {{ display: flex; justify-content: space-between; padding: 10px 0; border-bottom: 1px solid #f1f5f9; }}
            .stat-label {{ color: #64748b; font-weight: 500; font-size: 14px; }}
            .stat-value {{ text-align: right; color: #1e293b; font-weight: 600; font-size: 14px; }}
            .footer {{ text-align: center; font-size: 12px; color: #9ca3af; padding: 14px; border-top: 1px solid #f1f5f9; }}
        </style>
    </head>
    <body>
        <div class="card">
            <div class="header">
                <h1>Weather for {data['city_name']}</h1>
                <p>{data['country_info']} • {timestamp}</p>
            </div>
            <div class="temp-box">
                <div class="temp">{data['temp']}</div>
                <div class="condition">{data['emoji']} {data['condition']} (Feels like {data['feels_like']})</div>
            </div>
            <div class="stats">
                <div class="stat-row">
                    <span class="stat-label">💧 Humidity</span>
                    <span class="stat-value">{data['humidity']}</span>
                </div>
                <div class="stat-row">
                    <span class="stat-label">💨 Wind Speed</span>
                    <span class="stat-value">{data['wind']}</span>
                </div>
                <div class="stat-row">
                    <span class="stat-label">🌧️ Precipitation</span>
                    <span class="stat-value">{data['precip']}</span>
                </div>
            </div>
            <div class="footer">
                Automated Weather Report via Open-Meteo API
            </div>
        </div>
    </body>
    </html>
    """


# ==============================================================================
# MAIN OPERATIONS
# ==============================================================================
def handle_single_city(city_name, lat, lon, country_info="Germany"):
    try:
        data = fetch_weather(lat, lon)
        current = data["current"]
        temp = f"{current['temperature_2m']:.1f} °C"
        feels_like = f"{current['apparent_temperature']:.1f} °C"
        humidity = f"{current['relative_humidity_2m']}%"
        wind = f"{current['wind_speed_10m']} km/h"
        precip = f"{current['precipitation']} mm"
        code = current["weather_code"]
        cond_text, emoji = get_weather_description(code)

        print("\n" + "=" * 50)
        print(f"  Weather Report: {city_name} ({country_info})")
        print("=" * 50)
        print(f"  Condition:     {emoji} {cond_text}")
        print(f"  Temperature:   {temp} (Feels like {feels_like})")
        print(f"  Humidity:      {humidity}")
        print(f"  Wind Speed:    {wind}")
        print(f"  Precipitation: {precip}")
        print("=" * 50)

        details = {
            "city_name": city_name,
            "country_info": country_info,
            "temp": temp,
            "feels_like": feels_like,
            "humidity": humidity,
            "wind": wind,
            "precip": precip,
            "condition": cond_text,
            "emoji": emoji,
        }

        text_body = (
            f"Weather Report: {city_name} ({country_info})\n"
            f"Condition: {cond_text}\n"
            f"Temperature: {temp} (Feels like {feels_like})\n"
            f"Humidity: {humidity}\n"
            f"Wind Speed: {wind}\n"
            f"Precipitation: {precip}\n"
        )
        html_body = build_html_single_city(details)
        subject = f"Weather Report: {city_name} - {datetime.now().strftime('%d %b %Y')}"

        send_weather_email(subject, html_body, text_body)

    except requests.RequestException as e:
        print(f"Error fetching weather for {city_name}: {e}")


def handle_germany_overview():
    print("\n" + "=" * 70)
    print("                CURRENT WEATHER ACROSS GERMANY                ")
    print("=" * 70)
    header = f"{'City':<20} {'Condition':<22} {'Temp':<10} {'Feels Like':<12} {'Wind'}"
    print(header)
    print("-" * 70)

    def fetch_city_row(item):
        city, coords = item
        try:
            data = fetch_weather(coords["lat"], coords["lon"])
            current = data["current"]
            temp = f"{current['temperature_2m']:.1f} °C"
            feels_like = f"{current['apparent_temperature']:.1f} °C"
            wind = f"{current['wind_speed_10m']} km/h"
            humidity = f"{current['relative_humidity_2m']}%"
            cond_text, emoji = get_weather_description(current["weather_code"])
            condition = f"{emoji} {cond_text}"[:20]

            return {
                "city": city,
                "temp": temp,
                "feels_like": feels_like,
                "wind": wind,
                "humidity": humidity,
                "condition": cond_text,
                "emoji": emoji,
                "row_str": f"{city:<20} {condition:<22} {temp:<10} {feels_like:<12} {wind}",
            }
        except requests.RequestException as e:
            return {
                "city": city,
                "temp": "N/A",
                "feels_like": "N/A",
                "wind": "N/A",
                "humidity": "N/A",
                "condition": "Error",
                "emoji": "⚠️",
                "row_str": f"{city:<20} Failed to fetch data ({e})",
            }

    with ThreadPoolExecutor(max_workers=len(GERMAN_CITIES)) as executor:
        results = list(executor.map(fetch_city_row, GERMAN_CITIES.items()))

    for res in results:
        print(res["row_str"])

    print("=" * 70)
    print("Tip: You can check a specific city by running: python germany.py <city_name>")

    # Prepare email
    date_str = datetime.now().strftime("%d %b %Y")
    subject = f"🇩🇪 Germany Weather Overview - {date_str}"
    
    text_lines = ["Current Weather Across Germany:", "-" * 50]
    for r in results:
        text_lines.append(f"{r['city']}: {r['condition']} | Temp: {r['temp']} (Feels: {r['feels_like']}) | Wind: {r['wind']}")
    text_body = "\n".join(text_lines)
    
    html_body = build_html_overview(results)

    send_weather_email(subject, html_body, text_body)


def main():
    if len(sys.argv) > 1:
        city_query = " ".join(sys.argv[1:]).strip()
        print(f"Searching weather for '{city_query}'...")
        try:
            location = search_city(city_query)
            if not location:
                print(f"Could not find any location matching '{city_query}'.")
                return
            city_name = location.get("name", city_query)
            country = location.get("country", "Unknown")
            admin1 = location.get("admin1", "")
            region = f"{admin1}, {country}" if admin1 else country
            handle_single_city(city_name, location["latitude"], location["longitude"], region)
        except requests.RequestException as e:
            print(f"Network error while searching for city: {e}")
    else:
        handle_germany_overview()


if __name__ == "__main__":
    main()
