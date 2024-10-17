export class Player {
    constructor(sampleRate) {
        this.playbackNode = null;
        this.sampleRate = sampleRate;
        this.isPlaying = false;
    }

    async init() {
        const audioContext = new AudioContext({ sampleRate: this.sampleRate });
        await audioContext.audioWorklet.addModule("/static/js/audio/audio-playback-worklet.js");

        this.playbackNode = new AudioWorkletNode(audioContext, "audio-playback-worklet");
        this.playbackNode.connect(audioContext.destination);
    }

    play(buffer) {
        if (this.playbackNode) {
            this.stop();  // 기존 재생 중인 오디오 중지
            this.playbackNode.port.postMessage(buffer);
            this.isPlaying = true;
        }
    }

    stop() {
        if (this.playbackNode) {
            this.playbackNode.port.postMessage(null);
            this.isPlaying = false;
        }
    }
}
