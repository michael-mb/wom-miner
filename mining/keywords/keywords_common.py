import re
import logging
import sys
from unidecode import unidecode
import os

'''Provides common functions for the keyword mining process.'''

def clean_text(input_string):
    '''Cleans a string by removing special characters, numbers, and single characters.'''
    input_string = input_string.replace('ä', 'ae').replace('ö', 'oe').replace('ü', 'ue').replace('ß', 'ss')
    input_string = input_string.replace('-', '').replace('_', '')
    input_string = unidecode(input_string)
    symbols = r"[!\"#$%&'()*+,-./:;<=>?@[\]^_`{|}~]"
    input_string = re.sub(symbols, ' ', input_string)
    input_string = re.sub(r'\s+', ' ', input_string)
    words = input_string.split()
    words = [word for word in words if len(word) > 1 and not word.isdigit()]
    input_string = ' '.join(words)
    input_string = input_string.lower()
    return input_string.strip()