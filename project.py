import pymongo
import datetime
from pymongo import MongoClient, ASCENDING, DESCENDING
import json
import re
from beautifultable import BeautifulTable

anonymous = True
userID = None

# Mongoclient object (Online)
client = MongoClient(
    "mongodb+srv://cmput291:4B5VzRRSNz81cvqz@cmput291.7yrbk.mongodb.net/<dbname>?retryWrites=true&w=majority")

# Name of the database
db = client["291db"]

# Three collections (Posts, Tags, Votes)
postCol = db["Posts"]
tagsCol = db["Tags"]
votesCol = db["Votes"]


def delete_all(collection):
    """
    Delete all document in a collection
    Delete all rows in a table (SQL Version)
    """
    collection.delete_many({})


def insert_one(collection, document):
    collection.insert_one(document)

def getCurrentDateTime():
    return datetime.datetime.now().isoformat()[:23]

def parse_terms(title="", body=""):
    new_string = [i for i in re.split(
        "\s|[,.!?<>()/=:]", title+body) if len(i) > 2 and i != '"']
    no_duplicate = []

    for i in new_string:
        if i not in no_duplicate:
            no_duplicate.append(i)

    return no_duplicate

# key in ["posts", "tags", "votes"]


def fromJsonFile(fileName, key, isPost, collection):
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

        else:
            for entry in data[key]["row"]:
                # dict type
                collection.insert_one(entry)

    print("{} collection has been added.".format(key.upper()))



def post():
    """
    This function is responsible for giving
    user access to make a post given title and body
    text fields are filled and meet proper requirements
    """

    global userID

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
            # no tag entered by user
            break
    tag = tag.split()
    n = len(tag)
    s = ""
    for i in range(n):
        s += "<"+str(tag[i])+">"
    body = "<p>"+body+"</p>"
    post_q = {
         "Id":  getMaxID(postCol) + 1,
         "OwnerUserId": userID,
         "Title": title,
         "Body": body,
         "Tags": tag,
         "CreationDate": getCurrentDateTime(),
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


# fromJsonFile("Posts.json", "posts", True, postCol)
# fromJsonFile("Votes.json", "votes", False, votesCol)
# fromJsonFile("Tags.json", "tags", False, tagsCol)
# delete_all(votesCol)
# delete_all(tagsCol)

def getMaxID(collection):
    """
    Get the maximum id of a document in a collection
    """
    return collection.find_one(sort=[("Id", DESCENDING)])["Id"]


def answer(questionID, userID):
    """
    Answer the question by providing a text
    """

    text = input(f"Enter an answer for {questionID}: ")

    answerDict = {
        "Id": str(int(getMaxID(postCol)) + 1),
        "PostTypeId": "2",
        "ParentId": questionID,
        "CreationDate": getCurrentDateTime(),
        "Score": 0,
        "Body": text,
        "OwnerUserId": userID,
        "LastActivityDate": getCurrentDateTime(),
        "CommentCount": 0,
        "ContentLicense": "CC BY-SA 2.5"
      }

   # postCol.insert_one(answer)
    print(">>> Your Answer (id#{}) was added to Question (id#{}).".format(
        answerDict["Id"], questionID))

    
# print(datetime.datetime.now().isoformat())
# print(postCol)


# def generate_table(*args):
#     table = BeautifulTable()
#     table.columns.header = [i for i in args] 
#     table.set_style(BeautifulTable.STYLE_BOX)

def list_answers(questionID):
    """
    List answers of a selected question
    """
    answers = postCol.find({"PostTypeId": "2", "ParentId": questionID})

    count = 0

    print("\n{:>52}".format("ANSWERS FOR QUESTION " + questionID))

    print("\n{:>50}".format("\u2605 (accepted answer)"))

    table = BeautifulTable()

    table.columns.header = ["Body", "Creation Date", "Score"]

    table.set_style(BeautifulTable.STYLE_BOX)

    accId = int(postCol.find_one({"Id": questionID})["AcceptedAnswerId"])

    acceptedAnswer = postCol.find_one({"Id": str(accId)})

    table.rows.append([acceptedAnswer["Body"][0:80] + " " + "\u2605", acceptedAnswer["CreationDate"], acceptedAnswer["Score"]])

    for answer in answers:
        if int(answer["Id"]) != accId: 
            table.rows.append([answer["Body"][0:80], answer["CreationDate"], answer["Score"]])
            count += 1
    
    table.rows.header = [str(i) for i in range(1, count+2)]
    print(table)

def vote(postId):
    """
    Vote on a selected question
    Anonymous users can vote with no constraint
    """
    global userID

    vote = None

    if anonymous:

        vote =  {
            "Id": getMaxID(),
            "PostId": postId,
            "VoteTypeId": "2",
            "CreationDate": getCurrentDateTime()
        }

    else:
        
        vote =  {
            "Id": getMaxID(),
            "PostId": postId,
            "VoteTypeId": "2",
            "UserId": userID,
            "CreationDate": getCurrentDateTime()
        }
    
    # For each vote, the score field in Posts will also increase by one
    
    votesCol.insert_one(vote)
    print("Your vote for {} has been successfully casted.".format(postId))

# answer(12345, 14141)
# print(getMaxID(tagsCol))

def login():

    uid = input("Enter your user id (blank to skip): ")


    
    
 def menu():
    '''
    This is the main menu or the landing page
    where user can select various options:
    This includes: posting a question,
    searching for a post, Logging out 
    and Exiting
    '''
    
    while True:
        print('\nChoose an option: \n1. Post a Question \n2. Search\
         for posts\n3. Answer a question \n4. List Answers \n5. Log out\n0. Exit\n')
        inp = input('Please enter a command: ')
        if inp == '1':
            post()
        elif inp == '2':
            search()
        elif inp == '3':
            answer()
        elif inp == '4':
            list_answer()
        elif inp == '5':
            log_out()
        elif inp == '0':
            exit_program()
        else:
            invalid_command()


# list_answers("54")
# login()

