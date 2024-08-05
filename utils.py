import types
import hashlib
import os

from pytube import extract
from typing import get_args, get_origin

def parse_data(data):
    newdata = {}
    for i in data:
        yt = ""
        if len(i) == 5:
            try:
                yt = extract.video_id(i[4])
            except:
                yt = None
        if "or" in i[1].lower():
            ways = i[1].lower().replace(' ', '').split("or")
        else:
            ways = i[1].lower().replace(' ', '').split(",")
        routes = []
        if len(ways) > 1:
            descs = list(filter(None, i[2].split("\n")))
            if len(ways) != len(descs):
                print("a")
                raise ValueError("Length of ways and descriptions do not match")
            for j in range(len(ways)):
                start, end = ways[j].split("-")
                routes.append({
                    "start": int(start),
                    "end": int(end),
                    "desc": descs[j],
                    "type": "normal"
                })
        else:
            if ways[0] == "minigame":
                start, end, type_ = None, None, "minigame"
            else:
                try:
                    start, end = ways[0].split("-")
                    start, end = int(start), int(end)
                    type_ = "normal"
                except:
                    start, end, type_ = None, None, "other"
            routes.append({
                "start": start,
                "end": end,
                "desc": i[2],
                "type": type_
            })

        newdata.update({i[0]: {
            "routes": routes,
            "src": i[3],
            "yt": yt
        }})
    return newdata


def generate_cell_link(spreadsheet_id, sheet_id, row):
    return f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/edit#gid={sheet_id}&range=A{row}:F{row}"


def convert_string(value: str, target_type: callable):
    if value == "":
        return None
    return target_type(value)


def encode_sha1_with_salt(data: str) -> str:
    salt = b'xI25fpAapCQg'

    sha1 = hashlib.sha1()

    sha1.update(data.encode('utf-8'))
    sha1.update(salt)

    hash_digest = sha1.hexdigest()

    return hash_digest


def get_first_type(type):
    if get_origin(type) is types.UnionType:
        return get_args(type)[0]
    return type


def robtop_to_level_info(levelString: str):
    body = levelString.split("#")
    levels = parse_levels(body[0].split("|"))
    creators = parse_creators(body[1].split("|"))
    songs = parse_songs(body[2].split("~:~"))

    hashString = ""
    for level in levels:
        hashString += f"{level["1"][0]}{level["1"][-1]}{level["18"]}{level["37"]}"

    print(hashString)
    assert encode_sha1_with_salt(hashString) == body[4]


def parse_levels(levels: list[str]) -> list[dict[str, str]]:
    returnLevels = []

    for level in levels:
        data = level.split(":")
        keys = data[0::2]
        values = data[1::2]

        returnLevels.append(dict(zip(keys, values)))

    return returnLevels


def parse_creators(creators: list[str]) -> list[dict[str, [str, int]]]:
    returnCreators = []

    for creator in creators:
        info = creator.split(":")
        returnCreators.append({
            "userID": int(info[0]),
            "username": info[1],
            "accountID": int(info[2])
        })

    return returnCreators


def parse_songs(songs: list[str]) -> list[dict[str, str]]:
    returnSongs = []

    for song in songs:
        data = song.split("~|~")
        keys = data[0::2]
        values = data[1::2]

        returnSongs.append(dict(zip(keys, values)))

    return returnSongs


if __name__ == "__main__":
    robtop_to_level_info(
        "1:29165461:2:Blacklights:5:1:6:20:8:10:9:50:10:1013129:12:0:13:21:14:76421:17::43:6:25::18:9:19:21180:42:1:45:16836:3:SSBoYXZlIHJldHVybmVkLiBSZW1lbWJlciwgeW91IGNhbiB0dXJuIG9mZiBzaGFrZSBpbiB0aGUgc2V0dGluZ3MgaWYgaXQgYm90aGVycyB5b3UgdG9vIG11Y2guIEVuam95IQ==:15:3:30:0:31:0:37:3:38:1:39:8:46:1:47:2:35:477744#20:TheRealDarnoc:3223#1~|~477744~|~2~|~{dj-N} Blacklights [FULL]~|~3~|~35~|~4~|~dj-Nate~|~5~|~7.26~|~6~|~~|~10~|~http%3A%2F%2Faudio.ngfiles.com%2F477000%2F477744_dj-N-Blacklights-FULL.mp3~|~7~|~~|~8~|~1#1:0:10#0fa08672d9b941aba42e91a1a1d9d7b55d6e77bc"
    )
