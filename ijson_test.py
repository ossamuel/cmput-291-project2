import ijson

with open('Posts.json', 'r') as f:
    count = 0

    # ret = {'posts': {}}
    # for prefix, event, value in parser:
    #     if prefix.endswith('.Title'):
    #         ret['posts'][value] = value
    #         count += 1

    #     if count == 20:
    #         print(ret)
    #         exit(0)

    for item in ijson.items(f, 'posts.row.item'):
        print(type(item))
        count +=1
        if count == 5:
            break

    