function deleteMessage(messageId) {
    const request = new XMLHttpRequest();
    request.onreadystatechange = function () {
        console.log("Current readyState:", this.readyState);

        if (this.readyState === 4 && this.status === 200) {
            console.log(this.response);;
            const messageElement = document.getElementById('message_' + messageId);
            
            if (messageElement) {
                messageElement.remove();
            }
        
        }
    }
    request.open("DELETE", "/chat-message/" + messageId);
    request.send();
}

function chatMessageHTML(messageJSON) {
    const username = messageJSON.username;
    const message = messageJSON.message;
    const messageId = messageJSON.id;
    // let messageHTML = "<br><button onclick='deleteMessage(" + messageId + ")'>X</button> ";
    let messageHTML = '<br><button onclick="deleteMessage(\'' + messageId + '\')">X</button> ';
    messageHTML += "<span id='message_" + messageId + "'><b>" + username + "</b>: " + message + "</span>";
    return messageHTML;
}

function clearChat() {
    const chatMessages = document.getElementById("chat-messages");
    chatMessages.innerHTML = "";
}

function addMessageToChat(messageJSON) {
    const chatMessages = document.getElementById("chat-messages");
    chatMessages.innerHTML += chatMessageHTML(messageJSON);
    chatMessages.scrollIntoView(false);
    chatMessages.scrollTop = chatMessages.scrollHeight - chatMessages.clientHeight;
}

function sendChat() {
    const chatTextBox = document.getElementById("chat-text-box");
    const message = chatTextBox.value;
    chatTextBox.value = "";
    const request = new XMLHttpRequest();

    request.onreadystatechange = function () {
        if (this.readyState === 4 && this.status === 200) {
            console.log(this.response);
        }
    }
    const xsrfToken = document.getElementById("xsrf-token-input").value;
    const messageJSON = {"message": message, "xsrf_token": xsrfToken};
    // const messageJSON = {"message": message};
    request.open("POST", "/chat-message");
    request.send(JSON.stringify(messageJSON));
    chatTextBox.focus();
}

function updateChat() {
    const request = new XMLHttpRequest();
    request.onreadystatechange = function () {
        if (this.readyState === 4 && this.status === 200) {
            clearChat();
            const messages = JSON.parse(this.response);
            for (const message of messages) {
                addMessageToChat(message);
            }
        }
    }
    request.open("GET", "/chat-history");
    request.send();
}



function welcome() {
    document.addEventListener("keypress", function (event) {
        if (event.code === "Enter") {
            sendChat();
        }
    });

    document.getElementById("paragraph").innerHTML += "<br/>This text was added by JavaScript 😀";
    document.getElementById("chat-text-box").focus();

    updateChat();
    setInterval(updateChat, 2000);
}
