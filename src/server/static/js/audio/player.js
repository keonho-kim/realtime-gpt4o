export class Player {
    constructor(sampleRate) {
        this.playbackNode = null;
        this.sampleRate = sampleRate;
    }

    async init() {
        const audioContext = new AudioContext({ sampleRate: this.sampleRate });
        await audioContext.audioWorklet.addModule("/static/js/audio/audio-playback-worklet.js");

        this.playbackNode = new AudioWorkletNode(audioContext, "audio-playback-worklet");
        this.playbackNode.connect(audioContext.destination);
    }

    play(buffer) {
        if (this.playbackNode) {
            this.playbackNode.port.postMessage(buffer);
        }
    }

    stop() {
        if (this.playbackNode) {
            this.playbackNode.port.postMessage(null);
        }
    }
}
