import argparse
import time
import sys
import os

def main(modeltype, dataset="dataset", outputdir="output", validation=None, resume=None, check_nan=False, generate=False, generate_over=None):
    from models import SimpleModel, ProductOfExpertsModel, CompressiveAutoencoderModel
    from note_encodings import AbsoluteSequentialEncoding, RelativeJumpEncoding, ChordRelativeEncoding, CircleOfThirdsEncoding
    from queue_managers import StandardQueueManager, VariationalQueueManager
    import input_parts
    import leadsheet
    import training
    import pickle
    import theano
    import theano.tensor as T


    import numpy as np
    import relative_data
    import constants


    generate = generate or (generate_over is not None)
    should_setup = not generate
    unroll_batch_num = None if generate else training.BATCH_SIZE
    model_builders = {
        "simple_abs": (lambda:
            SimpleModel(
                AbsoluteSequentialEncoding(constants.BOUNDS.lowbound, constants.BOUNDS.highbound),
                [(300,0),(300,0)],
                dropout=0.5, setup=should_setup, nanguard=check_nan, unroll_batch_num=unroll_batch_num)),
        "simple_rel": (lambda:
            SimpleModel(
                RelativeJumpEncoding(),
                [(200,10),(200,10)],
                dropout=0.5, setup=should_setup, nanguard=check_nan, unroll_batch_num=unroll_batch_num)),
        "simple_rel_npn": (lambda:
            SimpleModel(
                RelativeJumpEncoding(),
                [(300,0),(300,0)],
                dropout=0.5, setup=should_setup, nanguard=check_nan, unroll_batch_num=unroll_batch_num)),
        "simple_cot": (lambda:
            SimpleModel(
                CircleOfThirdsEncoding(constants.BOUNDS.lowbound, (constants.BOUNDS.highbound-constants.BOUNDS.lowbound)//12),
                [(300,0),(300,0)],
                bounds=constants.NoteBounds(48, 84),
                dropout=0.5, setup=should_setup, nanguard=check_nan, unroll_batch_num=unroll_batch_num)),
        "poex": (lambda:
            ProductOfExpertsModel(
                [RelativeJumpEncoding(), ChordRelativeEncoding()],
                [[(200,10),(200,10)], [(200,10),(200,10)]],
                shift_modes=["drop","roll"],
                dropout=0.5, setup=should_setup, nanguard=check_nan, unroll_batch_num=unroll_batch_num)),
        "poex_npn": (lambda:
            ProductOfExpertsModel(
                [RelativeJumpEncoding(), ChordRelativeEncoding()],
                [[(300,0),(300,0)], [(300,0),(300,0)]],
                shift_modes=["drop","roll"],
                dropout=0.5, setup=should_setup, nanguard=check_nan, unroll_batch_num=unroll_batch_num)),
        "compae_std_abs": (lambda:
            CompressiveAutoencoderModel(
                StandardQueueManager(100, loss_fun=(lambda x: T.log(1+99*x)/T.log(100))),
                [AbsoluteSequentialEncoding(constants.BOUNDS.lowbound, constants.BOUNDS.highbound)],
                [[(300,0),(300,0)]],
                [[(300,0),(300,0)]],
                inputs=[[input_parts.BeatInputPart(),
                  input_parts.ChordShiftInputPart()]],
                shift_modes=["drop"],
                dropout=0.5, setup=should_setup, nanguard=check_nan, unroll_batch_num=unroll_batch_num)),
        "compae_std_abs_wipt": (lambda:
            CompressiveAutoencoderModel(
                StandardQueueManager(100, loss_fun=(lambda x: T.log(1+99*x)/T.log(100))),
                [AbsoluteSequentialEncoding(constants.BOUNDS.lowbound, constants.BOUNDS.highbound)],
                [[(300,0),(300,0)]],
                [[(300,0),(300,0)]],
                inputs=[[input_parts.BeatInputPart(),
                  input_parts.ChordShiftInputPart()]],
                shift_modes=["drop"],
                hide_output=False,
                dropout=0.5, setup=should_setup, nanguard=check_nan, unroll_batch_num=unroll_batch_num)),
        "compae_std_cot": (lambda:
            CompressiveAutoencoderModel(
                StandardQueueManager(100, loss_fun=(lambda x: T.log(1+99*x)/T.log(100))),
                [CircleOfThirdsEncoding(constants.BOUNDS.lowbound, (constants.BOUNDS.highbound-constants.BOUNDS.lowbound)//12)],
                [[(300,0),(300,0)]],
                [[(300,0),(300,0)]],
                inputs=[[input_parts.BeatInputPart(),
                  input_parts.ChordShiftInputPart()]],
                shift_modes=["drop"],
                bounds=constants.NoteBounds(48, 84),
                dropout=0.5, setup=should_setup, nanguard=check_nan, unroll_batch_num=unroll_batch_num)),
        "compae_std_cot_wipt": (lambda:
            CompressiveAutoencoderModel(
                StandardQueueManager(100, loss_fun=(lambda x: T.log(1+99*x)/T.log(100))),
                [CircleOfThirdsEncoding(constants.BOUNDS.lowbound, (constants.BOUNDS.highbound-constants.BOUNDS.lowbound)//12)],
                [[(300,0),(300,0)]],
                [[(300,0),(300,0)]],
                inputs=[[input_parts.BeatInputPart(),
                  input_parts.ChordShiftInputPart()]],
                shift_modes=["drop"],
                hide_output=False,
                bounds=constants.NoteBounds(48, 84),
                dropout=0.5, setup=should_setup, nanguard=check_nan, unroll_batch_num=unroll_batch_num)),
        "compae_std_rel": (lambda:
            CompressiveAutoencoderModel(
                StandardQueueManager(100, loss_fun=(lambda x: T.log(1+99*x)/T.log(100))),
                [RelativeJumpEncoding()],
                [[(200,10),(200,10)]],
                [[(200,10),(200,10)]],
                shift_modes=["drop"],
                dropout=0.5, setup=should_setup, nanguard=check_nan, unroll_batch_num=unroll_batch_num)),
        "compae_std_poex": (lambda:
            CompressiveAutoencoderModel(
                StandardQueueManager(100, loss_fun=(lambda x: T.log(1+99*x)/T.log(100))),
                [RelativeJumpEncoding(), ChordRelativeEncoding()],
                [[(200,10),(200,10)], [(200,10),(200,10)]],
                [[(200,10),(200,10)], [(200,10),(200,10)]],
                shift_modes=["drop","roll"],
                dropout=0.5, setup=should_setup, nanguard=check_nan, unroll_batch_num=unroll_batch_num)),
        "compae_std_poex_wipt": (lambda:
            CompressiveAutoencoderModel(
                StandardQueueManager(100, loss_fun=(lambda x: T.log(1+99*x)/T.log(100))),
                [RelativeJumpEncoding(), ChordRelativeEncoding()],
                [[(200,10),(200,10)], [(200,10),(200,10)]],
                [[(200,10),(200,10)], [(200,10),(200,10)]],
                shift_modes=["drop","roll"],
                hide_output=False,
                dropout=0.5, setup=should_setup, nanguard=check_nan, unroll_batch_num=unroll_batch_num)),
        "compae_std_poex_npn": (lambda:
            CompressiveAutoencoderModel(
                StandardQueueManager(100, loss_fun=(lambda x: T.log(1+99*x)/T.log(100))),
                [RelativeJumpEncoding(), ChordRelativeEncoding()],
                [[(300,0),(300,0)], [(300,0),(300,0)]],
                [[(300,0),(300,0)], [(300,0),(300,0)]],
                shift_modes=["drop","roll"],
                dropout=0.5, setup=should_setup, nanguard=check_nan, unroll_batch_num=unroll_batch_num)),
        "compae_std_poex_npn_wipt": (lambda:
            CompressiveAutoencoderModel(
                StandardQueueManager(100, loss_fun=(lambda x: T.log(1+99*x)/T.log(100))),
                [RelativeJumpEncoding(), ChordRelativeEncoding()],
                [[(300,0),(300,0)], [(300,0),(300,0)]],
                [[(300,0),(300,0)], [(300,0),(300,0)]],
                shift_modes=["drop","roll"],
                hide_output=False,
                dropout=0.5, setup=should_setup, nanguard=check_nan, unroll_batch_num=unroll_batch_num)),
        "compae_var_abs": (lambda:
            CompressiveAutoencoderModel(
                VariationalQueueManager(100, loss_fun=(lambda x: T.log(1+99*x)/T.log(100))),
                [AbsoluteSequentialEncoding(constants.BOUNDS.lowbound, constants.BOUNDS.highbound)],
                [[(300,0),(300,0)]],
                [[(300,0),(300,0)]],
                inputs=[[input_parts.BeatInputPart(),
                  input_parts.ChordShiftInputPart()]],
                shift_modes=["drop"],
                dropout=0.5, setup=should_setup, nanguard=check_nan, unroll_batch_num=unroll_batch_num)),
        "compae_var_rel": (lambda:
            CompressiveAutoencoderModel(
                VariationalQueueManager(100, loss_fun=(lambda x: T.log(1+99*x)/T.log(100))),
                [RelativeJumpEncoding()],
                [[(200,10),(200,10)]],
                [[(200,10),(200,10)]],
                shift_modes=["drop"],
                dropout=0.5, setup=should_setup, nanguard=check_nan, unroll_batch_num=unroll_batch_num)),
        "compae_var_poex": (lambda:
            CompressiveAutoencoderModel(
                VariationalQueueManager(100, loss_fun=(lambda x: T.log(1+99*x)/T.log(100))),
                [RelativeJumpEncoding(), ChordRelativeEncoding()],
                [[(200,10),(200,10)], [(200,10),(200,10)]],
                [[(200,10),(200,10)], [(200,10),(200,10)]],
                shift_modes=["drop","roll"],
                dropout=0.5, setup=should_setup, nanguard=check_nan, unroll_batch_num=unroll_batch_num)),
        "compae_var_poex_wipt": (lambda:
            CompressiveAutoencoderModel(
                VariationalQueueManager(100, loss_fun=(lambda x: T.log(1+99*x)/T.log(100))),
                [RelativeJumpEncoding(), ChordRelativeEncoding()],
                [[(200,10),(200,10)], [(200,10),(200,10)]],
                [[(200,10),(200,10)], [(200,10),(200,10)]],
                shift_modes=["drop","roll"],
                hide_output=False,
                dropout=0.5, setup=should_setup, nanguard=check_nan, unroll_batch_num=unroll_batch_num)),
    }
    assert modeltype in model_builders, "{} is not a valid model. Try one of {}".format(modeltype, list(model_builders.keys()))
    m = model_builders[modeltype]()

    leadsheets = training.find_leadsheets(dataset)

    if resume is not None:
        start_idx, paramfile = resume
        start_idx = int(start_idx)
        m.params = pickle.load( open(paramfile, "rb" ) )
    else:
        start_idx = 0

    if not os.path.exists(outputdir):
        os.makedirs(outputdir)

    if generate:
        print("Setting up generation")
        m.setup_produce()
        print("Starting to generate")
        start_time = time.process_time()
        if generate_over is not None:
            source, divwidth = generate_over
            if divwidth == 'full':
                divwidth = 0
            elif len(divwidth)>3 and divwidth[-3:] == 'bar':
                divwidth = int(divwidth[:-3])*(constants.WHOLE//constants.RESOLUTION_SCALAR)
            else:
                divwidth = int(divwidth)
            ch,mel = leadsheet.parse_leadsheet(source)
            lslen = leadsheet.get_leadsheet_length(ch,mel)
            if divwidth == 0:
                batch = ([ch],[mel]), source
            else:
                slices = [leadsheet.slice_leadsheet(ch,mel,s,s+divwidth) for s in range(0,lslen,divwidth)]
                batch = list(zip(*slices)), source
            training.generate(m, leadsheets, os.path.join(outputdir, "generated"), with_vis=True, batch=batch)
        else:
            training.generate(m, leadsheets, os.path.join(outputdir, "generated"), with_vis=True)
        end_time = time.process_time()
        print("Generation took {} seconds.".format(end_time-start_time))
    else:
        training.train(m, leadsheets, 50000, outputdir, start_idx, validation_leadsheets=validation)
        pickle.dump( m.params, open( os.path.join(outputdir, "final_params.p"), "wb" ) )

parser = argparse.ArgumentParser(description='Train a neural network model.')
parser.add_argument('modeltype', help='Type of model to construct')
parser.add_argument('--dataset', default='dataset', help='Path to dataset folder (with .ls files)')
parser.add_argument('--validation', help='Path to validation dataset folder (with .ls files)')
parser.add_argument('--outputdir', default='output', help='Path to output folder')
parser.add_argument('--check_nan', action='store_true', help='Check for nans during execution')
parser.add_argument('--resume', nargs=2, metavar=('TIMESTEP', 'PARAMFILE'), default=None, help='Where to restore from: timestep, and file to load')
group = parser.add_mutually_exclusive_group()
group.add_argument('--generate', action='store_true', help="Don't train, just generate. Should be used with restore.")
group.add_argument('--generate_over', nargs=2, metavar=('SOURCE', 'DIV_WIDTH'), default=None, help="Don't train, just generate, and generate over SOURCE chord changes divided into chunks of length DIV_WIDTH (or one contiguous chunk if DIV_WIDTH is 'full'). Can use 'bar' as a unit. Should be used with restore.")

if __name__ == '__main__':
    args = parser.parse_args()
    main(**vars(args))