# Examine the entropy results
# Yang Xu
# 9/10/2016

library(data.table)
library(lme4)
library(lmerTest)
library(ggplot2)

# read data
df = read.table(file = 'init_posts_entropy_samepos.txt', sep = ',', header = F)
colnames(df) = c('postId', 'sentId', 'entropy')
dt = data.table(df)

summary(dt$sentId)

# model
summary(lmer(entropy ~ sentId + (1|postId), dt))

# plot
p = ggplot(dt, aes(x = sentId, y = entropy)) +
    stat_summary(fun.data = mean_cl_boot, geom = 'ribbon', aes(.alpha = .5))
plot(p)
