import unittest
import numpy as np
from sklearn.datasets import load_iris, load_wine
from mdlp import MDLP
from ..Selection import Metrics


class Metrics_test(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        mdlp = MDLP(random_state=1)
        self.X_i_c, self.y_i = load_iris(return_X_y=True)
        self.X_i = mdlp.fit_transform(self.X_i_c, self.y_i).astype("int64")
        self.X_w_c, self.y_w = load_wine(return_X_y=True)
        self.X_w = mdlp.fit_transform(self.X_w_c, self.y_w).astype("int64")

    def test_entropy(self):
        metric = Metrics()
        datasets = [
            ([0, 0, 0, 0, 1, 1, 1, 1], 2, 1.0),
            ([0, 1, 0, 2, 1, 2], 3, 1.0),
            ([0, 0, 0, 0, 0, 0, 0, 2, 2, 2], 2, 0.8812908992306927),
            ([1, 1, 1, 5, 2, 2, 3, 3, 3], 4, 0.9455305560363263),
            ([1, 1, 1, 2, 2, 3, 3, 3, 5], 4, 0.9455305560363263),
            ([1, 1, 5], 2, 0.9182958340544896),
            (self.y_i, 3, 0.999999999),
        ]
        for dataset, base, entropy_expected in datasets:
            computed = metric.entropy(dataset, base)
            self.assertAlmostEqual(entropy_expected, computed)

    def test_differential_entropy(self):
        metric = Metrics()
        datasets = [
            ([0, 0, 0, 0, 1, 1, 1, 1], 6, 1.0026709900837547096),
            ([0, 1, 0, 2, 1, 2], 5, 1.3552453009332424),
            ([0, 0, 0, 0, 0, 0, 0, 2, 2, 2], 7, 1.7652626150881443),
            ([1, 1, 1, 5, 2, 2, 3, 3, 3], 8, 1.9094631320594582),
            ([1, 1, 1, 2, 2, 3, 3, 3, 5], 8, 1.9094631320594582),
            ([1, 1, 5], 2, 2.5794415416798357),
            (self.X_i_c, 37, 3.06627326925228),
            (self.X_w_c, 37, 63.13827518897429),
        ]
        for dataset, base, entropy_expected in datasets:
            computed = metric.differential_entropy(
                np.array(dataset, dtype="float64"), base
            )
            self.assertAlmostEqual(
                entropy_expected, computed, msg=str(dataset)
            )
        expected = [
            1.6378708764142766,
            2.0291571802275037,
            0.8273865123744271,
            3.203935772642847,
            4.859193341386733,
            1.3707315434976266,
            1.8794952925706312,
            -0.2983180654207054,
            1.4521478934625076,
            2.834404839362728,
            0.4894081282811191,
            1.361210381692561,
            7.6373991502818175,
        ]
        n_samples = self.X_w_c.shape[0]
        for c, res_expected in enumerate(expected):
            computed = metric.differential_entropy(
                self.X_w_c[:, c], n_samples - 1
            )
            self.assertAlmostEqual(computed, res_expected)

    def test_conditional_entropy(self):
        metric = Metrics()
        results_expected = [
            0.490953458537736,
            0.7110077966379169,
            0.15663362014829718,
            0.13032469395094992,
        ]
        for expected, col in zip(results_expected, range(self.X_i.shape[1])):
            computed = metric.conditional_entropy(
                self.X_i[:, col], self.y_i, 3
            )
            self.assertAlmostEqual(expected, computed)
        self.assertAlmostEqual(
            0.6309297535714573,
            metric.conditional_entropy(
                [1, 3, 2, 3, 2, 1], [1, 2, 0, 1, 1, 2], 3
            ),
        )
        # https://planetcalc.com/8414/?joint=0.4%200%0A0.2%200.4&showDetails=1
        self.assertAlmostEqual(
            0.5509775004326938,
            metric.conditional_entropy([1, 1, 2, 2, 2], [0, 0, 0, 2, 2], 2),
        )

    def test_information_gain(self):
        metric = Metrics()
        results_expected = [
            0.5090465414622638,
            0.28899220336208287,
            0.8433663798517026,
            0.8696753060490499,
        ]
        for expected, col in zip(results_expected, range(self.X_i.shape[1])):
            computed = metric.information_gain(self.X_i[:, col], self.y_i, 3)
            self.assertAlmostEqual(expected, computed)
        # https://planetcalc.com/8419/
        # ?_d=FrDfFN2COAhqh9Pb5ycqy5CeKgIOxlfSjKgyyIR.Q5L0np-g-hw6yv8M1Q8_
        results_expected = [
            0.806819679,
            0.458041805,
            1.336704086,
            1.378402748,
        ]
        for expected, col in zip(results_expected, range(self.X_i.shape[1])):
            computed = metric.information_gain(self.X_i[:, col], self.y_i, 2)
            self.assertAlmostEqual(expected, computed)

    def test_information_gain_continuous(self):
        metric = Metrics()
        # Wine
        results_expected = [
            0.4993916064992192,
            0.4049969724847222,
            0.2934244372102506,
            0.16970372100970632,
        ]
        for expected, col in zip(results_expected, range(self.X_w_c.shape[1])):
            computed = metric.information_gain_cont(
                self.X_w_c[:, col], self.y_w
            )
            self.assertAlmostEqual(expected, computed)
        # Iris
        results_expected = [
            0.32752672968734586,
            0.0,
            0.5281084030413838,
            0.0,
        ]
        for expected, col in zip(results_expected, range(self.X_i_c.shape[1])):
            computed = metric.information_gain_cont(
                self.X_i_c[:, col].reshape(-1, 1),  # reshape for coverage
                self.y_i,
            )
            self.assertAlmostEqual(expected, computed)

    def test_symmetrical_uncertainty(self):
        metric = Metrics()
        results_expected = [
            0.33296547388990266,
            0.19068147573570668,
            0.810724587460511,
            0.870521418179061,
        ]
        for expected, col in zip(results_expected, range(self.X_i.shape[1])):
            computed = metric.symmetrical_uncertainty(
                self.X_i[:, col], self.y_i
            )
            self.assertAlmostEqual(expected, computed)

    def test_symmetrical_uncertainty_continuous(self):
        metric = Metrics()
        results_expected = [
            0.3116626663552704,
            0.22524988105092494,
            0.24511182026415218,
            0.07114329389542708,
        ]
        for expected, col in zip(results_expected, range(self.X_w.shape[1])):
            computed = metric.symmetrical_unc_continuous(
                self.X_w_c[:, col], self.y_w
            )
            self.assertAlmostEqual(expected, computed)
