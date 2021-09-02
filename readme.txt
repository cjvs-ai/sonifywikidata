Program for sonification of humans on Wikidata.

Instructions for use:
- Ensure internet connection (needed for accessing Wikidata)
- Run program via command line with command: python sonify.py
- You will then be prompted to enter the name of the person for Sonification.
- The program runs you through the next steps, then launches Sonic Pi and plays the sonification.

Files included:
sonify.py
    Main python program
query.py
    Module called by sonify.py for querying Wikidata and extracting parameters for sonification from data
sonicpi.py
    Module called by sonify.py for launching Sonic Pi, generating MIDI notes, and sending paramters to Sonic Pi server
    using OSC protocol
sonfication.rb
    Ruby code which implements sonification mapping. Executed by Sonic Pi to produce the song.
requirements.txt
    Text file listing module requirements for python.

Software requirements:
Python (modules needed are given in requirements.txt)
Sonic Pi (open-source application, available for download at sonic-pi.net)
