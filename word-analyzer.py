import os
import re as re
import pickle

# words data structure:
#
# words
#     word
#          total frequency                    The number of times a word is present in a set of files
#          file frequency                     The number of different files a word is present in
#          agents                             The agents associated with a word
#               agent                         The agent
#                    frequency                The number of times a word is in a file with a given agent
#               ...
#          dispositions                       The outcomes associated with a word
#               disposition                   The choice selected by an agent
#                    frequency                The number of times a word is in a file with a given disposition
#               ...
#          phrases                            The phrases the word ends
#               phrase length
#                    previous word            The previous words in the phrase
#                         total frequency     The number of times a word completes a phrase of a specific length
#                         dispositions        The outcomes associated with a phrase
#                              disposition    The choice selected by an agent
#                              frequency      The number of times a phrase is in a file with a given disposition
#                         ...
#                    ...
#          ...
#     ...

# Constants
max_phrase_length = 7


def print_dictionary(dictionary, tabs=0):
    for key in dictionary:
        if isinstance(dictionary[key], dict):
            print("\t" * tabs + str(key))
            print_dictionary(dictionary[key], tabs + 1)
        else:
            print("\t" * tabs       + str(key))
            print("\t" * (tabs + 1) + str(dictionary[key]))

def write_dictionary(dictionary, path, formatted=True):

    if not formatted:
        pickle.dump(dictionary, open(path, 'wb'), -1)
        return

    def dictToString(dictionary, spaces=0):
        writeString = ''
        for key in dictionary:
            if isinstance(dictionary[key], dict):
                writeString += " " * spaces + str(key) + "\n"
                writeString += dictToString(dictionary[key], spaces + 1)
            else:
                writeString += " " * spaces       + str(key) + "\n"
                writeString += " " * (spaces + 1) + str(dictionary[key]) + "\n"
        return writeString

    writeString = dictToString(dictionary)

    with open(path, 'w') as outputfile:
        outputfile.write(writeString)


def words_from_file(filepath):
    words = {}   # All of the unique words. Has the form {word -> [(disposition, frequency),...]}

    disposition = filepath[filepath.find('_as_') + 4 : filepath.find('.txt')]
    agent       = filepath[filepath.find('_by_') + 4 : filepath.find('_as_')]

    with open(filepath, 'r') as file:
        for line in file:

            last_words = []                                  # Words to remember for phrase building. 0 is most recent.
            line = re.sub('[^0-9a-z ]+', '', line.lower())   # Make string lowercase and strip away trailing periods
            for word in line.split():

                if word not in words:
                    words[word]                    = {}
                    words[word]['dispositions']    = {}
                    words[word]['agents']          = {}
                    words[word]['phrases']         = {}
                    words[word]['start frequency'] = 0
                    words[word]['total frequency'] = 0
                    words[word]['file frequency']  = 1
                    for i in range(max_phrase_length):
                        words[word]['phrases'][i + 1] = {}   # Separate phrases based on length

                if disposition not in words[word]['dispositions']:
                    words[word]['dispositions'][disposition] = 0
                if agent not in words[word]['agents']:
                    words[word]['agents'][agent] = 0

                phrase_roots = []
                for part in last_words:
                    for i in range(len(phrase_roots)):
                        phrase_roots[i] = "%s %s" % (phrase_roots[i], part)   # Phrases are built backwards
                    phrase_roots.append(part)

                if not phrase_roots:                      # This means that this is the first word in the file
                    words[word]['start frequency'] += 1

                for root in phrase_roots:
                    root_size = len(root.split())
                    if root not in words[word]['phrases'][root_size]:
                        words[word]['phrases'][root_size][root] = 0

                    words[word]['phrases'][root_size][root] += 1

                new_last_words = [word,]
                for part in last_words:    # Push word to start of list and delete the last entry
                    new_last_words.append(part)
                if len(new_last_words) > max_phrase_length:
                    del new_last_words[-1]
                last_words = new_last_words


                words[word]['dispositions'][disposition] += 1
                words[word]['total frequency']           += 1
                words[word]['agents'][agent]             += 1

    return words

def words_from_directory(directorypath):
    allwords = {}

    total_files = 68155   # I found this beforhand
    total_done  = 1

    for root, dirs, files in os.walk(directorypath):
        for filename in files:
            
            filepath = os.path.join(root, filename)
            #print("\r", end="")
            progress = int(100.0 * total_done / total_files)
            print("\r|%s%s|" % (progress * '#', (100 - progress) * ' '), end="")
            total_done += 1

            filewords = words_from_file(filepath)
            
            for word, meta_dict in filewords.items():

                if word not in allwords:
                    allwords[word]                    = {}
                    allwords[word]['dispositions']    = {}
                    allwords[word]['agents']          = {}
                    allwords[word]['phrases']         = {}
                    allwords[word]['start frequency'] = 0
                    allwords[word]['total frequency'] = 0
                    allwords[word]['file frequency']  = 0
                    for i in range(max_phrase_length):
                        allwords[word]['phrases'][i + 1] = {}   # Separate phrases based on length

                allwords[word]['start frequency'] += meta_dict['start frequency']   # This should always be at most 1
                allwords[word]['file frequency']  += meta_dict['file frequency']    # This should always be 1
                allwords[word]['total frequency'] += meta_dict['total frequency']   # Adding the frequency of the word in the file

                for disposition, frequency in meta_dict['dispositions'].items():

                    if disposition not in allwords[word]['dispositions']:
                        allwords[word]['dispositions'][disposition] = 0
                
                    allwords[word]['dispositions'][disposition] += frequency

                for agent, frequency in meta_dict['agents'].items():

                    if agent not in allwords[word]['agents']:
                        allwords[word]['agents'][agent] = 0

                    allwords[word]['agents'][agent] += frequency

                for phrase_length in filewords[word]['phrases']:
                    for phrase_root in filewords[word]['phrases'][phrase_length]:

                        if phrase_root not in allwords[word]['phrases'][phrase_length]:
                            allwords[word]['phrases'][phrase_length][phrase_root] = 0

                        allwords[word]['phrases'][phrase_length][phrase_root] += filewords[word]['phrases'][phrase_length][phrase_root]

    return allwords


def meta_from_directory(directorypath):
    meta = {}
    meta['file count'] = 0

    for root, dirs, files in os.walk(directorypath):
        for filename in files:
            meta['file count'] += 1

    return meta



wordFrequencies = words_from_directory('../../Desktop/YouTube/Source/120mins/uploaded/downloaded/text-analysis-corpus/')
metaData = meta_from_directory('../../Desktop/YouTube/Source/120mins/uploaded/downloaded/text-analysis-corpus/')
print('\nWriting to files')
write_dictionary(wordFrequencies, 'word-frequencies.txt', False)
write_dictionary(wordFrequencies, 'word-frequencies-human.txt', True)
write_dictionary(metaData, 'meta.txt', False)
#print_dictionary(wordFrequencies)