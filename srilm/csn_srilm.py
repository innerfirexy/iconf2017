#!/usr/local/bin/python
# User the ngram-count and ngram binaries from SRILM to estimate the language models and
# to compute the sentence entropy
# Yang Xu
# 9/12/2016

import MySQLdb
import pickle
import sys
import re
import subprocess

# get db connection
def db_conn(db_name):
    # db init: ssh yvx5085@brain.ist.psu.edu -i ~/.ssh/id_rsa -L 1234:localhost:3306
    conn = MySQLdb.connect(host = "127.0.0.1",
                    user = "yang",
                    port = 3306,
                    passwd = "05012014",
                    db = db_name)
    return conn

# the func that trains and model and computes the entropy
def train_compute_samepos(data_file, res_file):
    data = pickle.load(open(data_file, 'rb'))
    fold_n = len(data)
    sent_n = len(data[data.keys()[0]])
    # for each fold
    for i in range(1, fold_n+1):
        # for each sentence position
        for j in range(0, sent_n):
            ################
            # training part
            ################
            # prepare
            train_sents = []
            for k in range(1, i) + range(i+1, fold_n+1):
                for item in data[k][j]:
                    train_sents.append(' '.join(item[1]))
            train_tmp_file = 'train_f' + str(i) + 's' + str(j) + '.tmp'
            with open(train_tmp_file, 'w') as fw:
                for s in train_sents:
                    fw.write(s + '\n')
            train_cmd = ['./ngram-count', '-order', '3', '-text', train_tmp_file, '-lm', train_tmp_file+'.model']
            # call subprocess
            print 'training fold %s sent_id %s ...' % (i, j)
            return_code = subprocess.check_call(train_cmd)
            if return_code == 0:
                print 'train success'
            else:
                print 'train failure'
            #################
            # computing part
            #################
            results = []
            for item in data[i][j]:
                # prepare
                sent = ' '.join(item[1])
                test_tmp_file = 'test_sent.tmp'
                with open(test_tmp_file, 'w') as fw:
                    fw.write(sent + '\n')
                # compute
                compute_cmd = ['./ngram','-order','3','-lm',train_tmp_file+'.model','-ppl',test_tmp_file]
                try:
                    output = subprocess.check_output(compute_cmd)
                    matches = re.findall(r'ppl=\s[0-9]*\.[0-9]+\s', output)
                    ppl = matches[0][5:].strip()
                except Exception as e:
                    print 'postId: ' + item[0]
                    print 'sentId: ' + str(j)
                    raise
                else:
                    result.append((item[0], ppl))
            # print progress
            sys.stdout.write('\rfold %s sent %s computed' % (i, j))
            sys.stdout.flush()


# main
if __name__ == '__main__':
    train_compute_samepos(data_file='../init_post_cvdata_all.pkl', res_file='test_run')
