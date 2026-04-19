import { useEffect, useState } from "react";

interface GameState {
  playerName: string;
  score: number;
}

function App() {
  const [game, setGame] = useState<GameState>({
    playerName: "",
    score: 0
  });

  const [name, setName] = useState("");

  const API_URL = "http://192.168.4.2:5009";

  useEffect(() => {
    const interval = setInterval(() => {
      fetch(`${API_URL}/game`)
        .then(res => res.json())
        .then(data => setGame(data));
    }, 1000);

    return () => clearInterval(interval);
  }, []);

  const startGame = async () => {
    await fetch(`${API_URL}/player`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({ name })
    });
  };

  return (
    <div style={styles.container}>
      <h1 style={styles.title}>⚽ CHUTE AO ALVO</h1>

      <div style={styles.card}>
        <input
          placeholder="Nome do jogador"
          value={name}
          onChange={(e) => setName(e.target.value)}
          style={styles.input}
        />
        <button onClick={startGame} style={styles.button}>
          Iniciar
        </button>
      </div>

      <div style={styles.scoreBoard}>
        <h2>{game.playerName}</h2>
        <p style={styles.score}>{game.score}</p>
      </div>
    </div>
  );
}

const styles: any = {
  container: {
    height: "100vh",
    backgroundColor: "#E60012", // Coca-cola red
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    justifyContent: "center",
    color: "white",
    fontFamily: "Arial"
  },
  title: {
    fontSize: "48px",
    marginBottom: "20px"
  },
  card: {
    background: "white",
    padding: "20px",
    borderRadius: "10px",
    marginBottom: "30px"
  },
  input: {
    padding: "10px",
    marginRight: "10px"
  },
  button: {
    backgroundColor: "#E60012",
    color: "white",
    border: "none",
    padding: "10px 20px",
    cursor: "pointer"
  },
  scoreBoard: {
    textAlign: "center"
  },
  score: {
    fontSize: "80px",
    fontWeight: "bold"
  }
};

export default App;