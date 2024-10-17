import { Player } from './player.js';
import { Recorder } from './recorder.js';

export class AudioManager {
    constructor(sampleRate, bufferSize) {
        this.player = new Player(sampleRate);
        this.recorder = new Recorder(sampleRate, this.handleAudioData.bind(this));
        this.bufferSize = bufferSize;
        this.buffer = new Uint8Array();
        this.onAudioData = null;
    }

    async start() {
        await this.player.init();
        await this.recorder.start();
    }

    async stop() {
        this.player.stop();
        await this.recorder.stop();
    }

    playAudio(base64Audio) {
        const binary = atob(base64Audio);
        const bytes = Uint8Array.from(binary, c => c.charCodeAt(0));
        const pcmData = new Int16Array(bytes.buffer);
        this.player.play(pcmData);
    }

    handleAudioData(data) {
        const uint8Array = new Uint8Array(data);
        this.appendToBuffer(uint8Array);

        if (this.buffer.length >= this.bufferSize) {
            const toSend = new Uint8Array(this.buffer.slice(0, this.bufferSize));
            this.buffer = new Uint8Array(this.buffer.slice(this.bufferSize));

            if (this.onAudioData) {
                this.onAudioData(toSend);
            }

            // 디버깅을 위한 로그 추가
            console.log('오디오 데이터 전송:', toSend.length);
        }
    }

    appendToBuffer(newData) {
        const newBuffer = new Uint8Array(this.buffer.length + newData.length);
        newBuffer.set(this.buffer);
        newBuffer.set(newData, this.buffer.length);
        this.buffer = newBuffer;
    }
}
