from pytube import extract


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
