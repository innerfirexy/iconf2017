#!/usr/local/bin/python
# Compute sentence entropy of CSN posts
# Yang Xu
# 9/9/2016

import MySQLdb
import pickle
import sys
import random
import spacy
import re

from nltk_legacy.ngram import NgramModel
from nltk.probability import LidstoneProbDist

# from nltk_legacy.ngram import NgramModel
# from nltk.probability import LidstoneProbDist

# get db connection
def db_conn(db_name):
    # db init: ssh yvx5085@brain.ist.psu.edu -i ~/.ssh/id_rsa -L 1234:localhost:3306
    conn = MySQLdb.connect(host = "127.0.0.1",
                    user = "yang",
                    port = 3306,
                    passwd = "05012014",
                    db = db_name)
    return conn

# tokenize sentences in initial posts
def tokenize_init_posts(nlp):
    conn = db_conn('csn')
    cur = conn.cursor()
    # select the text body of initial posts and its corresponding NodeID
    sql = 'select distinct NodeID, NodeRevisionBody from newforum'
    cur.execute(sql)
    data = cur.fetchall()
    # tokenize each text body
    results = []
    for r_idx, row in enumerate(data):
        if len(row[1].strip()) == 0: # handle empty text body
            continue
        try:
            doc = nlp(unicode(row[1]))
            for s_idx, sent in enumerate(doc.sents):
                raw = sent.text
                tokens = []
                for i, t in enumerate(sent):
                    if not t.is_punct:
                        if i == 0:
                            if t.pos_ == 'PROPN' or t.text == 'I':
                                tokens.append(t.text)
                            else:
                                tokens.append(t.text.lower())
                        else:
                            tokens.append(t.text)
                results.append((row[0], s_idx, raw, ' '.join(tokens)))
        except UnicodeDecodeError as e:
            print 'NodeID: ' + str(row[0])
            continue
        except Exception as e:
            raise
        # print progress
        if r_idx % 100 == 0:
            sys.stdout.write('\r%s/%s done.' % (r_idx, len(data)))
            sys.stdout.flush()
    pickle.dump(results, open('init_posts_tokenized_results.pkl', 'wb'))

# write the tokenized initial posts to db
def init_posts_2db():
    # create table
    conn = db_conn('csn')
    cur = conn.cursor()
    sql = 'create table if not exists initPostSents (postId int, sentId int, raw longtext, tokens longtext, \
        primary key (postId, sentId))'
    cur.execute(sql)
    # load data and insert to db
    data = pickle.load(open('init_posts_tokenized_results.pkl', 'rb'))
    for i, row in enumerate(data):
        (post_id, sent_id, raw, tokens) = row
        sql = 'insert into initPostSents values(%s, %s, %s, %s)'
        cur.execute(sql, (post_id, sent_id, raw, tokens))
        # print progress
        if i % 100 == 0:
            sys.stdout.write('\r%s/%s inserted' % (i, len(data)))
            sys.stdout.flush()
    conn.commit()

# clean the tokens col of initPostSents table, by
# removing new lines "\n", and replace urls, emails, and numbers with uniform symbols
def clean_init_posts_db(nlp):
    # db conn
    conn = db_conn('csn')
    cur = conn.cursor()
    # select data
    sql = 'select postId, sentId, tokens from initPostSents'
    cur.execute(sql)
    data = cur.fetchall()
    # clean and update
    cleaned_data = []
    for i, row in enumerate(data):
        post_id = row[0]
        sent_id = row[1]
        tokens_text = row[2]
        if len(tokens_text.strip()) == 0: # empty tokens
            continue
        tokens_text = tokens_text.replace('\n', ' ')
        tokens = map(unicode, tokens_text.split()) # get tokenized list
        doc = nlp.tokenizer.tokens_from_list(tokens) # build doc from the pre-existing tokens
        cleaned = []
        for t in doc:
            if t.is_punct or t.is_space:
                continue
            elif t.like_url:
                cleaned.append('URL')
            elif t.like_email:
                cleaned.append('EMAIL')
            elif t.like_num:
                cleaned.append('NUM')
            elif not t.is_alpha:
                if re.match(r'^\.+[x|X]+', t.shape_) is not None:
                    cleaned.append(re.sub(r'^\.+', '', t.text))
                else:
                    cleaned.append(t.text)
            else:
                cleaned.append(t.text)
        cleaned_text = ' '.join(cleaned)
        cleaned_data.append((post_id, sent_id, cleaned_text))
        # sql = 'update initPostSents set tokens = %s where postId = %s and sentId = %s'
        # cur.execute(sql, (cleaned_text, post_id, sent_id))
        # print process
        if i % 100 == 0:
            sys.stdout.write('\r%s/%s updated.' % (i, len(data)))
            sys.stdout.flush()
    pickle.dump(cleaned_data, open('init_posts_tokens_cleaned.pkl', 'wb'))

def update_cleaned_posts():
    # db conn
    conn = db_conn('csn')
    cur = conn.cursor()
    # load and update
    data = pickle.load(open('init_posts_tokens_cleaned.pkl', 'rb'))
    for i, row in enumerate(data):
        sql = 'update initPostSents set tokens = %s where postId = %s and sentId = %s'
        cur.execute(sql, (row[2], row[0], row[1]))
        # print process
        if i % 100 == 0:
            sys.stdout.write('\r%s/%s updated.' % (i, len(data)))
            sys.stdout.flush()
    conn.commit()

# the func to select all unique initial post Ids
def get_all_init_postIds():
    conn = db_conn('csn')
    cur = conn.cursor()
    sql = 'select distinct NodeID from newforum' # select all NodeIDs for initial posts
    cur.execute(sql)
    post_ids = [item[0] for item in cur.fetchall()]
    with open('init_NodeIDs_all.txt', 'w') as fw:
        for p_id in post_ids:
            fw.write(str(p_id)+'\n')
# the func that read post_ids from text file
def read_post_ids(file_name):
    post_ids = []
    with open(file_name, 'r') as fr:
        for line in fr:
            post_ids.append(line.strip())
    return post_ids


# the func that prepares data for cross-validation
# n-fold cross-validation are applied
def prepare_cv_data(post_ids, sent_n, fold_n, data_file):
    assert sent_n >= 1
    assert fold_n >= 2
    assert len(post_ids) > fold_n
    # db conn
    conn = db_conn('csn')
    cur = conn.cursor()
    # prepare cv folds
    random.shuffle(post_ids)
    fold_size = len(post_ids) / fold_n
    ids_folds = []
    for i in range(0, fold_n):
        if i < fold_n-1:
            ids_folds.append(post_ids[i*fold_size: (i+1)*fold_size])
        else:
            ids_folds.append(post_ids[i*fold_size:])
    # prepare the train and test set into a dict
    data_all = {i:[] for i in range(1, fold_n+1)}
    for i in range(1, fold_n+1):
        for j in range(0, sent_n):
            data_all[i].append([])
    for i in range(0, fold_n):
        for p_id in ids_folds[i]:
            sql = 'select tokens from initPostSents where postId = %s'
            cur.execute(sql, [p_id])
            rows = cur.fetchall()
            for j, row in enumerate(rows):
                text = row[0]
                if j >= sent_n:
                    break
                elif len(text.strip()) == 0:
                    continue
                else:
                    data_all[i+1][j].append((p_id, text.split()))
        sys.stdout.write('\r%s/%s prepared' % (i+1, fold_n))
        sys.stdout.flush()
    print 'dumping...'
    pickle.dump(data_all, open(data_file, 'wb'))
    print 'done.'

# the func that compute entropy using sentences from the same position as train and test sets
def entropy_same_pos(data_file, res_file):
    data = pickle.load(open(data_file, 'rb'))
    # fold_n = len(data)
    # sent_n = len(data[data.keys()[0]])
    fold_n = 2
    sent_n = 8
    results = []
    # for each fold
    for i in range(1, fold_n+1):
        # for each sentence position
        for j in range(0, sent_n):
            # train
            train_sents = []
            for k in range(1, i) + range(i+1, fold_n+1):
                for item in data[k][j]:
                    train_sents.append(item[1])
            print 'start training fold %s, sentId %s' % (i, j)
            lm = NgramModel(3, train_sents)
            pickle.dump(lm, open('models/m_'+'f'+str(i)+'_s'+str(j), 'wb'))
            # compute
            for item in data[i][j]:
                try:
                    ent = lm.entropy(item[1])
                except Exception as e:
                    print 'postId: ' + item[0]
                    print 'sentId: ' + str(j)
                    raise
                else:
                    results.append((item[0], j, ent))
    # write results to file
    with open(res_file, 'w') as fw:
        for row in results:
            fw.write(', '.join(map(str, row))+'\n')


## todo
# remove \n in tokens
# replace the url, email, num in tokens


# main
if __name__ == '__main__':
    # load
    # nlp = spacy.load('en')
    # tokenize initial posts
    # tokenize_init_posts(nlp)
    # insert tokenized initial posts to db
    # init_posts_2db()
    # clean tokens column
    # clean_init_posts_db(nlp)
    # update_cleaned_posts()

    # compute the entropy for the initial posts (longer than 8 sentences)
    # read postIds from .csv file
    # init_post_ids = []
    # with open('init_NodeIDs_gt8.csv', 'r') as fr:
    #     for line in fr:
    #         init_post_ids.append(line.strip())
    # compute
    # prepare_cv_data(init_post_ids, 8, 10, data_file='init_posts_cvdata.pkl')
    # entropy_same_pos(data_file='init_posts_cvdata.pkl', res_file='init_posts_entropy_samepos.txt')

    # prepare the data for all initial posts
    # get_all_init_postIds()
    post_ids = read_post_ids('init_NodeIDs_all.txt')
    prepare_cv_data(post_ids=post_ids, sent_n=10, fold_n=10, data_file='init_post_cvdata_all.pkl')
