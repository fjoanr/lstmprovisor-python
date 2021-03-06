import sys
import leadsheet
import argparse

def main(files, output=None, verbose=False):
    melody = []
    chords = []
    for f in files:
        if verbose:
            print(f)
        nc,nm = leadsheet.parse_leadsheet(f, verbose)
        melody.extend(nm)
        chords.extend(nc)
    if output is None:
        output = files[0] + "-cat.ls"
    leadsheet.write_leadsheet(chords, melody, output)

parser = argparse.ArgumentParser(description='Concatenate leadsheet files.')
parser.add_argument('files', nargs='+', help='Files to process')
parser.add_argument('--output', help='Name of the output file')
parser.add_argument('--verbose', action="store_true", help='Be verbose about processing')

if __name__ == '__main__':
    args = parser.parse_args()
    main(**vars(args))