import unittest
from mdlp import MDLP
from sklearn.datasets import load_wine, load_iris

from ..Selection import MFS


class MFS_test(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        mdlp = MDLP(random_state=1)
        X, self.y_w = load_wine(return_X_y=True)
        self.X_w = mdlp.fit_transform(X, self.y_w).astype("int64")
        X, self.y_i = load_iris(return_X_y=True)
        mdlp = MDLP(random_state=1)
        self.X_i = mdlp.fit_transform(X, self.y_i).astype("int64")

    def test_initialize(self):
        mfs = MFS()
        mfs.fcbs(self.X_w, self.y_w, 0.05)
        mfs._initialize()
        self.assertIsNone(mfs.get_results())
        self.assertListEqual([], mfs.get_scores())
        self.assertDictEqual({}, mfs._su_features)
        self.assertIsNone(mfs._su_labels)

    def test_csf_wine(self):
        mfs = MFS()
        expected = [6, 12, 9, 4, 10, 0]
        self.assertListEqual(
            expected, mfs.cfs(self.X_w, self.y_w).get_results()
        )
        expected = [
            0.5218299405215557,
            0.602513857132804,
            0.4877384978817362,
            0.3743688234383051,
            0.28795671854246285,
            0.2309165735173175,
        ]
        self.assertListEqual(expected, mfs.get_scores())

    def test_csf_iris(self):
        mfs = MFS()
        expected = [3, 2, 0, 1]
        computed = mfs.cfs(self.X_i, self.y_i).get_results()
        self.assertListEqual(expected, computed)
        expected = [
            0.870521418179061,
            0.8968651482682227,
            0.5908278453318913,
            0.40371971570693366,
        ]
        self.assertListEqual(expected, mfs.get_scores())

    def test_fcbs_wine(self):
        mfs = MFS()
        computed = mfs.fcbs(self.X_w, self.y_w, threshold=0.05).get_results()
        expected = [6, 9, 12, 0, 11, 4]
        self.assertListEqual(expected, computed)
        expected = [
            0.5218299405215557,
            0.46224298637417455,
            0.44518278979085646,
            0.38942355544213786,
            0.3790082191220976,
            0.24972405134844652,
        ]
        self.assertListEqual(expected, mfs.get_scores())

    def test_fcbs_iris(self):
        mfs = MFS()
        computed = mfs.fcbs(self.X_i, self.y_i, threshold=0.05).get_results()
        expected = [3, 2]
        self.assertListEqual(expected, computed)
        expected = [0.870521418179061, 0.810724587460511]
        self.assertListEqual(expected, mfs.get_scores())

    def test_compute_su_labels(self):
        mfs = MFS()
        mfs.fcbs(self.X_i, self.y_i, threshold=0.05)
        expected = [0.0, 0.0, 0.810724587460511, 0.870521418179061]
        self.assertListEqual(expected, mfs._compute_su_labels().tolist())
        mfs._su_labels = [1, 2, 3, 4]
        self.assertListEqual([1, 2, 3, 4], mfs._compute_su_labels())

    def test_invalid_threshold(self):
        mfs = MFS()
        with self.assertRaises(ValueError):
            mfs.fcbs(self.X_i, self.y_i, threshold=1e-5)

    def test_fcbs_exit_threshold(self):
        mfs = MFS()
        computed = mfs.fcbs(self.X_w, self.y_w, threshold=0.4).get_results()
        expected = [6, 9, 12]
        self.assertListEqual(expected, computed)
        expected = [
            0.5218299405215557,
            0.46224298637417455,
            0.44518278979085646,
        ]
        self.assertListEqual(expected, mfs.get_scores())