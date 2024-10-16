export class Recorder {
    constructor(sampleRate, onDataAvailable) {
        this.onDataAvailable = onDataAvailable;
        this.sampleRate = sampleRate;
        this.audioContext = null;
        this.mediaStream = null;
        this.mediaStreamSource = null;
        this.workletNode = null;
    }

    async start() {
        try {
            if (this.audioContext) {
                await this.audioContext.close();
            }

            this.audioContext = new (window.AudioContext || window.webkitAudioContext)({ sampleRate: this.sampleRate });

            await this.audioContext.audioWorklet.addModule("/static/js/audio/audio-processor-worklet.js");

            this.mediaStream = await navigator.mediaDevices.getUserMedia({ audio: true });
            this.mediaStreamSource = this.audioContext.createMediaStreamSource(this.mediaStream);

            this.workletNode = new AudioWorkletNode(this.audioContext, "audio-processor-worklet");
            this.workletNode.port.onmessage = event => {
                this.onDataAvailable(event.data.buffer);
            };

            this.mediaStreamSource.connect(this.workletNode);
            this.workletNode.connect(this.audioContext.destination);
        } catch (error) {
            console.error('Recorder start error:', error);
            this.stop();
            throw error;
        }
    }

    async stop() {
        if (this.mediaStream) {
            this.mediaStream.getTracks().forEach(track => track.stop());
            this.mediaStream = null;
        }

        if (this.audioContext) {
            await this.audioContext.close();
            this.audioContext = null;
        }

        this.mediaStreamSource = null;
        this.workletNode = null;
    }
}
