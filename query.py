"""
Module for querying Wikidata using the SPARQL endpoint with the Wikidata Query Service and extracting the relevant
facts from the query results.

Classes:
    Sparql

Functions:
    birth_year(df)
    death_year(df)
    birthplace(df)
    deathplace(df)
    gender(df)
    num_children(df)
    spouse(df)
    marraiges(df)
"""
import requests
import pandas as pd
from collections import OrderedDict
import datetime
from colorama import init, Fore, Style
init()  # Initialise text colouring


class Sparql:
    """
    A class for querying using the Wikidata Query Service.
    """
    def __init__(self):
        self.url = 'https://query.wikidata.org/sparql'  # URL for SPARQL request

    def get_options(self, person_label):
        """ Query Wikidata for items which are instance of human which match the name of person. """
        id_query = '''
        SELECT ?person ?personLabel ?personDescription ?occupation ?occupationLabel WHERE {{
          ?person wdt:P31 wd:Q5.
          ?person wdt:P106 ?occupation;
          rdfs:label "{name}"@en.
          SERVICE wikibase:label {{ bd:serviceParam wikibase:language "[AUTO_LANGUAGE],en". }}
        }}
        '''.format(name=person_label)

        # Return response as json
        id_response = requests.get(self.url, params={'query': id_query, 'format': 'json'})
        id_data = id_response.json()

        # Check if a result was found:
        if not id_data['results']['bindings']:
            print(Fore.RED + 'No Wikidata item with label "{name}" found!'.format(name=person_label) + Style.RESET_ALL)
            print()
            exit(1)  # End if no result found

        # Reformat as a dataframe
        id_dict = []
        for item in id_data['results']['bindings']:
            id_dict.append(OrderedDict({
                'QID': item['person']['value'][31:],  # Slice string to get q value
                'person url': item['person']['value'],
                'Person Description': item['personDescription']['value'] if 'personDescription' in item else None,
                'occupation': item['occupationLabel']['value']
            }))
        id_df = pd.DataFrame(id_dict)
        id_df = id_df.groupby(['QID', 'person url', 'Person Description'])['occupation'].apply(list).reset_index()
        return id_df

    def get_person_data(self, id_val):
        """ Query Wikidata for statements and qualifiers for the chosen item. """
        person_query = '''
        SELECT ?personLabel ?propertyLabel ?valueLabel ?value ?qualLabel ?pq_valLabel {{
          VALUES (?person) {{(wd:{q_val})}}

          ?person ?p ?statement .
          ?property wikibase:claim ?p.
          ?property wikibase:statementProperty ?ps.
          ?statement ?ps ?value .

          OPTIONAL {{
            ?statement ?pq_qual ?pq_val .
            ?qual wikibase:qualifier ?pq_qual .
          }}
          SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en" }}
        }} ORDER BY ?property ?statement ?value ?qual
        '''.format(q_val=id_val)

        # Return response as json
        person_response = requests.get(self.url, params={'query': person_query, 'format': 'json'})
        person_data = person_response.json()  # Convert

        # Reformat as dataframe
        person_dict = []
        for item in person_data['results']['bindings']:
            person_dict.append(OrderedDict({
                # 'person name': item['personLabel']['value'],
                'property': item['propertyLabel']['value'],
                'property value': item['valueLabel']['value'],
                'property identifier': item['value']['value'][31:],  # Slice string to get q value
                'qualifier': item['qualLabel']['value'] if 'qualLabel' in item else None,
                'qualifier value': item['pq_valLabel']['value'] if 'pq_valLabel' in item else None
            }))
        person_df = pd.DataFrame(person_dict)

        # Remove ID statements
        id_locs = person_df['property'].str.contains(r"\b[Ii][Dd]\b", regex=True)
        person_df = person_df[~id_locs]

        # Group by the property
        person_df = person_df.groupby(['property'])[['property value',
                                                     'property identifier',
                                                     'qualifier',
                                                     'qualifier value']].apply(lambda x: x.values.tolist())
        return person_df

    def get_coordinates(self, pob_qval):
        """ Query Wikidata for the coordinates of the place of birth for the chosen item. """
        coordinate_query = '''
        SELECT ?coordinateLabel WHERE {{
          VALUES (?location) {{(wd:{q_val})}}
          ?location wdt:P625 ?coordinate.
          SERVICE wikibase:label {{bd:serviceParam wikibase:language "[AUTO_LANGUAGE],en".}}
        }}
        '''.format(q_val=pob_qval)
        coordinate_response = requests.get(self.url, params={'query': coordinate_query,
                                                        'format': 'json'})  # Return response as json
        coordinate_data = coordinate_response.json()  # Convert to json

        if not coordinate_data['results']['bindings']:
            # Return None if place of birth has no coordinates
            return None, None
        else:
            # Extract longitude and latitude from result
            loc = coordinate_data['results']['bindings'][0]['coordinateLabel']['value']
            loc = loc.replace('Point(', '')  # Remove wrapper
            loc = loc.replace(')', '')
            loc = list(map(float, loc.split(' ')))
            # Rounded to nearest integer
            longitude = int(loc[0])  # Ranges +180 eastward, -180 westward
            latitude = int(loc[1])  # Ranges +90 northward, -90 southward
            return longitude, latitude


def birth_year(df):
    """ Get the birth year from DataFrame. If does not exist, exit the program. """
    dob_year = None
    try:
        dob = df.loc['date of birth'][0][0]
        dob_year = int(dob[0:4], 10)  # Extract the birth year
    except KeyError:
        print(Fore.RED + 'Not enough knowledge to produce sonification!' + Style.RESET_ALL)
        print()
        exit(1)
    return dob_year


def death_year(df):
    """ Get the death year from DataFrame. If does not exist, get the current year. """
    try:  # If person is deceased
        dod = df.loc['date of death'][0][0]
        dod_year = int(dod[0:4], 10)  # Extract death year
    except KeyError:  # If person is still alive, returns current year
        date = datetime.date.today()
        dod_year = date.year  # Current year
    return dod_year


def birthplace(df):
    """ If it exists, get the place of birth from DataFrame. """
    try:
        pob = df.loc['place of birth'][0][1]
    except KeyError:
        pob = None
    return pob


def deathplace(df):
    """ If it exists, get the place of death from DataFrame. """
    try:
        pod = df.loc['place of death'][0][1]
    except KeyError:
        pod = None
    return pod


def gender(df):
    """ Get the gender from DataFrame. """
    return df.loc['sex or gender'][0][0]


def num_children(df):
    """ Get the number of children from the DataFrame. """
    try:
        number = int(df.loc['number of children'][0][0])
    except KeyError:
        try:
            children = df.loc['child']
            number = len(children)
        except KeyError:
            number = 0
    return number


def spouse(df):
    """ Get the list of spouses from DataFrame, if there are none return number of spouses is 0. """
    try:
        spouses = df.loc['spouse']
        return spouses
    except KeyError:
        number_spouses = 0
        return number_spouses


def marriages(df):
    """ Get the marriage and divorce years from the qualifiers for people with spouses. """
    spouses = pd.DataFrame(df)
    indices = spouses.iloc[:][[0, 2]]
    index = pd.MultiIndex.from_frame(indices, names=['name', 'desc'])  # for multi-index

    info = spouses.iloc[:][3].tolist()
    df = pd.DataFrame(info, index=index)  # Structured DataFrame of spouses
    number_spouses = len(df.groupby(level=0))

    start = df.xs('start time', level=1)[0].tolist()  # Marriages
    try:
        end = df.xs('end time', level=1)[0].tolist()  # Endings
        dates = start + end
    except KeyError:
        dates = start
    years = []
    for date in dates:  # Convert to integer list of years
        val = int(date[0:4], 10)
        years.append(val)
    years.sort()
    return number_spouses, years
