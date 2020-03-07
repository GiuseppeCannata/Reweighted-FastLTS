import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression

from Reweighted_FastLTS import ReweightedFastLTS

df = pd.read_csv("hbk.csv",sep=';', dtype='float32')
X = df.values[:,:-1]
y = df["Y"].values
y[51] = -0.5

# FastLTS
lts = ReweightedFastLTS(X, y).fit()

fig, axs = plt.subplots(2, 1)

# Distance plot
axs[0].scatter(range(lts.n),lts.RD)
axs[0].plot([0,lts.n],[lts.d,lts.d])
axs[0].set_xlabel('Index')
axs[0].set_ylabel('Robust distance')

# Classificazione outliers
axs[1].scatter(lts.RD, lts.res)
axs[1].plot([0,max(lts.RD)],[2.5,2.5])
axs[1].plot([0,max(lts.RD)],[-2.5,-2.5])
axs[1].plot([lts.d,lts.d],[min(lts.res),max(lts.res)])
axs[1].set_xlabel('Robust Distance')
axs[1].set_ylabel('Standardized LTS residuals')

# Fitted model
plt.show()

print("\n\n  Summary outliers:")
good = [ i+1 for i,residuo in enumerate(lts.res) if (residuo < 2.5) and (residuo > -2.5) and lts.RD[i] > lts.d] # i+1 per confrontrlo con RStudio
bad = [ i+1 for i,residuo in enumerate(lts.res) if ((residuo > 2.5) or (residuo < -2.5)) and lts.RD[i] > lts.d]
vertical = [ i+1 for i,residuo in enumerate(lts.res) if ((residuo > 2.5) or (residuo < -2.5)) and lts.RD[i] < lts.d]

print("good: ",str(good))
print("vertical: ",str(vertical))
print("bad: ",str(bad))