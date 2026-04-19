using Microsoft.EntityFrameworkCore;

var builder = WebApplication.CreateBuilder(args);

// 1. Configuração do Banco de Dados (SQLite)
builder.Services.AddDbContext<GameDbContext>(options =>
    options.UseSqlite("Data Source=arena.db"));

builder.Services.AddCors(options =>
{
    options.AddPolicy("AllowFrontend", policy =>
    {
        policy.WithOrigins("http://localhost:5173", "http://localhost:3000")
              .AllowAnyHeader()
              .AllowAnyMethod();
    });
});

builder.Services.AddAuthorization();

var app = builder.Build();

app.UseCors("AllowFrontend");
app.UseAuthorization();

// 2. Inicialização do Banco de Dados
// Isso cria o arquivo .db na raiz do projeto e garante que existe um estado inicial
using (var scope = app.Services.CreateScope())
{
    var db = scope.ServiceProvider.GetRequiredService<GameDbContext>();
    db.Database.EnsureCreated();
    
    if (!db.GameStates.Any())
    {
        db.GameStates.Add(new GameState { Id = 1, PlayerName = "Jogador", Score = 0, ActiveTarget = -1 });
        db.SaveChanges();
    }
}

// 3. Endpoints refatorados para usar o banco de dados
app.MapPost("/player", async (PlayerRequest request, GameDbContext db) =>
{
    var state = await db.GameStates.FindAsync(1);
    
    state!.PlayerName = request.Name;
    state.Score = 0;
    
    await db.SaveChangesAsync();
    return Results.Ok(state);
});

app.MapPost("/hit", async (HitRequest request, GameDbContext db) =>
{
    var state = await db.GameStates.FindAsync(1);
    
    if (/*request.TargetId == state!.ActiveTarget &&*/ request.Hit)
    {
        state!.Score += 10;
        await db.SaveChangesAsync();
    }

    return Results.Ok(new { state!.Score });
});

app.MapGet("/game", async (GameDbContext db) =>
{
    var state = await db.GameStates.FindAsync(1);
    return Results.Ok(state);
});

app.Run();


// Models
public class GameDbContext : DbContext
{
    public GameDbContext(DbContextOptions<GameDbContext> options) : base(options) { }
    
    public DbSet<GameState> GameStates { get; set; }
}

public class GameState
{
    public int Id { get; set; } // Necessário para o Entity Framework criar a tabela
    public string PlayerName { get; set; } = "Jogador";
    public int Score { get; set; } = 0;
    public int ActiveTarget { get; set; } = -1;
}

public class PlayerRequest
{
    public string Name { get; set; } = "Jogador";
}

public class HitRequest
{
    public int TargetId { get; set; }
    public bool Hit { get; set; }
}