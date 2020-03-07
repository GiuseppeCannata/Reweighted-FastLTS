library(rrcov)
library(stats)


#modello robusto
hbk.lts <- ltsReg(Y~.,data=hbk, alpha=0.5)
plot(hbk.lts)


#Dataset
#data(hbk, package="robustbase")
#hbk.x <- hbk[, -c(4)]
#hbk.y <- hbk[,4]
#write.table(hbk, file="mydata.csv", sep=";")

#robust distance
#mcd <- CovMcd(x = hbk.x, alpha=0.5, use.correction = TRUE, nsamp = "deterministic")
#location <- getCenter(mcd)
#cov <- getCov(mcd)

#dist <- mahalanobis(hbk.x, location, cov,inverted = FALSE)
#robust_distance <- sqrt(dist)

