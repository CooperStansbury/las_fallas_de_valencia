import argparse
import ast
from mido import Message, MidiFile, MidiTrack
import numpy as np
import random
from distutils.util import strtobool


"""
TODO:
    - add a tunable velocity curve (per track or global or both?)
    - create subtractive/additive hit logic
"""

def get_base_params(midi, division, offset, base_velocity):
    """A function to ensure that minimal functionality is in all drum
    params.

    Args:
        - midi (int): the note that the drum will trigger. Defaults set
            to trigger bottom row of default drum rack in Ableton.
        - division (int): how to divide the phrase for this drum hit
        - offset (int): number of beats (`beat` param) to shift the drum phrase
        - base_velocity (int): the default velocity for the drum hit

    Returns:
        - base_params (dict)
    """
    return {
        'midi':midi,
        'division':division,
        'offset':offset,
        'base_velocity':base_velocity
    }


def update_drum_params(input_args, default_params):
    """A function to handle user input to a specific drum hit.

    Args:
        - input_args (string): passed from argparser, handled here.
        - default_params (dict): the default parameters

    Returns:
        - drum_params (dict): updated dictionary of parameters.
    """
    try:
        as_dict = ast.literal_eval(str(input_args))
    except ValueError:
        base_params = get_base_params(0, 0, 0, 0)
        print(f'The input string: `{input_args}` is not in the right format.')
        print('The input and each key should be enclosed in quotes.')
        print('Heres an example:')
        example = """ -kick "{'division':2}" """
        print('\t', example)
        print('Poissible parameters are: ')
        [print('\t', k) for k in base_params.keys()]

    for k, v in as_dict.items():
        default_params[k] = v
    return default_params



def get_division(beat, n_beats, hit_division, offset):
    """A fucntion to get a beat division pf the phrase length.

    Args:
        - beat (int): the number of timesteps of a default quarter note. 480
            is standard for 120bpm.
        - n_beats (int): number of beats in the phrase
        - hit_division (float): the number evenly distributed hits to place in
            the phrase

    Returns:
        - timings (list of int): a list of evenly space note durations (lengths)
    """
    BEAT_OFFSET = beat * offset

    # compute beat divisions
    phrase_length = int(beat * n_beats)
    hit_length = int(phrase_length / hit_division)
    n_hits = int(phrase_length / hit_length)
    timings = [hit_length] * int(n_hits)

    #always assume we should hit on beat 1 (t=0)
    timings = [BEAT_OFFSET] + timings

    # strip 'extra' hits
    extra_hits = np.argwhere(np.cumsum(timings) > phrase_length)
    [timings.pop(i[0]) for i in extra_hits]

    return timings


def build_beat(beat, n_beats, drums, save_path):
    """A function to create a single track midi object.

    Default is 120bpm.

    Args:
        - beat (int): beat length value of a 'quarter note' at 120bpm,
            480 represents a 'regular' quarter note.
        - n_beats (int): the maximum number of 'beats' as defined above of
            the entire phrase. phrase may be shorter.
        - drums (list of dict): the list of different drum parameters.
        - save_path (str): what to name the file
    """
    # (synchronous): all tracks start at the same time
    mid = MidiFile(type=1)

    for hit in drums:

        track = MidiTrack()
        mid.tracks.append(track)

        note = hit['midi']
        timings = get_division(beat=BEAT, n_beats=N_BEATS,
                               hit_division=hit['division'], offset=hit['offset'])

        velocity = hit['base_velocity']

        for t in timings:
            track.append(Message('note_on',
                                note=note,
                                velocity=velocity,
                                time=t))

            track.append(Message('note_off',
                                note=note,
                                channel=0,
                                velocity=velocity,
                                time=0))

    mid.save(save_path)


if __name__ == "__main__":
    desc = """A Python3 commandline tool to generate midi melodies. """
    parser = argparse.ArgumentParser(description=desc)

    parser.add_argument("-n", default=10,
                        help="Number of melodies to generate.")

    parser.add_argument("-output", nargs='?', default='output/',
                        help="Output path. Defaults to `output/`. Path is\
                        relative to execution.")

    parser.add_argument("-beat", nargs='?', default=480,
                        help="Beat length value of a 'quarter note' at 120bpm,\
                            480 represents a 'regular' quarter note.")

    parser.add_argument("-n_beats", nargs='?', default=16,
                        help="The maximum number of 'beats' from the `beat`\
                        parameter of the entire phrase. Phrase may be shorter.")

    parser.add_argument("-kick", nargs='?', default=None,
                        help="The kick parameters. Expects a dictionary input:\
                        {'division':2, 'offset':4}.")

    parser.add_argument("-snare", nargs='?', default=None,
                        help="The snare parameters. Expects a dictionary input:\
                        {'division':2, 'offset':4}.")

    parser.add_argument("-hh1", nargs='?', default=None,
                        help="The hi-hit (1) parameters. Expects a dictionary input:\
                        {'division':2, 'offset':4}.")

    parser.add_argument("-hh2", nargs='?', default=None,
                        help="The hi-hit (2) parameters. Expects a dictionary input:\
                        {'division':2, 'offset':4}.")

    parser.add_argument("-vel", nargs='?', default=100,
                        help="Velocity of the notes.")

    args = parser.parse_args()

    # argumnent variables
    N = int(args.n)
    OUTPUT_PATH = args.output
    BEAT = int(args.beat)
    N_BEATS = int(args.n_beats)
    VELOCITY = int(args.vel)

    ######## KICK
    KICK = get_base_params(midi=36,
                           division=8,
                           offset=0,
                           base_velocity=100)

    if not args.kick is None:
        KICK = update_drum_params(str(args.kick), KICK)

    ######## SNARE
    SNARE = get_base_params(midi=37,
                            division=4,
                            offset=1,
                            base_velocity=100)

    if not args.snare is None:
        SNARE = update_drum_params(str(args.snare), SNARE)

    ######## HH1
    HH1 = get_base_params(midi=38,
                          division=16,
                          offset=0,
                          base_velocity=100)

    if not args.hh1 is None:
        HH1 = update_drum_params(str(args.hh1), HH1)

    ######## HH2
    HH2 = get_base_params(midi=39,
                          division=32,
                          offset=0,
                          base_velocity=100)

    if not args.hh2 is None:
        HH2 = update_drum_params(str(args.hh2), HH2)

    ######## Full drum set
    DRUMSET = [KICK, SNARE, HH1, HH2]

    print("INPUT PARAMETERS:")
    print(f'Beat: {BEAT}')
    print(f'Phrase Length (in beats): {N_BEATS}')
    print(f'Kick Params:')
    [print(f'\t{k}:{v}') for k,v in KICK.items()]
    print(f'Snare Params:')
    [print(f'\t{k}:{v}') for k,v in SNARE.items()]
    print(f'Hi-Hat 1 Params:')
    [print(f'\t{k}:{v}') for k,v in HH1.items()]
    print(f'Hi-Hat 2 Params:')
    [print(f'\t{k}:{v}') for k,v in HH2.items()]
    
    for i in range(N):
        save_path = f'{OUTPUT_PATH}TEST_{i}.mid'
        build_beat(beat=BEAT, n_beats=N_BEATS, drums=DRUMSET,
                   save_path=save_path)
