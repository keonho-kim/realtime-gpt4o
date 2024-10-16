export class WebSocketManager {
    constructor(url) {
        this.url = url;
        this.ws = null;
        this.onMessage = null;
    }

    connect() {
        this.ws = new WebSocket(this.url);
        this.ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            if (this.onMessage) {
                this.onMessage(data);
            }
        };

        this.ws.onclose = () => {
            console.log('WebSocket 연결이 닫혔습니다. 재연결 시도 중...');
            setTimeout(() => this.connect(), 1000); // 1초 후 재연결 시도
        };

        this.ws.onerror = (error) => {
            console.error('WebSocket 오류:', error);
        };
    }

    disconnect() {
        if (this.ws) {
            this.ws.close();
            this.ws = null;
        }
    }

    isConnected() {
        return this.ws && this.ws.readyState === WebSocket.OPEN;
    }

    sendJson(data) {
        if (this.isConnected()) {
            this.ws.send(JSON.stringify(data));
        } else {
            console.error('WebSocket이 연결되지 않았습니다. 메시지를 보낼 수 없습니다.');
            this.connect(); // 연결이 끊어졌다면 재연결 시도
        }
    }

    sendAudio(audioData) {
        if (this.isConnected()) {
            const base64 = btoa(String.fromCharCode(...audioData));
            this.ws.send(JSON.stringify({type: 'input_audio_buffer.append', audio: base64}));
        } else {
            console.error('WebSocket이 연결되지 않았습니다. 오디오 데이터를 보낼 수 없습니다.');
            this.connect(); // 연결이 끊어졌다면 재연결 시도
        }
    }
}
