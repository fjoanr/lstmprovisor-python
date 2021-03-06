from .queue_base import QueueManager
import theano
import theano.tensor as T
from theano.sandbox.rng_mrg import MRG_RandomStreams
import numpy as np
import constants

class VariationalQueueManager( QueueManager ):
    """
    A variational-autoencoder-based queue manager, using a configurable loss
    """

    def __init__(self, feature_size, loss_fun=(lambda x:x), variational_loss_scale=1):
        """
        Initialize the manager.

        Parameters:
            feature_size: The width of a feature
            loss_fun: A function which computes the loss for each timestep. Should be an elementwise
                operation.
            variational_loss_scale: Factor by which to scale variational loss
        """
        self._feature_size = feature_size
        self._srng = MRG_RandomStreams(np.random.randint(0, 1024))
        self._loss_fun = loss_fun
        self._variational_loss_scale = np.array(variational_loss_scale, np.float32)

    @property
    def activation_width(self):
        return 1 + self.feature_size*2

    @property
    def feature_size(self):
        return self._feature_size

    def helper_sample(self, input_activations):
        """Helper method to sample from the input_activations. Also returns an (empty) info dict for child class use"""
        pre_strengths = input_activations[:,:,0]
        strengths = T.nnet.sigmoid(pre_strengths)
        strengths = T.set_subtensor(strengths[:,-1],1)

        means = input_activations[:,:,1:1+self.feature_size]
        stdevs = abs(input_activations[:,:,1+self.feature_size:]) + constants.EPSILON
        wiggle = self._srng.normal(means.shape)

        vects = means + (stdevs * wiggle)

        return strengths, vects, means, stdevs, {}

    def get_strengths_and_vects(self, input_activations):
        strengths, vects, means, stdevs, _ = self.helper_sample(input_activations)
        return strengths, vects

    def process(self, input_activations, extra_info=False):

        strengths, vects, means, stdevs, sample_info = self.helper_sample(input_activations)

        sparsity_losses = self._loss_fun(strengths)
        full_sparsity_loss = T.sum(sparsity_losses)

        means_sq = means**2
        variance = stdevs**2
        variational_loss = -0.5 * T.sum(1 + T.log(variance) - means_sq - variance) * self._variational_loss_scale

        full_loss = full_sparsity_loss + variational_loss

        info = {"sparsity_loss": full_sparsity_loss, "variational_loss":variational_loss}
        info.update(sample_info)
        if extra_info:
            return full_loss, strengths, vects, info
        else:
            return full_loss, strengths, vects
