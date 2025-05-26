# Keylogger

A simple keylogger that logs all keys, including special keys and modifier keys (Ctrl, Alt, Shift, Windows). Made in Python.

**⚠️ Software is for educational purposes, i'm not responsible for any damage caused by this tool.**

## Features

- Captures keystrokes including:
  - Regular keys
  - Special keys (F1-F12, arrows, etc.)
  - Modifier key combinations (Ctrl+Alt+Del, etc.)
- Logs active window title with keystrokes
- Reports logged data to Discord webhook at configurable intervals
- Multiple persistence methods:
  - Registry startup entry
  - Startup folder
  - Scheduled task
- Operates silently (console window hides at startup)

## Installation & Usage

1. **Replace the webhook URL** in the script with your own Discord webhook URL
2. Run the script with python (and as an administrator for persistence)

### Requirements

- Python 3.x
- Windows OS
- Required packages: `keyboard`, `requests`

Install dependencies with:
```pip install keyboard requests```


## Legal Disclaimer

This software is provided for educational purposes only. The author does not condone or support any unauthorized or illegal use of this software. It is the user's responsibility to ensure they have proper permission before testing or using this software on any system.
Unauthorized use of keylogging software may violate:
- Computer Fraud and Abuse Act (CFAA)
- Electronic Communications Privacy Act (ECPA)
- General Data Protection Regulation (GDPR)
- Various state and local privacy laws
The author assumes no liability for any misuse of this software.

## Contributing

Feel free to contribute to this project!

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
