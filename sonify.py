"""
Main program for sonification of a person's information on Wikidata.
The program implements a sonification mapping for knowledge about a given human on Wikidata.
User searches for Wikidata item by name of person and the program automatically launches Sonic Pi from which
a song about the person is played for the user.
"""
import pandas as pd
import time
import query
import sonicpi
from query import Sparql
from colorama import init, Fore, Style
from sonicpi import send_osc
init()  # Initialise text colouring


def read_name():
    """ Read name for Wikidata SPARQL query from command line input. """
    name = input(Fore.BLUE + 'Enter name of person for Wikidata search: ' + Style.RESET_ALL)
    return name


def read_row():
    """ Read row number to choose correct person. """
    row = int(input(Fore.BLUE + 'Choose row number from table above: ' + Style.RESET_ALL), 10)  # Read number as integer
    return row


if __name__ == '__main__':
    person_label = read_name()  # Name of person for query
    search = Sparql()  # SPARQL query instance
    options = search.get_options(person_label)  # Get Wikidata items matching name of person

    # If there are multiple humans on Wikidata with the same name, let the user choose the correct one
    if len(options.index) > 1:
        options.index.name = 'Row'
        num_options = len(options.index)
        print(Fore.BLUE + '{} matches found:'.format(num_options) + Style.RESET_ALL)
        # Print options for user to choose:
        with pd.option_context('display.max_rows', None, 'display.max_columns', None):
            print(options[['QID', 'Person Description']])
        choice = read_row()  # Choose correct one
    else:
        choice = 0

    # Get description, QID, and the url of the chosen person
    desc = options['Person Description'].iloc[choice]
    id_val = options['QID'].iloc[choice]
    id_url = options['person url'].iloc[choice]
    # Print information about the choice
    print(Fore.BLUE + '\nYou have chosen:' + Style.RESET_ALL)
    print('{name}\n{info}\n{q_val}\n{url}\n'.format(name=person_label, info=desc, q_val=id_val, url=id_url))

    data = search.get_person_data(id_val)  # Get content of chosen Wikidata item

    # Extract the relevant data for sonification:
    print('Extracting statements for sonification.')
    birth = query.birth_year(data)  # Year of birth
    death = query.death_year(data)  # Year of death or current year if still alive
    age = death-birth  # Age of person
    birthplace_q = query.birthplace(data)  # QID of the place of birth if known, None otherwise
    if birthplace_q is not None:  # If place of birth is known
        birth_lon, birth_lat = search.get_coordinates(birthplace_q)
    else:
        birth_lon, birth_lat = None, None

    deathplace_q = query.deathplace(data)  # QID of the place of death if known, None otherwise
    if deathplace_q is not None:  # If place of death is known
        death_lon, death_lat = search.get_coordinates(deathplace_q)
    else:
        death_lon, death_lat = None, None

    gender = query.gender(data)  # Gender of person

    children = query.num_children(data)  # Number of children

    num_spouses = query.spouse(data)  # Gets list of spouses if known or assigns 0 otherwise
    years = None
    if not isinstance(num_spouses, int):  # If num_spouses is not 0
        num_spouses, years = query.marriages(num_spouses)  # Get the number of spouses and years of marriage/end
    print('Completed!')

    # Begin Sonification
    print(Fore.MAGENTA + 'Sonification begins now!')

    # Number of beats is age
    beats = age

    # Gender
    if gender == 'male':
        gender_sample = 0
    else:
        gender_sample = 1

    # Latitude longitude pitch mapping
    d_major_scale = sonicpi.major_scale(38, 4)  # get MIDI values of 4 octave D major scale starting at D2
    scale_length = len(d_major_scale)
    birth_lon_note, birth_lat_note = None, None
    if birth_lon is not None:
        birth_lon = 180 + birth_lon
        birth_lat = 90 + birth_lat
        # Scaling
        birth_lon_scaled = float(birth_lon / 360)
        birth_lat_scaled = float(birth_lat / 180)
        # Mapping to major scale
        birth_lon_note = d_major_scale[int(round(birth_lon_scaled * scale_length))]
        birth_lat_note = d_major_scale[int(round(birth_lat_scaled * scale_length))]
    death_lon_note, death_lat_note = None, None
    if death_lon is not None:
        death_lon = 180 + death_lon
        death_lat = 90 + death_lat
        # Scaling
        death_lon_scaled = float(death_lon / 360)
        death_lat_scaled = float(death_lat / 180)
        # Mapping to major scale
        death_lon_note = d_major_scale[int(round(death_lon_scaled * scale_length))]
        death_lat_note = d_major_scale[int(round(death_lat_scaled * scale_length))]

    # Marriages
    marriage_beats = None
    divorce_beats = None
    if num_spouses != 0:
        events = len(years)
        if events == 1:
            marriage_beats = years[0] - birth
            divorce_beats = None
        elif (events % 2) == 0:
            marriage_years = years[::2]
            marriage_beats = [x - birth for x in marriage_years]
            divorce_years = years[1::2]
            divorce_beats = [x - birth for x in divorce_years]
        else:
            marriage_years = years[::2]
            marriage_beats = [x - birth for x in marriage_years]
            divorce_years = years[1::2]
            divorce_beats = [x - birth for x in divorce_years]

    # Children chord
    child_chord = None
    if children != 0:
        child_chord = sonicpi.major_7_chord(67, children)
        # print(child_chord)

    # Launch Sonic Pi
    sonicpi.launch_sonicpi()
    print('Launching Sonic Pi...')
    time.sleep(10)  # Wait until launched
    print('Playing now.')
    sonicpi.play_code()

    # Send information to Sonic Pi
    send_osc('/beats', beats, 'Age')
    send_osc('/gender', gender_sample, 'Gender')
    send_osc('/birth', [birth_lon_note, birth_lat_note], 'Place of Birth')
    send_osc('/death', [death_lon_note, death_lat_note], 'Place of Death')
    send_osc('/children', child_chord, 'Children')
    send_osc('/marriage', marriage_beats, 'Wedding(s)')
    send_osc('/divorce', divorce_beats, 'Divorce(s)')

    print('Sonification completed.' + Style.RESET_ALL)
