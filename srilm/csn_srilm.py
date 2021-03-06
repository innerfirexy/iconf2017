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
import glob
import os

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
def train_compute_samepos(data_file, res_file, cleanup=False):
    data = pickle.load(open(data_file, 'rb'))
    fold_n = len(data)
    sent_n = len(data[data.keys()[0]])
    results = []
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
            train_cmd = ['./ngram-count', '-order', '3', '-text', train_tmp_file, '-lm', train_tmp_file+'.model',
                '&>/dev/null']
            # call subprocess
            # print 'training fold %s sent_id %s ...' % (i, j)
            return_code = subprocess.check_call(train_cmd)
            if return_code != 0:
                print 'train failure'
                exit()
            #################
            # computing part
            #################
            test_sent_ids = []
            test_tmp_file = 'test_sent.tmp'
            with open(test_tmp_file, 'w') as fw:
                for item in data[i][j]:
                    fw.write(' '.join(item[1]) + '\n')
                    test_sent_ids.append(item[0])
            # compute
            compute_cmd = ['./ngram','-order','3','-lm',train_tmp_file+'.model','-ppl',test_tmp_file,'-debug','1']
            try:
                output = subprocess.check_output(compute_cmd, stderr=subprocess.STDOUT) # !
                # the old pattern misses the scientific numbers, e.g., ppl = 2.30674e+06
                # r'ppl=\s[0-9]*\.?[0-9]+\s'
                matches = re.findall(r'ppl=\s\S+\s', output)
                ppls = [m[5:].strip() for m in matches[:-1]] # do not include the last match,cuz it's the average value
            except Exception as e:
                print 'compute error \nfoldId: %s, sendId: %s' % (i, j)
                raise
            else:
                # compose results
                if len(test_sent_ids) != len(ppls):
                    print 'nomatch problem \nfoldId: %s, sendId: %s' % (i, j)
                    print 'test_sent_ids len: ' + str(len(test_sent_ids))
                    print 'ppls len: ' + str(len(ppls))
                    exit()
                res = [(test_sent_ids[k], j, ppls[k]) for k in range(0, len(ppls))]
                results += res
            # print progress
            sys.stdout.write('\rfold %s sent %s computed' % (i, j))
            sys.stdout.flush()
    # write results to file
    with open(res_file, 'w') as fw:
        for item in results:
            fw.write(','.join(map(str, item)) + '\n')
    # cleanup
    if (cleanup):
        files = glob.glob('*.tmp') + glob.glob('*.model')
        for f in files:
            os.remove(f)

# compute entropy, using hold-out folds as training set,
# do not differentiate sentence positions
def train_compute_diffpos(data_file, res_file, cleanup=False):
    data = pickle.load(open(data_file, 'rb'))
    fold_n = len(data)
    sent_n = len(data[data.keys()[0]])
    results = []
    # for each fold
    for i in range(1, fold_n+1):
        # prepare for training
        train_sents = []
        for j in range(1, i) + range(i+1, fold_n+1):
            for k in range(0, sent_n):
                for item in data[j][k]:
                    train_sents.append(' '.join(item[1]))
        train_tmp_file = 'train_f' + str(i) + '.tmp'
        with open(train_tmp_file, 'w') as fw:
            for s in train_sents:
                fw.write(s + '\n')
        # train
        train_cmd = ['./ngram-count', '-order', '3', '-text', train_tmp_file, '-lm', train_tmp_file+'.model']
        return_code = subprocess.check_call(train_cmd)
        if return_code != 0:
            print 'train failure'
        # for each sent_id in fold i
        test_tmp_file = 'test_sent.tmp'
        for j in range(0, sent_n):
            # prepare for computing
            test_sent_ids = []
            with open(test_tmp_file, 'w') as fw:
                for item in data[i][j]:
                    fw.write(' '.join(item[1]) + '\n')
                    test_sent_ids.append(item[0])
            # compute
            compute_cmd = ['./ngram','-order','3','-lm',train_tmp_file+'.model','-ppl',test_tmp_file,'-debug','1']
            try:
                output = subprocess.check_output(compute_cmd, stderr=subprocess.STDOUT) # !
                # the old pattern misses the scientific numbers, e.g., ppl = 2.30674e+06
                # r'ppl=\s[0-9]*\.?[0-9]+\s'
                matches = re.findall(r'ppl=\s\S+\s', output)
                ppls = [m[5:].strip() for m in matches[:-1]] # do not include the last match,cuz it's the average value
            except Exception as e:
                print 'compute error \nfoldId: %s, sendId: %s' % (i, j)
                raise
            else:
                # compose results
                if len(test_sent_ids) != len(ppls):
                    print '\nnomatch problem \nfoldId: %s, sendId: %s' % (i, j)
                    print 'test_sen_ids len: %s, ppls len: %s' % (len(test_sent_ids), len(ppls))
                    exit()
                res = [(test_sent_ids[k], j, ppls[k]) for k in range(0, len(ppls))]
                results += res
            # print progress
            sys.stdout.write('\rfold %s sent %s computed' % (i, j))
            sys.stdout.flush()
    # write results to file
    with open(res_file, 'w') as fw:
        for item in results:
            fw.write(','.join(map(str, item)) + '\n')
    # cleanup
    if (cleanup):
        files = glob.glob('*.tmp') + glob.glob('*.model')
        for f in files:
            os.remove(f)


# main
if __name__ == '__main__':
    # initial posts
    # train_compute_samepos(data_file='../init_post_cvdata_all.pkl', res_file='ppl_samepos.txt', cleanup=True)
    # train_compute_diffpos(data_file='../init_post_cvdata_all.pkl', res_file='ppl_diffpos.txt', cleanup=True)

    # first comments
    # train_compute_diffpos(data_file='../firstComm_cvdata_all.pkl', res_file='fc_ppl_diffpos.txt', cleanup=True)

    # all comments
    train_compute_diffpos(data_file='../allComm_cvdata_all.pkl', res_file='ac_ppl_diffpos.txt', cleanup=True)
