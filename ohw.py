import requests
import json
import sys
import argparse

parser = argparse.ArgumentParser(description="Find your favorite last.fm one hit wonders.")
parser.add_argument("api_key", type=str, help="Last.fm API key to use")
parser.add_argument("username", type=str, help="Last.fm username")
parser.add_argument("--stop-on-error", action=argparse.BooleanOptionalAction, default=False, help="Stop on a non 200 OK response from last.fm")
parser.add_argument("--batch-size", type=int, default=1000, metavar="size", help="How many scrobbles to grab from last.fm at a time.")
parser.add_argument("--timeframe", choices=['overall', '7day', '1month', '3month', '6month', '12month'], default='overall', help="The time period over which to retrieve top tracks for.")
parser.add_argument("--retry", type=int, default=None, metavar="total_retries", help="How many times to retry if last.fm returns a non 200 OK response.")
parser.add_argument("--limit", type=int, default=None, help="How many tracks to display.")
parser.add_argument("--max-unique", type=int, default=1, help="Change this to allow 2 hit wonders, etc.")

args = parser.parse_args()

headers = {
	'user-agent': 'one-hit-wonder-finder'
}
payload = {
    'api_key': args.api_key,
    'user': args.username,
    'period': args.timeframe,
    'limit': args.batch_size,
    'method': 'user.gettoptracks',
    'format': 'json'
}

parsed = {} # key: artist name, val: list of tuple of song/playcounts

cur_page = 1
pages = sys.maxsize # dummy till we know how many pages we need.
pages_set = False
retry = 0
while cur_page < pages:
    payload["page"] = cur_page
    r = requests.get('http://ws.audioscrobbler.com/2.0/', headers=headers, params=payload)
    to_json = r.json()
    if(r.status_code != 200):
        print("ERROR:", "code = " + str(r.json()["error"]), r.json()["message"])
        if args.retry is not None and args.retry > 0:
            if retry < args.retry:
                print("Retry #", str(retry+1) + "/" + str(args.retry))
                retry = retry + 1
                continue
        if args.stop_on_error or cur_page == 1:
            if(cur_page == 1):
                print("No results to parse.")
            sys.exit()
        else:
            break
    if not pages_set:
        pages = int(to_json["toptracks"]["@attr"]["totalPages"]) # our true # of pages that we need to paginate.
        pages_set = True
    for top_trk in to_json["toptracks"]["track"]:
        artist = top_trk["artist"]["name"]
        trk = top_trk["name"]
        cnt = top_trk["playcount"]
        #print(artist, trk, cnt)
        
        trk_cnt_tuple = (trk, cnt)
        
        if artist in parsed.keys():
            parsed[artist].append(trk_cnt_tuple)
        else:
            parsed[artist] = [trk_cnt_tuple]
    cur_page = cur_page + 1
    retry = 0
    print("Last.fm returned HTTP Status Code", r.status_code, "on request #" + str(cur_page-1) + " / " + str(pages) + " total")
    
#print(parsed)

tracks_shown = 0
for artist in parsed:
    list_of_tracks = parsed[artist]
    #print(top_trk, parsed[top_trk])
    if(len(list_of_tracks) <= args.max_unique):
        for track in list_of_tracks:
            print("#" + str(tracks_shown+1) + ": " + track[1] + " play(s) - " + artist + " - " + track[0])
            tracks_shown = tracks_shown + 1
            if args.limit is not None and tracks_shown == args.limit:
                break
