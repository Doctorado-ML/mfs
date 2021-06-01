from math import log
import numpy as np

from scipy.special import gamma, psi
from sklearn.neighbors import BallTree, KDTree, NearestNeighbors
from sklearn.feature_selection._mutual_info import _compute_mi

# from .entropy_estimators import mi, entropy as c_entropy


class Metrics:
    @staticmethod
    def information_gain_cont(x, y):
        """Measures the reduction in uncertainty about the value of y when the
        value of X continuous is known (also called mutual information)
        (https://www.sciencedirect.com/science/article/pii/S0020025519303603)

        Parameters
        ----------
        x : np.array
            values of the continuous variable
        y : np.array
            array of labels
        base : int, optional
            base of the logarithm, by default 2

        Returns
        -------
        float
            Information gained
        """
        return _compute_mi(
            x, y, x_discrete=False, y_discrete=True, n_neighbors=3
        )

    @staticmethod
    def _nearest_distances(X, k=1):
        """
        X = array(N,M)
        N = number of points
        M = number of dimensions
        returns the distance to the kth nearest neighbor for every point in X
        """
        knn = NearestNeighbors(n_neighbors=k + 1)
        knn.fit(X)
        d, _ = knn.kneighbors(X)  # the first nearest neighbor is itself
        return d[:, -1]  # returns the distance to the kth nearest neighbor

    @staticmethod
    def differential_entropy(x, k=1):

        """Returns the entropy of the X.
        Parameters
        ===========
        x : array-like, shape (n_samples, n_features)
            The data the entropy of which is computed
        k : int, optional
            number of nearest neighbors for density estimation
        Notes
        ======
        Kozachenko, L. F. & Leonenko, N. N. 1987 Sample estimate of entropy
        of a random vector. Probl. Inf. Transm. 23, 95-101.
        See also: Evans, D. 2008 A computationally efficient estimator for
        mutual information, Proc. R. Soc. A 464 (2093), 1203-1215.
        and:
        Kraskov A, Stogbauer H, Grassberger P. (2004). Estimating mutual
        information. Phys Rev E 69(6 Pt 2):066138.
        """
        if x.ndim == 1:
            x = x.reshape(-1, 1)
        # Distance to kth nearest neighbor
        r = Metrics._nearest_distances(x, k)  # squared distances
        n, d = x.shape
        volume_unit_ball = (np.pi ** (0.5 * d)) / gamma(0.5 * d + 1)
        """
        F. Perez-Cruz, (2008). Estimation of Information Theoretic Measures
        for Continuous Random Variables. Advances in Neural Information
        Processing Systems 21 (NIPS). Vancouver (Canada), December.
        return d*mean(log(r))+log(volume_unit_ball)+log(n-1)-log(k)
        """
        return (
            d * np.mean(np.log(r + np.finfo(x.dtype).eps))
            + np.log(volume_unit_ball)
            + psi(n)
            - psi(k)
        )

    @staticmethod
    def conditional_differential_entropy(x, y):
        """quantifies the amount of information needed to describe the outcome
        of Y discrete given that the value of X continuous is known
        computes H(Y|X)

        Parameters
        ----------
        x : np.array
            values of the continuous variable
        y : np.array
            array of labels
        base : int, optional
            base of the logarithm, by default 2

        Returns
        -------
        float
            conditional entropy of y given x
        """
        xy = np.c_[x, y]
        return Metrics.differential_entropy(xy) - Metrics.differential_entropy(
            x
        )

    @staticmethod
    def symmetrical_unc_continuous(x, y):
        """Compute symmetrical uncertainty. Using Greg Ver Steeg's npeet
        https://github.com/gregversteeg/NPEET

        Parameters
        ----------
        x : np.array
            values of the continuous variable
        y : np.array
            array of labels

        Returns
        -------
        float
            symmetrical uncertainty
        """

        return (
            2.0
            * Metrics.information_gain_cont(x, y)
            / (Metrics.differential_entropy(x) + Metrics.entropy(y))
        )

    @staticmethod
    def symmetrical_uncertainty(x, y):
        """Compute symmetrical uncertainty. Normalize* information gain (mutual
        information) with the entropies of the features in order to compensate
        the bias due to high cardinality features. *Range [0, 1]
        (https://www.sciencedirect.com/science/article/pii/S0020025519303603)

        Parameters
        ----------
        x : np.array
            values of the variable
        y : np.array
            array of labels

        Returns
        -------
        float
            symmetrical uncertainty
        """
        return (
            2.0
            * Metrics.information_gain(x, y)
            / (Metrics.entropy(x) + Metrics.entropy(y))
        )

    @staticmethod
    def conditional_entropy(x, y, base=2):
        """quantifies the amount of information needed to describe the outcome
        of Y given that the value of X is known
        computes H(Y|X)

        Parameters
        ----------
        x : np.array
            values of the variable
        y : np.array
            array of labels
        base : int, optional
            base of the logarithm, by default 2

        Returns
        -------
        float
            conditional entropy of y given x
        """
        xy = np.c_[x, y]
        return Metrics.entropy(xy, base) - Metrics.entropy(x, base)

    @staticmethod
    def entropy(y, base=2):
        """measure of the uncertainty in predicting the value of y

        Parameters
        ----------
        y : np.array
            array of labels
        base : int, optional
            base of the logarithm, by default 2

        Returns
        -------
        float
            entropy of y
        """
        _, count = np.unique(y, return_counts=True, axis=0)
        proba = count.astype(float) / len(y)
        proba = proba[proba > 0.0]
        return np.sum(proba * np.log(1.0 / proba)) / log(base)

    @staticmethod
    def information_gain(x, y, base=2):
        """Measures the reduction in uncertainty about the value of y when the
        value of X is known (also called mutual information)
        (https://www.sciencedirect.com/science/article/pii/S0020025519303603)

        Parameters
        ----------
        x : np.array
            values of the variable
        y : np.array
            array of labels
        base : int, optional
            base of the logarithm, by default 2

        Returns
        -------
        float
            Information gained
        """
        return Metrics.entropy(y, base) - Metrics.conditional_entropy(
            x, y, base
        )
