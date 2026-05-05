import { useEffect, useState } from 'react';
import * as signalR from '@microsoft/signalr';
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

  useEffect(() => {
    document.title = "Arena Coca-cola";

    const newConnection = new signalR.HubConnectionBuilder()
      .withUrl("http://localhost:5009/arenaHub")
      .withAutomaticReconnect()
      .build();

    newConnection.start()
      .then(() => {
        //console.log("SignalR conectado!");
        setConnection(newConnection);
        
        newConnection.on("UpdateGame", (state: GameState) => {
          //console.log("Recebido UpdateGame:", state);
          setGameState(state);
        });
      })
      .catch(err => {
        console.error("Erro ao conectar SignalR:", err);
      });

    return () => {
      if (newConnection) {
        newConnection.stop();
      }
    };
  }, []);

  const startGame = () => {
    if (!name.trim()) {
      setErrorMessage('Por favor, digite seu nome!');
      return;
    }
    
    setErrorMessage('');
    //console.log("Iniciando jogo com nome:", name);
    
    fetch(`http://localhost:5009/api/game/start?playerName=${name}`, { method: 'POST' })
      .then(response => {
        //console.log("Resposta do backend:", response);
        return response.json();
      })
      .then(data => {
        //console.log("Dados da resposta:", data);
      })
      .catch(err => console.error("Erro ao iniciar jogo:", err));
  };

  const resetToHome = () => {
    setGameState(null);
    setName('');
    setErrorMessage('');
  };

  if (gameState?.isGameOver) {
    return (
      <div className="container">
        <h1 className="game-over-title">Fim de Jogo!</h1>
        <h2 className="game-over-subtitle">Valeu, {gameState.playerName}!</h2>
        <p style={{ fontSize: '1.5rem', marginBottom: '0' }}>Sua pontuação final:</p>
        <div className="score-display" style={{ marginBottom: '3rem' }}>
          {gameState.score}
        </div>
        
        <button onClick={resetToHome} className="btn-outline">
          VOLTAR PARA O INÍCIO
        </button>
      </div>
    );
  }

  if (gameState && !gameState.isGameOver) {
    return (
      <div className="container">
        <div className="game-area">
          <h2 className="player-name">JOGADOR: {gameState.playerName}</h2>

          <div className="timer-display">
            {gameState.timeRemaining}s
          </div>

          <div className="score-display">
            {gameState.score}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="container">
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
          onKeyDown={(e) => e.key === 'Enter' && startGame()}
        />
        
        <div className={`error-message ${errorMessage ? 'visible' : ''}`}>
          {errorMessage}
        </div>

        <button onClick={startGame} className="btn-primary">
          Start
        </button>
      </div>
    </div>
  );
}

export default App;