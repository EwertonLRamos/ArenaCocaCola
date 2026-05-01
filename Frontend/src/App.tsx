import { useEffect, useState } from 'react';
import * as signalR from '@microsoft/signalr';
import './App.css'; // Certifique-se de importar o CSS aqui!

interface GameState {
  playerName: string;
  score: number;
  lives: number;
  isGameOver: boolean;
}

function App() {
  const [connection, setConnection] = useState<signalR.HubConnection | null>(null);
  const [gameState, setGameState] = useState<GameState | null>(null);
  const [name, setName] = useState('');
  const [errorMessage, setErrorMessage] = useState('');

  useEffect(() => {
    // Altera dinamicamente o título da página por segurança, caso o index.html não seja atualizado
    document.title = "Arena Coca-cola";

    const newConnection = new signalR.HubConnectionBuilder()
      .withUrl("http://localhost:5009/arenaHub")
      .withAutomaticReconnect()
      .build();

    newConnection.start().then(() => {
      setConnection(newConnection);
      
      newConnection.on("UpdateGame", (state: GameState) => {
        setGameState(state);
      });
    });

    return () => {
      if (newConnection) {
        newConnection.stop();
      }
    };
  }, []);

  const startGame = () => {
    if (!name.trim()) {
      setErrorMessage('⚠️ Por favor, digite seu nome!');
      return;
    }
    
    setErrorMessage('');
    
    fetch(`http://localhost:5009/api/game/start?playerName=${name}`, { method: 'POST' })
      .catch(err => console.error("Erro ao iniciar jogo:", err));
  };

  const resetToHome = () => {
    setGameState(null);
    setName('');
    setErrorMessage('');
  };

  // ==========================================
  // ESTADO 3: TELA DE GAME OVER
  // ==========================================
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

  // ==========================================
  // ESTADO 2: TELA DE JOGO ROLANDO
  // ==========================================
  if (gameState && !gameState.isGameOver) {
    return (
      <div className="container">
        <div className="game-area">
          <h2 className="player-name">JOGADOR: {gameState.playerName}</h2>

          <div className="score-display">
            {gameState.score}
          </div>

          <div className="lives-container">
            {[...Array(3)].map((_, i) => (
              <div 
                key={i} 
                className={`life-icon ${i >= gameState.lives ? 'lost' : ''}`}
              >
                ⚽
              </div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  // ==========================================
  // ESTADO 1: TELA INICIAL (Home)
  // ==========================================
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