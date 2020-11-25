from abc import abstractmethod
from bson.son import SON
import sys
import datetime
from pymongo import MongoClient, ASCENDING, DESCENDING, collection
from pymongo.collation import Collation
import json
import re
from beautifultable import BeautifulTable
from project_functions import *
import ijson
from tqdm import tqdm
import time

anonymous = True
userID = "ANONYMOUS"
ROWS_TO_DISPLAY = 8
client = None
db = None
postCol = tagsCol = votesCol = None

post_maxId = tags_maxId = votes_maxId = None


def drop_all():
    """
    Drop all collections in the database [CAUTION]
    """
    colList = db.list_collection_names()
    # Drop these collection if exist
    if "Posts" in colList:
       db.Posts.drop()
    if "Tags" in colList:
       db.Tags.drop()
    if "Votes" in colList:
       db.Votes.drop()



def delete_all(collection):
    # Three collections (table) (Posts, Tags, Votes)
    """
    Delete all document in a collection
    Delete all rows in a table (SQL Version)
    """
    collection.delete_many({})


def getCurrentDateTime():
    """
    Follows this format : 2020-09-06T03:15:37.153
    """
    return datetime.datetime.now().isoformat()[:23]


def parse_terms(title: str, body: str) -> dict:
    """
    Parse the terms for the terms array
    """
    res = [i for i in re.split(
        "\s|[-,.!?<>()/=:]", re.sub(re.compile('<.*?>'), ' ', title)+re.sub(re.compile('<.*?>'), ' ', body)) if len(i) > 2]

    # return {(idx, val) for idx, val in enumerate(dict.fromkeys(res))}


    # return list(dict.fromkeys(res))


    # terms = []
    # seen = set()
    # for i in res:
    #     if i not in seen:
    #         terms.append(i)
    #         seen.add(i)
    # return terms

    
    return list(set(res))
    


def readJsonFile(fileName: str, key: str, isPost: bool, collection: collection.Collection):
    with open(fileName) as file:
        source  = ijson.items(file, key + '.row.item')
        if isPost:
            collection.insert_many(tqdm(({**i,'Terms': parse_terms(i.get('Title', ''), i.get('Body', ''))} for i in source), desc='Parsing ' + fileName), ordered=False)
            print('Creating indexes for Terms...')
            postCol.create_index([('Terms', ASCENDING)])
        else:
            collection.insert_many(tqdm((i for i in source), desc='Parsing ' + fileName), ordered=False)
        print('Successfully stored ' + fileName + ' into the database.\n')

            
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
                # postCol.insert_one(combined)
                # postCol.create_index([('Terms', ASCENDING)])
                print(combined)
        else:
            for entry in data[key]["row"]:
                # dict type
                # collection.insert_one(entry)
                print(entry)

    print("{} collection has been added.".format(key.upper()))



def post():
    """
    This function is responsible for giving
    user access to make a post given title and body
    text fields are filled and meet proper requirements
    """

    global userID, post_maxId

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
    for y in tag:
        tag_occur = tagsCol.find_one({"TagName": str(y)})
        #if a user provided tag exists in collection
        if tag_occur:
            tagsCol.update_one({"Id": tag_occur.get('Id')}, {"$inc": {"Count": 1}})
        #if user tag does not exit in Tags collection
        #  - add as new row with unique id and count 1
        else:
            tag_q = {
            "Id":  str(getMaxID(tagsCol) + 1),
            "TagName": str(y),
            "Count": 1,
            }
            tagsCol.insert_one(tag_q)
    n = len(tag)
    s = ""
    for i in range(n):
        s += "<"+str(tag[i])+">"
    body = "<p>"+body+"</p>"
    post_q = {
         "Id":  str(post_maxId + 1),
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

    post_maxId += 1

    postCol.insert_one(post_q)
    print('Successfully made a post.\n')


def search():
    '''
    This function is responsible for searching for a post 
    based on keywords supplied by the user.
    The system retrieves all posts that contain at
    least one keyword either in title, body, or tag fields.
    '''
    while True:
        ask = input("Enter one or more keywords (separated by space): ")
        if format_check(ask): break
    ask = ask.split()
    result = []
  
    for keyword in ask:
        if len(keyword) >= 3:
            user_doc = postCol.find({"Terms": re.compile('^' + re.escape(keyword) + '$', re.IGNORECASE)})
            for x in user_doc:
                if x is not None:
                    # print(x.get("Id"))
                    result.append(x)
                 
        #for keywords of length 2 or less 
        #we search the fields: title, body and tag
        else:
            user_doc = postCol.find({
                '$or':[
                    {"Title": re.compile('^' + re.escape(keyword) + '$', re.IGNORECASE)},
                    {"Body": re.compile('^' + re.escape(keyword) + '$', re.IGNORECASE)},
                    {"Tags": re.compile('^' + re.escape(keyword) + '$', re.IGNORECASE)}
                ]
            })
            for x in user_doc:
                if x is not None:
                    # print(x.get("Id"))
                    result.append(x)
                 
    # for y in result:
    
    #     print(y.get("Id"))
    # print("total count", count)
    
    display(result)
 

def getMaxID(collection):
    """
    Get the maximum id of a document in a collection
    """
    max = 0
    # return collection.find_one(sort=[("_id", DESCENDING)])
    #return collection.find().sort([("Id", 1)]).collation({"locale": "en_US", "numericOrdering": True})["Id"]
    # return collection.find_one(sort=[("Id", DESCENDING)])["Id"]
    # return collection.find_one().sort("Id").collation(Collation(locale="en_US", numericOrdering=True))
    # abc < abcd 

    

    # return collection.create_index({"Id": 1}, {"collation": {"locale": "en_US", "numericOrdering": False}}).collation({"locale": "en_US", "numericOrdering": False}).find().sort(["Id", DESCENDING])
    # return collection.aggregate({
    #     "$group":{
    #         "Id": '',
    #         "last":{
    #             "$max" : "$Id"
    #         }   
    #     }

    # })

    pipeline = [
        {"$sort": SON([("Id", -1)])},
        {"$limit": 1}
    ]

    print(collection.aggregate(pipeline, collation={"locale": "en_US", "numericOrdering": False}))
    
def get_max_id(collection):
    # result = max(list(map(int, list(collection.find({}, {"Id": 1})))))
    # result = list(collection.find({}, {"Id": 1}))
    result = collection.find({}, {"Id": 1, "_id": 0})
    lst = []
    for i in result:
        lst.append(int(i["Id"]))

    # max = 0
    # for i in result:
    #     if int(i["Id"]) > max:
    #         max = int(i["Id"])
    # return max
    return max(lst)

def answer(questionID):
    """
    Answer the question by providing a text
    """

    global post_maxId

    text = input("Enter an answer for {}: ".format(questionID))

    answerDict = {
        "Id": str(post_maxId + 1),
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

    post_maxId += 1

    # Add the answer to the db
    postCol.insert_one(answerDict)
    
    print(">>> Your Answer (id#{}) for Question (id#{}) has been successfully added.".format(
        answerDict.get("Id"), questionID))

    
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

    accId = postCol.find_one({"Id": questionID})
    
    # Check if there's an accepted answer for the specific post
    check = accId.get('AcceptedAnswerId', 0)

    if check:
        # Get the accepted answer post
        acceptedAnswer = postCol.find_one({"Id": str(accId.get('AcceptedAnswerId'))})

        # Append the body with a star symbol
        table.rows.append([acceptedAnswer["Body"][0:80] + " " + "\u2605", acceptedAnswer["CreationDate"], acceptedAnswer["Score"]])
    
    for answer in answers:
        if int(answer["Id"]) != int(accId.get('AcceptedAnswerId')): 
            table.rows.append([answer["Body"][0:80], answer["CreationDate"], answer["Score"]])
            count += 1
    
    table.rows.header = [str(i) for i in range(1, count+2)]

    print(answers.__dict__)
    print(table)


def vote(postId):
    """
    Vote on a selected question
    Anonymous users can vote with no constraint
    """
    global userID, votes_maxId

    vote = None

    if anonymous:

        vote =  {
            "Id": str(votes_maxId + 1),
            "PostId": postId,
            "VoteTypeId": "2",
            "CreationDate": getCurrentDateTime()
        }

    else:
        #check if user has voted already on the post
        row = votesCol.find_one({"Id": str(postId), "UserId": str(userID)})
        if row:
            print("You can not vote more than once on a post! \n")
            return
        vote =  {
            "Id": str(votes_maxId + 1),
            "PostId": postId,
            "VoteTypeId": "2",
            "UserId": userID,
            "CreationDate": getCurrentDateTime()
        }
    
    # For each vote, the score field in Posts will also increase by one
    postCol.update_one({"Id": postId}, {"$inc": {"Score": 1}})

    # Insert the vote
    votesCol.insert_one(vote)

    votes_maxId += 1

    print("Your vote for {} has been successfully casted.".format(postId))


def seeAllFields(postId):
    """
    See all fields for the selected answer
    """
    row = postCol.find_one({"Id": str(postId)})

    table = BeautifulTable()

    table.set_style(BeautifulTable.STYLE_BOX)

    print("\n{:>52}".format("ALL FIELDS FOR ANSWER " + postId))

    # table.columns.header = ["Id", "Comment Count", "Content License", "Creation Date", "Favourite Count", "Body", "Last Activity Date", "Last Edit Date", "Last Editor UserID", "Owner User ID", "Post Type ID", "Score", "Tags", "Title", "ViewCount"]
    table.columns.header = ["Value"]
    # lst = [row["Id"], row["CommentCount"], row["ContentLicense"], row["CreationDate"], row["FavouriteCount"], row["Body"], row["LastActivityDate"], row["LastEditDate"], row["LastEditorUserId"], row["PostTypeId"], row["Score"], row["Tags"], row["Title"], row["ViewCount"]]
   

    for k in row.keys():
        table.rows.append([row[k]])

    table.rows.header = [i for i in row.keys()]
    print(table)
    
    
def createTable(lst:list):
    count = 0
    table = BeautifulTable()
    table.columns.header = ["Title", "CreationDate", "Score", "AnswerCount"]
    table.set_style(BeautifulTable.STYLE_BOX)
    for item in lst:
       #if post is question
        if int(item.get("PostTypeId")):
            table.rows.append([item.get("Title"), item.get("CreationDate"), item.get("Score"), item.get("AnswerCount")])
            count+=1

    table.rows.header = [str(i) for i in range(1, count+1)]
    return table

def display(lst:list):
    '''
    This function is responsible for getting all
    the search results and organzing the results
    determine how many rows possible in one page
    '''

    table = createTable(lst)
    # print(table)
    current_row = 0
    # print('1st items: ', list(lst.get("Id"))[0])
    while True:
        print('Please choose an option:')
        next_page = False
        previous_page = False
        page = []

        #no returned result 
        if not lst:
            print('No result was found.')
        else:
            page = lst[current_row:current_row + ROWS_TO_DISPLAY]

            print(table.rows[current_row:current_row + ROWS_TO_DISPLAY])
            
            print('\"1 - ' + str(len(page)) + '\": Select a post to do more actions.')

            if not current_row - ROWS_TO_DISPLAY < 0:
                previous_page = True
                print('\"p\": Go to previous page.')
            
            if not current_row + ROWS_TO_DISPLAY >= len(lst):
                next_page = True
                print('\"n\": Go to next page.')
        print('\"0\": Return to main menu. ')
        inp = input('\nPlease enter a command: ')
        if lst and len(inp) == 1 and inp in '123456789'[:ROWS_TO_DISPLAY]:
            # Select a post
            # print('page: ', page[int(inp)-1].get("Title"))
            actions(page[int(inp)-1].get("Id"))
        elif lst and inp == 'p' and previous_page:
            # Previous
            current_row -= ROWS_TO_DISPLAY
        elif lst and inp == 'n' and next_page:
            # Next
            current_row += ROWS_TO_DISPLAY
        elif inp == '0':
            return
        else:
            invalid_command()
            
def allPostFields(postId):
    '''
    This function is responsible for giving users
    the functionality to see all fields of the 
    question they selected 
    '''
    row = postCol.find_one({"Id": str(postId)})
    
    table = BeautifulTable()

    table.set_style(BeautifulTable.STYLE_BOX)

    print("\n{:>52}".format("ALL FIELDS FOR Post " + postId))

    table.columns.header = ["Value"]
    
    for k in row.keys():
        table.rows.append([row[k]])

    table.rows.header = [i for i in row.keys()]
    print(table)

def actions(postId):
    global userID
    print("Selected Post:", postId)
    #increase view count by 1 after question is selected
    postCol.update_one({"Id": postId}, {"$inc": {"ViewCount": 1}})
    #all fields of post selected by the user
    allPostFields(postId)
    while True:
        options = []
        print('Choose an action to perform on this post: ')
        options.append(answer)
        print_option(len(options), 'Answer a question')
        options.append(list_answers)
        print_option(len(options), 'List answers of question')
        options.append(vote)
        print_option(len(options), 'Vote on post')
        

        print('0. Return to search result. ')
        inp = input('Please enter a command: ')

        if int(inp) == 1 and inp in '123456789'[:len(options)]:
            options[int(inp) - 1](postId,userID)
        elif len(inp) == 1 and inp in '123456789'[:len(options)]:
            options[int(inp) - 1](postId)
        elif inp == '0':
            return
        else:
            invalid_command()          
def log_out():
    global anonymous, userID

    userID = "ANONYMOUS"
    anonymous = True
    print("Logged out.\n")
    log_in()


def log_in():
    global anonymous, userID

    print("LOGIN")

    uid = input("Enter your user id (blank to skip): ")
    
    # Check if the user id exists
    res = postCol.find_one({"UserId": str(uid)}).get("UserId")

    if res:
        userID = uid
        anonymous = False

    print("Welcome back, {}".format(userID))
    menu()


def menu():
    """
    This is the main menu or the landing page
    where user can select various options:
    This includes: posting a question,
    searching for a post, Logging out 
    and Exiting
    """

    global userID

    while True:
        print("\n*** LOGGED IN AS [{}] ***\nChoose an option: \n1. Post a Question \n2. Search\
        for questions\n3. Answer a question \n4. List Answers \n5. Log out\n0. Exit\n".format(userID))
        inp = input('Please enter a command: ')
        if inp == '1':
            post()
        elif inp == '2':
            search()
        elif inp == '3':
            log_out()
        elif inp == '0':
            exit_program()
        else:
            invalid_command()
    return 


# def main():
#     # print(getMaxID(postCol))
#     # fromJsonFile("Posts.json", "posts", True, postCol)
#     # fromJsonFile("Votes.json", "votes", False, votesCol)
#     print(type(postCol))
# if __name__ == "__main__":
#     main()
# def main():
#     # print(getMaxID(postCol))
#     # fromJsonFile("Posts.json", "posts", True, postCol)
#     # fromJsonFile("Tags.json", "tags", False, tagsCol)
#     # fromJsonFile("Votes.json", "votes", False, votesCol)
#     print(type(postCol))


# def main():
#     log_in()


# list_answers("54")
# login()

#delete_all(votesCol)
#delete_all(tagsCol)
#delete_all(postCol)



# fromJsonFile("Tags.json", "tags", False, tagsCol)


# seeAllFields("62059")



# log_in()

# getMaxID(postCol)

def connect_db():
    global client, db, postCol, tagsCol, votesCol
    if len(sys.argv) > 1:
        if sys.argv[1].isnumeric():
            client = MongoClient('localhost', int(sys.argv[1]))
        else:
            print('Given port is not a number! ')
            exit(1)
    else:
        # For development use
        client = MongoClient('localhost', 27017)
        # client = MongoClient("mongodb+srv://cmput291:4B5VzRRSNz81cvqz@cmput291.7yrbk.mongodb.net/291db?retryWrites=true&w=majority")



    db = client["291db"]
    postCol = db["Posts"]
    tagsCol = db["Tags"]
    votesCol = db["Votes"]


def store_data():
    global post_maxId, votes_maxId, tags_maxId

    print('-------Start building-------')
    start = time.time()
    readJsonFile('Posts.json', 'posts', True, postCol)
    readJsonFile('Tags.json', 'tags', False, tagsCol)
    readJsonFile('Votes.json', 'votes', False, votesCol)
    
    total = (int)(time.time() - start)

    print('\nTotal time spent: ' + (str)(total // 60) + 'min ' + (str)(total % 60) + 'sec')
    print('-------End building-------')
    
    post_maxId = get_max_id(postCol)
    votes_maxId = get_max_id(votesCol)
    tags_maxId = get_max_id(tagsCol)

    print(post_maxId, votes_maxId, tags_maxId)
def main():
    connect_db()
    # drop_all()
    # store_data()
    # log_in()
    # getMaxID(postCol)

    # print(post_maxId)
    # print(get_max_id(votesCol))
    # print(get_max_id(tagsCol))

if __name__ == "__main__":
    main()
