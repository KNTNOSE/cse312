import socketserver
import sys
from util.request import Request
import os
import html
import json

import pymongo
from pymongo import MongoClient

# Establish a connection to the MongoDB
mongo_client = MongoClient("mongo")
db = mongo_client["cse312"]
chat_collection = db["chat"]

class MyTCPHandler(socketserver.BaseRequestHandler):

    def handle(self):
        response = ""
        received_data = self.request.recv(2048)
        # print(self.client_address)
        # print("--- received data ---")
        # print(received_data)
        # print("--- end of data ---\n\n")
        request = Request(received_data)

        # TODO: Parse the HTTP request and use self.request.sendall(response) to send your response
        if request.path == '/':
            # リクエストが / の場合、public/index.html の内容を返す
            file_path = "public/index.html"
            
            if os.path.exists(file_path) and os.path.isfile(file_path):
                with open(file_path, "rb") as file:
                    content = file.read()
                
                content_length = len(content)
                content_length_header = f"Content-Length: {content_length}\r\n"
                response = (
                    b"HTTP/1.1 200 OK\r\n"
                    + content_length_header.encode("utf-8")
                    + b"Content-Type: text/html\r\n\r\n"
                    + content
                )

        elif request.path.startswith("/image/"):
            # リクエストが /image/ から始まる場合
            image_file_name = request.path[len("/image/"):]
            file_path = f"public/image/{image_file_name}"

            if os.path.exists(file_path) and os.path.isfile(file_path):
                with open(file_path, "rb") as file:
                    content = file.read()
                
                content_length = len(content)
                content_type_header = b"Content-Type: image/jpeg\r\n"  # JPEG画像の場合

                response = (
                    b"HTTP/1.1 200 OK\r\n"
                    + f"Content-Length: {content_length}\r\n".encode("utf-8")
                    + content_type_header
                    + b"\r\n"
                    + content
                )

        elif request.path == "/chat-message" and request.method == "POST":
            data = request.body.decode("utf-8")
            message = html.escape(data.split('=')[1])
            username = "Guest"
            
            # メッセージをデータベースに保存
            chat_collection.insert_one({
                "message": message,
                "username": username
            })

            response = b"HTTP/1.1 200 OK\r\nContent-Length: 16\r\n\r\nMessage received"

        elif request.path == "/chat-history" and request.method == "GET":
            
            messages = chat_collection.find()
            chat_history = [{
                "message": msg["message"],
                "username": msg["username"],
                "id": str(msg["_id"])
            } for msg in messages]
            
            chat_data = json.dumps(chat_history)
            response = (
                b"HTTP/1.1 200 OK\r\n"
                + f"Content-Length: {len(chat_data)}\r\n".encode('utf-8')
                + b"Content-Type: application/json\r\n\r\n"
                + chat_data.encode('utf-8')
            )

        else:
            # ファイルが存在しない場合、404 エラーを返す
            response = b"HTTP/1.1 404 Not Found\r\nContent-Length: 6\r\n\r\ninside"

        self.request.sendall(response)



def main():
    host = "0.0.0.0"
    port = 8080

    socketserver.TCPServer.allow_reuse_address = True

    server = socketserver.TCPServer((host, port), MyTCPHandler)

    print("Listening on port " + str(port))
    sys.stdout.flush()
    sys.stderr.flush()

    server.serve_forever()


if __name__ == "__main__":
    main()

if __name__ == "__main__":
    main()