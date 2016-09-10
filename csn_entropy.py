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
        tokens = tokens_text.split() # get tokenized list
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


# the func that compute entropy using sentences from the same position as train and test sets
# n-fold cross-validation are applied
def entropy_same_pos(post_ids, sent_n, fold_n):
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
    for i in range(0, fold_n):
        for p_id in ids_folds[i]:
            sql = ''
            cur.execute(sql)
            data =
            for
            data_all
    pass


## todo
# remove \n in tokens
# replace the url, email, num in tokens


# main
if __name__ == '__main__':
    # load
    nlp = spacy.load('en')
    # tokenize initial posts
    # tokenize_init_posts(nlp)
    # insert tokenized initial posts to db
    # init_posts_2db()
    # clean tokens column
    clean_init_posts_db(nlp)

    # compute the entropy for the initial posts (longer than 8 sentences)
