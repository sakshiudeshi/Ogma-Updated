import csv
import re, random, pickle
import numpy as np
import copy
import datetime
import jacc_thresh

from nltk import CFG, ChartParser, Tree

from sklearn.feature_extraction.text import CountVectorizer
from sklearn.feature_extraction.text import TfidfTransformer

# import textrazor_API, aylien_API
from APIs import uclassify_API, aylien_API

import warnings
warnings.filterwarnings("ignore",category=FutureWarning)

tfidf_transformer = TfidfTransformer()
count_vect = CountVectorizer()

gramLetter = "F"
gramFileName = "../Grammars/Grammar " + gramLetter + ".txt"
folder_type = "uClassify Aylien Grammar " + gramLetter

f = open(gramFileName, 'r')

grammar = f.read()
f.close()
# print grammarA

# productions = '''[S -> NP VP, NP -> Det N PP, Det -> 'an', N -> 'man', PP -> P NP, P -> 'on', NP -> Det N, Det -> 'my', N -> 'cat', VP -> VP PP, VP -> VP PP, VP -> V NP, V -> 'shot', NP -> 'Bob', PP -> P NP, P -> 'outside', NP -> Det N PP, Det -> 'an', N -> 'pajamas', PP -> P NP, P -> 'outside', NP -> 'Bob', PP -> P NP, P -> 'with', NP -> Det N PP, Det -> 'my', N -> 'pajamas', PP -> P NP, P -> 'in', NP -> Det N PP, Det -> 'my', N -> 'dog', PP -> P NP, P -> 'with', NP -> Det N PP, Det -> 'my', N -> 'cat', PP -> P NP, P -> 'by', NP -> Det N, Det -> 'an', N -> 'telescope']
# '''

# sentence = "an man on my cat shot Bob outside an pajamas outside Bob with my pajamas in my dog with my cat by an telescope" #Sentence has error
# sentence = "an dog in the man saw Bob in an dog in Bob outside an park on the elephant in my elephant in my elephant"
# sentence = "the elephant with my cat walked I with an dog outside John with a cat outside my dog with the man with my man"
# sentence = "my angry cat chased an tall snake wounded a tree ate Joe outside my log"
# sentence = "James built Stephen by a ship in an man with James by an cat with an tree with James outside Irene"
# sentence = "Elise captured the giraffe on an lawn by the squirrel near an binoculars by an squirrel outside I"
# sentence = "the fish by Mark viewed the giraffe with my man near my binoculars by Elise"
# sentence = "a fish went my monkey outside an squirrel in my lawn with Steve"
# sentence = "the baboon grabbed an salmon on my park by an gibbon outside Gemma"
# sentence = "Holly started Marcus outside forest
# sentence = "with a cat with cat province outside the outside cat cat cat in man Dylan Marcus province"
# sentence = "my school in I Olivia the school my business the home on Thomas"
# sentence = "an business knew my week the woman woman outside I in home with week in Thomas school in Alexander school outside room I Olivia by Thomas I I on Alexander by Olivia"
# sentence = "woman by I school in Thomas needed outside Alexander in an woman a school an school on a room a home Alexander company outside school room"
# sentence = "Dylan made a snake in pajamas on a cat with Marcus man on Marcus in Holly by Holly" # Grammar E error inducing sentence
# sentence = "an man on a cat ate John outside a pajamas on John on the man by my man with a elephant on the park"
# sentence = "an fish injured my monkey near a man near the monkey with I"
# sentence = "my woman apprehended an lemur outside my elephant on an gibbon with Gemma"
# sentence = "Marcus conflicted Holly outside the in Dylan on Holly"
# sentence = "Marcus started the camera on Marcus by Holly by camera by Holly camera an on Marcus Marcus"
# sentence = "Irene began monkey with my in a man in I with a telescope cat in I by Irene"
# sentence = "my lemur grabbed the baboon on I with an woman in I"
# sentence = "Mark viewed an lawn with Elise with Steve"
# sentence = "John wounded my elephant outside Bob by a monkey outside Mary"

# sentence = "an fish captured my lawn near a hedgehog near an monkey with I"
# sentence = "Irene caught James with an monkey in an country with Irene by the monkey on the man with I by James"
# sentence = "Marcus started a snake by hill on a man in Holly forest outside Marcus in Holly on Holly"
sentence = "school in I business by Thomas knew by Alexander with an school a home the week outside the woman a business Alexander business with school home"

jaccard_threshold = jacc_thresh.dict_jacc[folder_type]


iters = 200
prob_delta = 0.2




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
    # f = open("Split_Lines.txt", "w")
    # for line in split_lines:
    #     f.write(str(line) + " " + str(len(line)) + "\n")
    # f.close()
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
    return evaluate_api_jaccard(sentence, to_print)

def evaluate_local(sentence, to_print):
    sentence_list = np.array([sentence])
    # print sentence_list
    p1 = clf1.predict(tfidf_transformer.transform(count_vect.transform(sentence_list)))
    p2 = clf2.predict(tfidf_transformer.transform(count_vect.transform(sentence_list)))
    if (p1 != p2):
        if to_print:
            print p1, p2, sentence_list

        return True, p1, p2
    else:
        return False, p1, p2


def evaluate_api_jaccard(sentence, to_print):
    p1 = uclassify_API.get_label(sentence=sentence)
    p2 = aylien_API.get_label(sentence)
    jaccard_val = jaccard(p1, p2)

    if to_print:
        print jaccard_val, jaccard_val < jaccard_threshold

    return jaccard_val < jaccard_threshold, p1, p2

def evaluate_api(sentence, to_print):
    p1 = uclassify_API.get_label(sentence)[0]
    p2 = aylien_API.get_label(sentence)[0]
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

f = open('../Local Classifiers/multinomial_NB.pickle', 'rb')
clf1 = pickle.load(f)
f.close()


f = open('../Local Classifiers/SVM_Text_clf.pickle', 'rb')
clf2 = pickle.load(f)
f.close()

with open('../Local Classifiers/train.txt') as f:
    train = f.read().splitlines()

train_X = []
train_Y = []
for line in train:
    split = line.rsplit(' ', 1)
    train_X.append(split[0])

train_X_counts = count_vect.fit_transform(train_X)
# print train_X_counts.shape

X_train_tfidf = tfidf_transformer.fit_transform(train_X_counts)

productions = get_productions(sentence, grammar)
print productions
print ' '
prods = get_base_prods(str(productions))
dict = get_grammar_dict(grammar)
dict_keys = dict.keys()

prob_keys = [1.0/len(dict_keys)] * len(dict_keys)
print prob_keys
print ' '
print prods



error_set = set()
candidate_set = set()
sentence_values = []
latest_error_prods = prods

filename = "../DataFiles/ErrorDataNoBacktrackDirected_uClassify_Aylien_Grammar" + gramLetter + "_Jacc" + str(jaccard_threshold) + "_" + str(datetime.datetime.now()) + ".csv"
f = open(filename, "w")
file_writer = csv.writer(f, delimiter=',')
for i in xrange(iters):
    print i
    prod_choice = np.random.choice(dict_keys, p=prob_keys)
    prod_choice_loc = [i for i, x in enumerate(dict_keys) if x == prod_choice]
    # print prod_choice_loc

    mod = random.randint(0, len(prods) - 1)
    while prod_choice != prods[mod][0]:
        # print prod_choice, prods[mod][0]
        mod = random.randint(0, len(prods) - 1)

    rand = random.choice(dict[prods[mod][0]])

    current_prods = copy.deepcopy(prods)
    # Checks if generating the same sentence
    while (rand == current_prods[mod][1]):
        rand = random.choice(dict[prods[mod][0]])
        print rand


    current_sentence = sentence_from_prods(current_prods)
    current_eval, current_p1, current_p2 = evaluate(current_sentence, True)

    candidate_prods = copy.deepcopy(prods)
    candidate_prods[mod][1] = rand
    candidate_sentence = sentence_from_prods(candidate_prods)
    candidate_eval, candidate_p1, candidate_p2 = evaluate(candidate_sentence, True)

    # if candidate_sentence not in candidate_set:


    candidate_set.add(candidate_sentence)

    prods = copy.deepcopy(candidate_prods)

    if (False):
        prods = copy.deepcopy(current_prods)
        # print prods
        print " "
        print current_prods, sentence_from_prods(prods)
        print "Candidate -> " + candidate_sentence, candidate_eval
        print "Current -> " + current_sentence, current_eval
        print " "
        # print ''

    sentence_values.append(candidate_eval)

    if (candidate_eval):
        error_set.add(candidate_sentence)
        latest_error_prods = candidate_prods
        # prob_keys[prod_choice_loc[0]] = max(prob_keys[prod_choice_loc[0]] - prob_delta, 0)
        # norm = [float(i) / sum(prob_keys) for i in prob_keys]
        # prob_keys = norm
    # f.write(str(len(candidate_set)) + " " + str(len(error_set)) + "\n")
    file_writer.writerow([candidate_sentence, candidate_p1, candidate_p2, candidate_eval, len(candidate_set), len(error_set), str(datetime.datetime.now().time())])
    print ""

f.close()
print len(error_set)
print len(candidate_set)
print sentence_values

