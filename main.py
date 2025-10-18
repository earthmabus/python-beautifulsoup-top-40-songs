from bs4 import BeautifulSoup
import requests
import re

def load_website_data_from_internet(url: str, filename_to_cache: str):
    headers = { "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:143.0) Gecko/20100101 Firefox/143.0" }
    response = requests.get(url=url, headers=headers)

    # store the html document locally
    with open(filename_to_cache, "w") as output_file:
        output_file.write(response.text)

    # return the html document
    return response.text

# the filename will be in the format of: "https://top40weekly.com/all-us-top-40-singles-for-2021"
#
# we cache this locally on the disk as "all-us-top-40-singles-for-2021.html"
def load_website_data_from_localfile(url: str):
    cached_filename = f"{url.rsplit('/', 1)[-1]}.html"
    retval = None
    try:
        with open(cached_filename, "r") as input_file:
            retval = input_file.read()
            print(f"successfully loaded '{url}' locally")
    except FileNotFoundError as e:
        # unable to load the file locally, load it from the internet
        # TODO: remove the hardcoding
        retval = load_website_data_from_internet(url, cached_filename)
        print(f"successfully loaded '{url}' from the internet and saved locally as '{cached_filename}'")
    return retval


# create a pattern to detect the following pattern
# THIS_WK_RTG LAST_WK_RTG SONG
# where THIS_WK_RTG is a number from 1 to 99
# where LAST_WK_RTG is a number from 1 to 99 or the letter "D" or the string "re"
# where SONG is the rest of the line
# ex: 1 2 this is my song
# ex: 21 D welcome to hte party
# ex: 40 39 michael was here
top_40_singles_song_line_pattern1 = r'^([1-9]|[1-9][0-9]|[1-9][0-9][0-9])\s+([1-9]|[1-9][0-9]|[1-9][0-9][0-9]|D|re)\s+(.*)$'

# create a pattern to detect the following pattern
# THIS_WK_RTG SONG_NAME
# ex: 15 mikes song
top_40_singles_song_line_pattern2 = r'^([1-9]|[1-9][0-9]|[1-9][0-9][0-9])\s+(.*)$'

# songs that dropped off the list (i.e., was on top 40 and no longer there)
# create a pattern to detect the following pattern
# - LAST_WK_RTG SONG_NAME
# ex: - 35 bobs song
top_40_singles_song_line_pattern3 = r'^—\s+([1-9]|[1-9][0-9]|[1-9][0-9][0-9])\s+(.*)$'

def match_song_format_thiswk_lastwk_song(song_line):
    # determine if the song_line matches the following pattern:
    # THIS_WK_RTG LAST_WK_RTG SONG
    match_song = re.match(top_40_singles_song_line_pattern1, song_line)
    if match_song:
        this_wk, last_wk, song = match_song.groups()
        if last_wk == "D":
            last_wk = -1
        elif last_wk == "re":
            last_wk = -2
        else:
            last_wk = int(last_wk)
        return {
                "this_week_rating": int(this_wk),
                "last_week_rating": last_wk,
                "song": song
            }

    # determine if the song_line matches the following pattern:
    # THIS_WK_RTG SONG_NAME
    match_song = re.match(top_40_singles_song_line_pattern2, song_line)
    if match_song:
        this_wk, song = match_song.groups()
        return {
                "this_week_rating": int(this_wk),
                "last_week_rating": -3,
                "song": song
            }

    # determine if the song_line matches the following pattern:
    # THIS_WK_RTG SONG_NAME
    match_song = re.match(top_40_singles_song_line_pattern3, song_line)
    if match_song:
        last_wk, song = match_song.groups()
        return {
                "this_week_rating": 100000,
                "last_week_rating": int(last_wk),
                "song": song
            }

    return None

#
# songs will look like this:
#   <p>TW LW TITLE ARTIST (LABEL) WEEKS PEAK (WEEKS AT #1)<br/>1 7 MOOD –•– 24kGoldn featuring iann dior (Columbia) 21 (1) (7 WEEKS AT #1)<br/>2 14 positions –•– Ariana Grande (Republic) 10 (1) (1 WEEK AT #1)<br/>3 re BLINDING LIGHTS –•– the Weeknd (XO/ Republic) 56 (1) (4 WEEKS AT #1)<br/>4 21 HOLY –•– Justin Bieber featuring Chance the Rapper (Def Jam) 15 (3)<br/>5 44 DYNAMITE –•– BTS (Big Hit Entertainment/ Columbia/ Sony) 19 (1) (3 WEEKS AT #1)<br/>6 24 GO CRAZY –•– Chris Brown &amp; Young Thug (CBE/ RCA/ YSL/ 300/ Atlantic) 34 (6)<br/>7 25 LAUGH NOW CRY LATER –•– Drake featuring Lil Durk (Republic/ OVO) 20 (2)<br/>8 30 I HOPE –•– Gabby Barrett featuring Charlie Puth (Warner Nashville) 53 (3)<br/>9 1 ALL I WANT FOR CHRISTMAS IS YOU –•– Mariah Carey (Columbia) 44 (1) (5 WEEKS AT #1)<br/>10 27 LEVITATING –•– Dua Lipa featuring DaBaby (Warner) 13 (10)</p>
# return value is a [ { this_week_rating, last_week_rating, song }, ... ]
def process_song_paragraph(songs):
    found_songs = []

    #print()
    #print(songs)
    for song_line in songs:
        # attempting to re.match(...) on an empty line will raise an error... continue the loop if it's empty
        if type(song_line.get_text()) is not str:
            continue
        if len(song_line) == 0:
            continue

        # print(f"next song_line: '{song_line.get_text()}'" )

        # we're at a point where there's one or more characters in the song_line, so we can attempt to match...
        ms = match_song_format_thiswk_lastwk_song(song_line.get_text())
        if ms is not None:
            found_songs.append(ms)
        # else:
        #     print(f"NO MATCH --> {song_line.get_text()}")

    return found_songs

top_40_id_week_pattern = r"^US_Top_40_Singles_Week_Ending_([A-Z]+)_(\d{1,2})_(\d{4})$"
def identify_ids_for_top_40_singles_weeks(all_tags_with_ids):
    retval = []
    for tag in all_tags_with_ids:
        extracted_id = tag['id']
        match_id_pattern = re.match(top_40_id_week_pattern, extracted_id)
        if match_id_pattern:
            retval.append(extracted_id)
    return retval

def process_top_40_singles_for_week(weekly_list_header):
    all_song_for_week = []
    if weekly_list_header:
        songs = weekly_list_header.find_next()
        while songs is not None:
            found_songs = process_song_paragraph(songs)
            # print(f"found {len(found_songs)} songs: {found_songs}")

            # add the top 40 songs into all_song_for_week
            if found_songs is not None and len(found_songs) > 0:
                all_song_for_week.extend(found_songs)
                if len(all_song_for_week) >= 40:
                    break

            # get the next set of songs still within this week
            songs = songs.find_next('p')

    return all_song_for_week


for i in range(2010, 2026):
    html_doc = load_website_data_from_localfile(f"https://top40weekly.com/all-us-top-40-singles-for-{i}")
    soup = BeautifulSoup(html_doc, 'html.parser')

    all_tags_with_ids = soup.find_all(id=True)
    all_ids = identify_ids_for_top_40_singles_weeks(all_tags_with_ids)

    count = 0
    for id in all_ids:
        if count == 0:
            count +=1
            continue
        weekly_list_header = soup.find(id=id)
        all_songs = process_top_40_singles_for_week(weekly_list_header)
        print(f"id='{id}' has {len(all_songs)} songs")
        [print(s) for s in all_songs]
        count += 1
