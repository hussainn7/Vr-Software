# Speech Translator App

A modern, user-friendly speech translation application built with Python and Tkinter. This application allows users to:

- Convert speech to text in multiple languages
- Translate text between different languages
- Record video with audio
- Modern UI with smooth animations and effects

## Features

- Real-time speech recognition
- Multi-language support
- Modern UI with animations
- Video recording capability
- Typewriter effect for text display
- Interactive buttons with hover effects
- Status bar with real-time updates

## Requirements

- Python 3.x
- Tkinter
- PIL (Python Imaging Library)
- OpenAI API key

## Installation

1. Clone the repository:
```bash
git clone https://github.com/hussainn7/Vr-Software.git
cd Vr-Software
```

2. Install required packages:
```bash
pip install -r requirements.txt
```

3. Set up your OpenAI API key in `src/main.py`

## Usage

Run the application:
```bash
python src/main.py
```

## Project Structure

```
Vr-Software/
├── src/
│   ├── main.py              # Main application entry point
│   ├── ui/
│   │   └── app_ui.py        # UI implementation
│   ├── speech/
│   │   └── recognizer.py    # Speech recognition module
│   ├── translation/
│   │   └── translator.py    # Translation module
│   ├── video/
│   │   └── recorder.py      # Video recording module
│   └── utils/
│       └── openai_manager.py # OpenAI API utilities
├── requirements.txt         # Project dependencies
└── README.md               # Project documentation
```

## Contributing

Feel free to submit issues and enhancement requests!

## License

This project is licensed under the MIT License - see the LICENSE file for details.