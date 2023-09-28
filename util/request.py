class Request:

    def __init__(self, request: bytes):
        # TODO: parse the bytes of the request and populate the following instance variables

        self.request_str = request.decode("utf-8")

        self.body = b""
        self.method = ""
        self.path = ""
        self.http_version = ""
        self.headers = {}
        
        self.parse_headers()
        self.parse_body(request)
        self.cookies = self._parse_cookies()


    def parse_headers(self):
        headers_section = self.request_str.split('\r\n\r\n', 1)[0]
        request_line = headers_section.split('\r\n')[0]
        header_list = headers_section.split('\r\n')[1:]

        parts = request_line.split(' ')
        if len(parts) >= 2:
            self.method = parts[0]
            self.path = parts[1]
            self.http_version=parts[2]
        

        for header in header_list:
            header_name, header_value = header.split(': ', 1)

            if header_name in self.headers:
                if not isinstance(self.headers[header_name], list):
                    self.headers[header_name] = [self.headers[header_name]]
                self.headers[header_name].append(header_value)
            else:
                self.headers[header_name] = header_value

    def parse_body(self, request):
        if '\r\n\r\n' in self.request_str:
            body_section = self.request_str.split('\r\n\r\n', 1)[1]
            self.body = body_section.encode("utf-8")
        else:
            # リクエストが正しくない場合、エラーレスポンスを生成
            self.body = b"Bad Request"


    def set_content_length(self):
        content_length = len(self.body)
        self.headers["Content-Length"] = str(content_length)


    def _parse_cookies(self):
        """
        HTTPヘッダからクッキーを解析して辞書で返します。
        """
        cookies = {}
        cookie_header = self.headers.get('Cookie')
        if cookie_header:
            cookie_pairs = cookie_header.split(';')
            for pair in cookie_pairs:
                key, value = pair.strip().split('=', 1)
                cookies[key] = value
        return cookies

    def get_cookie(self, key, default=None):
        """
        指定されたキーのクッキーの値を返します。クッキーが存在しない場合はdefaultを返します。
        """
        return self.cookies.get(key, default)




