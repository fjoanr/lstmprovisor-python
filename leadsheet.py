import sexpdata
import re
from pprint import pprint
import fractions
import itertools

import constants
from functools import reduce

import numpy as np

def rotate(li, x):
    """
    Rotate list li by x spaces to the right, i.e.
        rotate([1,2,3,4],1) -> [4,1,2,3]
    """
    return li[-x % len(li):] + li[:-x % len(li)]

def chunkwise(t, size=2):
    """
    Return an iterator of tuples of size
    """
    it = iter(t)
    return zip(*[it]*size)

def gcd(it):
    def _gcd_helper(a,b):
        if a==0:
            return b
        else:
            return _gcd_helper(b%a, a)
    return reduce(_gcd_helper, it)

def repeat_print(li):

    last = None
    lastct = 0
    for c in li+[None]:
        if c == last:
            lastct += 1
        else:
            if last is not None:
                print(last, "*", lastct)
            last = c
            lastct = 1


def parse_chord(cstr,verbose=False):
    """
    Given a string representation of a chord, return a binary representation
    as a list of length 12, starting with C.
    """
    if cstr == "NC":
        return 0, constants.CHORD_TYPES["NC"]
    chord_match = re.match(r"([A-G](?:#|b)?)([^/]*)(?:/(.+))?", cstr)
    root_note, ctype, slash_note = chord_match.groups()

    try:
        ctype_vec = constants.CHORD_TYPES[ctype]
    except KeyError:
        if(verbose):
            print("WARNING: Could not find chord {}, substituting NC".format(cstr))
        ctype_vec = constants.CHORD_TYPES['NC']

    root_offset = constants.CHORD_NOTE_OFFSETS[root_note]
    if slash_note is None:
        return root_offset, ctype_vec
    else:
        # For a slash chord, we need to add the slashed note to the chord,
        # and also make it the bass note
        slash_offset = constants.CHORD_NOTE_OFFSETS[slash_note]
        shifted_ctype_vec = rotate(ctype_vec, root_offset-slash_offset)
        shifted_ctype_vec[0] = 1
        return slash_offset, shifted_ctype_vec


def parse_duration(durstr):
    accum_dur = 0

    parts = durstr.split("+")
    for part in parts:
        dot_match = re.match(r"([^\.]*)(\.*)", part)
        part = dot_match.group(1)
        num_dots = len(dot_match.group(2))

        tupl_parts = part.split("/")
        if len(tupl_parts) == 1:
            # Not a tuplet
            [dur_frac_str] = tupl_parts
            dur_frac = int(dur_frac_str)
            assert constants.WHOLE % dur_frac == 0, "Bad duration {} -> {} / {}".format(durstr, constants.WHOLE, dur_frac)
            slots = constants.WHOLE // dur_frac
        else:
            [dur_frac_str, tuplet_str] = tupl_parts
            dur_frac = int(dur_frac_str)
            dur_tupl = int(tuplet_str)
            assert (constants.WHOLE * (dur_tupl-1)) % (dur_frac * dur_tupl) == 0, "Bad duration {} -> {} / {}".format(durstr, (constants.WHOLE * (dur_tupl-1)), (dur_frac * dur_tupl))
            slots = constants.WHOLE * (dur_tupl-1) // (dur_frac * dur_tupl)

        for i in range(num_dots):
            assert (slots * 3) % 2 == 0, "Bad duration {} -> {} / {}".format(durstr, (slots * 3), 2)
            slots = slots * 3 // 2

        accum_dur += slots

    assert accum_dur % constants.RESOLUTION_SCALAR == 0, "Bad duration {}: {} not a multiple of resolution {}".format(durstr, accum_dur, constants.RESOLUTION_SCALAR)
    return accum_dur//constants.RESOLUTION_SCALAR

def parse_note(nstr):
    """
    Given a string representation of a note, return (midiOrNone, duration)
    """
    note_match = re.match(r"((?:[a-g]|r)(?:[#b]?))([\+\-]*)(.*)", nstr)
    note = note_match.group(1)
    octaveshift_str = note_match.group(2)
    duration_str = note_match.group(3)

    octaveshift = sum({"+":1,"-":-1}[x] for x in octaveshift_str)
    if nstr[0] == 'r':
        midival = None
    else:
        midival = constants.MIDDLE_C_MIDI + (constants.OCTAVE * octaveshift) + constants.NOTE_OFFSETS[note]

    duration = parse_duration(duration_str)

    return (midival, duration)


def parse_leadsheet(fn,verbose=False):
    with open(fn,'r') as f:
        contents = "\n".join(f.readlines())
    parsed = sexpdata.loads("({})".format(contents.replace("'","")))

    parts = [('default','',[])]
    for p in parsed:
        if not isinstance(p, list):
            parts[-1][2].append(p.value())
        elif not isinstance(p[0], list) and p[0].value() == 'part':
            def strval(x):
                return x.value() if isinstance(x,sexpdata.Symbol) else str(x)
            part_type = next((' '.join(strval(x) for x in l[1:]) for l in p if isinstance(l,list) and l[0].value() == "type"), None)
            title = next((' '.join(strval(x) for x in l[1:]) for l in p if isinstance(l,list) and l[0].value() == "title"), '')
            parts.append((part_type, title, []))

    chord_parts = [x for x in parts if x[0]=='chords']
    if len(chord_parts) == 0:
        chord_parts = [x for x in parts if x[0]=='default']
    assert len(chord_parts) == 1, 'Wrong number of chord parts!'

    chords_raw = [x for x in chord_parts[0][2] if x[0].isupper() or x in ("|", "/")]
    chords = []
    partial_measure = []
    last_chord = None
    for c in chords_raw:
        if c == "|":
            length_each = constants.WHOLE//(len(partial_measure)*constants.RESOLUTION_SCALAR)
            for chord in partial_measure:
                for x in range(length_each):
                    chords.append(chord)
            partial_measure = []
        else:
            if c != "/":
                last_chord = parse_chord(c,verbose)
            partial_measure.append(last_chord)

    melody = []
    for part_type, title, part_data in parts:
        if part_type == 'melody':
            melody_raw = [x for x in part_data if x[0].islower()]
            melody_proc = [parse_note(x) for x in melody_raw]
            mlen = sum(dur for n,dur in melody_proc)
            if mlen < len(chords):
                melody_proc.append((None, len(chords)-mlen))
            melody.extend(melody_proc)

    # print "Raw Chords: " + " ".join(chords_raw)
    # print "Raw Melody: " + " ".join(melody_raw)

    # print "Parsed chords: "
    # repeat_print(chords)
    # print "Parsed melody: "
    # pprint(melody)

    clen = len(chords)
    mlen = sum(dur for n,dur in melody)
    # Might have multiple melodies over the same chords
    assert mlen % clen == 0, "Notes and chords don't match in {}: {}, {}".format(fn, clen,mlen)

    return chords, melody

def constrain_melody(melody,bounds):
    new_melody = []
    for n,dur in melody:
        if n is None:
            new_melody.append((n,dur))
        else:
            while n >= bounds.highbound:
                n -= 12
            while n < bounds.lowbound:
                n += 12
            new_melody.append((n,dur))
    return new_melody

def get_leadsheet_length(chords, melody):
    return sum(dur for n,dur in melody)

def slice_leadsheet(chords, melody, start, end):

    sliced_melody_start = []
    sliced_melody_full = []

    timestep = 0
    for n,dur in melody:
        if start-dur < timestep <= start:
            sliced_melody_start.append((n,timestep+dur-start))
        elif start < timestep:
            sliced_melody_start.append((n,dur))
        timestep += dur

    timestep = start
    for n,dur in sliced_melody_start:
        if timestep < end-dur:
            sliced_melody_full.append((n,dur))
        elif end-dur <= timestep < end:
            sliced_melody_full.append((n,end-timestep))
        timestep += dur

    sliced_chords = [chords[i%len(chords)] for i in range(start,end)]

    clen = len(sliced_chords)
    mlen = sum(dur for n,dur in sliced_melody_full)
    assert clen == mlen, "clen {} and mlen {} do not match".format(clen,mlen)

    return sliced_chords, sliced_melody_full

def write_duration(duration):
    """
    Convert a number of slots to a duration string
    """
    q_dir = constants.QUARTER//constants.RESOLUTION_SCALAR
    whole_dir = constants.WHOLE//constants.RESOLUTION_SCALAR

    if duration > whole_dir:
        # Longer than a measure
        return "1+{}".format(write_duration(duration - whole_dir))
    elif q_dir % duration == 0:
        # Simple, shorter than a quarter note
        return {
            12:"32/3",
            6:"16/3",
            4:"16",
            3:"8/3",
            2:"8",
            1:"4"
        }[ q_dir//duration ]
    elif duration % q_dir == 0:
        # Simple, longer than a quarter note
        return {
            1:"4",
            2:"2",
            3:"2.",
            4:"1"
        }[ duration//q_dir ]
    elif duration > q_dir:
        # Longer than a quarter note, but not evenly divisible.
        # Break up long and short parts
        q_parts = duration % q_dir
        return "{}+{}".format(write_duration(duration-q_parts), write_duration(q_parts))
    else:
        # Find the shortest representation
        best = None
        for i in range(1,duration//2):
            cur_try = "{}+{}".format(write_duration(duration-i),write_duration(i))
            if best is None or len(cur_try) < len(best):
                best = cur_try
        return cur_try

def write_melody(melody):
    """
    Convert a list of melody to a string
    """
    notes = []
    for midi, dur in melody:
        if midi is None:
            notename = "r"
            octave_adj = ""
        else:
            delta_from_middle = midi - constants.MIDDLE_C_MIDI
            octaves = delta_from_middle // 12
            pitchclass = delta_from_middle % 12
            notename = list(constants.NOTE_OFFSETS.keys())[list(constants.NOTE_OFFSETS.values()).index(pitchclass)]

            if octaves < 0:
                octave_adj = "-"*(-octaves)
            else:
                octave_adj = "+"*octaves

        duration_str = write_duration(dur)

        notes.append(notename + octave_adj + duration_str)

    return " ".join(notes)

def write_chords(chords):
    """
    Convert a list of chords to a string
    """
    whole_dir = constants.WHOLE//constants.RESOLUTION_SCALAR

    parts = []
    for measure in chunkwise(chords, whole_dir):
        partial_measure = []
        last_seen = None
        for chord in measure:
            if chord == last_seen:
                partial_measure[-1][1] += 1
            else:
                last_seen = chord
                root,ctype = chord
                if ctype == constants.CHORD_TYPES["NC"]:
                    chord_str = "NC"
                else:
                    if ctype in list(constants.CHORD_TYPES.values()):
                        t_idx = list(constants.CHORD_TYPES.values()).index(ctype)
                        ctype_s = list(constants.CHORD_TYPES.keys())[t_idx]

                        r_idx = list(constants.CHORD_NOTE_OFFSETS.values()).index(root)
                        root_s = list(constants.CHORD_NOTE_OFFSETS.keys())[r_idx]

                        chord_str = root_s + ctype_s
                    else:
                        # Try slash chords: "root" is bass, look for true root
                        bass = root
                        mod_ctype = [0] + ctype[1:]
                        for offset in range(1,12):
                            true_root = (bass + offset) % 12
                            shifted_chord = rotate(ctype, -offset)
                            mod_shifted_chord = rotate(mod_ctype, -offset)
                            if shifted_chord in list(constants.CHORD_TYPES.values()):
                                t_idx = list(constants.CHORD_TYPES.values()).index(shifted_chord)
                            elif mod_shifted_chord in list(constants.CHORD_TYPES.values()):
                                t_idx = list(constants.CHORD_TYPES.values()).index(mod_shifted_chord)
                            else:
                                continue

                            ctype_s = list(constants.CHORD_TYPES.keys())[t_idx]

                            r_idx = list(constants.CHORD_NOTE_OFFSETS.values()).index(true_root)
                            root_s = list(constants.CHORD_NOTE_OFFSETS.keys())[r_idx]

                            slash_idx = list(constants.CHORD_NOTE_OFFSETS.values()).index(bass)
                            slash_s = list(constants.CHORD_NOTE_OFFSETS.keys())[slash_idx]

                            chord_str = root_s + ctype_s + '/' + slash_s
                            break
                        else:
                            print("Not a valid chord!")
                            chord_str = "NC"

                partial_measure.append([chord_str, 1])

        divisor = gcd(x[1] for x in partial_measure)
        for chord_str, ct in partial_measure:
            for _ in range(ct//divisor):
                parts.append(chord_str)
        parts.append("|")

    return " ".join(parts)

def write_leadsheet(chords, melody, filename=None):
    """
    Convert chords and a melody to a leadsheet file
    """
    full_leadsheet = """
(section (style swing))

(part (type chords))
{}
(part (type melody))
{}
""".format(write_chords(chords), write_melody(melody))

    if filename is not None:
        with open(filename,'w') as f:
            f.write(full_leadsheet)
    else:
        return full_leadsheet

