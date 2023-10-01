                auth_token = request.cookies.get("auth_token")

                if auth_token:  # ユーザーが認証済みの場合

                    user_data = None
                    for token_entry in tokens_collection.find():
                        if bcrypt.checkpw(auth_token.encode('utf-8'), token_entry["hashed_token"]):
                            user_data = token_entry
                            break
                    
                    if user_data:

                        xsrf_token = user_data["xsrf_token"]

                        if not xsrf_token:
                            xsrf_token = secrets.token_hex(16)
                            tokens_collection.update_one({"hashed_token": user_data["hashed_token"]}, {"$set": {"xsrf_token": xsrf_token}})
                            print("xsrf_token was generated")
                        else:
                            print('xsrf_token exists')
                    
                    # プレースホルダーをXSRFトークンで置き換えます
                    placeholder = "YOUR_XSRF_TOKEN_HERE"
                    content_str = content.decode('utf-8')  # バイト列を文字列に変換
                    content_str = content_str.replace(placeholder, xsrf_token)
                    content = content_str.encode('utf-8')  # 文字列をバイト列に変換

        
                
                content_length = len(content)
                content_length_header = f"Content-Length: {content_length}\r\n"
                response = (
                    b"HTTP/1.1 200 OK\r\n"
                    + content_length_header.encode("utf-8")
                    + b"Content-Type: text/html\r\n\r\n"
                    + content
                )