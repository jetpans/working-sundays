from util import load_json, store_json
subset = ["node/2162623568", "way/757296691", "node/482711193", "way/194940545", "node/2701208497",
          "node/8898067538", "node/1558018612", "way/924116254", "node/2877579783", "node/2701208483"]
main_data = load_json("data/rawdata.json")
small = {key: main_data[key] for key in subset}
print(small)
store_json(small, "data/one_cluster_subset.json")
