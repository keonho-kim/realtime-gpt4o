import { Player } from './audio/player.js';
import { Recorder } from './audio/recorder.js';
import { WebSocketManager } from './websocket/manager.js';
import { ChatManager } from './chat/manager.js';
import { AudioManager } from './audio/manager.js';

const BUFFER_SIZE = 4800;
const SAMPLE_RATE = 24000;

class App {
    constructor() {
        this.audioManager = new AudioManager(SAMPLE_RATE, BUFFER_SIZE);
        this.webSocketManager = new WebSocketManager('ws://' + window.location.host + '/ws');
        this.chatManager = new ChatManager('chat');
        this.isAudioOn = false;
        this.instructions = '';

        // DOM이 완전히 로드된 후에 초기화 메서드들을 호출합니다.
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => this.initialize());
        } else {
            this.initialize();
        }
    }

    initialize() {
        this.initializeUI();
        this.initializeSettingsModal();
        this.loadInstructions();
    }

    initializeUI() {
        const toggleButton = document.getElementById('toggleAudio');
        if (toggleButton) {
            toggleButton.addEventListener('click', () => this.toggleAudio());
        } else {
            console.error('toggleAudio 버튼을 찾을 수 없습니다.');
        }
    }

    initializeSettingsModal() {
        const elements = {
            settingsToggle: document.getElementById('settingsToggle'),
            settingsModal: document.getElementById('settingsModal'),
            closeModalButton: document.getElementById('closeModal'),
            saveButton: document.getElementById('saveInstructions'),
            expandButton: document.getElementById('expandInstructions'),
            instructionsInput: document.getElementById('instructionsInput'),
            collapsible: document.querySelector('.collapsible')
        };

        // 모든 필요한 요소가 존재하는지 확인
        for (const [key, element] of Object.entries(elements)) {
            if (!element) {
                console.error(`${key} 요소를 찾을 수 없습니다.`);
                return; // 필요한 요소가 없으면 초기화를 중단합니다.
            }
        }

        // 여기서부터 이벤트 리스너 
        elements.settingsToggle.addEventListener('click', () => {
            elements.settingsModal.classList.remove('hidden');
            setTimeout(() => {
                const modalContent = elements.settingsModal.querySelector('.modal-content');
                if (modalContent) {
                    modalContent.style.transform = 'translateY(0)';
                    modalContent.style.opacity = '1';
                }
            }, 10);
        });

        const closeModal = () => {
            const modalContent = elements.settingsModal.querySelector('.modal-content');
            modalContent.style.transform = 'translateY(20px)';
            modalContent.style.opacity = '0';
            setTimeout(() => {
                elements.settingsModal.classList.add('hidden');
            }, 300);
        };

        elements.closeModalButton.addEventListener('click', closeModal);

        elements.settingsModal.addEventListener('click', (event) => {
            if (event.target === elements.settingsModal) {
                closeModal();
            }
        });

        elements.saveButton.addEventListener('click', () => this.saveInstructions());

        elements.expandButton.addEventListener('click', () => {
            elements.instructionsInput.classList.toggle('expanded');
            elements.expandButton.querySelector('i').textContent = 
                elements.instructionsInput.classList.contains('expanded') ? 'close_fullscreen' : 'open_in_full';
        });

        elements.collapsible.addEventListener("click", function() {
            this.classList.toggle("active");
            var content = this.nextElementSibling;
            var arrow = this.querySelector('.collapsible-arrow');
            if (content.style.display === "block") {
                content.style.display = "none";
                arrow.textContent = 'arrow_right';
            } else {
                content.style.display = "block";
                arrow.textContent = 'arrow_drop_down';
            }
        });
    }

    async loadInstructions() {
        try {
            const response = await fetch('/api/instructions');
            const data = await response.json();
            this.instructions = data.instructions;
            document.getElementById('instructionsInput').value = this.instructions;
        } catch (error) {
            console.error('Instructions 로드 오류:', error);
        }
    }

    async saveInstructions() {
        const newInstructions = document.getElementById('instructionsInput').value;
        try {
            console.log('Saving instructions:', newInstructions);
            const response = await fetch('/api/instructions', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ instructions: newInstructions }),
            });
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            console.log('Server response:', data);
            
            if (data.status === 'success') {
                this.instructions = newInstructions;
                alert('Instructions가 성적으로 업데이트되었습니다.');
                document.getElementById('settingsModal').classList.add('hidden');
            } else {
                throw new Error(data.message || 'Unknown error occurred');
            }
        } catch (error) {
            console.error('Instructions 저장 오류:', error);
            alert(`Instructions 저장 중 오류 발생했습니다: ${error.message}`);
        }
    }

    async toggleAudio() {
        const toggleButton = document.getElementById('toggleAudio');
        
        if (!this.isAudioOn) {
            await this.startAudio();
            toggleButton.innerHTML = '<i class="material-icons">mic_off</i>';
            toggleButton.classList.add('active');
            this.isAudioOn = true;
        } else {
            await this.stopAudio();
            toggleButton.innerHTML = '<i class="material-icons">mic</i>';
            toggleButton.classList.remove('active');
            this.isAudioOn = false;
        }
    }

    async startAudio() {
        try {
            await this.audioManager.start();
            this.webSocketManager.connect();
            
            await new Promise(resolve => {
                const checkConnection = () => {
                    if (this.webSocketManager.ws && this.webSocketManager.ws.readyState === WebSocket.OPEN) {
                        resolve();
                    } else {
                        setTimeout(checkConnection, 100);
                    }
                };
                checkConnection();
            });
            
            const initialSettings = {
                type: 'initial_settings',
                instructions: this.instructions
            };
            console.log('Sending initial settings:', initialSettings);
            this.webSocketManager.sendJson(initialSettings);
            
            this.webSocketManager.onMessage = (data) => {
                if (data.type === 'response.audio.delta') {
                    this.audioManager.playAudio(data.delta);
                } else if (data.type === 'transcript') {
                    this.chatManager.addMessage(data.sender, data.transcript);
                } else if (data.type === 'error') {
                    console.error('오류 발생:', data.message);
                } else if (data.type === 'unhandled_event') {
                    console.warn('처리되지 않은 이벤트 타입:', data.event_type);
                } else if (data.type === 'end_of_turn') {
                    console.log('AI 턴 종료');
                    // AI 턴이 끝났을 때의 처리 (필요한 경우)
                } else if (data.type === 'input_audio_buffer.speech_started') {
                    console.log('사용자 음성 입력 시작');
                } else if (data.type === 'input_audio_buffer.speech_stopped') {
                    console.log('사용자 음성 입력 종료');
                } else if (data.type === 'response.output_item.added') {
                    console.log('AI 응답 항목 추가됨');
                }
                console.log('받은 메시지:', data);
            };

            this.audioManager.onAudioData = (audioData) => {
                if (this.isAudioOn) {
                    this.webSocketManager.sendAudio(audioData);
                }
            };

        } catch (error) {
            console.error('오디오 시작 오류', error);
            alert('오디오 시작 중 오류가 발생했습니다. 설정을 확인하고 ��시 시도해주세요.');
        }
    }

    async stopAudio() {
        this.webSocketManager.disconnect();
        await this.audioManager.stop();
    }
}

// App 인스턴스 생성을 함수로 래핑
function initApp() {
    window.app = new App();
}

// DOM이 로드되면 App 인스턴스를 생성
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initApp);
} else {
    initApp();
}
