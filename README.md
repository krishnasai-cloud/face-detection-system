Face Detection System v6.0

A real-time face, eye, and smile detection desktop application built with Python, OpenCV, and Tkinter. It supports live webcam input or video file playback, with adjustable detection sensitivity, multiple bounding-box styles, a privacy blur mode, and live session statistics — all wrapped in a custom dark-themed GUI.


Note: This is a desktop application, not a web app. It opens in its own native window (Tkinter) rather than a browser.




Features


🟦 Real-time face detection from webcam or video file
👁️ Eye detection — detects and highlights both eyes within each detected face
😄 Smile detection — flags smiling faces with an on-screen indicator
🔒 Privacy blur mode — automatically blurs detected faces
🎨 4 bounding-box styles — bracket, rect, cyber, minimal
🌈 6 color palettes for detection overlays
⚙️ Adjustable detection sensitivity — scale factor, minimum neighbors, minimum face size
📊 Live stats — FPS, faces in frame, total faces counted, peak count, frame count, resolution, session time
📸 Frame capture — save the current annotated frame as a PNG/JPEG
📝 Event log with timestamped detection events
🖥️ Custom dark-themed UI with animated particle background and splash screen



Demo

PanelDescriptionLeftCamera controls, detection settings, feature toggles, box style/colourCenterLive annotated video feed with real-time stats barRightLive face counter, session statistics, event log


Requirements


Python 3.9 – 3.12 (recommended)

Very new Python releases (3.13/3.14) may not yet have prebuilt OpenCV wheels. If installation fails, use Python 3.12 instead.




A webcam (optional — video files can be used instead)
Windows, macOS, or Li
