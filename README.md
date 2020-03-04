# Reweighted-FastLTS

<p>
The <a href="https://www.researchgate.net/publication/220451824_Computing_LTS_Regression_for_Large_Data_Sets">Reweighted-FastLTS<a> is a robust regression algorithm that allows you to detect anomalous observations.
A Python <a href="https://pypi.org/project/ltsfit/">implementation of FastLTS</a> by Michele Cappellari is based on the analysis of datasets with 3 predictors. Starting with the latter and after Prof. Peter Rousseeuw's lectures at the BigDat2020 winter school I implemented a python version of the Reweighted-FastLTS for (i) <i>p</i> predictors with <i>p < n</i> (n number of observations) (ii) <i>n < 600</i>.
<br><br>
The attributes of Reweighted-FastLTS python class is the same that would be obtained by invoking the <a href="https://www.rdocumentation.org/packages/robustbase/versions/0.93-5/topics/ltsReg">ltsReg</a> in RStudio.
Some doubts are about the implementation of FastMCD. In particular, I used <a href="https://scikit-learn.org/stable/modules/generated/sklearn.covariance.MinCovDet.html">MinCovDet<a> from the sklearn library, and I realized that the location and the covariance matrix are different from those obtained by RStudio. Consequence of this is that the Robust Distance turns out to be different.
<br><br>  
<h3>- Some examples</h3>
Below I report the results of some tests. In particular, the datasets used are Hawkins-Bradu-Kass data (HBK) and Stackloss data.
<br>
<h4>-- Hawkins-Bradu-Kass</h4>
</p>
