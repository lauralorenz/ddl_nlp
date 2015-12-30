from sklearn.cross_validation import KFold
from os import path, makedirs
import re
import numpy as np
import optparse


def tokenize_sentences(corpus=None):
    '''
    split the corpus into sentences.
    :param corpus: a string from a text file representing the corpus
    :return:
    '''
    return re.split('(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?)\s',corpus)

def generate_word2vec_folds(corpus='Empty', folds=3, seed=10):
    '''
    Generates a series of text files that each represent a training or test split of the text data.  Since word2vec does
    not conduct any calculations that rely on interactions across sentence boundaries this cross-validation k-fold generator
    splits the text by sentence and then chooses random sentences together into the same corpus.  This fold generator also
    assumes the original corpus and any ontological additions have not been added to the same file yet.  It expects both.
    The training set includes all of the ontological additions, not just a random subset.
    :return:
    '''
    #tokenize the corpus into sentences because we need to get a random sample of sentences from the resulting list.
    tokenized_corpus=tokenize_sentences(corpus)

    tokenized_corpus=np.array(tokenized_corpus)

    number_of_sentences=len(tokenized_corpus)

    kf = KFold(n=number_of_sentences, n_folds=folds, shuffle=True, random_state=seed)

    corpus_split = []
    for train_index, test_index in kf:
        corpus_split.append({'train':tokenized_corpus[train_index], 'test':tokenized_corpus[test_index]})

    return corpus_split

def collapse_corpus_sentence_list(folds_dict):
    '''
    Collapses the lists of sentences back down into a single string
    :param folds_dict: the dictionary that includes lists of sentences for every training, and test instance.
    :param ontology_text: The raw ontology text.
    :return:
    '''
    train_text = [' '.join(list(row['train'])) for row in folds_dict]
    test_text = [' '.join(list(row['test'])) for row in folds_dict]

    for row_index in range(len(folds_dict)):
        folds_dict[row_index] = {'train':train_text[row_index], 'test':test_text[row_index]}

    return folds_dict

def append_ontology_text(folds_dict, ontology_text):
    '''
    Appends the ontology text to the end of each training instance.
    :param ontology_text: Raw string of constructed ontology sentences.
    :return:
    '''

    if ontology_text is not None:
        for row_index in range(len(folds_dict)):
            folds_dict[row_index]['train'] = folds_dict[row_index]['train'] + ' ' + ontology_text

    return folds_dict

def store_file(folds_dict, input_data_dir):
    '''
    Derive the location to save the resulting json file that includes all of the fold definitions.  Each fold generates a
      seperate directory depending on the number of folds chosen.  Within each fold directory is a train and test directory.
      Files are stored in all proper locations after parsing a dict with all of the data in it..
    :param folds_dict:
    :return:
    '''
    def gen_fold_file(fold, fold_number, fold_dir, portion='train'):
        '''
        Given designation as either training or test and the fold number. Write the file to the correct location with
        correct name
        :param fold: the string text for the specific fold in question.
        :param fold_number: the index number for the fold
        :param portion: either training, test, or holdout if you are feeling that way.
        :return: None
        '''
        portion_dir = path.join(fold_dir, portion)
        if not path.exists(portion_dir):
            makedirs(portion_dir)
        fold_file = path.join(portion_dir, portion + '.txt')

        with open(fold_file,'wb') as outfile:
            outfile.write(fold[portion])

    current_dir = path.dirname(path.realpath(__file__))
    # assumes script being run from withing one of the sub-folders under fun_3000
    parent_dir = path.abspath(path.join(current_dir, '../..'))

    data_dir = path.join(parent_dir, 'data')

    specific_data_dir = path.join(data_dir, input_data_dir)

    if not path.exists(specific_data_dir):
        makedirs(specific_data_dir)

    # Generate a folder for each fold and under each fold folder builda  folder for train and test, then add a train
    # and test file in each folder.
    fold_number = 1
    for fold in folds_dict:
        fold_dir = path.join(specific_data_dir, str(fold_number))
        if not path.exists(fold_dir):
            makedirs(fold_dir)

        gen_fold_file(fold = fold, fold_number=str(fold_number), fold_dir=fold_dir, portion='train')

        gen_fold_file(fold = fold, fold_number=str(fold_number), fold_dir=fold_dir, portion='test')

        fold_number += 1

def read_inputs(input_data_dir, corpus_filename, ontology_filename):
    # Set data directory
    current_dir = path.dirname(path.realpath(__file__))
    parent_dir = path.abspath(path.join(current_dir, '../..'))

    data_dir = path.join(parent_dir, 'data')

    this_model_dir = path.join(data_dir, input_data_dir)
    corpus_filename = path.join(this_model_dir, corpus_filename)
    ontology_filename = path.join(this_model_dir, ontology_filename)

    with open(corpus_filename,'rb') as infile:
        corpus = infile.read()

    with open(ontology_filename,'rb') as infile:
        ontology = infile.read()

    return corpus, ontology


def run(input_data_dir, corpus_filename, ontology_filename=None, k=3, seed=10):
    corpus, ontology = read_inputs(input_data_dir, corpus_filename, ontology_filename)
    corpus_split=generate_word2vec_folds(corpus=corpus, folds=3)
    collapsed_lists=collapse_corpus_sentence_list(folds_dict=corpus_split)
    final_splits=append_ontology_text(folds_dict=collapsed_lists, ontology_text=ontology)
    store_file(folds_dict=final_splits, input_data_dir=input_data_dir)

run(input_data_dir='dog', corpus_filename='model_data.txt', ontology_filename='model_data.txt')

if __name__ == '__main__':

    parser = optparse.OptionParser()
    parser.add_option('-d', '--data_dir', dest='input_data_dir', default='', help='Specify data directory')
    parser.add_option('-k', '--folds', dest='k', default=3, help='Specify number of folds requested', type='int')
    parser.add_option('-c', '--corpus_filename', dest='corpus_filename', default='', help='Specify the location/filename of the corpus text')
    parser.add_option('-o', '--ontology_filename', dest='ontology_filename', default='', help='Specify the location/filename of the ontology text')
    parser.add_option('-s', '--seed', dest='seed', default=100, help='Specify the seed for the random number generator', type='int')
    (opts, args) = parser.parse_args()

    run(opts.input_data_dir, opts.corpus_filename, opts.ontology_filename, opts.k, opts.seed)