using CounterStrikeSharp.API;
using CounterStrikeSharp.API.Core;
using CounterStrikeSharp.API.Core.Attributes;
using Clutchboard.Models;
using Clutchboard.Services;
using System.Text.Json;

namespace Clutchboard;

[MinimumApiVersion(80)]
public class ClutchboardPlugin : BasePlugin
{
    public override string ModuleName    => "Clutchboard";
    public override string ModuleVersion => "1.0.0";
    public override string ModuleAuthor  => "clutchboard";

    private ApiClient _api = null!;
    private string _matchId = string.Empty;
    private int _currentRound;
    private bool _matchStartSent;
    private readonly Dictionary<ulong, string> _playerTeams = new();

    public override void Load(bool hotReload)
    {
        var cfg = LoadConfig();
        _api = new ApiClient(cfg.ApiUrl, cfg.ApiSecret);

        RegisterEventHandler<EventRoundStart>(OnRoundStart);
        RegisterEventHandler<EventRoundEnd>(OnRoundEnd);
        RegisterEventHandler<EventCsWinPanelMatch>(OnMatchEnd);
        RegisterEventHandler<EventPlayerConnectFull>(OnPlayerConnect);
        RegisterEventHandler<EventPlayerDeath>(OnPlayerDeath);
        RegisterEventHandler<EventPlayerHurt>(OnPlayerHurt);
        RegisterEventHandler<EventFlashbangDetonate>(OnFlashDetonate);
        RegisterEventHandler<EventSmokegrenadeDetonate>(OnSmokeDetonate);
        RegisterEventHandler<EventMolotovDetonate>(OnMolotovDetonate);
        RegisterEventHandler<EventHegrenadeDetonate>(OnHeDetonate);
        RegisterEventHandler<EventWeaponFire>(OnWeaponFire);
        RegisterEventHandler<EventPlayerTeam>(OnPlayerTeam);
    }

    public override void Unload(bool hotReload)
    {
        _api.Dispose();
    }

    // ── Match lifecycle ───────────────────────────────────────────────────────

    public override void OnMapStart(string mapName)
    {
        _matchId = Guid.NewGuid().ToString();
        _currentRound = 0;
        _matchStartSent = false;
        _playerTeams.Clear();
    }

    private HookResult OnRoundStart(EventRoundStart @event, GameEventInfo _)
    {
        if (_matchId == string.Empty)
        {
            _matchId = Guid.NewGuid().ToString();
            _matchStartSent = false;
            _playerTeams.Clear();
        }

        if (!_matchStartSent)
        {
            _matchStartSent = true;
            EmitConnectedPlayers();
            _api.EnqueueEvent(new MatchStartEventDto
            {
                MatchId   = _matchId,
                MapName   = CurrentMapName(),
                StartedAt = DateTime.UtcNow.ToString("O"),
            });
        }

        _currentRound++;
        _api.EnqueueEvent(new RoundStartEventDto
        {
            MatchId     = _matchId,
            RoundNumber = _currentRound,
        });
        return HookResult.Continue;
    }

    private HookResult OnRoundEnd(EventRoundEnd @event, GameEventInfo _)
    {
        if (_matchId == string.Empty) return HookResult.Continue;
        _api.EnqueueEvent(new RoundEndEventDto
        {
            MatchId     = _matchId,
            RoundNumber = _currentRound,
            Winner      = @event.Winner == 2 ? "T" : "CT",
            WinReason   = @event.Reason switch
            {
                7  => "bomb_exploded",
                8  => "bomb_defused",
                12 => "time_expired",
                _  => "elimination",
            },
        });
        return HookResult.Continue;
    }

    private HookResult OnMatchEnd(EventCsWinPanelMatch @event, GameEventInfo _)
    {
        if (_matchId == string.Empty) return HookResult.Continue;
        var teams = _playerTeams.ToDictionary(kv => kv.Key.ToString(), kv => kv.Value);
        _api.EnqueueEvent(new MatchEndEventDto
        {
            MatchId     = _matchId,
            TScore      = 0, // TODO: read from game state
            CtScore     = 0,
            PlayerTeams = teams,
        });
        _playerTeams.Clear();
        _matchId = string.Empty;
        return HookResult.Continue;
    }

    // ── Player events ─────────────────────────────────────────────────────────

    private static ulong SteamId(CCSPlayerController p) =>
        p.AuthorizedSteamID?.SteamId64 ?? p.SteamID;

    private static bool IsBot(CCSPlayerController p) => p.IsBot;

    // Returns false when steam auth hasn't resolved yet — avoids FK violations on the players table.
    private static bool HasSteamId(CCSPlayerController p) => SteamId(p) != 0UL;

    private void EmitConnectedPlayers()
    {
        foreach (var p in Utilities.GetPlayers())
        {
            if (p == null || !p.IsValid || IsBot(p) || !HasSteamId(p)) continue;
            _api.EnqueueEvent(new PlayerConnectEventDto
            {
                SteamId     = (long)SteamId(p),
                DisplayName = p.PlayerName,
            });
        }
    }

    private static string CurrentMapName()
    {
        var bspName = Server.MapName;
        // Workshop maps live at <gameDir>/maps/workshop/<workshopId>/<bsp>.bsp.
        // Scan to find which workshop folder owns the current BSP so the API can
        // resolve the real display name from Steam Workshop.
        try
        {
            var workshopDir = Path.Combine(Server.GameDirectory, "maps", "workshop");
            if (Directory.Exists(workshopDir))
            {
                foreach (var dir in Directory.EnumerateDirectories(workshopDir))
                {
                    if (File.Exists(Path.Combine(dir, bspName + ".bsp")))
                        return $"workshop/{Path.GetFileName(dir)}/{bspName}";
                }
            }
        }
        catch { /* non-critical */ }
        return bspName;
    }

    private HookResult OnPlayerConnect(EventPlayerConnectFull @event, GameEventInfo _)
    {
        var p = @event.Userid;
        if (p == null || !p.IsValid || IsBot(p)) return HookResult.Continue;
        _api.EnqueueEvent(new PlayerConnectEventDto
        {
            SteamId     = (long)SteamId(p),
            DisplayName = p.PlayerName,
        });
        return HookResult.Continue;
    }

    private HookResult OnPlayerTeam(EventPlayerTeam @event, GameEventInfo _)
    {
        var p = @event.Userid;
        if (p == null || !p.IsValid || IsBot(p)) return HookResult.Continue;
        var sid = SteamId(p);
        // Team 3 = CT, Team 2 = T, Team 0 = Unassigned, Team 1 = Spectator
        if (@event.Team is 2 or 3)
            _playerTeams[sid] = @event.Team == 3 ? "CT" : "T";
        else
            _playerTeams.Remove(sid);
        return HookResult.Continue;
    }

    private HookResult OnPlayerDeath(EventPlayerDeath @event, GameEventInfo _)
    {
        if (_matchId == string.Empty) return HookResult.Continue;
        var victim = @event.Userid;
        if (victim == null || !victim.IsValid || IsBot(victim) || !HasSteamId(victim)) return HookResult.Continue;
        var killer   = @event.Attacker;
        var assister = @event.Assister;
        _api.EnqueueEvent(new KillEventDto
        {
            MatchId         = _matchId,
            RoundNumber     = _currentRound,
            KillerSteamId   = killer?.IsValid   == true ? (long?)SteamId(killer)   : null,
            VictimSteamId   = (long)SteamId(victim),
            AssisterSteamId = assister?.IsValid == true ? (long?)SteamId(assister) : null,
            Weapon          = @event.Weapon,
            Headshot        = @event.Headshot,
            Penetrated      = @event.Penetrated > 0,
            Noscope         = @event.Noscope,
            Thrusmoke       = @event.Thrusmoke,
        });
        return HookResult.Continue;
    }

    private HookResult OnPlayerHurt(EventPlayerHurt @event, GameEventInfo _)
    {
        if (_matchId == string.Empty) return HookResult.Continue;
        var victim = @event.Userid;
        if (victim == null || !victim.IsValid || IsBot(victim) || !HasSteamId(victim)) return HookResult.Continue;
        var attacker = @event.Attacker;
        _api.EnqueueEvent(new DamageEventDto
        {
            MatchId          = _matchId,
            RoundNumber      = _currentRound,
            AttackerSteamId  = attacker?.IsValid == true ? (long?)SteamId(attacker) : null,
            VictimSteamId    = (long)SteamId(victim),
            Weapon           = @event.Weapon,
            Damage           = @event.DmgHealth,
            DamageArmor      = @event.DmgArmor,
            Hitgroup         = @event.Hitgroup.ToString(),
        });
        return HookResult.Continue;
    }

    // ── Utility events ────────────────────────────────────────────────────────

    private HookResult OnFlashDetonate(EventFlashbangDetonate @event, GameEventInfo _)
    {
        // Individual player blind durations arrive via EventPlayerBlind — not yet implemented.
        // TODO: Register EventPlayerBlind to emit FlashEventDto per blinded player.
        return HookResult.Continue;
    }

    private HookResult OnSmokeDetonate(EventSmokegrenadeDetonate @event, GameEventInfo _)
    {
        EmitUtility(@event.Userid, "smoke_start");
        return HookResult.Continue;
    }

    private HookResult OnMolotovDetonate(EventMolotovDetonate @event, GameEventInfo _)
    {
        EmitUtility(@event.Userid, "molotov_detonate");
        return HookResult.Continue;
    }

    private HookResult OnHeDetonate(EventHegrenadeDetonate @event, GameEventInfo _)
    {
        EmitUtility(@event.Userid, "he_detonate");
        return HookResult.Continue;
    }

    private void EmitUtility(CCSPlayerController? player, string eventType)
    {
        if (_matchId == string.Empty || player == null || !player.IsValid) return;
        _api.EnqueueEvent(new UtilityEventDto
        {
            MatchId     = _matchId,
            RoundNumber = _currentRound,
            SteamId     = (long)SteamId(player),
            EventType   = eventType,
        });
    }

    private HookResult OnWeaponFire(EventWeaponFire @event, GameEventInfo _)
    {
        if (_matchId == string.Empty) return HookResult.Continue;
        var p = @event.Userid;
        if (p == null || !p.IsValid) return HookResult.Continue;
        _api.EnqueueEvent(new WeaponFireEventDto
        {
            MatchId     = _matchId,
            RoundNumber = _currentRound,
            SteamId     = (long)SteamId(p),
            Weapon      = @event.Weapon,
        });
        return HookResult.Continue;
    }

    // ── Config ────────────────────────────────────────────────────────────────

    private PluginConfig LoadConfig()
    {
        var path = Path.Combine(ModuleDirectory, "config.json");
        if (!File.Exists(path))
        {
            var defaults = new PluginConfig();
            File.WriteAllText(path, JsonSerializer.Serialize(defaults, new JsonSerializerOptions { WriteIndented = true }));
            return defaults;
        }
        return JsonSerializer.Deserialize<PluginConfig>(File.ReadAllText(path)) ?? new PluginConfig();
    }
}
