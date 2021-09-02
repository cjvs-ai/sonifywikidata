"""
Module for interacting with Sonic Pi and sending OSC bundles to Sonic Pi.
Also includes two functions which dynamically generate MIDI notes for major scale and major 7 arpeggio.

Functions:
    launch_sonicpi()
    plau_code()
    send_osc(path, value, label)
    major_scale(root, octaves)
    major_7_chord(root, num_children)
"""
import os
import pyautogui
from pythonosc import udp_client


def launch_sonicpi():
    """ Launches Sonic Pi application or switches to it if already opened. """
    path = '/Applications/Sonic\ Pi.app'
    os.system(f"open {path}")


def play_code():
    """ Trigger Sonic Pi to run code via key commands. """
    pyautogui.keyDown('command')
    pyautogui.keyDown('r')
    pyautogui.keyUp('command')
    pyautogui.keyUp('r')


def send_osc(path, values, label):
    """ Send OSC bundles to Sonic Pi server. Checks if there are None values. Prints notification to
    user after bundle is sent. """
    if isinstance(values, list) and any(x is None for x in values):  # Check if is None
        values = 'None'
    elif values is None:
        values = 'None'
    sender = udp_client.SimpleUDPClient('127.0.0.1', 4560)  # Sonic Pi server
    sender.send_message(path, values)   # Send osc message
    print('{} sent to Sonic Pi via OSC.'.format(label))


def major_scale(root, octaves):
    """ Generate MIDI note values of the major scale based on 2,2,1,2,2,2,1 pattern. """
    scale = [root, ]
    for octave in range(octaves):
        for i in range(2):
            next_note = scale[-1]+2
            scale.append(next_note)
        for i in range(1):
            next_note = scale[-1]+1
            scale.append(next_note)
        for i in range(3):
            next_note = scale[-1]+2
            scale.append(next_note)
        for i in range(1):
            next_note = scale[-1]+1
            scale.append(next_note)
    return scale


def major_7_chord(root, num_children):
    """ Generate MIDI note values of the major 7 chord based on 4,3,4,1 pattern. """
    chord = [root, ]
    remain = num_children-1
    while remain > 0:
        if (len(chord) % 2) != 0:  # Case add 4
            next_note = chord[-1]+4
            chord.append(next_note)
            remain = remain-1
        elif (len(chord) % 4) == 0:  # Case add 1
            next_note = chord[-1]+1
            chord.append(next_note)
            remain = remain-1
        else:
            next_note = chord[-1]+3
            chord.append(next_note)
            remain = remain-1
    return chord
