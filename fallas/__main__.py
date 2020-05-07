import argparse
from mido import Message, MidiFile, MidiTrack
import numpy as np
import random
from distutils.util import strtobool

# def get_timings(beat, max_length, rand_beat):
def get_timings(beat, max_length):
    """A function to return a list of note timings.

    Args:
        - beat (int): beat length value of a 'quarter note' at 120bpm,
            480 represents a 'regular' quarter note
        - max_length (int): the maximum number of 'beats' as defined above of
            the entire phrase. phrase may be shorter.
        - rand_beat (bool): should the beats be randon (True), or uniform
            (False)?

    Returns:
        - timings (list): a list of note durations
    """
    BEATS = [int(beat/4),
             int(beat/2),
             int(beat),
             int(beat*2),
             int(beat*4)]

    total_steps = beat * max_length
    timings = [beat] * max_length
    return timings


def build_beat(beat, max_length, save_path):
    """A function to create a single track midi object.

    Default is 120bpm.

    Args:
        - beat (int): beat length value of a 'quarter note' at 120bpm,
            480 represents a 'regular' quarter note.
        - max_length (int): the maximum number of 'beats' as defined above of
            the entire phrase. phrase may be shorter.
        - rand_beat (bool): should the beats be randon (True), or uniform
            (False)?
        - velocity (int): velocity of the midi notes
        - rests (bool): if true output will contain random offsets in note
            start position
        - save_path (str): what to name the file
    """
    # (synchronous): all tracks start at the same time
    mid = MidiFile(type=1)
    track = MidiTrack()
    mid.tracks.append(track)

    timings = get_timings(beat, max_length)

    # temp vars
    note = MIDI_MAP['kick']
    velocity = 100

    t = 0
    for timing in timings:
        track.append(Message('note_on', note=note,
                             velocity=velocity, time=t))
        track.append(Message('note_off', note=note,
                             velocity=velocity, time=timing+t))

        t += timing


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

    parser.add_argument("-max_length", nargs='?', default=16,
                        help="The maximum number of 'beats' from the `beat`\
                        parameter of the entire phrase. Phrase may be shorter.")

    # parser.add_argument("-tracks", nargs='?', default=1,
    #                     help="The number of 'voices' (as separate tracks) in\
    #                     the output files.")
    #

    #
    # parser.add_argument("-rand_beat", nargs='?', default=True,
    #                     help="Should the beats be random (True), or should they\
    #                     be constant (False)?")
    #
    # parser.add_argument("-vel", nargs='?', default=100,
    #                     help="Velocity of the notes.")
    #
    # parser.add_argument("-rests", nargs='?', default=False,
    #                     help="Should the output contain random rests?")

    args = parser.parse_args()

    global MIDI_MAP

    MIDI_MAP = {
        'kick':36,
        'snare':37,
        'hat1':38,
        'hat2':39,
        'perc1':40,
        'perc2':41
    }

    N = int(args.n)
    OUTPUT_PATH = args.output
    BEAT = int(args.beat)
    MAX_LENGTH = int(args.max_length)

    # TRACKS = int(args.tracks)
    # VELOCITY = int(args.vel)
    # RESTS = args.rests
    # RAND_BEAT = args.rand_beat


    # print("INPUT PARAMETERS:")
    # print(f'Velocity: {VELOCITY}')
    # print(f'Beat: {BEAT}')
    # print(f'Maximum Phrase Length: {MAX_LENGTH}')
    # print(f'Random Beats: {RAND_BEAT}')
    # print(f'Tracks: {TRACKS}')
    # print(f'Rests Enabled: {RESTS}')


    for i in range(N):
        save_path = f'{OUTPUT_PATH}TEST_{i}.mid'
        build_beat(beat=BEAT, max_length=MAX_LENGTH, save_path=save_path)

        # build_beat(beat=BEAT,max_length=MAX_LENGTH, rand_beat=RAND_BEAT,
        #       velocity=VELOCITY,rests=RESTS,save_path=save_path)
