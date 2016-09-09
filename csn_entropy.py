#!/usr/local/bin/python
# Compute sentence entropy of CSN posts
# Yang Xu
# 9/9/2016

import MySQLdb
import pickle
import sys
import spacy

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
        if r_idx % 100 == 0:
            sys.stdout.write('\r%s/%s done.' % (r_idx, len(data)))
            sys.stdout.flush()
    pickle.dump(results, open('init_posts_tokenized_results.pkl', 'wb'))

# main
if __name__ == '__main__':
    # load
    nlp = spacy.load('en')
    # tasks
    tokenize_init_posts(nlp)
