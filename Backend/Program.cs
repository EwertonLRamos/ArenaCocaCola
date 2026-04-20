using Microsoft.AspNetCore.SignalR;
using Microsoft.EntityFrameworkCore;

var builder = WebApplication.CreateBuilder(args);

// Configuração de CORS para o React
builder.Services.AddCors(options => options.AddPolicy("ArenaPolicy", 
    p => p.WithOrigins("http://localhost:5173").AllowAnyMethod().AllowAnyHeader().AllowCredentials()));

builder.Services.AddSignalR();
builder.Services.AddDbContext<ArenaContext>(opt => opt.UseSqlite("Data Source=arena.db"));

var app = builder.Build();

app.UseCors("ArenaPolicy");

// Gerenciamento de estado simples (Singleton para a Arena)
var gameState = new GameState();

// Hub do SignalR
app.MapHub<ArenaHub>("/arenaHub");

// Endpoints da API
app.MapPost("/api/game/start", async (string playerName, IHubContext<ArenaHub> hub) => {
    gameState.Reset(playerName);
    await hub.Clients.All.SendAsync("UpdateGame", gameState);
    return Results.Ok(new { message = "Jogo iniciado", player = playerName });
});

app.MapPost("/api/game/hit", async (IHubContext<ArenaHub> hub) => {
    if (gameState.IsGameOver) return Results.BadRequest("Jogo finalizado");
    
    gameState.Score++;
    await hub.Clients.All.SendAsync("UpdateGame", gameState);
    return Results.Ok(gameState);
});

app.MapPost("/api/game/miss", async (IHubContext<ArenaHub> hub, ArenaContext db) => {
    if (gameState.IsGameOver) return Results.BadRequest("Jogo finalizado");

    gameState.Lives--;
    if (gameState.Lives <= 0) {
        gameState.IsGameOver = true;
        // Salvar no Ranking (SQLite)
        db.Players.Add(new Player { Name = gameState.PlayerName, Score = gameState.Score });
        await db.SaveChangesAsync();
    }
    
    await hub.Clients.All.SendAsync("UpdateGame", gameState);
    return Results.Ok(gameState);
});

app.Run();

// Modelos e Infra
public class GameState {
    public string PlayerName { get; set; } = "";
    public int Score { get; set; } = 0;
    public int Lives { get; set; } = 3;
    public bool IsGameOver { get; set; } = false;
    public void Reset(string name) { PlayerName = name; Score = 0; Lives = 3; IsGameOver = false; }
}

public class ArenaHub : Hub { }
public class Player { public int Id { get; set; } public string Name { get; set; } = ""; public int Score { get; set; } }
public class ArenaContext : DbContext {
    public ArenaContext(DbContextOptions<ArenaContext> options) : base(options) { }
    public DbSet<Player> Players => Set<Player>();
}