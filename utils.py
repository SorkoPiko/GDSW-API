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


def robtop_to_level_info(levelString: str) -> tuple[list[dict[str, str]], list[dict[str, [str, int]]], list[dict[str, str]], list[str]]:
    if levelString == "-1":
        return [], [], [], []
    body = levelString.split("#")
    levels = parse_levels(body[0].split("|"))
    creators = parse_creators(body[1].split("|"))
    songs = parse_songs(body[2].split("~:~"))

    hashString = ""
    for level in levels:
        hashString += f"{level["1"][0]}{level["1"][-1]}{level["18"]}{level["38"]}"

    assert encode_sha1_with_salt(hashString) == body[4]

    return levels, creators, songs, body[3].split(":")


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
