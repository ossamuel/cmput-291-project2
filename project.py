import pymongo
from pymongo import MongoClient
import json

# Mongoclient object (Online)
client = MongoClient("mongodb+srv://cmput291:4B5VzRRSNz81cvqz@cmput291.7yrbk.mongodb.net/<dbname>?retryWrites=true&w=majority")

# Name of the database
db = client["291db"]

# Three collections (Posts, Tags, Votes)
postCol = db["Posts"]
tagsCol = db["Tags"]
votesCol = db["Votes"]

# Insert into collection
# post1 =  {
#         "Id": "1",
#         "PostTypeId": "1",
#         "AcceptedAnswerId": "9",
#         "CreationDate": "2010-08-17T19:22:37.890",
#         "Score": 16,
#         "ViewCount": 28440,
#         "Body": "<p>What is the hardware and software differences between Intel and PPC Macs?</p>\n",
#         "OwnerUserId": "10",
#         "LastEditorUserId": "15",
#         "LastEditDate": "2010-09-08T15:12:04.097",
#         "LastActivityDate": "2017-09-21T12:16:56.790",
#         "Title": "What is the difference between Intel and PPC?",
#         "Tags": "<hardware><mac><powerpc><macos>",
#         "AnswerCount": 9,
#         "CommentCount": 0,
#         "FavoriteCount": 6,
#         "ContentLicense": "CC BY-SA 2.5"
#       }
# postCol.insert_one(post1)

# tag1 =   {
#         "Id": "4",
#         "TagName": "hardware",
#         "Count": 1435,
#         "ExcerptPostId": "20888",
#         "WikiPostId": "20887"
#       }

# tagsCol.insert_one(tag1)

# vote1 = {
    #     "Id": "1",
    #     "PostId": "1",
    #     "VoteTypeId": "2",
    #     "CreationDate": "2010-08-17T00:00:00.000"
    #   }

# votesCol.insert_one(vote1)

tags2 = {
        "Id": "6",
        "TagName": "snow-leopard",
        "Count": 1197,
        "ExcerptPostId": "8990",
        "WikiPostId": "8989"
      }

# tagsCol.insert_one(tags2)

def insert_one(collection, document):
    collection.insert_one(document)


# key in ["posts", "tags", "votes"]
def fromJsonFile(fileName, key):
    """
    Reads json file and constructs a collection for each (except for Posts collection)
    """
    
    # open the file
    with open(fileName) as file:
        # load the json
        data = json.load(file)
        # go through every single dict
        for entry in data[key]["row"]:
            # dict type
            print(entry)
            print("\n")
            # insert_one()

fromJsonFile("Posts.json", "posts")


