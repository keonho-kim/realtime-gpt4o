export class ChatManager {
    constructor(chatElementId) {
        this.chatElement = document.getElementById(chatElementId);
    }

    addMessage(sender, text) {
        const message = document.createElement('div');
        message.className = `message ${sender}`;
        
        // 텍스트를 그대로 설정
        message.textContent = text;
        
        this.chatElement.appendChild(message);
        this.chatElement.scrollTop = this.chatElement.scrollHeight;
    }
}
