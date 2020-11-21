import pymongo
from pymongo import MongoClient, ASCENDING, DESCENDING
import json
import re

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

def delete_all(collection):
    """
    Delete all document in a collection
    Delete all rows in a table (SQL Version)
    """
    collection.delete_many({})

def insert_one(collection, document):
    collection.insert_one(document)

def parse_terms(title="", body=""):    
    new_string = [i for i in re.split("\s|[,.!?<>()/=:]", title+body) if len(i) > 2 and i != '"']
    no_duplicate = []
    
    for i in new_string:
        if i not in no_duplicate:
            no_duplicate.append(i)

    return no_duplicate

# key in ["posts", "tags", "votes"]
def fromJsonFile(fileName, key, isPost):
    """
    Reads json file and constructs a collection for each (except for Posts collection)
    """
    
    # open the file
    with open(fileName) as file:
        # load the json
        data = json.load(file)
        # go through every single dict
        if isPost:
            count = 0
            for entry in data[key]["row"]:
                
                title = entry.get("Title", 0)
                body = entry.get("Body", 0)
                terms = None

                # Title and body exists
                if title and body:
                    terms = parse_terms(entry["Title"], entry["Body"])

                # Only title exists
                elif title:
                    terms = parse_terms(entry["Title"])

                # Only body exists
                elif body:
                    terms = (parse_terms(entry["Body"]))
                
                termsDict = {"Terms": terms}
                
                combined = {**entry, **termsDict}
                postCol.insert_one(combined)
                postCol.create_index([('Terms', ASCENDING)])
            
              #  print(combied)
              #  print("\n")
        else:
            for entry in data[key]["row"]:
                # dict type
                print(entry)
                print("\n")
                # insert_one()
    
    print("Done!")

fromJsonFile("Posts.json", "posts", True)
# delete_all(postCol)

def post():
    '''
    This function is responsible for giving 
    user access to make a post given title and body
    text fields are filled and meet proper requirements
    '''
    global user_id
    print("\nMAKE A POST")
    title = body = ''
    while True:
        title = input('Please enter a title for the post: \n')
        if format_check(title, 1): break
    
    while True:
        body = input('Please enter a body for the post: \n')
        if format_check(body, 1): break
    while True:
        tag = input('Please enter a tags for the post: \n')
        if tag:
            if format_check(tag, 1): break
            
        else:
            #no tag entered by user
            break
    tag = tag.split()
    n = len(tag)
    s = ""
    for i in range(n):
        s+="<"+str(tag[i])+">"
    body = "<p>"+body+"</p>"
    post_q = {
         "Id":  getMAXID(postCol) + 1,
         "OwnerUserId": user_id,
         "Title": title,
         "Body": body,
         "Tags": tag,
         "CreationDate": datetime.datetime.now().isoformat(),
         "OwnerUserId": userID,
         "Score": 0,
         "ViewCount": 0,
         "AnswerCount": 0,
         "CommentCount": 0,
         "FavoriteCount": 0,
         "ContentLicense": "CC BY-SA 2.5"
    }
    postCol.insert_one(post_q) 
    print('Successfully made a post.\n')

