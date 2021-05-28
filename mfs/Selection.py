from math import log, sqrt
from sys import float_info
from itertools import combinations
import numpy as np


class Metrics:
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


class MFS:
    """Compute Fast Fast Correlation Based Filter
    Yu, L. and Liu, H.; Feature Selection for High-Dimensional Data: A Fast
    Correlation Based Filter Solution,Proc. 20th Intl. Conf. Mach. Learn.
    (ICML-2003)

    and

    Correlated Feature Selection as in "Correlation-based Feature Selection for
    Machine Learning" by Mark A. Hall
    """

    def __init__(self):
        self._initialize()

    def _initialize(self):
        """Initialize the attributes so support multiple calls using same
        object
        """
        self._result = None
        self._scores = []
        self._su_labels = None
        self._su_features = {}

    def _compute_su_labels(self):
        """Compute symmetrical uncertainty between each feature of the dataset
        and the labels and store it to use in future calls

        Returns
        -------
        list
            vector with sym. un. of every feature and the labels
        """
        if self._su_labels is None:
            num_features = self.X_.shape[1]
            self._su_labels = np.zeros(num_features)
            for col in range(num_features):
                self._su_labels[col] = Metrics.symmetrical_uncertainty(
                    self.X_[:, col], self.y_
                )
        return self._su_labels

    def _compute_su_features(self, feature_a, feature_b):
        """Compute symmetrical uncertainty between two features and stores it
        to use in future calls

        Parameters
        ----------
        feature_a : int
            index of the first feature
        feature_b : int
            index of the second feature

        Returns
        -------
        float
            The symmetrical uncertainty of the two features
        """
        if (feature_a, feature_b) not in self._su_features:
            self._su_features[
                (feature_a, feature_b)
            ] = Metrics.symmetrical_uncertainty(
                self.X_[:, feature_a], self.X_[:, feature_b]
            )
        return self._su_features[(feature_a, feature_b)]

    def _compute_merit(self, features):
        """Compute the merit function for cfs algorithms

        Parameters
        ----------
        features : list
            list of features to include in the computation

        Returns
        -------
        float
            The merit of the feature set passed
        """
        # lgtm has already recognized that this is a false positive
        rcf = self._su_labels[
            features
        ].sum()  # lgtm [py/hash-unhashable-value]
        rff = 0.0
        k = len(features)
        for pair in list(combinations(features, 2)):
            rff += self._compute_su_features(*pair)
        return rcf / sqrt(k + (k ** 2 - k) * rff)

    def cfs(self, X, y):
        """Correlation-based Feature Selection
        with a forward best first heuristic search

        Parameters
        ----------
        X : np.array
            array of features
        y : np.array
            vector of labels

        Returns
        -------
        self
            self
        """
        self._initialize()
        self.X_ = X
        self.y_ = y
        s_list = self._compute_su_labels()
        # Descending order
        feature_order = (-s_list).argsort().tolist()
        continue_condition = True
        candidates = []
        # start with the best feature (max symmetrical uncertainty wrt label)
        first_candidate = feature_order.pop(0)
        candidates.append(first_candidate)
        self._scores.append(s_list[first_candidate])
        while continue_condition:
            merit = float_info.min
            id_selected = None
            for idx, feature in enumerate(feature_order):
                candidates.append(feature)
                merit_new = self._compute_merit(candidates)
                if merit_new > merit:
                    id_selected = idx
                    merit = merit_new
                candidates.pop()
            candidates.append(feature_order[id_selected])
            self._scores.append(merit)
            del feature_order[id_selected]
            if len(feature_order) == 0:
                # Force leaving the loop
                continue_condition = False
            if len(self._scores) >= 5:
                """
                "To prevent the best first search from exploring the entire
                feature subset search space, a stopping criterion is imposed.
                The search will terminate if five consecutive fully expanded
                subsets show no improvement over the current best subset."
                as stated in Mark A. Hall Thesis
                """
                item_ant = -1
                for item in self._scores[-5:]:
                    if item_ant == -1:
                        item_ant = item
                    if item > item_ant:
                        break
                    else:
                        item_ant = item
                else:
                    continue_condition = False
        self._result = candidates
        return self

    def fcbs(self, X, y, threshold):
        """Fast Correlation-Based Filter

        Parameters
        ----------
        X : np.array
            array of features
        y : np.array
            vector of labels
        threshold : float
            threshold to select relevant features

        Returns
        -------
        self
            self

        Raises
        ------
        ValueError
            if the threshold is less than a selected value of 1e-4
        """
        if threshold < 1e-4:
            raise ValueError("Threshold cannot be less than 1e-4")
        self._initialize()
        self.X_ = X
        self.y_ = y
        s_list = self._compute_su_labels()
        feature_order = (-s_list).argsort()
        feature_dup = feature_order.copy().tolist()
        self._result = []
        for index_p in feature_order:
            # Don't self compare
            feature_dup.pop(0)
            # Remove redundant features
            if s_list[index_p] == 0.0:
                # the feature has been removed from the list
                continue
            if s_list[index_p] < threshold:
                break
            # Remove redundant features
            for index_q in feature_dup:
                su_pq = self._compute_su_features(index_p, index_q)
                if su_pq >= s_list[index_q]:
                    # remove feature from list
                    s_list[index_q] = 0.0
            self._result.append(index_p)
            self._scores.append(s_list[index_p])
        return self

    def get_results(self):
        """Return the results of the algorithm applied if any

        Returns
        -------
        list
            list of features indices selected
        """
        return self._result

    def get_scores(self):
        """Return the scores computed for the features selected

        Returns
        -------
        list
            list of scores of the features selected
        """
        return self._scores
