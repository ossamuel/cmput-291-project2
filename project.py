import datetime
from pymongo import MongoClient, ASCENDING, DESCENDING, collection
from pymongo.collation import Collation
import json
import re
from beautifultable import BeautifulTable
from project_functions import *
import ijson

anonymous = True
userID = "ANONYMOUS"
ROWS_TO_DISPLAY = 8
# Mongoclient object (Online)
client = MongoClient("mongodb+srv://cmput291:4B5VzRRSNz81cvqz@cmput291.7yrbk.mongodb.net/<dbname>?retryWrites=true&w=majority")

# Local Mongoclient
# client = MongoClient("mongodb://localhost:27017/")

# Name of the database
db = client["291db"]

# List of collections


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

# Three collections (table) (Posts, Tags, Votes)
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
    """
    Follows this format : 2020-09-06T03:15:37.153
    """
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

def readJsonFile(fileName: str, key: str, isPost: bool, collection: collection.Collection):
    with open(fileName) as file:
        for item in ijson.items(file, key + '.row.item'):
            # if isPost:
            #     getTags(item.get('Title', ''))
            print(item)

            

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



# delete_all(votesCol)
# delete_all(tagsCol)
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
    count = 0
    for keyword in ask:
        if len(keyword) >= 3:
            user_doc = postCol.find({"Terms": re.compile('^' + re.escape(keyword) + '$', re.IGNORECASE)})
            for x in user_doc:
                if x is not None:
                    # print(x.get("Id"))
                    result.append(x)
                    count+=1
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
                    count+=1
    # for y in result:
    
    #     print(y.get("Id"))
    # print("total count", count)
    
    display(result)
 

def getMaxID(collection):
    """
    Get the maximum id of a document in a collection
    """
    # return collection.find_one(sort=[("Id": {"$toInt": "Id"}, DESCENDING)])["Id"]
    return collection.find().sort("Id").collation(Collation(locale="en_US", numericOrdering=True))

    # return collection.aggregate({
    #     "$group":{
    #         "Id": '',
    #         "last":{
    #             "$max" : "$Id"
    #         }   
    #     }

    # })

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

    accId = postCol.find_one({"Id": questionID}, {"AcceptedAnswerId"})
    
    # Check if there's an accepted answer for the specific post
    if accId.get('AcceptedAnswerId'):
        # Get the accepted answer post
        acceptedAnswer = postCol.find_one({"Id": str(accId.get('AcceptedAnswerId'))})

        # Append the body with a star symbol
        table.rows.append([acceptedAnswer["Body"][0:80] + " " + "\u2605", acceptedAnswer["CreationDate"], acceptedAnswer["Score"]])
    
    for answer in answers:
        if int(answer["Id"]) != int(accId.get('AcceptedAnswerId')): 
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
            "Id": getMaxID(votesCol),
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
            "Id": getMaxID(votesCol),
            "PostId": postId,
            "VoteTypeId": "2",
            "UserId": userID,
            "CreationDate": getCurrentDateTime()
        }
    
    # For each vote, the score field in Posts will also increase by one
    postCol.update_one({"Id": postId}, {"$inc": {"Score": 1}})

    # Insert the vote
    votesCol.insert_one(vote)

    print("Your vote for {} has been successfully casted.".format(postId))


# answer(12345, 14141)
# print(getMaxID(tagsCol))

def seeAllFields(postId):
    """
    See all fields for the selected answer
    """
    row = postCol.find_one({"Id": str(postId)})

    #print(row.keys())

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

    if uid:
        userID = uid
        anonymous = False

    print(f"Welcome back, {userID}")
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
        print(f'\n*** LOGGED IN AS [{userID}] ***\nChoose an option: \n1. Post a Question \n2. Search\
        for questions\n3. Answer a question \n4. List Answers \n5. Log out\n0. Exit\n')
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

    return 


def main():
    # print(getMaxID(postCol))
    # fromJsonFile("Posts.json", "posts", True, postCol)
    # fromJsonFile("Votes.json", "votes", False, votesCol)
    print(type(postCol))
if __name__ == "__main__":
    main()

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

def main():
    # readJsonFile('Posts.json', 'posts', True, postCol)
    # readJsonFile('Tags.json', 'tags', False, tagsCol)
    # readJsonFile('Votes.json', 'votes', False, votesCol)
    getTags("Write a program that supports the following operations on the MongoDB database created in Phase 1.")

if __name__ == "__main__":
    main()

