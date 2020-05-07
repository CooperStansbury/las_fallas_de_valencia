import argparse
from mido import Message, MidiFile, MidiTrack
import numpy as np
import random
from distutils.util import strtobool


"""
TODO:
    - add a tunable velocity curve (per track or global or both?)
    - create subtractive/additive hit logic
"""

def get_division(beat, n_beats, hit_division):
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
    phrase_length = beat * n_beats
    hit_length = int(phrase_length/hit_division)
    n_hits = int(phrase_length/hit_length)
    timings = [hit_length] * n_hits
    return timings



def build_beat(beat, n_beats, velocity, divisions, offsets, save_path):
    """A function to create a single track midi object.

    Default is 120bpm.

    Args:
        - beat (int): beat length value of a 'quarter note' at 120bpm,
            480 represents a 'regular' quarter note.
        - n_beats (int): the maximum number of 'beats' as defined above of
            the entire phrase. phrase may be shorter.
        - velocity (int): velocity of the midi notes
        - divisions (dict): specific beat divisions for each hit
        - offsets (dict): specific beat offsets for each hit
        - save_path (str): what to name the file
    """
    # (synchronous): all tracks start at the same time
    mid = MidiFile(type=1)

    for hit, div in divisions.items():

        track = MidiTrack()
        mid.tracks.append(track)

        note = MIDI_MAP[hit]
        timings = get_division(beat=BEAT, n_beats=N_BEATS, hit_division=div)

        # offset = offsets[hit]
        # # alter timings based on offset
        # timings[0] += offset
        # timings[len(timings)-1] -= offset

        intial_hit = 0
        if offsets[hit]:
            intial_hit = timings[0]
            timings = timings[:-1] # all but last hit


        for t in timings:
            track.append(Message('note_on',
                                note=note,
                                velocity=velocity,
                                time=t))

            track.append(Message('note_off',
                                note=note,
                                channel=0,
                                velocity=velocity,
                                time=div))
    mid.save(save_path)

    # track = MidiTrack()
    # mid.tracks.append(track)
    #
    # kick = MIDI_MAP['kick']
    # snare = MIDI_MAP['snare']
    #
    # t = 0
    # for timing in phrase_length:
    #
    #     track.append(Message('note_on',
    #                         note=kick,
    #                         channel=0,
    #                         velocity=velocity,
    #                         time=0))
    #
    #     track.append(Message('note_on',
    #                         note=snare,
    #                         channel=1,
    #                         velocity=velocity,
    #                         time=0))
    #
    #     track.append(Message('note_off',
    #                         note=kick,
    #                         channel=0,
    #                         velocity=velocity,
    #                         time=beat))
    #
    #     track.append(Message('note_off',
    #                         note=snare,
    #                         channel=1,
    #                         velocity=velocity,
    #                         time=0))
    #
    #     t += timing
    #
    #
    # mid.save(save_path)


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

    parser.add_argument("-vel", nargs='?', default=100,
                        help="Velocity of the notes.")

    # parser.add_argument("-tracks", nargs='?', default=1,
    #                     help="The number of 'voices' (as separate tracks) in\
    #                     the output files.")

    # parser.add_argument("-rand_beat", nargs='?', default=True,
    #                     help="Should the beats be random (True), or should they\
    #                     be constant (False)?")

    # parser.add_argument("-rests", nargs='?', default=False,
    #                     help="Should the output contain random rests?")

    args = parser.parse_args()

    # argumnent variables
    N = int(args.n)
    OUTPUT_PATH = args.output
    BEAT = int(args.beat)
    N_BEATS = int(args.n_beats)
    VELOCITY = int(args.vel)

    # we'll hardcode ableton drum rack mappings for now
    global MIDI_MAP
    MIDI_MAP = {
        'kick':36,
        'snare':37,
        'hh1':38,
        'hh2':39,
    }

    DIVISIONS = {
        'kick':4,
        'snare':4,
        'hh1':8,
        'hh2':16
    }

    OFFSETS = {
        'kick':False,
        'snare':True,
        'hh1':False,
        'hh2':False
    }


    # TRACKS = int(args.tracks)
    # RESTS = args.rests
    # RAND_BEAT = args.rand_beat

    print("INPUT PARAMETERS:")
    print(f'Beat: {BEAT}')
    print(f'Phrase Length (in beats): {N_BEATS}')
    print(f'Velocity: {VELOCITY}')
    # print(f'Random Beats: {RAND_BEAT}')
    # print(f'Tracks: {TRACKS}')
    # print(f'Rests Enabled: {RESTS}')


    for i in range(N):
        save_path = f'{OUTPUT_PATH}TEST_{i}.mid'
        build_beat(beat=BEAT, n_beats=N_BEATS, divisions=DIVISIONS,
                   offsets=OFFSETS, velocity=VELOCITY,save_path=save_path)

        # build_beat(beat=BEAT,max_length=MAX_LENGTH, rand_beat=RAND_BEAT,
        #       velocity=VELOCITY,rests=RESTS,save_path=save_path)
