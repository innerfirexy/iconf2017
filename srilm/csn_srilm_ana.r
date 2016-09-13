# analyze results
# Yang Xu
# 9/12/2016

library(data.table)
library(lme4)
library(lmerTest)
library(ggplot2)

# read samepos data
df = read.table(file = 'ppl_samepos.txt', sep = ',', header = F)
colnames(df) = c('postId', 'sentId', 'ppl')
dt = data.table(df)
dt$ent = log(dt$ppl, 2)

# distr
plot(density(dt$ppl))
plot(density(dt$ent))

# model
summary(lmer(ppl ~ sentId + (1|postId), dt)) # ***
summary(lmer(ppl ~ sentId + (1|postId), dt[sentId<=3,])) # ***
summary(lmer(ppl ~ sentId + (1|postId), dt[sentId>3,])) # insig

# plot
# ppl
p = ggplot(dt, aes(x = sentId, y = ppl)) +
    stat_summary(fun.data = mean_cl_boot, geom = 'ribbon', aes(.alpha = .5)) +
    stat_summary(fun.y = mean, geom = 'line') +
    scale_x_continuous(breaks=0:9) + ylab('perplexity')
pdf('ppl_vs_sid.pdf_samepos', 5, 5)
plot(p)
dev.off()

# entropy
p = ggplot(dt, aes(x = sentId, y = ent)) +
    stat_summary(fun.data = mean_cl_boot, geom = 'ribbon', aes(.alpha = .5)) +
    stat_summary(fun.y = mean, geom = 'line') +
    scale_x_continuous(breaks=0:9) + ylab('entropy')
pdf('ent_vs_sid_samepos.pdf', 5, 5)
plot(p)
dev.off()


## diffpos data
df2 = read.table(file = 'ppl_diffpos.txt', sep = ',', header = F)
colnames(df2) = c('postId', 'sentId', 'ppl')
dt2 = data.table(df2)
dt2$ent = log(dt2$ppl, 2)

# models
summary(lmer(ppl ~ sentId + (1|postId), dt2)) # ***
summary(lmer(ent ~ sentId + (1|postId), dt2)) # ***

# plots
p1 = ggplot(dt2, aes(x = sentId, y = ppl)) +
    stat_summary(fun.data = mean_cl_boot, geom = 'ribbon', aes(.alpha = .5)) +
    stat_summary(fun.y = mean, geom = 'line') +
    scale_x_continuous(breaks=0:9) + ylab('perplexity')
pdf('ppl_vs_sid_diffpos.pdf', 5, 5)
plot(p1)
dev.off()

p2 = ggplot(dt2, aes(x = sentId, y = ent)) +
    stat_summary(fun.data = mean_cl_boot, geom = 'ribbon', aes(.alpha = .5)) +
    stat_summary(fun.y = mean, geom = 'line') +
    scale_x_continuous(breaks=0:9) + ylab('entropy')
pdf('ent_vs_sid_diffpos.pdf', 5, 5)
plot(p2)
dev.off()


## first comments results
df3 = read.table(file = 'fc_ppl_diffpos.txt', sep = ',', header = F)
colnames(df3) = c('postId', 'sentId', 'ppl')
dt3 = data.table(df3)
dt3$ent = log(dt3$ppl, 2)

summary(lmer(ppl ~ sentId + (1|postId), dt3)) # ***
summary(lmer(ent ~ sentId + (1|postId), dt3)) # *

p1 = ggplot(dt3, aes(x = sentId, y = ppl)) +
    stat_summary(fun.data = mean_cl_boot, geom = 'ribbon', aes(.alpha = .5)) +
    stat_summary(fun.y = mean, geom = 'line') +
    scale_x_continuous(breaks=0:9) + ylab('perplexity')
pdf('firstComm_ppl_vs_sid_diffpos.pdf', 5, 5)
plot(p1)
dev.off()

p2 = ggplot(dt3, aes(x = sentId, y = ent)) +
    stat_summary(fun.data = mean_cl_boot, geom = 'ribbon', aes(.alpha = .5)) +
    stat_summary(fun.y = mean, geom = 'line') +
    scale_x_continuous(breaks=0:9) + ylab('entropy')
pdf('firstComm_ent_vs_sid_diffpos.pdf', 5, 5)
plot(p2)
dev.off()

# examine
mean(dt3[sentId == 0, ent]) # 6.18
mean(dt3[sentId == 1, ent]) # 6.25
mean(dt3[sentId == 0, ppl]) # 233.46
mean(dt3[sentId == 1, ppl]) # 198.44
# maybe caused by the shape of distr

# combine initial posts and first comments
dt2[, type:='initial posts']
dt3[, type:='first comments']
dt.all = rbindlist(list(dt2, dt3))

p = ggplot(dt.all, aes(x = sentId, y = ent)) +
    stat_summary(fun.data = mean_cl_boot, geom = 'ribbon', aes(fill = type, .alpha = .5)) +
    stat_summary(fun.y = mean, geom = 'line', aes(lty = type)) +
    scale_x_continuous(breaks=0:9) + ylab('entropy') +
    theme(legend.position = c(.8, .2))
pdf('init_firstcomment_ent_diffpos.pdf', 5, 5)
plot(p)
dev.off()
