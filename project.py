from abc import abstractmethod
from re import findall
from bson.son import SON
import sys
import datetime
from pymongo import MongoClient, collection
from pymongo.collation import Collation
import json
import re
from beautifultable import BeautifulTable
from project_functions import *
import ijson
from tqdm import tqdm
import time
import string


userID = None
client = None
db = None
postCol = tagsCol = votesCol = None

ROWS_TO_DISPLAY = 8
REBUILD_DATABASE = False

tags_maxId = post_maxId = votes_maxId = None


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


def parse_terms(title: str, body: str, tags: str) -> list:
    '''
    Create terms for the given title and body.
    '''
    # res = [i.lower() for i in re.split(
    #     "\s|[-,.!?<>()/=:]", re.sub(re.compile('<.*?>'), ' ', title)+ ' ' + re.sub(re.compile('<.*?>'), ' ', body)) if len(i) > 2]

    res = [i for i in (title + ' ' + body + ' ' + tags).lower().translate(str.maketrans(string.punctuation + '\n', ' ' * (len(string.punctuation)+1))).split(' ') if len(i) > 2]

    # return {(idx, val) for idx, val in enumerate(dict.fromkeys(res))}
    # return list(dict.fromkeys(res))

    terms = []
    seen = set()
    for i in res:
        if i not in seen:
            terms.append(i)
            seen.add(i)
    return terms

    # return list(set(res))
    


def readJsonFile(fileName: str, key: str, isPost: bool, collection: collection.Collection):
    '''
    Read and parse the json file, then store the data into the  given database.
    '''
    with open(fileName) as file:
        source  = ijson.items(file, key + '.row.item')
        if isPost:
            collection.insert_many(tqdm(({**i,'Terms': parse_terms(i.get('Title', ''), i.get('Body', ''), i.get('Tags', ''))} for i in source), desc='Parsing ' + fileName), ordered=False)
            print('Creating indexes for Terms...')
            postCol.create_index([('Terms', 'text')])
        else:
            collection.insert_many(tqdm((i for i in source), desc='Parsing ' + fileName), ordered=False)
        print('Successfully stored ' + fileName + ' into the database.\n')

 
def post():
    """
    This function is responsible for giving
    user access to make a post given title and body
    text fields are filled and meet proper requirements
    """

    global userID, post_maxId, tags_maxId

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
            "Id":  str(tags_maxId + 1),
            "TagName": str(y),
            "Count": 1,
            }
            tagsCol.insert_one(tag_q)
            tags_maxId += 1
    n = len(tag)
    s = ""
    for i in range(n):
        s += "<"+str(tag[i])+">"
    body = "<p>"+body+"</p>"
    post_q = {
         "Id":  str(post_maxId + 1),
         "PostTypeId": "1",
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
    print('Successfully made a post with (id#{}).\n'.format(post_q["Id"]))


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
            for i in postCol.find({"$text": {"$search": keyword.lower()}}):
                if i:
                    result.append(i)

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
                if x:
                    # print(x.get("Id"))
                    result.append(x)
                     
    display(result)
 

def get_max_id(collection):
    """
    Get the max id of a collection
    """

    result = collection.find({}, {"Id": 1, "_id": 0})
    lst = []
    for i in result:
        lst.append(int(i["Id"]))

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
        if int(answer["Id"]) != int(check): 
            table.rows.append([answer["Body"][0:80], answer["CreationDate"], answer["Score"]])
            count += 1
    
    if check:
        table.rows.header = [str(i) for i in range(1, count+2)]
    else:
        table.rows.header = [str(i) for i in range(1, count+1)]

    print(table)


def vote(postId):
    """
    Vote on a selected question
    Anonymous users can vote with no constraint
    """
    global userID, votes_maxId

    vote = None

    if not userID:

        vote =  {
            "Id": str(votes_maxId + 1),
            "PostId": postId,
            "VoteTypeId": "2",
            "CreationDate": getCurrentDateTime()
        }

    else:
        #check if user has voted already on the post
        row = votesCol.find_one({"PostId": str(postId), "UserId": str(userID)})
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

    table.columns.header = ["Value"]

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


def find_average_score(user:None, post_type: str):
    sum_score = 0
    i = 0
    post_str = ''
    if post_type == '1':
        post_str = 'question'
    elif post_type == '2':
        post_str = 'answer'
    else:
        print('Invalid post_type: expected 1 or 2, got', post_type)
        return

    for i, item in enumerate(postCol.find({'OwnerUserId':user, 'PostTypeId': post_type}, {'_id':0, 'Score':1}), 1):
            sum_score += item['Score']

    if i > 0:
        print('User', user, 'owns', i, post_str + ', with an average score of', format(sum_score / i, '.2f'))
    else:
        print('User', user, 'has 0', post_str)


def report():
    if userID:
        print('---REPORT---')
        find_average_score(userID, '1')
        find_average_score(userID, '2')

        i = 0
        for i, item in enumerate(postCol.find({'OwnerUserId':userID, 'PostTypeId': '2'}, {'_id':0, 'Score':1}), 1):
            continue
        print('User', userID, 'owns', i, 'votes.\n')
        
        





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

        if inp in '123456789'[:len(options)]  and len(inp) == 1:
            options[int(inp) - 1](postId)
        # elif len(inp) == 1 and inp in '123456789'[:len(options)]:
        #     options[int(inp) - 1](postId)
        elif inp == '0':
            return
        else:
            invalid_command()          
def log_out():
    global userID

    userID = None
    print("Logged out.\n")
    log_in()


def log_in():
    global userID

    print("LOGIN")

    uid = input("Enter your user id (blank to skip): ")
    
    # Check if the user id exists
    res = postCol.find_one({"OwnerUserId": str(uid)})

    if res:
        userID = uid
        print("Welcome back, user {}".format(userID))
        report()
        menu()

    elif len(uid) == 0:
        print("Welcome Guest User.")
        menu()

    else:
        print("UserID does not exist. Try again.")
        log_in()

def menu():
    """
    This is the main menu or the landing page
    where user can select various options:
    This includes: posting a question,
    searching for a post, Logging out 
    and Exiting
    """

    global userID

    login_str = 'in'
    while True:
        
        if userID:
            login_str = 'out'
        else:
            login_str = "in"
        print("Choose an option: \n1. Post a Question \
        \n2. Search for questions\n3. Log " + login_str + "\n0. Exit\n")
        inp = input('Please enter a command: ')
        if inp == '1':
            post()
        elif inp == '2':
            search()
        elif inp == '3':
            if userID:
                log_out()
            else:
                log_in()
        elif inp == '0':
            exit_program()
        else:
            invalid_command()
    return 



def connect_db():
    '''
    Connect to the database with a port number from commandline argument.
    If no port number is given, the program auto connects to port 27017
    '''
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

        # MongoDB Online Instance
        # client = MongoClient("mongodb+srv://cmput291:4B5VzRRSNz81cvqz@cmput291.7yrbk.mongodb.net/291db?retryWrites=true&w=majority")



    db = client["291db"]
    postCol = db["Posts"]
    tagsCol = db["Tags"]
    votesCol = db["Votes"]


def store_data():
    '''
    Store all data into the database.
    '''
    
    print('-------Start building-------')
    start = time.time()
    readJsonFile('Posts.json', 'posts', True, postCol)
    readJsonFile('Tags.json', 'tags', False, tagsCol)
    readJsonFile('Votes.json', 'votes', False, votesCol)
    
    total = (int)(time.time() - start)

    print('\nTotal time spent: ' + (str)(total // 60) + 'min ' + (str)(total % 60) + 'sec')
    print('-------End building-------')

def get_all_max():
    global post_maxId, votes_maxId, tags_maxId
    post_maxId = get_max_id(postCol)
    votes_maxId = get_max_id(votesCol)
    tags_maxId = get_max_id(tagsCol)

def main():
    connect_db()
    if REBUILD_DATABASE:
        drop_all()
        store_data()
    get_all_max()
    log_in()

if __name__ == "__main__":
    main()
