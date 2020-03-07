import numpy as np
from numpy.linalg import inv
from scipy.stats import chi2, norm
from sklearn.covariance import MinCovDet
from sklearn.linear_model import LinearRegression
from sklearn.utils.random import sample_without_replacement


class ReweightedFastLTS():

    def __init__(self, X, y, alpha=0.5, use_correction=True, intercept=True):

        self.X = X  # X
        self.y = y  # y
        self.n = X.shape[0]  # num of observations
        self.p = X.shape[1] + 1  # num of predictors + intercept
        self.use_correction = use_correction
        self.intercept = intercept
        self.alpha = alpha

        # Befor reigwheithed
        self.raw_weights = None
        self.raw_model = None
        self.h = None  # quan
        self.raw_scale = None
        self.raw_res = None  # res / scale
        self.raw_index = None  # H_subset_good
        self.raw_correction = None  # correction in RStudio raw.cnp2[2]

        # After reigwheithed
        self.weights = None
        self.model = None
        self.scale = None
        self.res = None
        self.correction = None  # correction in RStudio cnp2[2]

        self.RD = None  # vector Robust distance
        self.d = None  # threshold Robust distance

        # Controllo inputs
        if self.alpha < 0.5 or self.alpha > 1:
            raise ValueError("alpha non in range [0.5, 1]")
        if self.p < 1:
            raise ValueError("The p value must be greater than 1")
        if self.n > 600:
            raise ValueError("Case not implemented yet. The number of observations must be less than 600")
        if not intercept:
            raise ValueError("Case not implemented yet")

    def fit(self):

        _ = self._ReweightedFastLTS()

        # Robust Distance
        v_rd = self._Robust_Distance()

        self.RD = v_rd

        return self

    def _ReweightedFastLTS(self):

        if self.alpha == 1:  # normal Linear regression

            model_old = LinearRegression().fit(self.X, self.y)
            res = self._residuals(LS, self.X, self.y)
            scale_old = np.sqrt((1 / (self.n - self.p)) * np.sum(res ** 2))
            res_std_old = res / scale_old
            d = np.sqrt(chi2.ppf((0.975), df=self.p))  # Threshold for Robust Distance
            weights = np.array([1 if abs(r) <= d else 0 for r in res_std_old])
            # - Reighweight
            model_new = LinearRegression().fit(self.X, self.y, sample_weight=weights)
            y_pred_new = model_new.predict(self.X)
            res_new = self.y - y_pred_new
            scale_new = np.sqrt(np.sum(weights * (res_new ** 2)) / (np.sum(weights) - 1))
            res_std_new = res_new / scale_new

            self.h = self.n
            H_subset_good = None
            factor_old = None
            correction_old = None
            factor_new = None
            correction_new = None

        else:  # alpha < 1

            # - Applicazione Del FastLTS
            H_subset_good, model_old = self._FastLTS()

            # - Start Reighweited
            # -- Residuals standardize old sub-optimal model
            y_pred_old = model_old.predict(self.X)
            res_old = self.y - y_pred_old
            if self.use_correction:
                correction_old = self._LTScnp(self.p - 1, self.n)  # correction factor
            else:
                correction_old = 1
            factor_old = self._chn(self.h, self.n)
            scale_old = np.sqrt(np.mean(sorted((res_old ** 2))[:self.h])) * factor_old * correction_old
            res_std_old = res_old / scale_old
            # -- Reweight old model
            weights = np.array([1 if abs(r) <= 2.5 else 0 for r in res_std_old])

            # -- Fit new ottimal model for values under threshold 'd' of Robust Distance
            model_new = LinearRegression().fit(self.X, self.y, sample_weight=weights)
            # --- Residuals standardize new optimal model
            y_pred_new = model_new.predict(self.X)
            res_new = self.y - y_pred_new
            if self.use_correction:
                correction_new = self._LTScnp_rew(self.p - 1, self.n)
            else:
                correction_new = 1
            factor_new = self._chn(np.sum(weights), self.n)
            scale_new = np.sqrt(np.sum(weights * (res_new ** 2)) / (np.sum(weights) - 1)) * factor_new * correction_new
            res_std_new = res_new / scale_new

        d = np.sqrt(chi2.ppf((0.975), df=self.p))  # thresold Robust Distance

        # Save
        # raw --> old
        self.raw_index = H_subset_good
        self.raw_model = model_old
        self.raw_scale = scale_old
        self.raw_res = res_std_old
        self.raw_weights = weights
        self.raw_correction = correction_old  # in RStudio raw.cnp2[2]

        # new
        self.model = model_new
        self.scale = scale_new
        self.res = res_std_new
        self.correction = correction_new  # in RStudio cnp2[2]
        self.d = d

        return self

    def _FastLTS(self):

        h = self._h_alpha_n()
        m = 500
        models = []
        Q = np.empty(m)

        for j in range(m):
            w = np.random.choice(self.n, size=self.p, replace=False)
            LS = LinearRegression().fit(self.X[w], self.y[w])
            for _ in range(3):  # Run C-step
                res = self._residuals(LS, self.X, self.y)
                H_subset = np.argsort(np.abs(res))[:h]  # Fit the h points with smallest errors
                LS = LinearRegression().fit(self.X[H_subset], self.y[H_subset])

            res = self._residuals(LS, self.X[H_subset], self.y[H_subset])
            Q[j] = np.sum(res ** 2)
            models.append(LS)

        # Perform full C-steps only for the 10 best results
        w = np.argsort(Q)
        nbest = 10
        model_good = None
        H_subset_good = None
        best = np.inf
        for j in range(nbest):
            Qm_uno = np.inf
            Qm = np.inf
            model1 = models[w[j]]
            while True:  # Run C-steps to convergence
                Qm_uno = Qm
                res = self._residuals(model1, self.X, self.y)
                H_subset1 = np.argsort(np.abs(res))[:h]  # Fit the h points with smallest errors
                model1 = LinearRegression().fit(self.X[H_subset1], self.y[H_subset1])
                res = self._residuals(model1, self.X[H_subset1], self.y[H_subset1])
                Qm = np.sum(res ** 2)
                if (Qm_uno == Qm):
                    break

            if Qm < best:
                model_good = model1  # Save best solution
                H_subset_good = H_subset1
                best = Qm

        return H_subset_good, model_good

    def _Robust_Distance(self):

        cov = MinCovDet(support_fraction=self.alpha).fit(self.X)

        Roussew = cov.reweight_covariance(self.X)
        Rmean = Roussew[0]

        Rmatrix_cov = Roussew[1]  # not equal to RStudio
        inv_cov = np.linalg.inv(Rmatrix_cov)
        v_rd = np.empty(self.n)

        for i in range(self.n):
            sca = self.X[i] - Rmean
            RD = np.sqrt(np.dot(np.dot(sca, inv_cov), sca))
            v_rd[i] = RD

        return v_rd

    def _residuals(self, model, X, y):

        y_pred = model.predict(X)
        res = y - y_pred

        return res

    # Calculate the size of H_subset
    def _h_alpha_n(self):
        n2 = (self.n + self.p + 1) / 2
        h = int(2 * n2 - self.n + 2 * (self.n - n2) * self.alpha)
        self.h = h
        return h

    def _LTScnp(self, p, n):

        coefeqpkwad500 = np.array([[-0.746945886714663, 0.56264937192689, 3],
                                   [-0.535478048924724, 0.543323462033445, 5]]).T

        y1_500 = coefeqpkwad500[0] / p ** coefeqpkwad500[1]
        y_500 = np.log(- y1_500)
        A_500 = [[1, np.log(1 / ((coefeqpkwad500[2, 0] * (p ** 2))))],
                 [1, np.log(1 / ((coefeqpkwad500[2, 1] * (p ** 2))))]]
        coeffic_500 = np.dot(inv(np.array(A_500)), np.array(y_500))
        fp_500_n = 1 - np.exp(coeffic_500[0]) / (n ** coeffic_500[1])

        coefeqpkwad875 = np.array([[-0.458580153984614, 1.12236071104403, 3],
                                   [-0.267178168108996, 1.1022478781154, 5]]).T
        y1_875 = coefeqpkwad875[0] / p ** coefeqpkwad875[1]
        y_875 = np.log(- y1_875)
        A_875 = [[1, np.log(1 / ((coefeqpkwad875[2, 0] * (p ** 2))))],
                 [1, np.log(1 / ((coefeqpkwad875[2, 1] * (p ** 2))))]]
        coeffic_875 = np.dot(inv(np.array(A_875)), np.array(y_875))

        fp_500_n = 1 - np.exp(coeffic_500[0]) / (n ** coeffic_500[1])
        fp_875_n = 1 - np.exp(coeffic_875[0]) / (n ** coeffic_875[1])

        if (self.alpha <= 0.875):
            fp_alpha_n = fp_500_n + (fp_875_n - fp_500_n) / 0.375 * (self.alpha - 0.500)
        else:  ##	 0.875 < alpha <= 1
            fp_alpha_n = fp_875_n + (1 - fp_875_n) / 0.125 * (self.alpha - 0.875)

        return 1 / fp_alpha_n

    def _LTScnp_rew(self, p, n):

        coefeqpkwad875 = np.array([[-0.474174840843602, 1.39681715704956, 3],
                                   [-0.276640353112907, 1.42543242287677, 5]]).T
        coefeqpkwad500 = np.array([[-0.773365715932083, 2.02013996406346, 3],
                                   [-0.337571678986723, 2.02037467454833, 5]]).T

        y1_500 = coefeqpkwad500[0] / p ** coefeqpkwad500[1]
        y_500 = np.log(- y1_500)
        A_500 = [[1, np.log(1 / ((coefeqpkwad500[2, 0] * (p ** 2))))],
                 [1, np.log(1 / ((coefeqpkwad500[2, 1] * (p ** 2))))]]
        coeffic_500 = np.dot(inv(np.array(A_500)), np.array(y_500))
        fp_500_n = 1 - np.exp(coeffic_500[0]) / (n ** coeffic_500[1])

        y1_875 = coefeqpkwad875[0] / p ** coefeqpkwad875[1]
        y_875 = np.log(- y1_875)
        A_875 = [[1, np.log(1 / ((coefeqpkwad875[2, 0] * (p ** 2))))],
                 [1, np.log(1 / ((coefeqpkwad875[2, 1] * (p ** 2))))]]
        coeffic_875 = np.dot(inv(np.array(A_875)), np.array(y_875))

        fp_500_n = 1 - np.exp(coeffic_500[0]) / (n ** coeffic_500[1])
        fp_875_n = 1 - np.exp(coeffic_875[0]) / (n ** coeffic_875[1])

        if (self.alpha <= 0.875):
            fp_alpha_n = fp_500_n + (fp_875_n - fp_500_n) / 0.375 * (self.alpha - 0.5)
        else:  ##	 0.875 < alpha <= 1
            fp_alpha_n = fp_875_n + (1 - fp_875_n) / 0.125 * (self.alpha - 0.875)

        return 1 / fp_alpha_n

    def _chn(self, quan, n):
        a = norm.ppf((quan + n) / (2 * n))
        return 1 / np.sqrt(1 - (2 * n) / (quan / a) * norm.pdf(a))

    def summary(self):
        print("Summary:\n")
        dic = self.__dict__
        for key, value in dic.items():
            print(key, ":", value, "\n")