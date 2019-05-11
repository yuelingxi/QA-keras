#-*- coding: utf-8 -*-


import os
os.environ['KERAS_BACKEND'] = 'tensorflow'
import keras.backend as K
K.set_image_dim_ordering('tf')
from imp import reload
import numpy as np
import io

import globalvar as gl
from data_preprocessor import tokenize, loadEmbeddingsIndex, generateWord2VectorMatrix
from keras.preprocessing.sequence import pad_sequences
from loadModel import creatCNNModel, creat_model_for_predicate
from itertools import islice

import sys
reload(sys)
sys.setdefaultencoding('utf8')


class CNNpredict:
    ques_maxlen=9
    rela_maxlen=3
    EMBEDDING_DIM=200
    NUM_FILTERS = 128
    LSTM_DIM = 150
    RelaFile = "./data/relation_fenci.txt"
    preprocessWordVector_files = "reducedW2V.txt"
    preprocessWordVector_path = "/data/ylx/"
    CLASS_INDEX= None
    relation_vec= None
    wd_idx=None
    model=None
    embedding_matrix = None
    NUM_OF_RELATIONS = 708
    def __init__(self):
        gl.set_NUM_OF_RELATIONS(self.NUM_OF_RELATIONS)
        gl.set_LSTM_DIM(self.LSTM_DIM)
        gl.set_EMBEDDING_DIM(self.EMBEDDING_DIM)
        gl.set_ques_maxlen(self.ques_maxlen)
        gl.set_relation_maxlen(self.rela_maxlen)
        gl.set_NUM_FILTERS(self.NUM_FILTERS)
        self.CLASS_INDEX = self.load_CLASS_INDEX()
        self.relation_vec, self.wd_idx, self.embedding_matrix = self.prepareWork()
        self.model = self.loadCNNModelFromFile()
        inpute_question = "创始人 是 谁"
        self.predicated_quick( inpute_question)
    def how_big(self):
        return(len(self.thing))

    def predicated_quick(self, inpute_question):



        # 构造数据
        str2 = inpute_question.decode('utf-8', 'ignore')
        # print(str2)
        question = [tokenize(str2)]
        # print(str(question).decode('string_escape'))

        # print(str(relations).decode('string_escape'))
        # f = open('relation.txt', 'w')  # 若是'wb'就表示写二进制文件
        # f.write(str(relations))
        # f.close()
        # f = open('question.txt', 'w')  # 若是'wb'就表示写二进制文件
        # f.write(str(question))
        # f.close()

        # 获取问题和关系最大长度

        # 对训练集和测试集，进行word2vec
        question_vec = self.vectorize_dialog(self.wd_idx,question, self.ques_maxlen)
        questions_vec = np.tile(question_vec, (self.NUM_OF_RELATIONS, 1))
        print("questions_vec")
        print(np.array(questions_vec).shape)

        y = self.model.predict([self.relation_vec, questions_vec], batch_size=10000)
        # print(y)
        tag, num, index = self.decode_predictions2( y, top=1)
        # print('Predicted tag=:')
        # print(tag.decode('string_escape'))
        # print('Predicted num=:')
        # print(num)
        # print('Predicted index=:')
        # print(index)
        # print(result)
        # print('Predicted:')
        # for lines in result:
        #   for line in lines:
        #      print(str(line).decode('string_escape'))
        # 结果
        return tag

    def loadCNNModelFromFile(self):
        # 加载模型


        model = creatCNNModel(self.EMBEDDING_DIM, self.wd_idx, self.embedding_matrix, self.ques_maxlen, self.rela_maxlen, self.NUM_FILTERS, self.LSTM_DIM,
                              0.01)

        model.load_weights(filepath='my_model_weights.h5', by_name=True)

        return model

    def prepareWork(self):

        relations = self.parse_relation()
        # 建立词表。词表就是文本中所有出现过的单词组成的词表。
        temp = []

        f = io.open(os.path.join(self.preprocessWordVector_path, self.preprocessWordVector_files), 'r', encoding='UTF-8')
        for line in islice(f, 1, None):
            values = line.split()

            try:
                coefs = np.asarray(values[1:], dtype='float32')
                word = values[0]
            except:
                continue
            # coefs = np.asarray(values[1:], dtype='float32')
            temp.append(word)
        f.close()
        lexicon = set(temp)
        lexicon = sorted(lexicon)
        lexicon_size = len(lexicon) + 1
        print("lexicon_size")
        print(lexicon_size)
        # word2vec，并求出对话集和问题集的最大长度，padding时用。
        wd_idx = dict((wd, idx + 1) for idx, wd in enumerate(lexicon))
        # 获取问题和关系最大长度


        # 计算分位数，在get_dialog函数中传参给max_len
        # dia_80 = np.percentile(map(len, (x for x, _, _ in train + test)), 80)

        gl.set_relation_maxlen(self.rela_maxlen)
        # 对训练集和测试集，进行word2vec
        # 对训练集和测试集，进行word2vec
        # question_vec = vectorize_dialog(question, wd_idx, ques_maxlen)
        relation_vec = self.vectorize_dialog( wd_idx,relations, self.rela_maxlen)
        # print("question_vec:")
        # print(str(question_vec).decode('string_escape'))

        # questions_vec = np.tile(question_vec, (NUM_OF_RELATIONS, 1))
        # print("questions_vec")
        # print(np.array(questions_vec).shape)
        print("relation_vec")
        print(np.array(relation_vec).shape)

        embedding_index = loadEmbeddingsIndex(self.preprocessWordVector_path, self.preprocessWordVector_files)
        embedding_matrix = generateWord2VectorMatrix(embedding_index, wd_idx)
        return relation_vec, wd_idx, embedding_matrix
    def decode_predictions2(self,preds, top=1):
        top_indices = preds.argmax()
        tag=self.CLASS_INDEX[top_indices]
        num=preds[top_indices]
        return tag,num,top_indices

    def load_CLASS_INDEX(self):
        CLASS_INDEX = []

        f2 = io.open('./data/relation.txt', 'r', encoding='UTF-8')
        for rela in f2:
            rela = rela.strip()
            CLASS_INDEX.append(rela)
            # print(rela.decode('string_escape'))
        f2.close()
        return CLASS_INDEX



    def parse_relation (self):
        relation = []
        f2 = io.open(self.RelaFile, 'r', encoding='UTF-8')
        for rela in f2:
            #print(rela)
            relation.append(tokenize(rela.strip()))
        f2.close()
        return relation


    def vectorize_dialog(self,wd_idx,data, maxlen ):
    #向量化,返回对应词表的索引号
        vec = []
        for line in data:
            idx = [(wd_idx)[w] for w in line ]

            vec.append(idx)
        #序列长度归一化，分别找出对话，问题和答案的最长长度，然后相对应的对数据进行padding。
        return  pad_sequences(vec, maxlen = maxlen)




model = CNNpredict()

