from bs4 import BeautifulSoup
import requests
import re


def load_website_data_from_internet():
    headers = { "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:143.0) Gecko/20100101 Firefox/143.0" }

    response = requests.get(url=f"https://top40weekly.com/all-us-top-40-singles-for-2021", headers=headers)
    html_doc = response.text

    # store the html document locally
    with open("all-us-top-40-singles-for-2021.html", "w") as output_file:
        output_file.write(html_doc)

    # return the html document
    return html_doc

def load_website_data_from_localfile(filename: str):
    retval = None
    try:
        with open(filename, "r") as input_file:
            retval = input_file.read()
            print(f"successfully loaded '{filename}' locally")
    except FileNotFoundError as e:
        # unable to load the file locally, load it from the internet
        # TODO: remove the hardcoding
        retval = load_website_data_from_internet()
        print(f"successfully loaded '{filename}' from the internet and saved locally")
    return retval


#
# songs will look like this:
#   <p>TW LW TITLE ARTIST (LABEL) WEEKS PEAK (WEEKS AT #1)<br/>1 7 MOOD –•– 24kGoldn featuring iann dior (Columbia) 21 (1) (7 WEEKS AT #1)<br/>2 14 positions –•– Ariana Grande (Republic) 10 (1) (1 WEEK AT #1)<br/>3 re BLINDING LIGHTS –•– the Weeknd (XO/ Republic) 56 (1) (4 WEEKS AT #1)<br/>4 21 HOLY –•– Justin Bieber featuring Chance the Rapper (Def Jam) 15 (3)<br/>5 44 DYNAMITE –•– BTS (Big Hit Entertainment/ Columbia/ Sony) 19 (1) (3 WEEKS AT #1)<br/>6 24 GO CRAZY –•– Chris Brown &amp; Young Thug (CBE/ RCA/ YSL/ 300/ Atlantic) 34 (6)<br/>7 25 LAUGH NOW CRY LATER –•– Drake featuring Lil Durk (Republic/ OVO) 20 (2)<br/>8 30 I HOPE –•– Gabby Barrett featuring Charlie Puth (Warner Nashville) 53 (3)<br/>9 1 ALL I WANT FOR CHRISTMAS IS YOU –•– Mariah Carey (Columbia) 44 (1) (5 WEEKS AT #1)<br/>10 27 LEVITATING –•– Dua Lipa featuring DaBaby (Warner) 13 (10)</p>
# return value is a [ { this_week_rating, last_week_rating, song }, ... ]
def process_song_paragraph(songs):
    found_songs = []

    print()
    print(songs)
    for song_line in songs:
        print(f"next song_line: '{song_line.get_text()}'" )
        # attempting to re.match(...) on an empty line will raise an error... continue the loop if it's empty
        if len(song_line) == 0:
            continue

        # we're at a point where there's one or more characters in the song_line, so we can attempt to match...
        match_song = re.match(song_line_pattern, song_line)
        if match_song:
            num1, num2, song = match_song.groups()
            if num2 == "D":
                num2 = -1
            elif num2 == "re":
                num2 = -2
            else:
                num2 = int(num2)
            found_songs.append(
                {
                    "this_week_rating": int(num1),
                    "last_week_rating": num2,
                    "song": song
                }
            )
            print(f"matched! num={num1}, code={num2}, song='{song}'")
        else:
            print(f"NO MATCH --> {song_line}")

    return found_songs

#html_doc = load_website_data_from_internet()
html_doc = load_website_data_from_localfile("all-us-top-40-singles-for-2021.html")



# create a pattern to detect the following setup
# NUM CODE SONG_NAME
# where NUM1 is a number from 1 to 40
# where NUM2 is a number from 1 to 40 or the letter D or the re
# where SONG_NAME is the rest of the line
# ex: 1 2 this is my song
# ex: 21 D welcome to hte party
# ex: 40 39 michael was here
song_line_pattern = r'^([1-9]|[1-3][0-9]|40)\s+([1-9]|[1-3][0-9]|40|D|re)\s+(.*)$'


soup = BeautifulSoup(html_doc, 'html.parser')

weekly_list_header = soup.find(id="US_Top_40_Singles_Week_Ending_JANUARY_9_2021")
all_songs = []
if weekly_list_header:
    songs = weekly_list_header.find_next()
    while songs is not None:
        found_songs = process_song_paragraph(songs)
        print(found_songs)
        songs = songs.find_next('p')

        # if the first item in this new list is 1 more than the last item in the list we're creating then append songs to all_songs since it's a continuation of the list based on numerical ordering
        print(len(songs))
        if found_songs is not None and len(found_songs) > 0:
            if len(all_songs) == 0:
                all_songs = found_songs
            else:
                if found_songs[0]['this_week_rating'] == all_songs[len(all_songs) - 1]['this_week_rating'] + 1:
                    all_songs.extend(songs)
                else:
                    break

[print(s) for s in all_songs]
