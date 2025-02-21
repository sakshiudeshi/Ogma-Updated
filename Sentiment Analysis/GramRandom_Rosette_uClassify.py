import csv
import re, random, pickle
import numpy as np
import copy
import datetime

from nltk import CFG, ChartParser, Tree, Nonterminal

from sklearn.feature_extraction.text import CountVectorizer
from sklearn.feature_extraction.text import TfidfTransformer
from random import choice
import jacc_thresh

from google.cloud import language
from google.cloud.language import enums
from google.cloud.language import types

# import textrazor_API, aylien_API
import rosette_API, uclassify_API

import warnings
warnings.filterwarnings("ignore",category=FutureWarning)

tfidf_transformer = TfidfTransformer()
count_vect = CountVectorizer()

# grammarA = CFG.fromstring('''S -> NP VP
# VP -> V NP | V NP PP | VP PP
# PP -> P NP
# V -> "saw" | "ate" | "walked" | "shot" | "killed" | "wounded"
# NP -> "John" | "Mary" | "Bob" | Det N | Det N PP | "I"
# Det -> "a" | "an" | "the" | "my" | "an" | "my"
# N -> "man" | "dog" | "cat" | "telescope" | "park" | "elephant" | "pajamas" | "cat" | "dog"
# P -> "in" | "on" | "by" | "with" | "outside"''')

gramLetter = "F"
gramFileName = "Grammar " + gramLetter + ".txt"
folder_type = "Rosette uClassify Grammar " + gramLetter

f = open(gramFileName, 'r')
grammar_string = f.read()
f.close()
# print grammarA
grammar = CFG.fromstring(grammar_string)

# productions = '''[S -> NP VP, NP -> Det N PP, Det -> 'an', N -> 'man', PP -> P NP, P -> 'on', NP -> Det N, Det -> 'my', N -> 'cat', VP -> VP PP, VP -> VP PP, VP -> V NP, V -> 'shot', NP -> 'Bob', PP -> P NP, P -> 'outside', NP -> Det N PP, Det -> 'an', N -> 'pajamas', PP -> P NP, P -> 'outside', NP -> 'Bob', PP -> P NP, P -> 'with', NP -> Det N PP, Det -> 'my', N -> 'pajamas', PP -> P NP, P -> 'in', NP -> Det N PP, Det -> 'my', N -> 'dog', PP -> P NP, P -> 'with', NP -> Det N PP, Det -> 'my', N -> 'cat', PP -> P NP, P -> 'by', NP -> Det N, Det -> 'an', N -> 'telescope']
# '''

# sentence = "an man on my cat shot Bob outside an pajamas outside Bob with my pajamas in my dog with my cat by an telescope" #Sentence has error
# sentence = "an dog in the man saw Bob in an dog in Bob outside an park on the elephant in my elephant in my elephant"
# sentence = "the elephant with my cat walked I with an dog outside John with a cat outside my dog with the man with my man"
# sentence = "my elephant shot an cat in an cat in I in an cat outside I in I outside an pajamas in an dog in I in my cat in an pajamas"
# sentence = "Joe saw  a frightened angry tall little tall bear said a fish saw a frightened squirrel said a frightened little tree on Buster"
# sentence = "Elise viewed I with my monkey with Steve near Mark near Mark near a giraffe"
# sentence = "a babbon disabled an park outside Gary outside my owl"
# sentence = "my park inside an baboon with Nick damaged Gemma in Gemma near Gary"
# sentence = "James built Stephen by a ship in an man with James by an cat with an tree with James outside Irene"
sentence = "Holly captured the bus by the snake Holly Marcus on the pajamas"

iters = 200
prob_delta = 0.2

# jaccard_threshold = 0.3
jaccard_threshold = jacc_thresh.dict_jacc[folder_type]

client = language.LanguageServiceClient()

def get_label_google(inp_text):
    print inp_text
    text = inp_text
    document = types.Document(
        content=text,
        type=enums.Document.Type.PLAIN_TEXT)

    # Detects the sentiment of the text
    sentiment = client.analyze_sentiment(document=document).document_sentiment

    score = sentiment.score
    mag = sentiment.magnitude
    print "score, mag"
    print score, mag
    print ""
    # print score
    response_list = []
    if score > 0.25:
        response_list.append(["POSITIVE", score])
    elif score < -0.25:
        response_list.append(["NEGATIVE", score])
    else:
        response_list.append(["NEUTRAL", score])
    return response_list[0]


def jaccard(a, b):
    l1 = set()
    l2 = set()

    for item in a:
        l1.add(item[0])

    for item in b:
        l2.add(item[0])

    l = l1.intersection(l2)
    return float(len(l)) / (len(l1) + len(l2) - len(l))

def get_productions(sentence, grammar):
    trees = []
    sent = sentence.split(' ')
    print sent
    cfgGrammar = CFG.fromstring(grammar)

    parser = ChartParser(cfgGrammar)
    for tree in parser.parse(sent):
        trees.append(str(tree).replace("\n", " "))

    # print trees[0]
    t = Tree.fromstring(trees[0])
    return t.productions()



def get_grammar_dict(grammar):
    lines = grammar.split("\n")

    quoted = re.compile('"([^"]*)"')
    split_lines = []

    for line in lines:
        split_lines.append(line.split('->'))

    line_d = {}
    for line in split_lines:
        if quoted.findall(line[1]):
            line_d[line[0].strip()] = quoted.findall(line[1])
    return line_d


# print line_d
def get_base_prods(productions):
    single_quoted = re.compile(r"'(.*?)'")
    prods = []
    for prod in productions.split(","):
        if single_quoted.findall(prod.strip()):
            p = prod.strip().split(" -> ")
            prods.append([p[0], single_quoted.findall(p[1])[0]])


    return prods

def sentence_from_prods(prods):
    list = []
    for p in prods:
        list.append(p[1])
    return " ".join(list)

def evaluate(sentence, to_print=False):
    # return evaluate_local(sentence, to_print)
    # return evaluate_api(sentence, to_print)
    # return evaluate_api_jaccard(sentence, to_print)
    return evaluate_simple(sentence, to_print)

def evaluate_simple(sentence, to_print):
    p1 = rosette_API.get_label(sentence=sentence)
    p2 = get_label_google(sentence)

    if (p1[0] != p2[0]):
        if to_print:
            print p1, p2, sentence

        return True, p1, p2
    else:
        return False, p1, p2


# def evaluate_local(sentence, to_print):
#     sentence_list = np.array([sentence])
#     # print sentence_list
#     p1 = clf1.predict(tfidf_transformer.transform(count_vect.transform(sentence_list)))
#     p2 = clf2.predict(tfidf_transformer.transform(count_vect.transform(sentence_list)))
#     if (p1 != p2):
#         if to_print:
#             print p1, p2, sentence_list
#
#         return True, p1, p2
#     else:
#         return False, p1, p2


def evaluate_api_jaccard(sentence, to_print):
    p1 = rosette_API.get_label(sentence=sentence)
    p2 = get_label_google(sentence)
    jaccard_val = jaccard(p1, p2)

    if to_print:
        print jaccard_val, jaccard_val < jaccard_threshold

    return jaccard_val < jaccard_threshold, p1, p2

def evaluate_api(sentence, to_print):
    p1 = rosette_API.get_label(sentence=sentence)[0]
    p2 = get_label_google(sentence)[0]
    val = False
    print " "
    if(p1[0] != p2[0]):
        val = True, p1, p2
        if to_print:
            print "Case 1"
    elif (p1[0] == p2[0] and abs(p1[1] - p2[1]) > 0.5):
        val = True, p1, p2
        if to_print:
            print "Case 2"
    else:
        val = False, p1, p2
        if to_print:
            print "Case 3"

    print p1, p2, val
    print " "
    return val

def produce(gr, symbol):
    words = []
    productions = gr.productions(lhs = symbol)
    production = choice(productions)
    for sym in production.rhs():
        if not type(sym) == Nonterminal:
            words.append(sym)
        else:
            words.extend(produce(gr, sym))
    return words



error_set = set()
candidate_set = set()
sentence_values = []
# latest_error_prods = prods

filename = "DataFiles/ErrorDataRandom_Rosette_Google_Grammar" + gramLetter + "_Jacc_" + str(jaccard_threshold) + "_" + str(datetime.datetime.now()) + ".csv"
f = open(filename, "w")
file_writer = csv.writer(f, delimiter=',')

for i in xrange(iters):
    wordsA = produce(grammar, grammar.start())
    candidate_sentence = ' '.join(word for word in wordsA)
    candidate_eval, candidate_p1, candidate_p2 = evaluate(candidate_sentence, True)

    candidate_set.add(candidate_sentence)
    if (candidate_eval):
        error_set.add(candidate_sentence)

    print candidate_sentence, candidate_eval

    file_writer.writerow([candidate_sentence, candidate_p1, candidate_p2, candidate_eval, len(candidate_set), len(error_set), str(datetime.datetime.now().time())])



f.close()
print len(error_set)
print len(candidate_set)
print sentence_values

