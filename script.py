from bs4 import BeautifulSoup
import csv
import os
import argparse
import re
import sys


def parse_html(filename):
    message_rows = []
    html = open(filename, encoding='utf-8').read()
    soup = BeautifulSoup(html, features="html.parser")

    msgs = soup.findAll("div", {"class": "message default clearfix"})
    for msg in msgs:
        row = []
        
        # MessageID
        row.append(msg.attrs["id"])
        
        # Date and time
        time = msg.find("div", {"class": "pull_right date details"}).attrs["title"]
        date, time = time.split()
        row.extend((date, time))

        # Sender
        row.append(msg.find("div", {"class": "from_name"}).text.strip())

        # Message
        msg_text = msg.find("div", {"class": "text"})
        if msg_text:
            row.append(msg_text.text.strip())
        else:
            # You have probably exported only text messages
            # and those where no text message is found are actually images, videos, etc. posted
            row.append("NA")
            
        # Attachments - Documents, images, videos attached to message
        # Caution: In this state, the script can only handle exported images. Stickers, videos, and voicemails will be ignored
        msg_attach = msg.find("div", {"class": "media_wrap clearfix"})
        if msg_attach:
            if msg_attach.find("div", {"class": "title bold"}):
                # If there is bold text in attachment, it is the "not downloaded" signifier
                # Therefore, there is probably no further useful information apart from said title
                attachment = msg_attach.find("div", {"class": "title bold"}).text.strip()
                row.append(attachment)
            elif msg_attach.find("a", {"class": "photo_wrap clearfix pull_left"}):
                # If this appears, we're dealing with an image
                attachment = msg_attach.findAll('img')
                row.append(attachment)
            else:
                # If both fail, there is no attachment
                row.append("NA")
        else:
            row.append("NA")      
        
        #Reply_to_Msg - If message is in reply to a previous message
        msg_reply = msg.find("div", {"class":"reply_to details"})
        if msg_reply:
            rep_id = re.findall("message[0-9]+", str(msg_reply))
            row.append(rep_id[0])
        else:
            # If no reply: include NA
            row.append("NA")
        
        # Forwarded_from - External group name if message was forwarded from another Telegram group/account
        msg_forward = msg.find("div", {"class": "forwarded body"})
        if msg_forward:
            forw_info = msg_forward.find("div", {"class": "from_name"})
            forw_info.span.decompose()
            row.append(forw_info.text.strip())
        else:
            # If not forwarded: include NA
            row.append("NA")
        

            
        message_rows.append(row)
    return(message_rows)



def main():
    parser = argparse.ArgumentParser(description="""A simple Python script to parse a Telegram archive and export it as a csv file. 
    By default, it takes the html files (Telegram archive) from the current directory.""")
    parser.add_argument("-f", "--file", help="Html file alone, contening the messages to scrap.")
    parser.add_argument("-d", "--directory", help="Directory containing the html files.")

    args = parser.parse_args()
    directory = ""
    filename  = ""
    
    # Location of the Telegram archive
    if args.directory:
        if os.path.isdir(args.directory):
            directory = args.directory
            if not directory.endswith('/'):
                directory = directory + '/'
        else:
            print("Parameter does not exist or is not a directory.")
            sys.exit()
    elif args.file:
        if os.path.isfile(args.file):
            filename = args.file
        else:
            print("Parameter does not exist or is not a file.")
            sys.exit()
    else:
        # If no agurment is supplied, use the current directory
        directory = os.path.dirname(os.path.realpath(__file__)) + '/'

    output_rows = []
    output_rows.append(("ID", "Date", "Time", "Sender", "Message", "Attachment", "Responds_to", "Forward_from"))

    if directory:
        for html_file in os.listdir(directory):
            filename = os.fsdecode(directory + html_file)
            if filename.endswith(".html"):
                rows = parse_html(filename)
                output_rows.extend(rows)
    elif filename:
        output_rows = parse_html(filename)

    with open("output.csv", "w", encoding='utf-8', newline='') as csv_file:
        writer = csv.writer(csv_file)
        writer.writerows(output_rows)


if __name__== "__main__":
    main()
