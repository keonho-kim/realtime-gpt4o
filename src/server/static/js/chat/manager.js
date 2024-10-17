export class ChatManager {
    constructor(chatElementId) {
        this.chatElement = document.getElementById(chatElementId);
    }

    addMessage(sender, text) {
        const message = document.createElement('div');
        message.className = `message ${sender}`;
        
        // 마크다운을 HTML로 변환
        const htmlContent = marked.parse(text);
        
        // XSS 공격 방지를 위한 기본적인 sanitize 함수
        const sanitize = (html) => {
            const temp = document.createElement('div');
            temp.textContent = html;
            return temp.innerHTML;
        };
        
        // 안전하게 HTML 삽입
        message.innerHTML = sanitize(htmlContent);
        
        this.chatElement.appendChild(message);
        this.chatElement.scrollTop = this.chatElement.scrollHeight;
        
        // 코드 블록에 대한 구문 강조 적용 (선택사항)
        message.querySelectorAll('pre code').forEach((block) => {
            hljs.highlightBlock(block);
        });
    }
}
