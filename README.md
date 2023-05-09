# Speech-Stress-Detector
A stress detection app

1. Set up the Python environment in Raspberry pi which is connected to the LCD display.
2. Run the command: pip install numpy==1.23.4 pyaudio==0.2.12 librosa==0.9.2 matplotlib==3.7.1 pygame==2.3.0 noisereduce==2.0.1
3. Run the command:  sudo apt-get install python3-pil.imagetk
4. Download the zip file containing the source code or clone the github link - https://github.com/Ranji02/Speech-Stress-Detector.git
5. Extract the folder which contains the autostart folder. 
6. Move this folder to .config folder which is present inside the pi folder.
7. The autostart folder contains the "SpeechStressDetector" executable file. The application can run on both ways. 
8. First way, Whenever the Raspberry pi OS is booted, the application start automatically.
9. Another way of running the application is to double click on the "SpeechStressDetector" executable file.
