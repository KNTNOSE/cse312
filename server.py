import socketserver
import sys
from util.request import Request
import os
import html
import json
import bcrypt
import uuid
import pymongo
from pymongo import MongoClient
from bson.objectid import ObjectId

# Establish a connection to the MongoDB
mongo_client = MongoClient("mongo")
db = mongo_client["cse312"]
chat_collection = db["chat"]
users_collection = db["users"]
tokens_collection = db["tokens"]

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

        elif request.path == "/style.css":
            file_path = "public/style.css"

            if os.path.exists(file_path) and os.path.isfile(file_path):
                with open(file_path, "rb") as file:
                    content = file.read()
                
                content_length = len(content)
                content_length_header = f"Content-Length: {content_length}\r\n"
                response = (
                    b"HTTP/1.1 200 OK\r\n"
                    + content_length_header.encode("utf-8")
                    + b"Content-Type: text/css\r\n\r\n"
                    + content
                )

        elif request.path == "/functions.js":
            file_path = "public/functions.js"

            if os.path.exists(file_path) and os.path.isfile(file_path):
                with open(file_path, "rb") as file:
                    content = file.read()
                
                content_length = len(content)
                content_length_header = f"Content-Length: {content_length}\r\n"
                response = (
                    b"HTTP/1.1 200 OK\r\n"
                    + content_length_header.encode("utf-8")
                    + b"Content-Type: text/js\r\n\r\n"
                    + content
                )

        elif request.path == "/chat-message" and request.method == "POST":
            data = request.body.decode("utf-8")
            parsed_data = json.loads(data)
            message = html.escape(parsed_data["message"])
            
            auth_token = request.cookies.get("auth_token")
            username = 'Guest'

            if auth_token:
                token_entry = None
                for entry in tokens_collection.find():  # ユーザー名でフィルタリングせずにすべてのトークンを検索
                    if bcrypt.checkpw(auth_token.encode('utf-8'), entry["hashed_token"]):
                        token_entry = entry
                        print(token_entry)
                        break
                if token_entry:
                    username = token_entry["username"]  # 認証されたユーザー名を取得
                    print(username)
            
            # メッセージをデータベースに保存
            chat_collection.insert_one({
                "message": message,
                "username": username
            })

            response = b"HTTP/1.1 200 OK\r\nContent-Length: 16\r\n\r\nMessage received"

        elif request.path.startswith("/chat-message/") and request.method == "DELETE":
            message_id_str = request.path.split("/")[-1]
            message_id = ObjectId(message_id_str)
            print(message_id)
            
            # Authenticate the user using the auth_token
            auth_token = request.cookies.get("auth_token")
            print(auth_token)

            username = 'Guest'
            if auth_token:
                # Iterate through each token in the tokens_collection to find a match
                for token_entry in tokens_collection.find():
                    if bcrypt.checkpw(auth_token.encode('utf-8'), token_entry["hashed_token"]):
                        username = token_entry["username"]
                        print(username)
                        break

                    else:
                        print('token_entry was not Found')
            
            message = chat_collection.find_one({"_id": message_id})
            print(message)

            if not message:
                response = b"HTTP/1.1 404 Not Found\r\n\r\nMessage not found"
            elif message["username"] != username:
                response = b"HTTP/1.1 403 Forbidden\r\n\r\nCannot delete others' messages"
            else:
                # Setting the soft delete flag
                chat_collection.update_one({"_id": message_id}, {"$set": {"deleted": True}})
                response = b"HTTP/1.1 200 OK\r\n\r\nMessage marked as deleted"
            


        elif request.path == "/chat-history" and request.method == "GET":
            
            messages = chat_collection.find({"deleted": {"$ne": True}})

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

        elif request.path == "/register" and request.method == 'POST':
            data = request.body.decode("utf-8")
            parsed_data = dict(item.split("=") for item in data.split("&"))

            username = html.escape(parsed_data["username_reg"])
            password = parsed_data["password_reg"]

            salt = bcrypt.gensalt()
            hashed_pw = bcrypt.hashpw(password.encode('utf-8'), salt)

            users_collection.insert_one({
                "username": username,
                "hashed_pw": hashed_pw
            })

            response = b"HTTP/1.1 200 OK\r\nContent-Length: 17\r\n\r\nRegister succeded"

        elif request.path == '/login' and request.method == 'POST':
            data = request.body.decode("utf-8")
            parsed_data = dict(item.split("=") for item in data.split("&"))

            username = html.escape(parsed_data["username_login"])
            password = parsed_data["password_login"]

            user = users_collection.find_one({"username": username})

            if user and bcrypt.checkpw(password.encode('utf-8'), user["hashed_pw"]):
                auth_token = str(uuid.uuid4())
                hashed_token = bcrypt.hashpw(auth_token.encode('utf-8'), bcrypt.gensalt())

                # トークンハッシュをデータベースに保存
                tokens_collection.insert_one({
                    "username": username,
                    "hashed_token": hashed_token
                })

                response = (
                    b"HTTP/1.1 303 See Other\r\n"
                    + f"Set-Cookie: auth_token={auth_token}; HttpOnly; Max-Age=3600\r\nLocation: /\r\n\r\n".encode('utf-8'))
                

            else:
                response = b"HTTP/1.1 401 Unauthorized\r\n\r\nInvalid credentials."

        # elif request.path == '/delete' and request.method == 'POST':
        #     data = request.body.decode("utf-8")
        #     parsed_data = dict(item.split("=") for item in data.split("&"))

        #     message_id = html.escape(parsed_data["messageId"])
        #     auth_token = request.cookies.get("auth_token")
        #     username = users_collection.find_one({
                
        #     })




        elif request.path == "/visit-counter":
            cookie = request.get_cookie("visit_count")
            
            # Cookieの値を取得してカウントを増やす
            if cookie:
                count = int(cookie) + 1
            else:
                count = 1
            
            # クッキーの期限を1時間後に設定
            import datetime
            expiration = datetime.datetime.utcnow() + datetime.timedelta(hours=3)
            expiration_str = expiration.strftime('%a, %d %b %Y %H:%M:%S GMT')
            set_cookie_header = f'Set-Cookie: visit_count={count}; Expires={expiration_str}; Path=/; HttpOnly\r\n'
            
            response = (
                b"HTTP/1.1 200 OK\r\n"
                + set_cookie_header.encode('utf-8')
                + f"Content-Length: {len(str(count))}\r\n".encode('utf-8')
                + b"Content-Type: text/plain\r\n\r\n"
                + str(count).encode('utf-8')
            )

        else:
            # ファイルが存在しない場合、404 エラーを返す
            response = b"HTTP/1.1 404 Not Found\r\nContent-Length: 6\r\n\r\nNot Found"

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