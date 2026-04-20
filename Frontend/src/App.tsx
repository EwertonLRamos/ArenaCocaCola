import { useEffect, useState } from 'react';
import * as signalR from '@microsoft/signalr';

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

  useEffect(() => {
    const newConnection = new signalR.HubConnectionBuilder()
      .withUrl("http://localhost:5000/arenaHub")
      .withAutomaticReconnect()
      .build();

    newConnection.start().then(() => {
      setConnection(newConnection);
      newConnection.on("UpdateGame", (state: GameState) => setGameState(state));
    });
  }, []);

  const startGame = () => fetch(`http://localhost:5000/api/game/start?playerName=${name}`, { method: 'POST' });

  // Estilo Coca-Cola UI
  const cocaRed = "#F40009";

  if (!gameState || gameState.isGameOver) {
    return (
      <div style={{ backgroundColor: cocaRed, height: '100vh', color: 'white', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', fontFamily: 'sans-serif' }}>
        <h1 style={{ fontSize: '3rem', marginBottom: '1rem' }}>Arena Coca-Cola</h1>
        {gameState?.isGameOver && <h2>FIM DE JOGO! Score: {gameState.score}</h2>}
        <input 
          placeholder="Nome do Jogador" 
          value={name} 
          onChange={e => setName(e.target.value)}
          style={{ padding: '15px', borderRadius: '25px', border: 'none', width: '250px', textAlign: 'center', fontSize: '1.2rem' }}
        />
        <button onClick={startGame} style={{ marginTop: '20px', padding: '15px 40px', borderRadius: '25px', border: '2px solid white', backgroundColor: 'transparent', color: 'white', fontWeight: 'bold', cursor: 'pointer', fontSize: '1.2rem' }}>
          START
        </button>
      </div>
    );
  }

  return (
    <div style={{ backgroundColor: cocaRed, height: '100vh', color: 'white', textAlign: 'center', paddingTop: '50px', fontFamily: 'sans-serif' }}>
      <header>
        <h2 style={{ opacity: 0.9 }}>JOGADOR: {gameState.playerName}</h2>
        <div style={{ fontSize: '8rem', fontWeight: '900', margin: '20px 0' }}>{gameState.score}</div>
        <div style={{ display: 'flex', justifyContent: 'center', gap: '15px' }}>
          {[...Array(3)].map((_, i) => (
            <div key={i} style={{ fontSize: '2rem', filter: i < gameState.lives ? 'none' : 'grayscale(100%)', opacity: i < gameState.lives ? 1 : 0.3 }}>
              🥤
            </div>
          ))}
        </div>
      </header>
    </div>
  );
}

export default App;