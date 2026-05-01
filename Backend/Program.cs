using Microsoft.AspNetCore.SignalR;
using Microsoft.EntityFrameworkCore;

var builder = WebApplication.CreateBuilder(args);

// Configuração de CORS para o React
builder.Services.AddCors(options => options.AddPolicy("ArenaPolicy", 
    p => p.WithOrigins("http://localhost:5173").AllowAnyMethod().AllowAnyHeader().AllowCredentials()));

builder.Services.AddSignalR();
builder.Services.AddDbContext<ArenaContext>(opt => opt.UseSqlite("Data Source=arena.db"));

// 1. Registrando o HttpClient para a API se comunicar com o hardware (Python)
builder.Services.AddHttpClient("PythonHardware", client => 
{
    // IMPORTANTE: Se o script Python estiver rodando em outra máquina (ex: um Raspberry Pi), 
    // substitua localhost pelo IP do hardware na rede (ex: http://192.168.1.100:5010/)
    client.BaseAddress = new Uri("http://localhost:5010/"); 
});

var app = builder.Build();

// using (var scope = app.Services.CreateScope())
// {
//     var db = scope.ServiceProvider.GetRequiredService<ArenaContext>();
//     db.Database.EnsureCreated();
// }

app.UseCors("ArenaPolicy");

var gameState = new GameState();

app.MapHub<ArenaHub>("/arenaHub");

// 2. Modificado para avisar o Python quando o jogo começar
app.MapPost("/api/game/start", async (string playerName, IHubContext<ArenaHub> hub, IHttpClientFactory httpClientFactory, ArenaContext db) => {
    
    // 1. Garante que qualquer banco residual seja apagado e um novo seja criado limpo
    await db.Database.EnsureDeletedAsync();
    await db.Database.EnsureCreatedAsync();

    gameState.Reset(playerName);
    
    // Avisa o React via SignalR
    await hub.Clients.All.SendAsync("UpdateGame", gameState);
    
    // Dispara o comando para o hardware Python iniciar
    try 
    {
        var client = httpClientFactory.CreateClient("PythonHardware");
        await client.PostAsync("iniciar", null);
    }
    catch (Exception ex)
    {
        Console.WriteLine($"Erro ao conectar com o hardware: {ex.Message}");
    }

    return Results.Ok(new { message = "Jogo iniciado e banco de dados recriado", player = playerName });
});

// 3. Novo endpoint caso precise forçar a parada do hardware no meio do jogo
app.MapPost("/api/game/stop", async (IHubContext<ArenaHub> hub, IHttpClientFactory httpClientFactory) => {
    gameState.IsGameOver = true;
    await hub.Clients.All.SendAsync("UpdateGame", gameState);
    
    try 
    {
        var client = httpClientFactory.CreateClient("PythonHardware");
        await client.PostAsync("parar", null);
    }
    catch (Exception ex) { Console.WriteLine($"Erro ao parar o hardware: {ex.Message}"); }

    return Results.Ok(new { message = "Jogo parado manualmente" });
});

app.MapPost("/api/game/hit", async (IHubContext<ArenaHub> hub) => {
    if (gameState.IsGameOver) return Results.BadRequest("Jogo finalizado");
    
    gameState.Score++;
    await hub.Clients.All.SendAsync("UpdateGame", gameState);
    return Results.Ok(gameState);
});

// 4. Mantido igual. O retorno Ok(gameState) enviará "isGameOver": true ou false.
app.MapPost("/api/game/miss", async (IHubContext<ArenaHub> hub, ArenaContext db) => {
    if (gameState.IsGameOver) return Results.BadRequest("Jogo finalizado");

    gameState.Lives--;
    if (gameState.Lives <= 0) {
        gameState.IsGameOver = true;
        
        // 2. Destrói o banco de dados assim que o Game Over é decretado
        try 
        {
            await db.Database.EnsureDeletedAsync();
            Console.WriteLine("Game Over: Banco de dados excluído com sucesso.");
        }
        catch (Exception ex)
        {
            Console.WriteLine($"Erro ao excluir o banco: {ex.Message}");
        }
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