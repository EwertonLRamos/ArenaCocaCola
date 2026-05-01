using Microsoft.AspNetCore.SignalR;
using Microsoft.EntityFrameworkCore;

var builder = WebApplication.CreateBuilder(args);

builder.Services.AddCors(options => options.AddPolicy("ArenaPolicy", 
    p => p.WithOrigins("http://localhost:5173").AllowAnyMethod().AllowAnyHeader().AllowCredentials()));

builder.Services.AddSignalR();
builder.Services.AddDbContext<ArenaContext>(opt => opt.UseSqlite("Data Source=arena.db"));

builder.Services.AddHttpClient("PythonHardware", client => 
{
    client.BaseAddress = new Uri("http://localhost:5010/"); 
});

var app = builder.Build();

app.UseCors("ArenaPolicy");

var gameState = new GameState();
CancellationTokenSource? gameTimerCts = null;

app.MapHub<ArenaHub>("/arenaHub");

app.MapPost("/api/game/start", async (string playerName, IHubContext<ArenaHub> hub, IHttpClientFactory httpClientFactory, ArenaContext db) => {
    
    await db.Database.EnsureDeletedAsync();
    await db.Database.EnsureCreatedAsync();

    gameState.Reset(playerName);
    gameTimerCts?.Cancel();
    gameTimerCts = new CancellationTokenSource();
    
    await hub.Clients.All.SendAsync("UpdateGame", gameState);
    
    try 
    {
        var client = httpClientFactory.CreateClient("PythonHardware");
        await client.PostAsync("iniciar", null);
    }
    catch (Exception ex)
    {
        Console.WriteLine($"Erro ao conectar com o hardware: {ex.Message}");
    }

    // Inicia task de contagem regressiva de 90 segundos
    _ = Task.Run(async () => await RunGameTimerAsync(gameState, hub, httpClientFactory, gameTimerCts.Token));

    return Results.Ok(new { message = "Jogo iniciado com temporizador de 90 segundos", player = playerName });
});

app.MapPost("/api/game/stop", async (IHubContext<ArenaHub> hub, IHttpClientFactory httpClientFactory) => {
    gameState.IsGameOver = true;
    await hub.Clients.All.SendAsync("UpdateGame", gameState);
    
    try 
    {
        var client = httpClientFactory.CreateClient("PythonHardware");
        await client.PostAsync("parar", null);
    }
    catch (Exception ex) 
    { 
        Console.WriteLine($"Erro ao parar o hardware: {ex.Message}"); 
    }

    return Results.Ok(new { message = "Jogo parado manualmente" });
});

app.MapPost("/api/game/hit", async (IHubContext<ArenaHub> hub) => {
    if (gameState.IsGameOver) return Results.BadRequest("Jogo finalizado");
    
    gameState.Score++;
    await hub.Clients.All.SendAsync("UpdateGame", gameState);
    return Results.Ok(gameState);
});

// Método auxiliar para execução da contagem regressiva
async Task RunGameTimerAsync(GameState state, IHubContext<ArenaHub> hub, IHttpClientFactory httpClientFactory, CancellationToken cancellationToken)
{
    try
    {
        while (!cancellationToken.IsCancellationRequested && !state.IsGameOver)
        {
            await Task.Delay(1000, cancellationToken);
            
            var elapsed = (DateTime.UtcNow - state.GameStartTime).TotalSeconds;
            state.TimeRemaining = Math.Max(0, GameState.GameDuration - (int)Math.Round(elapsed));
            
            await hub.Clients.All.SendAsync("UpdateGame", state, cancellationToken: cancellationToken);
            
            if (state.TimeRemaining <= 0)
            {
                state.IsGameOver = true;
                await hub.Clients.All.SendAsync("UpdateGame", state, cancellationToken: cancellationToken);
                
                try
                {
                    var client = httpClientFactory.CreateClient("PythonHardware");
                    await client.PostAsync("parar", null, cancellationToken);
                    Console.WriteLine("Hardware parado: tempo de 90 segundos expirou.");
                }
                catch (Exception ex)
                {
                    Console.WriteLine($"Erro ao parar hardware no timeout: {ex.Message}");
                }
                
                break;
            }
        }
    }
    catch (OperationCanceledException)
    {
        Console.WriteLine("Timer cancelado.");
    }
    catch (Exception ex)
    {
        Console.WriteLine($"Erro no timer de jogo: {ex.Message}");
    }
}

app.Run();

public class GameState {
    public string PlayerName { get; set; } = "";
    public int Score { get; set; } = 0;
    public int TimeRemaining { get; set; } = 90;
    public bool IsGameOver { get; set; } = false;
    public DateTime GameStartTime { get; set; } = DateTime.UtcNow;
    public const int GameDuration = 90;
    
    public void Reset(string name) 
    { 
        PlayerName = name; 
        Score = 0; 
        TimeRemaining = GameDuration; 
        IsGameOver = false; 
        GameStartTime = DateTime.UtcNow;
    }
}

public class ArenaHub : Hub { }

public class Player 
{ 
    public int Id { get; set; } 
    public string Name { get; set; } = ""; 
    public int Score { get; set; }
}

public class ArenaContext : DbContext 
{
    public ArenaContext(DbContextOptions<ArenaContext> options) : base(options) { }
    public DbSet<Player> Players => Set<Player>();
}