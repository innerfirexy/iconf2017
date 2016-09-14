# Carry out survey experiments on the basic stats about the dialogue structure in CSN
# Yang Xu
# 9/9/2016

library(data.table)
library(RMySQL)

# db conn
# ssh yvx5085@brain.ist.psu.edu -i ~/.ssh/id_rsa -L 1234:localhost:3306
conn = dbConnect(MySQL(), host = '127.0.0.1', user = 'yang', port = 1234, password = "05012014", dbname = 'csn')

# dialogue length, in number of comments
sql = 'select CommentID, NodeID from newforum'
df = dbGetQuery(conn, sql) # takes 78 sec from China to USA
dt = data.table(df)
setkey(dt, NodeID)

dt.len = dt[, .N, by = NodeID]
summary(dt.len$N) # mean = 8.6, median = 6
plot(density(dt.len[N <= 20, N]))
hist(dt.len[N <= 20, N])

# sentence number in a dialogue
sql = 'select PostID, SentenceID from Sentence'
df.s = dbGetQuery(conn, sql)
dt.s = data.table(df.s)
setkey(dt.s, PostID)
dt.sn = dt.s[, .(sentN = .N), by = PostID]

# join dt and dt.sn
# number of sentences in all comments (excluding initial post)
setkey(dt, CommentID)
dt.join = dt[dt.sn, nomatch = 0] # inner join
dt.join.sn = dt.join[, .(sentNum = sum(sentN)), by = NodeID]
summary(dt.join.sn$sentNum) # mean = 57, median = 37, q1 = 17, q3 = 72

# the number of sentences in the thread initial post
setkey(dt, NodeID)
dt.init = dt.sn[dt]
dt.init[, CommentID := NULL]
dt.init = unique(dt.init)
summary(dt.init$sentN) # mean = 10, median = 8, q1 = 4, q3 = 12
# save the NodeIDs of initial posts that have >= 8 sentences to file
write.table(dt.init[sentN >= 8, PostID], file = 'init_NodeIDs_gt8.txt', row.names = F, col.names = F)


# survey about first comments
sql = 'select postId, sentId from firstCommSents'
df = dbGetQuery(conn, sql)
dt.fc = data.table(df)
setkey(dt.fc, postId)

dt.fc.sn = dt.fc[, .(sentN = .N), by = postId]
summary(dt.fc.sn$sentN) # mean=7.7, median=6, q1=3, q3=10

write.table(dt.fc.sn$postId, file='firstComm_postIds_all.txt', row.names=F, col.names=F)


## survey all comments (including the first comments)
sql = 'select postId, sentId from allCommSents'
df = dbGetQuery(conn, sql)
dt.ac = data.table(df)
setkey(dt.ac, postId)

dt.ac.sn = dt.ac[, .(sentN = .N), by = postId]
summary(dt.ac.sn$sentN) # mean=7.2, median=5, q1=3,q3=9

write.table(dt.ac.sn$postId, file='allComm_postIds_all.txt', row.names=F, col.names=F)
