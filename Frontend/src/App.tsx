import { useEffect, useState } from 'react';
import * as signalR from '@microsoft/signalr';
import gift from './assets/presente-branco.png';
import './App.css';

interface GameState {
  playerName: string;
  score: number;
  timeRemaining: number;
  isGameOver: boolean;
}

function App() {
  const [connection, setConnection] = useState<signalR.HubConnection | null>(null);
  const [gameState, setGameState] = useState<GameState | null>(null);
  const [name, setName] = useState('');
  const [errorMessage, setErrorMessage] = useState('');

  const [showTerms, setShowTerms] = useState(false);
  const [showCountdown, setShowCountdown] = useState(false);

  const [countdown, setCountdown] = useState(3);
  const [isPreparing, setIsPreparing] = useState(true);

  useEffect(() => {
    document.title = "Arena Coca-cola";

    const newConnection = new signalR.HubConnectionBuilder()
      .withUrl("http://localhost:5009/arenaHub")
      .withAutomaticReconnect()
      .build();

    newConnection.start()
      .then(() => {
        setConnection(newConnection);

        newConnection.on("UpdateGame", (state: GameState) => {
          setGameState(state);
        });
      })
      .catch(err => console.error("Erro ao conectar SignalR:", err));

    return () => {
      newConnection.stop();
    };
  }, []);

  const handleStartClick = () => {
    if (!name.trim()) {
      setErrorMessage('Por favor, digite seu nome!');
      return;
    }

    setErrorMessage('');
    setShowTerms(true);
  };

  const startGame = () => {
  setShowTerms(false);
  setShowCountdown(true);
  setIsPreparing(true);

  // "Prepare-se..."
  setTimeout(() => {
    setIsPreparing(false);

    let counter = 3;
    setCountdown(counter);

    const interval = setInterval(() => {
      counter--;
      setCountdown(counter);

      if (counter === 0) {
        clearInterval(interval);

        // 👇 deixa o "Já!" aparecer antes de sair da tela
        setTimeout(() => {
          fetch(`http://localhost:5009/api/game/start?playerName=${name}`, { method: 'POST' })
            .catch(err => console.error("Erro ao iniciar jogo:", err));

          setShowCountdown(false);
        }, 800); // pode ajustar (600–1000ms fica bom)
      }
    }, 1000);
  }, 1000);
};

  const resetToHome = () => {
    setGameState(null);
    setName('');
    setErrorMessage('');
  };

  // ===========================
  // TELA DE CONTAGEM
  // ===========================
  if (showCountdown) {
    const getCountdownText = () => {
      if (isPreparing) return "Prepare-se...";

      switch (countdown) {
        case 3: return "3";
        case 2: return "2";
        case 1: return "1";
        case 0: return "Já!";
        default: return "";
      }
    };

    return (
      <div className="container background">
        <div className="challenge-box">
          <div className="countdown-text">
            {getCountdownText()}
          </div>

          <div className="gift-container">
            <img src={gift} alt="Presente" className="gift-image" />

            <div className="gift-content">
              <span className="challenge-top">Faça</span>
              <span className="challenge-number">25</span>
              <span className="challenge-bottom">pontos</span>
              <span className="challenge-reward">e ganhe um brinde!</span>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // ===========================
  // TERMOS
  // ===========================
  if (showTerms) {
    return (
      <div className="terms-overlay">
        <div className="terms-modal">
          <h2>Termo de Uso de Imagem</h2>
          <p>
            Para participar da <b>Arena Coca-Cola</b>, é necessário autorizar o uso da sua imagem.
            Ao prosseguir, você concorda com a captação e divulgação durante o evento.
          </p>

          <div className="terms-actions">
            <button className="btn-outline" onClick={() => setShowTerms(false)}>
              Recusar
            </button>

            <button className="btn-primary" onClick={startGame}>
              Aceitar e Jogar
            </button>
          </div>
        </div>
      </div>
    );
  }

  // ===========================
  // GAME OVER
  // ===========================
  if (gameState?.isGameOver) {
    return (
      <div className="container background">
        <h1 className="game-over-title">Fim de Jogo!</h1>
        <h2 className="game-over-subtitle">Valeu, {gameState.playerName}!</h2>

        <p>Sua pontuação final:</p>
        <div className="score-display">{gameState.score}</div>

        <button onClick={resetToHome} className="btn-outline">
          VOLTAR
        </button>
      </div>
    );
  }

  // ===========================
  // JOGO RODANDO
  // ===========================
  if (gameState && !gameState.isGameOver) {
    return (
      <div className="container background">
        <div className="player-info">
          <span className="player-label">Jogador</span>
          <span className="player-name">{gameState.playerName}</span>
        </div>

        <div className="timer-display">
          {gameState.timeRemaining}s
        </div>

        <div className="score-display">
          {gameState.score}
        </div>
      </div>
    );
  }

  // ===========================
  // HOME
  // ===========================
  return (
    <div className="container background">
      <h1 className="title">Arena<br />Coca-Cola</h1>

      <div className="input-group">
        <input 
          className={`player-input ${errorMessage ? 'has-error' : ''}`}
          placeholder="Digite seu Nome" 
          value={name} 
          onChange={e => {
            setName(e.target.value);
            if (errorMessage) setErrorMessage('');
          }}
          onKeyDown={(e) => e.key === 'Enter' && handleStartClick()}
        />

        <div className={`error-message ${errorMessage ? 'visible' : ''}`}>
          {errorMessage}
        </div>

        <button onClick={handleStartClick} className="btn-primary">
          Start
        </button>
      </div>
    </div>
  );
}

export default App;