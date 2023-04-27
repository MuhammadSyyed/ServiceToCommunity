class Chatbox {
    constructor() {
        this.args = {
            openButton: document.querySelector('.chatbox__button'),
            chatBox: document.querySelector('.chatbox__support'),
            sendButton: document.querySelector('.send__button')
        }

        this.state = false;
        this.messages = [];

        // create WebSocket object
        this.socket = new WebSocket('ws://127.0.0.1:8000/ws/1');

        // add onmessage event handler
        this.socket.onmessage = event => {
            const message = JSON.parse(event.data);
            this.messages.push(message);
            this.updateChatText(this.args.chatBox);
        };
        this.socket.onopen = event => {
            this.socket.send("ping");
        };
    }

    display() {
        const { openButton, chatBox, sendButton } = this.args;

        openButton.addEventListener('click', () => this.toggleState(chatBox))

        sendButton.addEventListener('click', () => this.onSendButton(chatBox))

        const node = chatBox.querySelector('input');
        node.addEventListener("keyup", ({ key }) => {
            if (key === "Enter") {
                this.onSendButton(chatBox)
            }
        })
    }

    toggleState(chatbox) {
        this.state = !this.state;

        // show or hides the box
        if (this.state) {
            chatbox.classList.add('chatbox--active')
        } else {
            chatbox.classList.remove('chatbox--active')
        }
    }

    onSendButton(chatbox) {
        var textField = chatbox.querySelector('input');
        let text1 = textField.value
        if (text1 === "") {
            return;
        }

        // send message using WebSocket
        this.socket.send(text1);

        // clear input field
        textField.value = '';
    }

    updateChatText(chatbox) {
        var html = '';
        this.messages.slice().reverse().forEach(function (item, index) {
            if (item.sender === "bot") {
                html += '<div class="messages__item messages__item--visitor">' + item.msg + '</div>'
            }
            else {
                html += '<div class="messages__item messages__item--operator">' + item.msg + '</div>'
            }
        });

        const chatmessage = chatbox.querySelector('.chatbox__messages');
        chatmessage.innerHTML = html;
    }
}


const chatbox = new Chatbox();
chatbox.display();