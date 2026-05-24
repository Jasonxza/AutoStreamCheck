# Twitch Auto-Watcher Daemon

A lightweight, automated Python dashboard that monitors a specific Twitch streamer's live status. When they go live, it automatically opens their stream in your default browser and tracks your watch time and viewer statistics locally. 

This script features a built-in auto-updater to pull the latest releases directly from this repository.

## ✨ Features
* **Automated Launching:** Opens your default web browser the exact minute the target streamer goes live.
* **Live Statistics:** Tracks the streamer's current game, stream title, and live viewer count.
* **Personal Tracking:** Logs your total watch time and calculates the average, highest, and lowest viewer counts across your viewing sessions.
* **Auto-Saving:** Automatically saves your progress locally to prevent data loss.
* **Self-Updating:** Automatically checks GitHub for new versions of the script on launch and patches itself.

## 💡 Recommended Setup
**We strongly recommend running this script on a laptop.** Laptops are power-efficient, quiet, and can be easily kept running overnight. 

*   **Tip:** Ensure your laptop is plugged into power and your Windows Power & Sleep settings are configured to **"Never"** turn off the screen or go to sleep while plugged in, otherwise the script cannot monitor the stream while you are away.

## ⚙️ Prerequisites
To run this script, you need:
1. [Python 3.8+](https://www.python.org/downloads/) installed on your system.
2. A Twitch Developer App Client ID and Secret.
3. The exact **Twitch Username** of the streamer.

### How to get Twitch API Keys:
1. Log into the [Twitch Developer Console](https://dev.twitch.tv/console).
2. Click **Register Your Application**.
3. Name it, set the OAuth Redirect URL to `http://localhost`, and set Category to **Application Integration**.
4. Click **Manage** on your new app to copy your **Client ID** and generate a **Client Secret**.

### How to get the correct Twitch Username:
The "Username" is not necessarily the display name you see with spaces. It is the ID used in the URL.
*   Navigate to the streamer's channel page on [Twitch.tv](https://www.twitch.tv/).
*   Look at the URL in your browser address bar: `twitch.tv/example_name`.
*   The **"example_name"** part is your target username. Copy this exactly as it appears.

## 🚀 Installation & Setup

1. **Download the project:**
   Clone this repository or download the ZIP file and extract it to a folder.
```cmd
   git clone [https://github.com/Jasonxza/AutoStreamCheck.git](https://github.com/Jasonxza/AutoStreamCheck.git)
