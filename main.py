from models import SimpleModel, ProductOfExpertsModel
from note_encodings import RelativeJumpEncoding, ChordRelativeEncoding
import leadsheet
import training
import pickle

import sys
import os

import numpy as np
import relative_data

def main(dataset="dataset", outputdir="output"):
    # (100,10),(100,10)
    # (300,20),(300,20)
    m = ProductOfExpertsModel([RelativeJumpEncoding(), ChordRelativeEncoding()], [[(200,10),(200,10)], [(200,10),(200,10)]], ["drop","roll"], dropout=0.5, setup=False)
    m.setup_generate()
    m.setup_train()

    leadsheets = training.find_leadsheets(dataset)

    training.train(m, leadsheets, 50000, outputdir)

    pickle.dump( m.params, open( os.path.join(outputdir, "final_params.p"), "wb" ) )

if __name__ == '__main__':
    if len(sys.argv) == 1:
        main()
    else:
        main(sys.argv[1], sys.argv[2])