import json

with open('Tags.json') as tags:
    data = json.load(tags)
    
    # print(data["tags"]["row"])

    for entry in data["tags"]["row"]:
          print(entry)
          print("\n")


with open('Votes.json') as votes:
    data = json.load(votes)
    
    # print(data["votes"]["row"])

    for entry in data["votes"]["row"]:
          print(entry)
          print("\n")

with open('Posts.json') as post:
    data = json.load(post)
    
    print(data["posts"]["row"])

    # for entry in data["posts"]["row"]:
    #       print(entry)
    #       print("\n")



# def fromJsonFile(fileName, key):
#     with open(fileName) as key:
#         data = json.load(key)
        
#         print(data[key]["row"])

#         # for entry in data["tags"]["row"]:
#         #     print(entry)
#         #     print("\n")
