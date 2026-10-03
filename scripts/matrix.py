import json
print("matrix=" + json.dumps({"repo": json.load(open("repos.json"))}))
