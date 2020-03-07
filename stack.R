data("stackloss")
S.lts <- ltsReg(stack.loss~.,data=stackloss, alpha=0.5)
plot(S.lts)