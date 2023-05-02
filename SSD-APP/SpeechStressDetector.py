import tkinter as tk
from tkinter import Scrollbar, filedialog, PhotoImage
from PIL import Image,ImageTk
import os, pathlib
import numpy as np
import wave, time, threading, pyaudio
import librosa
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import pygame
import pickle
import tkinter.scrolledtext as st


# Create a Tkinter window
root = tk.Tk()
window_width = int(root.winfo_screenwidth())-10
window_height = int(root.winfo_screenheight())-85
root.geometry(f"{window_width}x{window_height}")
root.title("Speech Stress Detector")

img_file_name = "stress_icon.ico"
current_dir = pathlib.Path(__file__).parent.resolve() # current directory
img_path = os.path.join(current_dir, img_file_name)

img = PhotoImage(file=img_path)  # Replace "image.png" with any image file.
root.iconphoto(False, img)
root.resizable(0, 0)

pygame.mixer.init()

audio_playing = False
start_time = 0
show_waveform = tk.BooleanVar()
show_waveform.set(False)


# Define global variables for audio recording
sample_rate = 44100
file_path = ""
record = False
stop_reset = False
label = ""
record_button = ""
play_button = ""
message = ""
canvas = ""

# Define a function to start recording audio
def start_recording():
    global record, record_button, message, stop_reset, canvas, show_waveform
    if record:
        record = False
        stop_reset = False
        record_button.config(text="Start Record")
        
    elif record == False:
        record = True
        stop_reset = False
        if canvas:
            # hide the waveform plot
            canvas.get_tk_widget().place_forget()
            show_waveform.set(False)

        record_button.config(text="Stop Record")
        threading.Thread(target=stop_recording).start()
        message.config(text="Recording Started...")
        

# Define a function to stop recording audio
def stop_recording():
    global record,file_path, stop_reset
    audio = pyaudio.PyAudio()
    stream = audio.open(format=pyaudio.paInt16, channels=1, rate=44100, input=True, frames_per_buffer=1024)
    frames = []
    start = time.time()
    while record:
        data = stream.read(1024)
        frames.append(data)
        passed = time.time() - start
        secs = passed % 60
        mins = passed // 60
        hours = mins // 60

        label.config(text=f"{int(hours):02d}:{int(mins):02d}:{int(secs):02d}")

    stream.stop_stream()
    stream.close()
    audio.terminate()

    exists = True

    i = 1
    while exists:
        if os.path.exists(f"recording{i}.wav"):
            i+=1
        else:
            exists = False

    if not stop_reset:
        stop_reset = False
        file_path = f"recording{i}.wav"  #Can change directory
        audio_file = wave.open(file_path,"wb")
        audio_file.setnchannels(1)
        audio_file.setsampwidth(audio.get_sample_size(pyaudio.paInt16))
        audio_file.setframerate(44100) 
        audio_file.writeframes(b"".join(frames))
        audio_file.close()
        message.config(text="Recording Stopped and Saved as \"" + file_path + "\"") 
        
        # show the waveform plot
        plot_waveform(file_path)
        show_waveform.set(True)   
    else:
        message.config(text="Recording Cancelled...") 


def plot_waveform(file_path, x = 370, y = 350):
    # open the WAV file
    with wave.open(file_path, "rb") as wav_file:

        audio_data = wav_file.readframes(wav_file.getnframes())

        # convert the audio data to a numpy array
        audio_np = np.frombuffer(audio_data, dtype=np.int16)

        # create a Figure object and add a subplot
        fig = Figure(figsize=(3, 1), dpi=70)
        ax = fig.add_subplot(111)

        # plot the waveform
        ax.plot(audio_np, color='#82014f')

        # set the x and y axis labels and limits 
        ax.set_xlabel("Time") 
        ax.set_ylabel("Amplitude") 
        ax.set_xlim([0, len(audio_np)]) 
        # ax.set_ylim([-32768, 32768])

        # create a canvas for the plot
        global canvas
        canvas = FigureCanvasTkAgg(fig, master=root)
        canvas.draw()

        # place the canvas in the Tkinter window
        canvas.get_tk_widget().place(x=x, y=y, width=1000, height=320)


def play_audio():
    global audio_playing, start_time, canvas, show_waveform, stop_reset
    global show_waveform
    message.config(text="")
    label.config(text="00:00:00")
    if audio_playing:
        message.config(text="Audio Playing Stopped")
        play_button.config(text="Play Audio")
        pygame.mixer.music.stop()
        audio_playing = False
        start_time = 0

    else:
        if canvas:
            # hide the waveform plot
            canvas.get_tk_widget().place_forget()
            show_waveform.set(False)
        file_path = filedialog.askopenfilename(filetypes=[("Wave Audio", ".wav"), ("MPEG-4 Audio", ".m4a")])
        if file_path:
            pygame.mixer.music.load(file_path)
            message.config(text="Audio \"" + file_path + "\" is playing!!!")
            play_button.config(text="Stop Play")
            stop_reset = False
            pygame.mixer.music.play()  
            audio_playing = True

            # show the waveform plot
            plot_waveform(file_path)
            show_waveform.set(True)   
            
        check_audio()
        update_time_label()


def check_audio():
    global audio_playing, stop_reset
    if not pygame.mixer.music.get_busy() and audio_playing and not stop_reset:
        stop_reset = False
        message.config(text="Audio Played Fully")
        play_button.config(text="Play Audio")
        label.config(text="00:00:00")
        canvas.get_tk_widget().place_forget()
        show_waveform.set(False)
        audio_playing = False  
    else:
        root.after(100, check_audio)

def update_time_label():
    if audio_playing:
        current_time = pygame.mixer.music.get_pos() / 1000
        hours = int(current_time // 3600)
        minutes = int((current_time % 3600) // 60)
        seconds = int(current_time % 60)
        label.config(text=f"{int(hours):02d}:{int(minutes):02d}:{int(seconds):02d}")
        root.after(100, update_time_label)


# Define function to extract Spectral features from audio files
def extract_spec_features(file_path):
    audio, sample_rate = librosa.load(file_path, res_type="kaiser_fast")
    spectral_features = librosa.feature.melspectrogram(y=audio, sr=sample_rate)
    spectral_features = spectral_features.T
    spectral_features = np.mean(spectral_features,axis=0)
    return spectral_features


# Define a function to upload audio
def upload_audio():
    global file_path, message, message1
    message.config(text="")
    message1.config(text="", bg='#eeccff')

    file_path = filedialog.askopenfilename(initialdir="/home/pi/Desktop",filetypes=[("Audio files", "*.wav")])
    
    if file_path:
        message.config(text="You have uploaded :" + file_path + "!!!")


    loaded_first_phase_model = pickle.load(open(os.path.join(current_dir, 'RF_Model_MS95.pkl'),'rb'))
    loaded_final_model = pickle.load(open(os.path.join(current_dir, 'Final_Model91.pkl'),'rb'))

    spec_feature = extract_spec_features(file_path)
    stress_state = loaded_first_phase_model.predict([spec_feature])
    # "Stress state" of each speech MS feature predicted by first phase Random Forest model

    if stress_state[0] == 0:
        state = [0]
    else:
        state = [1]

    # show the waveform plot
    plot_waveform(file_path)
    show_waveform.set(True) 

    data = np.concatenate((spec_feature,state))
    level = loaded_final_model.predict([data])
    message1.config(text=level[0] + " Stress detected...", bg="white")


def record_reset():
    global sample_rate, file_path, record, stop_reset, record_button, label, show_waveform, message
    sample_rate = 44100
    file_path = ""
    stop_reset = True
    record = False
    label.config(text="00:00:00")
    message.config(text="")
    canvas.get_tk_widget().place_forget()
    show_waveform.set(False)
    record_button.config(text="Start Record")


def play_reset():
    global stop_reset, label, play_button, message, show_waveform, audio_playing
    stop_reset = True
    audio_playing = False
    label.config(text="00:00:00")
    message.config(text="")
    pygame.mixer.music.stop()
    canvas.get_tk_widget().place_forget()
    show_waveform.set(False)
    play_button.config(text="Play Audio")


def detect_reset():
    global message, message1, detect_button, show_waveform
    message.config(text="")
    canvas.get_tk_widget().place_forget()
    show_waveform.set(False)


def reset():
    global stop_reset, record_button, label, play_button

    label.config(text="00:00:00")
    message.config(text="")
    record_button.config(text="Start Record")
    play_button.config(text="Play Audio")


def record_page():
    global record_button, label, message, reset_button

    message = tk.Label(main_frame, text="", width=100, font=("Arial", 10, "bold"),  bg='#eeccff')
    message.place(x=250, y=60)

    record_button = tk.Button(main_frame, bd=3, text="Start Record",font=("Arial", 20, "bold"), fg='#82014f', command=start_recording, width=15)
    record_button.place(x=500, y=90)

    reset_button = tk.Button(main_frame, bd=3, text="Reset",font=("Arial", 20, "bold"), fg='#82014f', command=record_reset, width=15)
    reset_button.place(x=500, y=152)
    
    label = tk.Label(main_frame, text="00:00:00", fg='#82014f', width=15, font=("Arial", 20, "bold"))
    label.place(x=502, y=214)


def detect_page():
    global detect_button, message, message1, label
    message = tk.Label(main_frame, text="", width=100, font=("Arial", 10, "bold"),  bg='#eeccff')
    message.place(x=250, y=60)

    message1 = tk.Label(main_frame, text="", width=75, font=("Arial", 20, "bold"),  bg='#eeccff')
    message1.place(x=2, y=90)

    detect_button = tk.Button(main_frame, bd=3, text="Upload Audio",font=("Arial", 20, "bold"), fg='#82014f', command=upload_audio, width=15)
    detect_button.place(x=500, y=152)


def play_page():
    global play_button, message, label
    message = tk.Label(main_frame, text="", width=100, font=("Arial", 10, "bold"),  bg='#eeccff')
    message.place(x=250, y=60)

    play_button = tk.Button(main_frame, bd=3, text="Play Audio", font=("Arial", 20, "bold"), fg='#82014f', command=play_audio, width=15)
    play_button.place(x=500, y=90)

    reset_button = tk.Button(main_frame, bd=3, text="Reset", font=("Arial", 20, "bold"), fg='#82014f', command=play_reset, width=15)
    reset_button.place(x=500, y=152)

    label = tk.Label(main_frame, text="00:00:00", fg='#82014f', width=15, font=("Arial", 20, "bold"))
    label.place(x=502, y=214)


def plot_img(filepath):
    global text_area
    
    img = ImageTk.PhotoImage(Image.open(filepath).resize((400,250))) 
    text_area.image_create(tk.END, image=img)
    label = tk.Label(main_frame, image=img)
    label.image = img 
    # text_area.insert(tk.END, f"\n\t\t{filepath}\n")
    label.pack()


def about_page():
    global about_button, message, text_area

    about_frame = tk.Frame(main_frame)

    app_name = tk.Label(main_frame, text="Speech Stress Detector", font=("Courier New", 30, "bold"), fg="#82014f", bg='#eeccff')
    app_name.pack()

    text_area = st.ScrolledText(main_frame, wrap=tk.WORD,
                            width = 80, 
                            height = window_height, 
                            font = ("Times New Roman",
                                    16), yscrollcommand=Scrollbar.set)
  
    text_area.pack(fill=tk.BOTH, expand=True)

    # Inserting Text which is read only
    text_area.insert(tk.END,
    """\
    
                Stress is the prevalent mental health condition among millions of individuals worldwide according to world health organization’s 
    predictions. The current stress diagnosis is  subjective, ineffective and requires a lot of specialised labour. To make the stress detection 
    method a palatable choice to spot the early warning signs of stress we have designed an application which is a non-invasive form of assessment. 
    Through this application the level of stress of an individual is detected and displayed.

    To start with the application,
           1.  Record the audio. Click on the record button and speak for a minimum seconds for proper detection and stop the recoding.
           2.  Click on the detect stress button. An upload button will be displayed. Using this upload the desired audio file to know its stress level.
           3.  To listen to the required existing audio click on the play audio button to play it.
    
    An waveform of the audio will also be displayed in all steps.

    Some example waveforms for each stress level is given below,

        1) No Stress\n\n\n    """)
              
    plot_img(os.path.join(current_dir, 'no_300.png'))
    plot_img(os.path.join(current_dir, 'no_301.png'))
    plot_img(os.path.join(current_dir, 'no_370.png'))
    text_area.insert(tk.END, """\n\t A_Nonstress.300_AUDIO_6.wav                 \t\t\t        Nonstress.301_AUDIO_1.wav \t\t\t\t\t\t   A_Nonstress.370_AUDIO_1.wav\n\n    """)
    plot_img(os.path.join(current_dir, 'no_312.png'))
    plot_img(os.path.join(current_dir, 'no_374.png'))
    text_area.insert(tk.END, """\n\t A_Nonstress.312_AUDIO_10.wav                 \t\t\t A_Nonstress.374_AUDIO_1.wav \t\t\t\t""")

    text_area.insert(tk.END,
    """\n\n\n
        2) Mild Stress\n
    """)
    plot_img(os.path.join(current_dir, 'mild_710.png'))
    plot_img(os.path.join(current_dir, 'mild_316.png'))
    plot_img(os.path.join(current_dir, 'mild_368.png'))
    text_area.insert(tk.END, """\n\t   Nonstress.710_AUDIO_6.wav                 \t\t\t        A_Nonstress.316_AUDIO_1.wav \t\t\t\t\t\t  A_Nonstress.368_AUDIO_18.wav\n\n    """)
    plot_img(os.path.join(current_dir, 'mild_335.png'))
    plot_img(os.path.join(current_dir, 'mild_313.png'))
    text_area.insert(tk.END, """\n\t    A_Nonstress.335_AUDIO_11.wav                 \t\t\t  Nonstress.313_AUDIO_10.wav \t\t\t\t""")

    text_area.insert(tk.END,
    """\n\n\n
        3) Moderate Stress\n
    """)

    plot_img(os.path.join(current_dir, 'mod_359.png'))
    plot_img(os.path.join(current_dir, 'mod_372.png'))
    plot_img(os.path.join(current_dir, 'mod_337.png'))
    text_area.insert(tk.END, """\n\t     A_Stress.359_AUDIO_7.wav                 \t\t\t        A_Stress.372_AUDIO_18.wav \t\t\t\t\t\t       A_Stress.337_AUDIO_31.wav\n\n    """)
    plot_img(os.path.join(current_dir, 'mod_376.png'))
    plot_img(os.path.join(current_dir, 'mod_655.png'))
    text_area.insert(tk.END, """\n\t    A_Stress.376_AUDIO_12.wav                 \t\t\t     A_Stress.655_AUDIO_0.wav \t\t\t\t""")

    text_area.insert(tk.END,
    """\n\n\n
        4) Severe Stress\n
    """)
    
    plot_img(os.path.join(current_dir, 'sev_309.png'))
    plot_img(os.path.join(current_dir, 'sev_377.png'))
    plot_img(os.path.join(current_dir, 'sev_453.png'))
    text_area.insert(tk.END, """\n\t     A_Stress.309_AUDIO_5.wav               \t\t\t            A_Stress.377_AUDIO_23.wav\t\t\t\t\t\t     Stress.453_AUDIO_0.wav\n\n    """)
    plot_img(os.path.join(current_dir, 'sev_332.png'))
    plot_img(os.path.join(current_dir, 'sev_405.png'))
    text_area.insert(tk.END, """\n\t    A_Stress.332_AUDIO_11.wav                    \t\t\t     A_Stress.405_AUDIO_2.wav \t\t\t\t""")

    text_area.insert(tk.END,
    """\n\n\n
        5) Extreme Stress\n
    """)
    
    plot_img(os.path.join(current_dir, 'extreme_346.png'))
    plot_img(os.path.join(current_dir, 'extreme_308.png'))
    plot_img(os.path.join(current_dir, 'extreme_362.png'))
    text_area.insert(tk.END, """\n\t     Stress.346_AUDIO_11.wav                         \t\t\t        A_Stress.308_AUDIO_3.wav \t\t\t\t\t\t       A_Stress.362_AUDIO_8.wav\n\n    """)
    plot_img(os.path.join(current_dir, 'extreme_311.png'))
    plot_img(os.path.join(current_dir, 'extreme_426.png'))
    text_area.insert(tk.END, """\n\t    Stress.311_AUDIO_3.wav                          \t\t\t     Stress.426_AUDIO_11.wav \t\t\t\t""")

    text_area.insert(tk.END, """\n\n\n\n""")

    # Making the text read only
    text_area.configure(state ='disabled')
    text_area.pack()
    about_frame.pack(pady=30, padx=30)


def hide_indicators():
    record_indicate.config(bg='#ccffdd')
    detect_indicate.config(bg='#ccffdd')
    play_indicate.config(bg='#ccffdd')
    about_indicate.config(bg='#ccffdd')


def delete_pages():
    global canvas, message, stop_reset, audio_playing, record
    stop_reset = True
    audio_playing = False
    record = False

    if canvas:
        # hide the waveform plot
        canvas.get_tk_widget().place_forget()
        show_waveform.set(False)
    pygame.mixer.music.stop()
    for frame in main_frame.winfo_children():
        frame.destroy()


def indicate(lb,page):
    hide_indicators()
    lb.config(bg='#82014f')
    delete_pages()
    page()


options_frame = tk.Frame(root, bg='#ccffdd', highlightbackground='#82014f', highlightthickness=2)

record_btn = tk.Button(options_frame, text='Record Audio', font=("Arial", 22, "bold"), fg= '#82014f', bd=0, bg='#faafca', command=lambda: indicate(record_indicate,record_page))

record_btn.place(x=20, y=100, width=210, height=57)

record_indicate = tk.Label(options_frame,text='', bg='#ccffdd')
record_indicate.place(x=5, y=100, width=10, height=57)

detect_btn = tk.Button(options_frame, text='Detect Stress', font=("Arial", 22, "bold"), fg='#82014f', bd=0, bg='#faafca', command=lambda: indicate(detect_indicate,detect_page))

detect_btn.place(x=20, y=200, width=210, height=57)

detect_indicate = tk.Label(options_frame,text='', bg='#ccffdd')
detect_indicate.place(x=5, y=200, width=10, height=57)

play_btn = tk.Button(options_frame, text='Play Audio', font=("Arial", 22, "bold"), fg= '#82014f', bd=0, bg='#faafca', command=lambda: indicate(play_indicate,play_page))

play_btn.place(x=20, y=300, width=210, height=57)

play_indicate = tk.Label(options_frame,text='', bg='#ccffdd')
play_indicate.place(x=5, y=300, width=10, height=57)

about_btn = tk.Button(options_frame, text='About', font=("Arial", 22, "bold"), fg= '#82014f', bd=0, bg='#faafca', command=lambda: indicate(about_indicate,about_page), width=10)

about_btn.place(x=20, y=400, width=210, height=57)
about_indicate = tk.Label(options_frame,text='', bg='#ccffdd')
about_indicate.place(x=5, y=400, width=10, height=57)

options_frame.pack(side=tk.LEFT)
options_frame.pack_propagate(False)
options_frame.configure(width= 245, height=window_height)




main_frame = tk.Frame(root, highlightbackground='#82014f', bg='#eeccff', highlightthickness=3)
main_frame.pack(side=tk.LEFT)
main_frame.pack_propagate(False)
main_frame.configure(width= window_width-233, height=window_height)


# Create buttons to record or upload audio
title = tk.Label(main_frame, text="Speech Stress Detector", font=("Courier New", 50, "bold"), fg="#82014f", bg='#eeccff')
title.place(x=220, y=250)

# Start the Tkinter event loop
root.mainloop()







