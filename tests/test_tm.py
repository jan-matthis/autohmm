from __future__ import print_function

import unittest
from unittest import TestCase

import numpy as np

from numpy.testing import assert_, assert_raises
from numpy.testing import assert_array_equal, assert_array_almost_equal

from hmmlearn.utils import normalize

from autohmm import tm

np.seterr(all='warn')

def test_precision_prior_wrong_nb():
    with assert_raises(ValueError):
        m = tm.THMM(n_unique = 2)
        m.precision_prior_ = np.array([0.7, 0.8, 0.9])

def test_precision_prior_unique():
    m = tm.THMM(n_unique = 2, n_tied = 1)
    m.precision_prior_ = np.array([[0.7], [0.3]])
    correct_prior = np.array([0.7, 0.7, 0.3, 0.3])
    correct_prior = correct_prior.reshape(4, 1, 1)
    assert_array_equal(m._precision_prior_, correct_prior)

def fit_hmm_and_monitor_log_likelihood(h, X, n_iter=1):
    h.n_iter = 1        # make sure we do a single iteration at a time
    h.init_params = ''  # and don't re-init params
    loglikelihoods = np.empty(n_iter, dtype=float)
    for i in range(n_iter):
        h.fit(X)
        loglikelihoods[i], _ = h.score_samples(X)
    return loglikelihoods

class PlainGaussianHMM(TestCase):
    def setUp(self):
        self.prng = np.random.RandomState(42)

        self.n_unique = 2
        self.n_components = 2
        self.startprob = np.array([0.6, 0.4])
        self.transmat = np.array([[0.7, 0.3], [0.4, 0.6]])
        self.mu = np.array([0.7, -2.0])
        self.var = np.array([0.2, 0.2])

        self.h = tm.THMM(n_unique=self.n_unique, random_state=self.prng)
        self.h.startprob_ = self.startprob
        self.h.transmat_ = self.transmat
        self.h.mu_ = self.mu
        self.h.var_ = self.var

    def test_fit(self, params='stpmaw', n_iter=5, **kwargs):
        h = self.h
        h.params = params

        lengths = 1000
        X, _state_sequence = h.sample(lengths, random_state=self.prng)

        # Perturb
        pstarting = self.prng.rand(self.n_components)
        normalize(pstarting)
        h.startprob_ = pstarting
        ptransmat = self.prng.rand(self.n_components, self.n_components)
        normalize(ptransmat, axis=1)
        h.transmat_ = ptransmat

        # TODO: Test more parameters, generate test cases
        trainll = fit_hmm_and_monitor_log_likelihood(
            h, X, n_iter=n_iter)

        # Check that the log-likelihood is always increasing during training.
        #diff = np.diff(trainll)
        #self.assertTrue(np.all(diff >= -1e-6),
        #                "Decreasing log-likelihood: {0}" .format(diff))

        assert_array_almost_equal(h.mu_.reshape(-1),
                                  self.mu.reshape(-1), decimal=1)
        assert_array_almost_equal(h.var_.reshape(-1),
                                  self.var.reshape(-1), decimal=1)
        assert_array_almost_equal(h.transmat_.reshape(-1),
                                  self.transmat.reshape(-1), decimal=2)

class MultivariateGaussianHMM(TestCase):
    def setUp(self):
        self.prng = np.random.RandomState(42)
        self.n_unique = 2
        self.n_features = 3
        self.n_components = 6
        self.startprob = np.array([0.6, 0.4])
        self.transmat = np.array([[0.7, 0.3], [0.4, 0.6]])

        self.mu = np.array([[0.7, -2.0, 0.1],
                            [-0.7, 2.0, -0,1]])

        self.precision = np.array([[[599, 394], [800, 834]],
                                    [[375, 353], [342, 353]]])

        self.h = tm.THMM(n_unique=self.n_unique, n_tied = 2, random_state=self.prng)
        self.h.startprob_ = self.startprob
        self.h.transmat_ = self.transmat
        self.h.mu_ = self.mu
        self.h.precision_ = self.precision

class TiedGaussianHMM(TestCase):
    def setUp(self):
        self.prng = np.random.RandomState(42)

        self.n_unique = 2
        self.n_components = 6
        self.startprob = np.array([0.6, 0.4])
        self.transmat = np.array([[0.7, 0.3], [0.4, 0.6]])

        self.mu = np.array([0.7, -2.0])
        self.var = np.array([0.2, 0.2])
        self.h = tm.THMM(n_unique=self.n_unique, n_tied = 2, random_state=self.prng)
        self.h.startprob_ = self.startprob
        self.h.transmat_ = self.transmat
        self.h.mu_ = self.mu
        self.h.var_ = self.var

    def test_fit(self, params='stpmaw', n_iter=50, **kwargs):
        h = self.h
        self.transmat = np.copy(h.transmat_)
        h.params = params
        lengths = 10000
        X, _state_sequence = h.sample(lengths, random_state=self.prng)

        # Perturb
        pstarting = self.prng.rand(self.n_components)
        normalize(pstarting)
        h.startprob_ = pstarting

        template = np.zeros((6,6))
        noise = np.random.normal(3, 2, 12)
        nb = 0
        for row in range(5):
            template[row][row] = noise[nb]
            nb = nb + 1
            template[row][row+1] = noise[nb]
            nb = nb + 1
        template[5][0] = noise[nb]
        nb = nb + 1
        template[5][5] = noise[nb]
        template = abs(template)

        h.transmat_ = np.copy(template)


        # TODO: Test more parameters, generate test cases
        trainll = fit_hmm_and_monitor_log_likelihood(
            h, X, n_iter=n_iter)

        # Check that the log-likelihood is always increasing during training.
        #diff = np.diff(trainll)
        #self.assertTrue(np.all(diff >= -1e-6),
        #                "Decreasing log-likelihood: {0}" .format(diff))

        assert_array_almost_equal(h.mu_.reshape(-1),
                                  self.mu.reshape(-1), decimal=2)
        assert_array_almost_equal(h.var_.reshape(-1),
                                  self.var.reshape(-1), decimal=2)
        assert_array_almost_equal(h.transmat_.reshape(-1),
                                  self.transmat.reshape(-1), decimal=2)


if __name__ == '__main__':
    unittest.main()
