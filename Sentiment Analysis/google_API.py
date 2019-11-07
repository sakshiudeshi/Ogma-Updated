# Imports the Google Cloud client libr
from google.cloud import language
from google.cloud.language import enums
from google.cloud.language import types

# Instantiates a client
client = language.LanguageServiceClient()

# The text to analyze
text = u'Hello, world!'
document = types.Document(
    content=text,
    type=enums.Document.Type.PLAIN_TEXT)

# Detects the sentiment of the text
sentiment = client.analyze_sentiment(document=document).document_sentiment

# print('Text: {}'.format(text))
# print('Sentiment: {}, {}'.format(sentiment.score, sentiment.magnitude))

sentence = "John wounded my elephant outside Bob by a monkey outside Mary"

def get_label(inp_text):
    print inp_text
    text = inp_text
    document = types.Document(
        content=text,
        type=enums.Document.Type.PLAIN_TEXT)

    # Detects the sentiment of the text
    sentiment = client.analyze_sentiment(document=document).document_sentiment

    score = sentiment.score
    print score
    response_list = []
    if score > 0.25:
        response_list.append(["POSITIVE", score])
    elif score < -0.25:
        response_list.append(["NEGATIVE", score])
    else:
        response_list.append(["NEUTRAL", score])
    return response_list

print get_label("I hate you!! I hope I never see you again")