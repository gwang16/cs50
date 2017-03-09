import nltk

class Analyzer():
    """Implements sentiment analysis."""

    def __init__(self, positives, negatives):
        """Initialize Analyzer."""

        # initialize dictionary
        pos_dict = {}
        neg_dict = {}
        
        # read into dictionary
        with open('positive-words.txt', 'r') as lines:
            for line in lines:
                if (line.startswith(';') or line.strip() == ""):
                    continue
                else:
                    pos_dict[line.strip()] = 1

        with open('negative-words.txt', 'r') as lines:
            for line in lines:
                if (line.startswith(';') or line.strip() == ""):
                    continue
                else:
                    neg_dict[line.strip()] = 1
        
        # assign class attributes
        self.positives = pos_dict
        self.negatives = neg_dict
        
    def analyze(self, text):
        """Analyze text for sentiment, returning its score."""

        # use class TweetTokenizer from module nltk.tokenize
        tokenizer = nltk.tokenize.TweetTokenizer()
        tokens = tokenizer.tokenize(text)
        
        # calculate score of text
        score = 0
        for s in tokens:
            if self.positives.get(s) != None:
                score += 1
            elif self.negatives.get(s) != None:
                score -= 1
            else:
                continue
                
        return score
