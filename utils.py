from pytube import extract


def parse_data(data):
    newdata = {}
    for i in data:
        yt = ""
        if len(i) == 5:
            try:
                yt = f"https://youtu.be/{extract.video_id(i[4])}"
            except:
                yt = ""
        newdata.update({i[0]: {
            "sw": i[1],
            "desc": i[2],
            "src": i[3],
            "yt": yt
        }})
    return newdata


def generate_cell_link(spreadsheet_id, sheet_id, row):
    return f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/edit#gid={sheet_id}&range=A{row}:F{row}"
