import re

post1 =  {
        "Id": "1",
        "PostTypeId": "1",
        "AcceptedAnswerId": "9",
        "CreationDate": "2010-08-17T19:22:37.890",
        "Score": 16,
        "ViewCount": 28440,
        "Body": "<p>What is the hardware and software differences between Intel and PPC Macs?</p>\n",
        "OwnerUserId": "10",
        "LastEditorUserId": "15",
        "LastEditDate": "2010-09-08T15:12:04.097",
        "LastActivityDate": "2017-09-21T12:16:56.790",
        "Title": "What is the difference between Intel and PPC?",
        "Tags": "<hardware><mac><powerpc><macos>",
        "AnswerCount": 9,
        "CommentCount": 0,
        "FavoriteCount": 6,
        "ContentLicense": "CC BY-SA 2.5"
        # "Terms": [
        #     "index0":"term",
        #     "index1":"term1"

        # ]
}


string = "<p>The VPN software I use for work (<a href=\"http://www.lobotomo.com/products/IPSecuritas/\">IPSecuritas</a>) requires me to turn off Back To My Mac to start it's connection, so I frequently turn off Back To My Mac in order to use my VPN connection (the program does this for me). I forget to turn it back on however and I'd love to know if there was something I could run (script, command) to turn it back on.</p>\n"
string1 = "<p>I have Microsoft Office/2008 on my MacBook Pro. Office doesn't support RTL languages like Farsi and Arabic, and I know that Office/2010 (for Windows) also has the same problem.</p>\n\n<p>Do you think the lack of support is because of business competition, or some other reason?</p>\n"

split_string = re.split("\s|[,.!?<>()/=:]", string1)
clean_string = []

for i in split_string:
    if len(i) > 2 and i != '"':
        clean_string.append(i)



# print(split_string)
# print(clean_string)

def parse_string(title, body):    
    new_string = [i for i in re.split("\s|[,.!?<>()/=:]", title+body) if len(i) > 2 and i != '"']
    return new_string

parse_string("Why doesn't Microsoft Office/2008(& later) support RTL languages?", "<p>I have Microsoft Office/2008 on my MacBook Pro. Office doesn't support RTL languages like Farsi and Arabic, and I know that Office/2010 (for Windows) also has the same problem.</p>\n\n<p>Do you think the lack of support is because of business competition, or some other reason?</p>\n")