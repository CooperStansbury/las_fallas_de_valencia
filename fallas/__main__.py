import argparse
import ast
from mido import Message, MidiFile, MidiTrack
import numpy as np
import random
from distutils.util import strtobool


"""
TODO:
    - additive hit logic
    - add global control commands (things that affect all drums)
    - add a 'repeater' command?
    - add a tunable velocity curve (per track or global or both?)
    - swing/shuffle params?
"""

def get_base_params(midi, division, offset, remove, base_velocity,
                    probibility_add, depth_add, repeater):
    """A function to ensure that minimal functionality is in all drum
    params.

    Args:
        - midi (int): the note that the drum will trigger. Defaults set
            to trigger bottom row of default drum rack in Ableton.
        - division (int): how to divide the phrase for this drum hit
        - offset (int): number of beats (`beat` param) to shift the drum phrase
        - remove (float): the proportion of total hits that are removed (with)
            uniform distribution
        - base_velocity (int): the default velocity for the drum hit
        - probibility_add (float): the probability that given drum strike is
            used to trigger a new drum strike
        - depth_add (int): the granularity of the new strikes. Higher == closer
            together
        - repeater (int): hardly knower. the lamba value in the Poisson
            distribution that determines how many new stikes will be added

    Returns:
        - base_params (dict)
    """
    return {
        'midi':midi,
        'div':division,
        'off':offset,
        'rem':remove,
        'vel':base_velocity,
        'px_add':probibility_add,
        'depth': depth_add,
        'rep':repeater
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
        example = """ -kick "{'div':2}" """
        print('\t', example)
        print('Poissible parameters are: ')
        [print('\t', k) for k in base_params.keys()]
    except Exception as e:
        print(e)

    for k, v in as_dict.items():
        if k in default_params:
            default_params[k] = v
    return default_params


def get_division(beat, n_beats, hit_division, offset):
    """A fucntion to get a beat division of the phrase length.

    Args:
        - beat (int): the number of timesteps of a default quarter note. 480
            is standard for 120bpm.
        - n_beats (int): number of beats in the phrase
        - hit_division (float): the number evenly distributed hits to place in
            the phrase
        - offset (int): how many beats to offset the timings

    Returns:
        - timings (list of int): a list of evenly space note durations (lengths)
    """
    BEAT_OFFSET = int(beat * offset)

    # compute beat divisions
    phrase_length = int(beat * n_beats)
    hit_length = int(phrase_length / hit_division)
    n_hits = int(phrase_length / hit_length)
    timings = [hit_length] * int(n_hits)

    #always assume we should hit on beat 1 (t=0)
    timings = [BEAT_OFFSET] + timings

    return timings


def trim_timings(phrase_length, timings):
    """A function to remove beats that fall beyond the the bounds of the phrase

    Args:
        - phrase_length (int): the length of the phrase
        - timings (list of int): a list of evenly space note durations (lengths)

    Returns:
        - timings (list of int): updated list
    """
    extra_hits = np.argwhere(np.cumsum(timings) > int(phrase_length)).ravel()

    if len(extra_hits) != 0:
        all_to_end = np.min(extra_hits)
        del timings[all_to_end:]

    return timings


def beat_stripper(timings, removal_proportion):
    """A function to remove a proportion of the total number of hits based
    on uniform probability of removal.

    Args:
        - timings (list of int): a list of evenly space note durations (lengths)
        - removal_proportion (float): the proportion of items to remove (1=all)

    Returns:
        - timings (list of int): updated list
    """
    phrase_len = len(timings)
    n_to_rm = int(phrase_len * removal_proportion)
    rm_idx = np.random.randint(0, phrase_len-1, n_to_rm)

    timings_stripped = []
    for i, hit in enumerate(timings):
        if not i in rm_idx:
            timings_stripped.append(hit)
        else:
            timings_stripped.append(hit + hit)
    return timings_stripped


def beat_perturber(beat, timings, probibility_add, depth, repeater):
    """A function to change a beat timing pattern (additively)

    Args:
        - timings (list of int): a list of evenly space note durations (lengths)
        - change_prob (float): the probaility that a hit is used as trigger/root
            for a new hit
        - depth (int): the number of integer divisions of `BEAT` that are
            possible note position offsets (smaller means possible to clump)
        - repeater (int): the lambda in the poisson distribition use to
            determine how many new hits are added (w/ constant timings)

    Returns:
        - timings (list of int): updated list
    """
    # the possibilities
    perturbances = []

    for i in range(2, depth+2):
        perturbances.append(int(beat / i))

    # roll a Gaussian distributition for every
    # current drum hit, perturb those below the probability threshold
    px_vec = np.random.random(len(timings)-1)
    indices_to_perturb = np.argwhere(px_vec < probibility_add).ravel()

    for idx in indices_to_perturb:
        # randomly sample from the 'perturbenaces'
        random_perturb = np.random.choice(perturbances, 1)[0]
        n_reps = np.random.poisson(repeater)
        timings = timings[0:idx] + ([random_perturb] * n_reps) + timings[idx:]

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
    phrase_length = int(beat * n_beats)
    # (synchronous): all tracks start at the same time
    mid = MidiFile(type=1)

    for hit in drums:
        track = MidiTrack()
        mid.tracks.append(track)

        note = hit['midi']
        timings = get_division(beat=BEAT,
                               n_beats=N_BEATS,
                               hit_division=hit['div'],
                               offset=hit['off'])

        # random removal logic
        timings = beat_stripper(timings=timings, removal_proportion=hit['rem'])

        # add hits
        timings = beat_perturber(beat=beat, timings=timings,
                                 probibility_add=hit['px_add'],
                                 depth=hit['depth'],
                                 repeater=hit['rep'])

        timings = trim_timings(phrase_length=phrase_length, timings=timings)

        # STUBBED for fun Fourier velcoity profiles
        velocity = hit['vel']

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
                        {'div':2, 'offset':4}.")

    parser.add_argument("-snare", nargs='?', default=None,
                        help="The snare parameters. Expects a dictionary input:\
                        {'div':2, 'offset':4}.")

    parser.add_argument("-hh1", nargs='?', default=None,
                        help="The hi-hit (1) parameters. Expects a dictionary input:\
                        {'div':2, 'offset':4}.")

    parser.add_argument("-hh2", nargs='?', default=None,
                        help="The hi-hit (2) parameters. Expects a dictionary input:\
                        {'div':2, 'offset':4}.")

    parser.add_argument("-vel", nargs='?', default=100,
                        help="Velocity of the notes.")

    args = parser.parse_args()

    # input variables
    N = args.n
    OUTPUT_PATH = args.output
    BEAT = args.beat
    N_BEATS = args.n_beats
    VELOCITY = args.vel

    ######## KICK
    KICK = get_base_params(midi=36,
                           division=8,
                           offset=0,
                           remove=0,
                           base_velocity=100,
                           probibility_add=.1,
                           depth_add=2,
                           repeater=1)

    if not args.kick is None:
        KICK = update_drum_params(str(args.kick), KICK)

    ######## SNARE
    SNARE = get_base_params(midi=37,
                            division=4,
                            offset=2,
                            remove=0,
                            base_velocity=100,
                            probibility_add=0,
                            depth_add=0,
                            repeater=0)

    if not args.snare is None:
        SNARE = update_drum_params(str(args.snare), SNARE)

    ######## HH1
    HH1 = get_base_params(midi=38,
                          division=8,
                          offset=0,
                          remove=.7,
                          base_velocity=100,
                          probibility_add=.3,
                          depth_add=3,
                          repeater=4)

    if not args.hh1 is None:
        HH1 = update_drum_params(str(args.hh1), HH1)

    ######## HH2
    HH2 = get_base_params(midi=39,
                          division=32,
                          offset=0,
                          remove=.25,
                          base_velocity=100,
                          probibility_add=.1,
                          depth_add=2,
                          repeater=6)

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

    for i in range(int(N)):
        save_path = f'{OUTPUT_PATH}TEST_{i}.mid'
        build_beat(beat=BEAT, n_beats=N_BEATS, drums=DRUMSET,
                   save_path=save_path)
